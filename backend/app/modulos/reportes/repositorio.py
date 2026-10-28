"""Acceso a la colección `reportes` (ids ObjectId: se regresan como texto en `_id`)."""

from datetime import datetime

from pymongo import ReturnDocument
from pymongo.database import Database

from app.nucleo.bd import ahora, object_id

CAMPOS_OPCIONALES = ("nivel_afluencia", "ruta_id", "lugar_id", "comentario")


def _reporte(doc: dict) -> dict:
    salida = {
        "_id": str(doc["_id"]),
        "tipo": doc["tipo"],
        "ubicacion": doc["ubicacion"],
        "observado_en": doc["observado_en"],
        "vigente_hasta": doc["vigente_hasta"],
        "confirmaciones": doc.get("confirmaciones", 0),
        "estado": doc.get("estado", "pendiente"),
    }
    salida.update({c: doc[c] for c in CAMPOS_OPCIONALES if doc.get(c) is not None})
    return salida


class RepositorioReportes:
    def __init__(self, bd: Database):
        self.bd = bd

    def crear(self, datos: dict) -> dict:
        doc = {
            **{c: datos.get(c) for c in CAMPOS_OPCIONALES if datos.get(c) is not None},
            "tipo": datos["tipo"],
            "ubicacion": datos["ubicacion"],
            "observado_en": datos["observado_en"],
            "vigente_hasta": datos["vigente_hasta"],
            "confirmaciones": 0,
            "estado": "pendiente",
            "id_usuario": datos["id_usuario"],
            "created_at": ahora(),
        }
        self.bd.reportes.insert_one(doc)
        return _reporte(doc)

    def vigentes(self, momento: datetime, ruta_id: str | None = None) -> list[dict]:
        """Reportes con `vigente_hasta` posterior a `momento`, del más reciente al más antiguo."""
        filtro: dict = {"vigente_hasta": {"$gt": momento}}
        if ruta_id:
            filtro["ruta_id"] = ruta_id
        return [_reporte(d) for d in self.bd.reportes.find(filtro).sort("observado_en", -1)]

    # ─────────────────────────── Panel de administración ───────────────────────────
    # Los reportes no tienen borrado lógico: el dashboard cuenta todos los que existen.

    def recientes(self, limite: int, estado: str | None = None) -> list[dict]:
        filtro = {"estado": estado} if estado else {}
        return [_reporte(d) | {"id_usuario": d.get("id_usuario")} for d in self.bd.reportes.find(filtro).sort("observado_en", -1).limit(limite)]

    def cambiar_estado(self, id_reporte: str, estado: str) -> dict | None:
        oid = object_id(id_reporte)
        doc = oid and self.bd.reportes.find_one_and_update(
            {"_id": oid}, {"$set": {"estado": estado, "updated_at": ahora()}}, return_document=ReturnDocument.AFTER
        )
        return _reporte(doc) | {"id_usuario": doc.get("id_usuario")} if doc else None

    def borrar(self, id_reporte: str) -> bool:
        oid = object_id(id_reporte)
        return bool(oid) and self.bd.reportes.delete_one({"_id": oid}).deleted_count == 1
