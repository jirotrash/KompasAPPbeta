"""Acceso a la colección `solicitudes_rutas` (_id ObjectId: se regresa como texto en `id`)."""

from pymongo import ReturnDocument
from pymongo.database import Database

from app.nucleo.bd import ahora, object_id


def _solicitud(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "id_usuario": doc["id_usuario"],
        "origen": doc["origen"],
        "destino": doc["destino"],
        "comentario": doc.get("comentario"),
        "estado": doc["estado"],
        "nota_admin": doc.get("nota_admin"),
        "creado_en": doc["created_at"],
        "actualizado_en": doc["updated_at"],
    }


class RepositorioSolicitudes:
    def __init__(self, bd: Database):
        self.bd = bd

    def crear(self, datos: dict) -> dict:
        momento = ahora()
        doc = {**datos, "estado": "pendiente", "nota_admin": None, "created_at": momento, "updated_at": momento}
        self.bd.solicitudes_rutas.insert_one(doc)
        return _solicitud(doc)

    def del_usuario(self, id_usuario: int) -> list[dict]:
        return [_solicitud(d) for d in self.bd.solicitudes_rutas.find({"id_usuario": id_usuario}).sort("created_at", -1)]

    def recientes(self, limite: int, estado: str | None = None) -> list[dict]:
        filtro = {"estado": estado} if estado else {}
        return [_solicitud(d) for d in self.bd.solicitudes_rutas.find(filtro).sort("created_at", -1).limit(limite)]

    def actualizar(self, id_solicitud: str, campos: dict) -> dict | None:
        oid = object_id(id_solicitud)
        doc = oid and self.bd.solicitudes_rutas.find_one_and_update(
            {"_id": oid}, {"$set": {**campos, "updated_at": ahora()}}, return_document=ReturnDocument.AFTER
        )
        return _solicitud(doc) if doc else None

    def borrar(self, id_solicitud: str) -> bool:
        oid = object_id(id_solicitud)
        return bool(oid) and self.bd.solicitudes_rutas.delete_one({"_id": oid}).deleted_count == 1
