"""Acceso a la colección `historial_rutas` (el transporte va como referencia extendida {id, nombre})."""

from pymongo.database import Database

from app.nucleo.bd import ahora, hora_local, siguiente_id


def _recorrido(doc: dict) -> dict:
    return {
        "id": doc["_id"],
        "id_ruta": doc["id_ruta"],
        "id_transporte": doc["transporte"]["id"],
        "transporte": doc["transporte"]["nombre"],
        "tiempo_estimado": doc["tiempo_estimado"],
        "creado_en": hora_local(doc.get("created_at")),
    }


class RepositorioHistorial:
    def __init__(self, bd: Database):
        self.bd = bd

    def crear(self, id_usuario: int, id_ruta: int, transporte: dict, tiempo_estimado: int) -> dict:
        momento = ahora()
        doc = {
            "_id": siguiente_id(self.bd, "historial_rutas"),
            "id_usuario": id_usuario,
            "id_ruta": id_ruta,
            "transporte": {"id": transporte["id"], "nombre": transporte["nombre"]},
            "tiempo_estimado": tiempo_estimado,
            "created_at": momento,
            "updated_at": momento,
            "deleted_at": None,
        }
        self.bd.historial_rutas.insert_one(doc)
        return _recorrido(doc)

    def del_usuario(self, id_usuario: int) -> list[dict]:
        """Del más reciente al más antiguo."""
        consulta = self.bd.historial_rutas.find({"id_usuario": id_usuario, "deleted_at": None}).sort("_id", -1)
        return [_recorrido(d) for d in consulta]
