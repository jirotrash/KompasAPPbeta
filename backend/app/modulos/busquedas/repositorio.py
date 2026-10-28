"""Acceso a la colección `busquedas` (_id ObjectId: se regresa como texto en `id`)."""

from pymongo.database import Database

from app.nucleo.bd import ahora


def _busqueda(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "id_usuario": doc.get("id_usuario"),
        "origen": doc["origen"],
        "destino": doc["destino"],
        "datos_suficientes": doc["datos_suficientes"],
        "opciones_autobus": doc.get("opciones_autobus", 0),
        "rutas": doc.get("rutas", []),
        "distancia_km": doc.get("distancia_km"),
        "creado_en": doc["created_at"],
    }


class RepositorioBusquedas:
    def __init__(self, bd: Database):
        self.bd = bd

    def crear(self, datos: dict) -> None:
        self.bd.busquedas.insert_one({**datos, "created_at": ahora()})

    def recientes(self, limite: int, solo_sin_autobus: bool) -> list[dict]:
        filtro = {"datos_suficientes": False} if solo_sin_autobus else {}
        return [_busqueda(d) for d in self.bd.busquedas.find(filtro).sort("created_at", -1).limit(limite)]
