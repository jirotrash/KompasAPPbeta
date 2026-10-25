"""Acceso a la colección `rutas`. El trazo es un GeoJSON LineString ([[lng, lat], ...])."""

from pymongo.database import Database

from app.nucleo.bd import ahora, siguiente_id


def _ruta(doc: dict) -> dict:
    return {"id": doc["_id"], "_id": str(doc["_id"]), "trazo": doc["trazo"]["coordinates"]}


class RepositorioRutas:
    def __init__(self, bd: Database):
        self.bd = bd

    def listar(self) -> list[dict]:
        return [_ruta(d) for d in self.bd.rutas.find({"deleted_at": None}).sort("_id", 1)]

    def por_id(self, id_ruta: int) -> dict | None:
        doc = self.bd.rutas.find_one({"_id": id_ruta, "deleted_at": None})
        return _ruta(doc) if doc else None

    def crear(self, trazo: list[list[float]]) -> dict:
        """Guarda un trazo recorrido por el equipo (lo usan las pruebas y los scripts)."""
        momento = ahora()
        doc = {
            "_id": siguiente_id(self.bd, "rutas"),
            "trazo": {"type": "LineString", "coordinates": trazo},
            "created_at": momento,
            "updated_at": momento,
            "deleted_at": None,
        }
        self.bd.rutas.insert_one(doc)
        return _ruta(doc)
