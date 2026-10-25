"""Copia los datos del esquema MySQL `kompas` a MongoDB (se usa una sola vez).

Uso (desde backend/, con el venv activo):
    pip install -r requirements-migracion.txt
    set MYSQL_URL=mysql+pymysql://root:pass@localhost:3306/kompas      # PowerShell: $env:MYSQL_URL="..."
    python -m scripts.migrar_mysql_a_mongo [--limpiar]

- Lee MySQL con consultas `text()` (no usa modelos ORM) y escribe en MONGO_URI / MONGO_DB.
- Conserva los ids, junta `residencia` dentro del usuario, convierte el LINESTRING a GeoJSON y
  lat/lng de los lugares a Point.
- Un trazo que no sea GeoJSON válido se reporta y se omite (no se trunca ni se inventa).
- Idempotente: con --limpiar vacía las colecciones antes; sin él usa replace_one(..., upsert=True).
- Al final imprime la tabla comparativa MySQL vs MongoDB.

Lo que MySQL no guardaba (contexto, presupuesto y evaluación de los planes) NO se inventa: se omite.
"""

import argparse
import os
import re
import sys
from datetime import date, datetime, time

from pymongo.database import Database

from app.compartido.texto import INTERESES, MOVILIDADES, clave
from app.nucleo.bd import ZONA_HORARIA, get_bd
from scripts.preparar_bd import ajustar_contadores, crear_colecciones

# tabla MySQL → colección MongoDB (para la tabla comparativa)
EQUIVALENCIAS = [
    ("usuarios", "usuarios"),
    ("residencia", "usuarios.residencia"),
    ("categorias", "categorias"),
    ("transportes", "transportes"),
    ("lugares_de_interes", "lugares"),
    ("rutas", "rutas"),
    ("historial_rutas", "historial_rutas"),
    ("planes", "planes"),
]


def con_zona(valor: datetime | date | None) -> datetime | None:
    """MySQL guarda hora local sin zona: se le pone America/Mexico_City."""
    if valor is None:
        return None
    if not isinstance(valor, datetime):
        valor = datetime.combine(valor, time.min)
    return valor.replace(tzinfo=ZONA_HORARIA) if valor.tzinfo is None else valor


def tiempos(fila: dict) -> dict:
    return {c: con_zona(fila.get(c)) for c in ("created_at", "updated_at", "deleted_at")}


def wkt_a_coordenadas(wkt: str | bytes | None) -> list[list[float]] | None:
    """'LINESTRING(-99.49 19.28, ...)' → [[-99.49, 19.28], ...]. None si no es un LineString válido."""
    if wkt is None:
        return None
    if isinstance(wkt, bytes):
        wkt = wkt.decode()
    encontrado = re.fullmatch(r"\s*LINESTRING\s*\((.*)\)\s*", wkt, re.IGNORECASE)
    if not encontrado:
        return None
    try:
        coordenadas = [[float(n) for n in par.split()] for par in encontrado.group(1).split(",")]
    except ValueError:
        return None
    validas = all(len(p) == 2 and -180 <= p[0] <= 180 and -90 <= p[1] <= 90 for p in coordenadas)
    return coordenadas if validas and len(coordenadas) >= 2 else None


class Migracion:
    def __init__(self, conexion, bd: Database, limpiar: bool):
        self.conexion = conexion
        self.bd = bd
        self.limpiar = limpiar
        self.problemas: list[str] = []

    def filas(self, sql: str) -> list[dict]:
        from sqlalchemy import text

        return [dict(f._mapping) for f in self.conexion.execute(text(sql))]

    def guardar(self, coleccion: str, docs: list[dict]) -> None:
        if self.limpiar:
            self.bd[coleccion].delete_many({})
            if docs:
                self.bd[coleccion].insert_many(docs)
            return
        for doc in docs:
            self.bd[coleccion].replace_one({"_id": doc["_id"]}, doc, upsert=True)

    def catalogos(self) -> tuple[dict, dict]:
        categorias = {
            f["id_categoria"]: {"_id": f["id_categoria"], "nombre": f["nombre"], "descripcion": f["descripcion"], **tiempos(f)}
            for f in self.filas("SELECT * FROM categorias")
        }
        transportes = {
            f["id_transporte"]: {"_id": f["id_transporte"], "nombre": f["nombre"], **tiempos(f)}
            for f in self.filas("SELECT * FROM transportes")
        }
        self.guardar("categorias", list(categorias.values()))
        self.guardar("transportes", list(transportes.values()))
        return categorias, transportes

    def usuarios(self) -> None:
        residencias = {}
        for r in self.filas("SELECT * FROM residencia WHERE deleted_at IS NULL ORDER BY id_residencia"):
            # Si un usuario tuviera varias, se conserva la primera (la misma que leía la API)
            residencias.setdefault(
                r["id_usuario"],
                {"id": r["id_residencia"], **{c: r[c] for c in ("calle", "numero_interior", "numero_exterior", "municipio", "colonia", "estado")}},
            )
        docs = [
            {
                "_id": u["id_usuario"],
                "nombre": u["nombre"],
                "primer_apellido": u["primer_apellido"],
                "segundo_apellido": u["segundo_apellido"],
                "correo": u["correo"],
                "password": u["password"],
                "fecha_nacimiento": con_zona(u["fecha_nacimiento"]),
                "rol": "usuario",  # MySQL no tenía roles; usar scripts/crear_admin.py
                "residencia": residencias.get(u["id_usuario"]),
                **tiempos(u),
            }
            for u in self.filas("SELECT * FROM usuarios")
        ]
        self.guardar("usuarios", docs)

    def lugares(self, categorias: dict) -> None:
        docs = []
        for l in self.filas("SELECT * FROM lugares_de_interes"):
            categoria = categorias.get(l["id_cat"])
            docs.append(
                {
                    "_id": l["id_lugar"],
                    "nombre": l["nombre"],
                    "ubicacion": {"type": "Point", "coordinates": [float(l["longitud"]), float(l["latitud"])]},
                    "categoria": {"id": l["id_cat"], "nombre": categoria["nombre"] if categoria else None},
                    "id_usuario": l["id_usuario"],
                    **tiempos(l),
                }
            )
        self.guardar("lugares", docs)

    def rutas(self) -> None:
        try:  # MySQL 8 con SRID 4326 usa lat-lng por defecto: se pide lng-lat como GeoJSON
            filas = self.filas("SELECT id_ruta, ST_AsText(ruta, 'axis-order=long-lat') AS wkt, created_at, updated_at, deleted_at FROM rutas")
        except Exception:  # noqa: BLE001 — MariaDB no acepta axis-order y guarda x, y tal cual
            self.conexion.rollback()
            filas = self.filas("SELECT id_ruta, ST_AsText(ruta) AS wkt, created_at, updated_at, deleted_at FROM rutas")
        docs = []
        for r in filas:
            coordenadas = wkt_a_coordenadas(r["wkt"])
            if coordenadas is None:
                self.problemas.append(f"rutas.id_ruta={r['id_ruta']}: el trazo no es un LineString GeoJSON válido; se omitió.")
                continue
            docs.append({"_id": r["id_ruta"], "trazo": {"type": "LineString", "coordinates": coordenadas}, **tiempos(r)})
        self.guardar("rutas", docs)

    def historial(self, transportes: dict) -> None:
        docs = [
            {
                "_id": h["id_historial"],
                "id_usuario": h["id_usuario"],
                "id_ruta": h["id_ruta"],
                "transporte": {"id": h["id_transporte"], "nombre": transportes.get(h["id_transporte"], {}).get("nombre")},
                "tiempo_estimado": h["tiempo_estimado"],
                **tiempos(h),
            }
            for h in self.filas("SELECT * FROM historial_rutas")
        ]
        self.guardar("historial_rutas", docs)

    def planes(self, categorias: dict, transportes: dict) -> None:
        docs = []
        for p in self.filas("SELECT * FROM planes"):
            categoria = categorias.get(p["id_categoria"], {}).get("nombre")
            transporte = transportes.get(p["id_transporte"], {}).get("nombre")
            fecha = con_zona(p["fecha_plan"])
            doc = {
                "_id": p["id_plan"],
                "id_usuario": p["id_usuario"],
                "no_acompanantes": p["no_acompanantes"],
                "tiempo_disponible": p["tiempo_disponible"],
                "categoria": {"id": p["id_categoria"], "nombre": categoria},
                "transporte": {"id": p["id_transporte"], "nombre": transporte},
                # MySQL solo guardaba una categoría y un transporte: son el primer interés y la primera movilidad
                "intereses": [clave(categoria)] if categoria and clave(categoria) in INTERESES else [],
                "movilidad": [clave(transporte)] if transporte and clave(transporte) in MOVILIDADES else [],
                "fecha_plan": fecha,
                "hora_salida": fecha.strftime("%H:%M") if fecha else None,
                **tiempos(p),
            }
            docs.append(doc)
        self.guardar("planes", docs)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limpiar", action="store_true", help="vacía las colecciones destino antes de copiar")
    args = parser.parse_args()
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    url = os.environ.get("MYSQL_URL")
    if not url:
        sys.exit("Falta la variable MYSQL_URL (ej. mysql+pymysql://root:pass@localhost:3306/kompas).")
    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        sys.exit("Instala las dependencias de migración: pip install -r requirements-migracion.txt")

    bd = get_bd()
    crear_colecciones(bd)
    motor = create_engine(url)
    with motor.connect() as conexion:
        migracion = Migracion(conexion, bd, args.limpiar)
        categorias, transportes = migracion.catalogos()
        migracion.usuarios()
        migracion.lugares(categorias)
        migracion.rutas()
        migracion.historial(transportes)
        migracion.planes(categorias, transportes)
        conteo_mysql = {t: conexion.execute(text(f"SELECT COUNT(*) FROM `{t}`")).scalar() for t, _ in EQUIVALENCIAS}
    motor.dispose()
    ajustar_contadores(bd)

    conteo_mongo = {c: bd[c].count_documents({}) for _, c in EQUIVALENCIAS if "." not in c}
    conteo_mongo["usuarios.residencia"] = bd.usuarios.count_documents({"residencia": {"$ne": None}})
    print(f"\nMigración MySQL → MongoDB (base `{bd.name}`)\n")
    print(f"{'Tabla MySQL':<20}{'Registros':>10}   {'Colección MongoDB':<22}{'Documentos':>10}")
    print("-" * 66)
    for tabla, coleccion in EQUIVALENCIAS:
        print(f"{tabla:<20}{conteo_mysql[tabla]:>10}   {coleccion:<22}{conteo_mongo[coleccion]:>10}")
    if migracion.problemas:
        print("\nRegistros omitidos:")
        for problema in migracion.problemas:
            print(f"  - {problema}")


if __name__ == "__main__":
    main()
