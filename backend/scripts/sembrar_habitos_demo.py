"""Genera recorridos SINTÉTICOS con rutinas para entrenar y probar el asistente de machine learning.

Todo lo que crea lleva `demo: true` (el dashboard lo excluye salvo que se pida incluirlo).

Uso (desde backend/, con el venv activo y la base ya preparada con scripts.preparar_bd):
    python -m scripts.sembrar_habitos_demo                 # 12 semanas, 3 usuarios con rutinas distintas
    python -m scripts.sembrar_habitos_demo --semanas 20
    python -m scripts.sembrar_habitos_demo --borrar        # borra recorridos, usuarios y rutas demo de este script

- Esquema real de `historial_rutas` (id_usuario, id_ruta, transporte {id, nombre}, tiempo_estimado).
- Si la base tiene menos de 5 rutas, crea 5 rutas "Demo · …" (trazos de referencia, NO líneas reales).
- Usuarios: demo@kompas.mx (estudiante) y habitos.oficina@ / habitos.nocturno@kompas.mx (contraseña
  aleatoria que nadie conoce). Cada uno tiene su propia rutina: el modelo debe aprender la de cada quien.
- ~10 % de días tienen un viaje fuera de rutina (ruido) para que la validación no sea trivial.
- Semilla fija: la demo es reproducible. Correrlo dos veces primero borra lo anterior de este script.
"""

import argparse
import random
import secrets
import sys
from datetime import timedelta

from pymongo.database import Database

from app.compartido.geo import distancia_por_calles_km, esta_dentro_de_zona
from app.nucleo.bd import ZONA_HORARIA, ahora, get_bd, siguiente_id
from app.nucleo.seguridad import hash_password
from scripts.preparar_bd import ajustar_contadores
from scripts.sembrar_actividad_demo import densificar

SEMILLA = 31
ORIGEN_DEMO = "habitos"  # marca de este script (las rutas y usuarios demo de otros scripts no se tocan)
MIN_POR_KM = {"Transporte público": 5, "Taxi/App": 2.6, "Caminando": 12}
PROBABILIDAD_RUIDO = 0.10

# Trazos de referencia [lng, lat] dentro de la zona piloto. Son datos demo: no son líneas reales.
RUTAS_DEMO = [
    ("Demo · Centro de Toluca – UTVT", [[-99.656, 19.292], [-99.60, 19.292], [-99.53, 19.30], [-99.466, 19.331]], ("Centro de Toluca", "UTVT")),
    ("Demo · UTVT – Centro de Lerma", [[-99.466, 19.331], [-99.49, 19.31], [-99.5115, 19.285]], ("UTVT", "Centro de Lerma")),
    ("Demo · Centro de Toluca – Metepec", [[-99.656, 19.292], [-99.63, 19.27], [-99.605, 19.255]], ("Centro de Toluca", "Metepec")),
    ("Demo · Toluca – San Mateo Atenco", [[-99.656, 19.292], [-99.60, 19.28], [-99.5335, 19.2675]], ("Centro de Toluca", "San Mateo Atenco")),
    ("Demo · Toluca oriente", [[-99.656, 19.292], [-99.635, 19.287], [-99.61, 19.28]], ("Centro de Toluca", "Toluca oriente")),
]

# (índice de ruta, días de la semana 0=lunes, hora mínima, hora máxima, transporte, probabilidad de que ocurra)
PERFILES = {
    "demo@kompas.mx": [  # estudiante de la UTVT
        (0, range(0, 5), 6.5, 7.5, "Transporte público", 0.9),
        (1, range(0, 5), 14.5, 16.0, "Transporte público", 0.8),
        (2, (4, 5), 18.5, 21.0, "Taxi/App", 0.7),
        (3, (6,), 10.0, 12.5, "Transporte público", 0.6),
        (4, (0, 2), 19.5, 20.5, "Caminando", 0.6),
    ],
    "habitos.oficina@kompas.mx": [  # trabaja en Toluca oriente y regresa a Metepec
        (4, range(0, 5), 8.0, 9.0, "Transporte público", 0.9),
        (2, range(0, 5), 18.0, 19.5, "Transporte público", 0.85),
        (3, (5,), 11.0, 13.0, "Taxi/App", 0.6),
    ],
    "habitos.nocturno@kompas.mx": [  # sale de noche y los sábados va a Lerma
        (2, (1, 3), 21.0, 22.5, "Taxi/App", 0.8),
        (1, (5,), 9.0, 11.0, "Transporte público", 0.7),
        (0, (4,), 16.0, 17.5, "Transporte público", 0.6),
    ],
}


def minutos_de(ruta: dict, transporte: str) -> int:
    coords = ruta["trazo"]["coordinates"]
    km = distancia_por_calles_km({"lat": coords[0][1], "lng": coords[0][0]}, {"lat": coords[-1][1], "lng": coords[-1][0]})
    return min(24 * 60, max(3, round(km * MIN_POR_KM[transporte] * random.uniform(0.85, 1.25))))


def asegurar_rutas(bd: Database) -> list[dict]:
    """Las primeras 5 rutas de la base; si faltan, crea las rutas demo de este script."""
    rutas = list(bd.rutas.find({"deleted_at": None}).sort("_id", 1).limit(len(RUTAS_DEMO)))
    if len(rutas) >= len(RUTAS_DEMO):
        return rutas
    momento = ahora()
    for nombre, puntos, (inicio, fin) in RUTAS_DEMO[len(rutas):]:
        if not all(esta_dentro_de_zona({"lat": lat, "lng": lng}) for lng, lat in puntos):
            sys.exit(f"La ruta demo {nombre} queda fuera de la zona piloto.")
        doc = {
            "_id": siguiente_id(bd, "rutas"),
            "trazo": {"type": "LineString", "coordinates": densificar(puntos)},
            "nombre": nombre,
            "paradas": [
                {"nombre": inicio, "ubicacion": {"type": "Point", "coordinates": puntos[0]}},
                {"nombre": fin, "ubicacion": {"type": "Point", "coordinates": puntos[-1]}},
            ],
            "demo": True,
            "origen_demo": ORIGEN_DEMO,
            "created_at": momento,
            "updated_at": momento,
            "deleted_at": None,
        }
        bd.rutas.insert_one(doc)
        rutas.append(doc)
    return rutas


def asegurar_usuario(bd: Database, correo: str) -> int:
    usuario = bd.usuarios.find_one({"correo": correo, "deleted_at": None})
    if usuario:
        return usuario["_id"]
    momento = ahora()
    doc = {
        "_id": siguiente_id(bd, "usuarios"),
        "nombre": "Hábitos",
        "primer_apellido": correo.split("@")[0].split(".")[-1].capitalize(),
        "segundo_apellido": None,
        "correo": correo,
        "password": hash_password(secrets.token_urlsafe(24)),
        "fecha_nacimiento": momento.replace(year=2003, month=5, day=10, hour=0, minute=0, second=0, microsecond=0),
        "rol": "usuario",
        "residencia": None,
        "demo": True,
        "origen_demo": ORIGEN_DEMO,
        "created_at": momento,
        "updated_at": momento,
        "deleted_at": None,
    }
    bd.usuarios.insert_one(doc)
    return doc["_id"]


def _recorrido(bd: Database, id_usuario: int, ruta: dict, transporte: dict, momento) -> dict:
    return {
        "_id": siguiente_id(bd, "historial_rutas"),
        "id_usuario": id_usuario,
        "id_ruta": ruta["_id"],
        "transporte": {"id": transporte["_id"], "nombre": transporte["nombre"]},
        "tiempo_estimado": minutos_de(ruta, transporte["nombre"]),
        "demo": True,
        "origen_demo": ORIGEN_DEMO,
        "created_at": momento,
        "updated_at": momento,
        "deleted_at": None,
    }


def sembrar(bd: Database, semanas: int) -> dict[str, int]:
    random.seed(SEMILLA)
    transportes = {t["nombre"]: t for t in bd.transportes.find({"deleted_at": None})}
    if any(nombre not in transportes for nombre in MIN_POR_KM):
        sys.exit("Faltan transportes: corre primero python -m scripts.preparar_bd")
    rutas = asegurar_rutas(bd)

    hoy = ahora().astimezone(ZONA_HORARIA).replace(hour=0, minute=0, second=0, microsecond=0)
    conteo = {}
    for correo, rutina in PERFILES.items():
        id_usuario = asegurar_usuario(bd, correo)
        docs = []
        for dias_atras in range(semanas * 7, 0, -1):
            dia = hoy - timedelta(days=dias_atras)
            for indice, dias, desde, hasta, nombre, probabilidad in rutina:
                if dia.weekday() in dias and random.random() <= probabilidad:
                    momento = dia + timedelta(hours=random.uniform(desde, hasta))
                    docs.append(_recorrido(bd, id_usuario, rutas[indice], transportes[nombre], momento))
            if random.random() < PROBABILIDAD_RUIDO:  # viaje fuera de rutina
                momento = dia + timedelta(hours=random.uniform(6, 22))
                docs.append(_recorrido(bd, id_usuario, random.choice(rutas), transportes["Transporte público"], momento))
        if docs:
            bd.historial_rutas.insert_many(docs)
        conteo[correo] = len(docs)
    ajustar_contadores(bd)
    return conteo


def borrar(bd: Database) -> dict[str, int]:
    filtro = {"demo": True, "origen_demo": ORIGEN_DEMO}
    return {c: bd[c].delete_many(filtro).deleted_count for c in ("historial_rutas", "usuarios", "rutas")}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--semanas", type=int, default=12)
    parser.add_argument("--borrar", action="store_true", help="borra lo que creó este script")
    args = parser.parse_args()
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    bd = get_bd()
    if args.borrar:
        print(f"Datos demo de hábitos borrados de `{bd.name}`: {borrar(bd)}")
        return
    if args.semanas < 1:
        sys.exit("--semanas debe ser mayor que 0.")
    # Reproducible: lo anterior de este script se reemplaza (los recorridos, no las rutas ni los usuarios)
    bd.historial_rutas.delete_many({"demo": True, "origen_demo": ORIGEN_DEMO})
    conteo = sembrar(bd, args.semanas)
    print(f"Recorridos demo en `{bd.name}` (demo: true), {args.semanas} semanas:")
    for correo, total in conteo.items():
        print(f"  {correo:<30}{total:>5}")


if __name__ == "__main__":
    main()
