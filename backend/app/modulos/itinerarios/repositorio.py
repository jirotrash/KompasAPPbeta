"""Acceso a la colección `planes`: lo que eligió el usuario y la evaluación del sistema experto."""

from pymongo.database import Database

from app.nucleo.bd import ahora, hora_local, siguiente_id


def _plan_guardado(doc: dict) -> dict:
    """Los mismos campos que regresaba GET /api/planes con MySQL."""
    return {
        "id": doc["_id"],
        "no_acompanantes": doc["no_acompanantes"],
        "tiempo_disponible": doc["tiempo_disponible"],
        "categoria": doc["categoria"]["nombre"],
        "transporte": doc["transporte"]["nombre"],
        "fecha_plan": hora_local(doc.get("fecha_plan")),
        "creado_en": hora_local(doc.get("created_at")),
    }


class RepositorioPlanes:
    def __init__(self, bd: Database):
        self.bd = bd

    def guardar(self, plan: dict) -> int:
        """`plan` trae los campos de MIGRACION_MONGODB.md §3.4; aquí se agregan id y fechas."""
        momento = ahora()
        doc = {
            "_id": siguiente_id(self.bd, "planes"),
            **plan,
            "created_at": momento,
            "updated_at": momento,
            "deleted_at": None,
        }
        self.bd.planes.insert_one(doc)
        return doc["_id"]

    def del_usuario(self, id_usuario: int) -> list[dict]:
        """Del más reciente al más antiguo."""
        consulta = self.bd.planes.find({"id_usuario": id_usuario, "deleted_at": None}).sort("_id", -1)
        return [_plan_guardado(d) for d in consulta]
