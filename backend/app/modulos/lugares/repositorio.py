"""Acceso a la colección `lugares`. Documento → dict con la forma que espera la app (src/types/dominio.ts).

La base no tiene horario, costo, calificación ni foto de los lugares: van en null (no se inventan).
El sistema experto no usa estos lugares: el planificador trabaja con Google Places (app/ia/servicio.py).
"""

from pymongo import ReturnDocument
from pymongo.database import Database

from app.compartido.geo import geo_punto
from app.compartido.texto import interes_de
from app.nucleo.bd import ahora, siguiente_id


def _lugar(doc: dict) -> dict:
    lng, lat = doc["ubicacion"]["coordinates"]
    categoria = (doc.get("categoria") or {}).get("nombre")
    return {
        "_id": str(doc["_id"]),
        "id": doc["_id"],
        "nombre": doc["nombre"],
        "lat": lat,
        "lng": lng,
        "ubicacion": geo_punto(lat, lng),
        "categoria": categoria,
        "id_categoria": (doc.get("categoria") or {}).get("id"),
        "interes": interes_de(categoria),
        # Campos que la app muestra y la base todavía no tiene
        "horario": None,
        "costo_promedio": None,
        "calificacion": None,
        "afluencia": None,
        "foto_url": None,
        "contextos": [],
    }


class RepositorioLugares:
    def __init__(self, bd: Database):
        self.bd = bd

    def listar(self) -> list[dict]:
        return [_lugar(d) for d in self.bd.lugares.find({"deleted_at": None}).sort("_id", 1)]

    def por_id(self, id_lugar: int) -> dict | None:
        doc = self.bd.lugares.find_one({"_id": id_lugar, "deleted_at": None})
        return _lugar(doc) if doc else None

    def crear(self, campos: dict) -> dict:
        """campos: nombre, categoria {id, nombre} (referencia extendida), ubicacion (Point) e id_usuario."""
        momento = ahora()
        doc = {"_id": siguiente_id(self.bd, "lugares"), **campos, "created_at": momento, "updated_at": momento, "deleted_at": None}
        self.bd.lugares.insert_one(doc)
        return _lugar(doc)

    def actualizar(self, id_lugar: int, campos: dict) -> dict | None:
        doc = self.bd.lugares.find_one_and_update(
            {"_id": id_lugar, "deleted_at": None},
            {"$set": {**campos, "updated_at": ahora()}},
            return_document=ReturnDocument.AFTER,
        )
        return _lugar(doc) if doc else None

    def borrar(self, id_lugar: int) -> bool:
        resultado = self.bd.lugares.update_one({"_id": id_lugar, "deleted_at": None}, {"$set": {"deleted_at": ahora()}})
        return resultado.modified_count == 1
