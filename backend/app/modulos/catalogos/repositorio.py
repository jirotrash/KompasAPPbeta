"""Acceso a las colecciones `categorias` y `transportes`. Todas las consultas filtran el borrado lógico."""

from pymongo import ReturnDocument
from pymongo.database import Database

from app.compartido.texto import clave
from app.nucleo.bd import ahora, siguiente_id


def _catalogo(doc: dict) -> dict:
    salida = {"id": doc["_id"], "nombre": doc["nombre"]}
    if "descripcion" in doc:
        salida["descripcion"] = doc.get("descripcion")
    return salida


class RepositorioCatalogos:
    def __init__(self, bd: Database):
        self.bd = bd

    def listar(self, coleccion: str) -> list[dict]:
        return [_catalogo(d) for d in self.bd[coleccion].find({"deleted_at": None}).sort("_id", 1)]

    def categorias(self) -> list[dict]:
        return self.listar("categorias")

    def transportes(self) -> list[dict]:
        return self.listar("transportes")

    def transporte_por_id(self, id_transporte: int) -> dict | None:
        return self.por_id("transportes", id_transporte)

    def por_id(self, coleccion: str, id_doc: int) -> dict | None:
        doc = self.bd[coleccion].find_one({"_id": id_doc, "deleted_at": None})
        return _catalogo(doc) if doc else None

    def crear(self, coleccion: str, campos: dict) -> dict:
        """El nombre es único aunque el documento esté borrado: si existe uno borrado con ese nombre, se restaura."""
        momento = ahora()
        restaurado = self.bd[coleccion].find_one_and_update(
            {"nombre": campos["nombre"], "deleted_at": {"$ne": None}},
            {"$set": {**campos, "updated_at": momento, "deleted_at": None}},
            return_document=ReturnDocument.AFTER,
        )
        if restaurado:
            return _catalogo(restaurado)
        doc = {"_id": siguiente_id(self.bd, coleccion), **campos, "created_at": momento, "updated_at": momento, "deleted_at": None}
        self.bd[coleccion].insert_one(doc)
        return _catalogo(doc)

    def actualizar(self, coleccion: str, id_doc: int, campos: dict) -> dict | None:
        doc = self.bd[coleccion].find_one_and_update(
            {"_id": id_doc, "deleted_at": None},
            {"$set": {**campos, "updated_at": ahora()}},
            return_document=ReturnDocument.AFTER,
        )
        if doc and coleccion == "categorias":
            # Referencia extendida: los lugares guardan una copia del nombre de su categoría
            self.bd.lugares.update_many({"categoria.id": id_doc}, {"$set": {"categoria.nombre": doc["nombre"]}})
        return _catalogo(doc) if doc else None

    def borrar(self, coleccion: str, id_doc: int) -> bool:
        resultado = self.bd[coleccion].update_one({"_id": id_doc, "deleted_at": None}, {"$set": {"deleted_at": ahora()}})
        return resultado.modified_count == 1

    def lugares_con_categoria(self, id_categoria: int) -> int:
        return self.bd.lugares.count_documents({"categoria.id": id_categoria, "deleted_at": None})

    def por_clave(self, coleccion: str, valor: str) -> dict | None:
        """Busca en un catálogo por el valor de la app ("cafe" → documento "Café")."""
        return next((c for c in self.listar(coleccion) if clave(c["nombre"]) == valor), None)
