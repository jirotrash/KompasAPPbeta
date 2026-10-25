"""Crea la base de MongoDB: colecciones, validadores $jsonSchema, índices y datos de desarrollo.

Uso (desde backend/, con el venv activo):
    python -m scripts.preparar_bd              # crea lo que falte; carga datos de desarrollo si está vacía
    python -m scripts.preparar_bd --recrear    # BORRA la base MONGO_DB y la crea de nuevo
    python -m scripts.preparar_bd --sin-datos  # solo colecciones e índices

Toma la conexión de MONGO_URI y el nombre de la base de MONGO_DB, así que sirve igual para MongoDB
local, para Atlas y para la base de pruebas (kompas_test).
"""

import argparse
import json
import sys
from pathlib import Path

from pymongo import ASCENDING, DESCENDING, GEOSPHERE, IndexModel
from pymongo.database import Database

CARPETA_BD = Path(__file__).resolve().parent.parent / "database"
DATOS = "datos_desarrollo.json"

_ID_ENTERO = {"bsonType": ["int", "long"]}
_TEXTO = {"bsonType": "string"}
_TEXTO_O_NULO = {"bsonType": ["string", "null"]}
_FECHA_O_NULO = {"bsonType": ["date", "null"]}
_PUNTO = {
    "bsonType": "object",
    "required": ["type", "coordinates"],
    "properties": {
        "type": {"enum": ["Point"]},
        "coordinates": {"bsonType": "array", "minItems": 2, "maxItems": 2, "items": {"bsonType": "number"}},
    },
}
_REFERENCIA = {"bsonType": "object", "required": ["id", "nombre"], "properties": {"id": _ID_ENTERO, "nombre": _TEXTO}}

# Validación de esquema (MIGRACION_MONGODB.md §3.5). validationLevel "moderate": no frena documentos viejos
VALIDADORES = {
    "usuarios": {
        "bsonType": "object",
        "required": ["_id", "nombre", "primer_apellido", "correo", "password", "rol"],
        "properties": {
            "_id": _ID_ENTERO,
            "nombre": _TEXTO,
            "primer_apellido": _TEXTO,
            "segundo_apellido": _TEXTO_O_NULO,
            "correo": _TEXTO,
            "password": _TEXTO,
            "fecha_nacimiento": _FECHA_O_NULO,
            "rol": {"enum": ["usuario", "admin"]},
            "residencia": {"bsonType": ["object", "null"]},
            "deleted_at": _FECHA_O_NULO,
        },
    },
    "lugares": {
        "bsonType": "object",
        "required": ["_id", "nombre", "ubicacion", "categoria"],
        "properties": {
            "_id": _ID_ENTERO,
            "nombre": _TEXTO,
            "ubicacion": _PUNTO,
            "categoria": _REFERENCIA,
            "id_usuario": _ID_ENTERO,
            "deleted_at": _FECHA_O_NULO,
        },
    },
    "planes": {
        "bsonType": "object",
        "required": ["_id", "id_usuario", "no_acompanantes", "tiempo_disponible", "categoria", "transporte", "fecha_plan"],
        "properties": {
            "_id": _ID_ENTERO,
            "id_usuario": _ID_ENTERO,
            "contexto": {"enum": ["solo", "pareja", "amigos", "familia"]},
            "no_acompanantes": {"bsonType": ["int", "long"], "minimum": 0},
            "presupuesto": {
                "bsonType": "object",
                "required": ["min", "max"],
                "properties": {"min": {"bsonType": "number"}, "max": {"bsonType": "number"}},
            },
            "tiempo_disponible": {"bsonType": ["int", "long"], "minimum": 1},
            "intereses": {"bsonType": "array", "items": {"enum": ["comer", "cafe", "cultura", "entretenimiento", "aire_libre"]}},
            "movilidad": {"bsonType": "array", "items": {"enum": ["caminando", "transporte_publico", "taxi_app", "combinado"]}},
            "categoria": _REFERENCIA,
            "transporte": _REFERENCIA,
            "fecha_plan": {"bsonType": "date"},
            "evaluacion": {"bsonType": "object"},
            "deleted_at": _FECHA_O_NULO,
        },
    },
    "reportes": {
        "bsonType": "object",
        "required": ["tipo", "ubicacion", "observado_en", "vigente_hasta", "confirmaciones", "estado"],
        "properties": {
            "tipo": {"enum": ["afluencia", "cierre_total", "accidente", "manifestacion"]},
            "nivel_afluencia": {"enum": ["baja", "media", "alta"]},
            "ubicacion": _PUNTO,
            "observado_en": {"bsonType": "date"},
            "vigente_hasta": {"bsonType": "date"},
            "confirmaciones": {"bsonType": ["int", "long"], "minimum": 0},
            "estado": {"enum": ["pendiente", "verificado", "descartado"]},
            "comentario": _TEXTO,
        },
    },
}

INDICES = {
    "usuarios": [IndexModel([("correo", ASCENDING)], unique=True, name="correo_unico")],
    "categorias": [IndexModel([("nombre", ASCENDING)], unique=True, name="nombre_unico")],
    "transportes": [IndexModel([("nombre", ASCENDING)], unique=True, name="nombre_unico")],
    "lugares": [
        IndexModel([("ubicacion", GEOSPHERE)], name="ubicacion_2dsphere"),
        IndexModel([("categoria.id", ASCENDING)], name="categoria"),
    ],
    "rutas": [IndexModel([("trazo", GEOSPHERE)], name="trazo_2dsphere")],
    "historial_rutas": [
        IndexModel([("id_usuario", ASCENDING), ("_id", DESCENDING)], name="usuario_recientes"),
        IndexModel([("created_at", ASCENDING)], name="created_at"),
    ],
    "planes": [
        IndexModel([("id_usuario", ASCENDING), ("_id", DESCENDING)], name="usuario_recientes"),
        IndexModel([("created_at", ASCENDING)], name="created_at"),
    ],
    # Sin índice TTL a propósito: los reportes vencidos se conservan para las estadísticas
    "reportes": [
        IndexModel([("ubicacion", GEOSPHERE)], name="ubicacion_2dsphere"),
        IndexModel([("vigente_hasta", ASCENDING)], name="vigente_hasta"),
        IndexModel([("ruta_id", ASCENDING)], name="ruta_id"),
    ],
    "bitacora_laboratorio": [IndexModel([("tipo", ASCENDING), ("creado_en", ASCENDING)], name="tipo_fecha")],
    "contadores": [],
}

# Colecciones con _id entero: su contador se ajusta al _id máximo
CON_CONTADOR = ("usuarios", "categorias", "transportes", "lugares", "rutas", "historial_rutas", "planes")


def crear_colecciones(bd: Database) -> None:
    existentes = set(bd.list_collection_names())
    for nombre, indices in INDICES.items():
        validador = VALIDADORES.get(nombre)
        opciones = {"validator": {"$jsonSchema": validador}, "validationLevel": "moderate"} if validador else {}
        if nombre not in existentes:
            bd.create_collection(nombre, **opciones)
        elif opciones:
            bd.command("collMod", nombre, **opciones)
        if indices:
            bd[nombre].create_indexes(indices)


def cargar_datos(bd: Database) -> None:
    from app.nucleo.bd import ahora

    datos = json.loads((CARPETA_BD / DATOS).read_text(encoding="utf-8"))
    momento = ahora()
    for coleccion in ("usuarios", "categorias", "transportes", "lugares", "rutas"):
        docs = [{**d, "created_at": momento, "updated_at": momento, "deleted_at": None} for d in datos.get(coleccion, [])]
        if docs:
            bd[coleccion].insert_many(docs)


def ajustar_contadores(bd: Database) -> None:
    for coleccion in CON_CONTADOR:
        ultimo = next(bd[coleccion].find({}, {"_id": 1}).sort("_id", -1).limit(1), None)
        seq = ultimo["_id"] if ultimo else 0
        bd.contadores.update_one({"_id": coleccion}, {"$max": {"seq": seq}}, upsert=True)


def resumen(bd: Database) -> str:
    filas = [(n, bd[n].estimated_document_count(), len(bd[n].index_information())) for n in sorted(INDICES)]
    ancho = max(len(n) for n, *_ in filas)
    lineas = [f"{'Colección':<{ancho}}  Documentos  Índices", "-" * (ancho + 21)]
    lineas += [f"{n:<{ancho}}  {d:>10}  {i:>7}" for n, d, i in filas]
    return "\n".join(lineas)


def preparar(recrear: bool = False, con_datos: bool = True, silencioso: bool = False, bd: Database | None = None) -> Database:
    from app.nucleo.bd import cliente
    from app.nucleo.config import get_settings

    def avisar(mensaje: str) -> None:
        if not silencioso:
            print(mensaje)

    if bd is None:
        nombre = get_settings().mongo_db
        cli = cliente()
        cli.admin.command("ping")
        if recrear:
            cli.drop_database(nombre)
            avisar(f"Base `{nombre}` borrada.")
        bd = cli[nombre]

    crear_colecciones(bd)
    avisar(f"Base `{bd.name}`: colecciones, validadores e índices listos.")
    if con_datos and bd.usuarios.estimated_document_count() == 0:
        cargar_datos(bd)
        avisar(f"  ✓ {DATOS}")
        avisar("Usuario de prueba: demo@kompas.mx / demo1234 (rol admin)")
    ajustar_contadores(bd)
    avisar(resumen(bd))
    return bd


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--recrear", action="store_true", help="borra la base si ya existe")
    parser.add_argument("--sin-datos", action="store_true", help="no carga los datos de desarrollo")
    args = parser.parse_args()

    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    preparar(recrear=args.recrear, con_datos=not args.sin_datos)


if __name__ == "__main__":
    main()
