"""Copia la base local (MONGO_URI/MONGO_DB) a Atlas (MONGO_URI_ATLAS/MONGO_DB_ATLAS). Va en un solo sentido.

Uso (desde backend/, con el venv activo):
    python -m scripts.copiar_a_atlas

- Crea en Atlas las colecciones, validadores e índices de preparar_bd.py (lo que el usuario de Atlas tenga permiso).
- Cada documento se copia por su _id: si ya existe en Atlas se reemplaza con el local; nada se duplica.
- No borra lo que solo exista en Atlas ni toca la base local. Se puede correr las veces que haga falta.
- Al final ajusta `contadores` para que los ids nuevos no choquen con los copiados.
"""

import sys

from pymongo import MongoClient, ReplaceOne
from pymongo.database import Database
from pymongo.errors import OperationFailure

from app.nucleo.config import get_settings
from scripts.preparar_bd import ajustar_contadores, crear_colecciones, resumen

LOTE = 500


def copiar_coleccion(origen: Database, destino: Database, nombre: str) -> int:
    total = 0
    lote: list[ReplaceOne] = []
    for doc in origen[nombre].find():
        lote.append(ReplaceOne({"_id": doc["_id"]}, doc, upsert=True))
        if len(lote) == LOTE:
            total += _escribir(destino, nombre, lote)
            lote = []
    if lote:
        total += _escribir(destino, nombre, lote)
    return total


def _escribir(destino: Database, nombre: str, lote: list[ReplaceOne]) -> int:
    # Son datos que la base local ya aceptó: los documentos viejos (migrados de MySQL) no siempre cumplen el validador
    try:
        destino[nombre].bulk_write(lote, ordered=False, bypass_document_validation=True)
    except OperationFailure as error:
        # Sin permiso para saltar la validación (13 en MongoDB, 8000 "AtlasError" en Atlas): se intenta con validación
        if "bypassDocumentValidation" not in str(error):
            raise
        destino[nombre].bulk_write(lote, ordered=False)
    return len(lote)


def main() -> None:
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    ajustes = get_settings()
    if not ajustes.mongo_uri_atlas:
        sys.exit("Falta MONGO_URI_ATLAS en backend/.env")

    origen = MongoClient(ajustes.mongo_uri, serverSelectionTimeoutMS=3000)[ajustes.mongo_db]
    destino = MongoClient(ajustes.mongo_uri_atlas, serverSelectionTimeoutMS=10000)[ajustes.mongo_db_atlas]
    origen.client.admin.command("ping")
    destino.client.admin.command("ping")
    print(f"Copiando local `{origen.name}` → Atlas `{destino.name}`")

    try:
        crear_colecciones(destino)
        print("  ✓ colecciones, validadores e índices")
    except OperationFailure as error:
        # Crear colecciones e índices sí se puede; cambiar el validador de una que ya existe pide collMod
        print(f"  ! Atlas no dejó crear o actualizar validadores/índices ({error.code}); se copian solo los datos")

    for nombre in sorted(n for n in origen.list_collection_names() if not n.startswith("system.")):
        print(f"  {nombre:<22} {copiar_coleccion(origen, destino, nombre):>6} documentos")

    ajustar_contadores(destino)
    print(resumen(destino))


if __name__ == "__main__":
    main()
