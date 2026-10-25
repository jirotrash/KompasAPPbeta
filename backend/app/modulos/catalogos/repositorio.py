"""Acceso a las colecciones `categorias` y `transportes`. Todas las consultas filtran el borrado lógico."""

from pymongo.database import Database

from app.compartido.texto import clave


def _catalogo(doc: dict) -> dict:
    salida = {"id": doc["_id"], "nombre": doc["nombre"]}
    if "descripcion" in doc:
        salida["descripcion"] = doc.get("descripcion")
    return salida


class RepositorioCatalogos:
    def __init__(self, bd: Database):
        self.bd = bd

    def _listar(self, coleccion: str) -> list[dict]:
        return [_catalogo(d) for d in self.bd[coleccion].find({"deleted_at": None}).sort("_id", 1)]

    def categorias(self) -> list[dict]:
        return self._listar("categorias")

    def transportes(self) -> list[dict]:
        return self._listar("transportes")

    def transporte_por_id(self, id_transporte: int) -> dict | None:
        doc = self.bd.transportes.find_one({"_id": id_transporte, "deleted_at": None})
        return _catalogo(doc) if doc else None

    def por_clave(self, coleccion: str, valor: str) -> dict | None:
        """Busca en un catálogo por el valor de la app ("cafe" → documento "Café")."""
        return next((c for c in self._listar(coleccion) if clave(c["nombre"]) == valor), None)
