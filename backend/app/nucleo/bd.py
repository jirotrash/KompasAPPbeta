"""Conexión a MongoDB con PyMongo. Un solo cliente para toda la app (pool de conexiones)."""

from datetime import datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

from pymongo import MongoClient, ReturnDocument
from pymongo.database import Database

from app.nucleo.config import get_settings

ZONA_HORARIA = ZoneInfo("America/Mexico_City")


@lru_cache
def cliente() -> MongoClient:
    s = get_settings()
    # tz_aware + tzinfo: las fechas que se leen regresan en hora de Toluca
    return MongoClient(s.mongo_uri, tz_aware=True, tzinfo=ZONA_HORARIA, serverSelectionTimeoutMS=3000)


def get_bd() -> Database:
    """Dependencia de FastAPI: `bd: Database = Depends(get_bd)`."""
    return cliente()[get_settings().mongo_db]


def bd_disponible() -> bool:
    try:
        cliente().admin.command("ping")
        return True
    except Exception:
        return False


def siguiente_id(bd: Database, coleccion: str) -> int:
    """Id entero consecutivo por colección (la app espera `id: number`). Vive en `contadores`."""
    doc = bd.contadores.find_one_and_update(
        {"_id": coleccion}, {"$inc": {"seq": 1}}, upsert=True, return_document=ReturnDocument.AFTER
    )
    return doc["seq"]


def ahora() -> datetime:
    """Fecha y hora actual con zona horaria (America/Mexico_City)."""
    return datetime.now(ZONA_HORARIA)


def hora_local(fecha: datetime | None) -> datetime | None:
    """Fecha de la base → hora de Toluca sin zona horaria, igual que la regresaba MySQL (contrato de la API)."""
    if fecha is None:
        return None
    if fecha.tzinfo is not None:
        fecha = fecha.astimezone(ZONA_HORARIA).replace(tzinfo=None)
    # MySQL guardaba segundos enteros (TIMESTAMP sin fracción)
    return fecha.replace(microsecond=0)
