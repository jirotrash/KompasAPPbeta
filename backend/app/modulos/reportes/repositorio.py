"""Acceso a la colección `reportes` (ids ObjectId: se regresan como texto en `_id`)."""

from datetime import datetime

from pymongo.database import Database

from app.nucleo.bd import ahora

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
