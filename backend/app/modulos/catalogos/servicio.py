"""Catálogos de categorías y transportes con la `clave` que usa la app. Otros módulos los piden aquí."""

from app.compartido.texto import clave
from app.modulos.catalogos.repositorio import RepositorioCatalogos


class ServicioCatalogos:
    def __init__(self, repo: RepositorioCatalogos):
        self.repo = repo

    def categorias(self) -> list[dict]:
        return [{**c, "descripcion": c.get("descripcion"), "clave": clave(c["nombre"])} for c in self.repo.categorias()]

    def transportes(self) -> list[dict]:
        return [{**t, "clave": clave(t["nombre"])} for t in self.repo.transportes()]

    def categoria_por_clave(self, valor: str) -> dict | None:
        return self.repo.por_clave("categorias", valor)

    def transporte_por_clave(self, valor: str) -> dict | None:
        return self.repo.por_clave("transportes", valor)

    def transporte_por_id(self, id_transporte: int) -> dict | None:
        return self.repo.transporte_por_id(id_transporte)
