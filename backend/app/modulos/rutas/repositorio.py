"""Acceso a la colección `rutas`. El trazo es un GeoJSON LineString ([[lng, lat], ...])."""

from pymongo import ReturnDocument
from pymongo.database import Database

from app.nucleo.bd import ahora, siguiente_id


def _campos(trazo: list[list[float]], nombre: str | None, paradas: list[dict] | None) -> dict:
    return {
        "trazo": {"type": "LineString", "coordinates": [list(p) for p in trazo]},
        "nombre": nombre,
        "paradas": [{"nombre": p["nombre"], "ubicacion": p["ubicacion"]} for p in paradas or []],
    }


def _ruta(doc: dict) -> dict:
    ruta = {"id": doc["_id"], "_id": str(doc["_id"]), "trazo": doc["trazo"]["coordinates"]}
    # Opcionales: nombre de la línea y paradas reales capturadas por el equipo ({nombre, ubicacion: Point})
    if doc.get("nombre"):
        ruta["nombre"] = doc["nombre"]
    if doc.get("paradas"):
        ruta["paradas"] = [{"nombre": p["nombre"], "ubicacion": p["ubicacion"]} for p in doc["paradas"]]
    return ruta


class RepositorioRutas:
    def __init__(self, bd: Database):
        self.bd = bd

    def listar(self) -> list[dict]:
        return [_ruta(d) for d in self.bd.rutas.find({"deleted_at": None}).sort("_id", 1)]

    def por_id(self, id_ruta: int) -> dict | None:
        doc = self.bd.rutas.find_one({"_id": id_ruta, "deleted_at": None})
        return _ruta(doc) if doc else None

    def crear(self, trazo: list[list[float]], nombre: str | None = None, paradas: list[dict] | None = None) -> dict:
        """Guarda un trazo recorrido por el equipo (panel de administración, pruebas y scripts)."""
        momento = ahora()
        doc = {
            "_id": siguiente_id(self.bd, "rutas"),
            **_campos(trazo, nombre, paradas),
            "created_at": momento,
            "updated_at": momento,
            "deleted_at": None,
        }
        self.bd.rutas.insert_one(doc)
        return _ruta(doc)

    def actualizar(self, id_ruta: int, trazo: list[list[float]], nombre: str | None, paradas: list[dict]) -> dict | None:
        doc = self.bd.rutas.find_one_and_update(
            {"_id": id_ruta, "deleted_at": None},
            {"$set": {**_campos(trazo, nombre, paradas), "updated_at": ahora()}},
            return_document=ReturnDocument.AFTER,
        )
        return _ruta(doc) if doc else None

    def borrar(self, id_ruta: int) -> bool:
        """Borrado lógico: el historial y los reportes que apuntan a la ruta se conservan."""
        resultado = self.bd.rutas.update_one({"_id": id_ruta, "deleted_at": None}, {"$set": {"deleted_at": ahora()}})
        return resultado.modified_count == 1
