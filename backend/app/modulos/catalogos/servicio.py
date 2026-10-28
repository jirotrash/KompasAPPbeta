"""Catálogos de categorías y transportes con la `clave` que usa la app. Otros módulos los piden aquí.

Las categorías y transportes cuya clave usan la app y el sistema experto (texto.INTERESES y texto.MOVILIDADES)
están protegidos en el panel: no se borran ni cambian de clave (sí de acentos, mayúsculas o descripción).
"""

from pymongo.errors import DuplicateKeyError

from app.compartido.texto import INTERESES, MOVILIDADES, clave
from app.modulos.catalogos.repositorio import RepositorioCatalogos
from app.nucleo.errores import Conflicto, DatosInvalidos, NoEncontrado

PROTEGIDAS = {"categorias": INTERESES, "transportes": MOVILIDADES}
NO_ENCONTRADO = {"categorias": "No encontramos esa categoría.", "transportes": "No encontramos ese medio de transporte."}


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

    def categoria_por_id(self, id_categoria: int) -> dict | None:
        return self.repo.por_id("categorias", id_categoria)

    # ─────────────────────────── Panel de administración ───────────────────────────

    @staticmethod
    def _con_protegida(coleccion: str, items: list[dict]) -> list[dict]:
        return [{**i, "protegida": i["clave"] in PROTEGIDAS[coleccion]} for i in items]

    def categorias_admin(self) -> list[dict]:
        return self._con_protegida("categorias", self.categorias())

    def transportes_admin(self) -> list[dict]:
        return self._con_protegida("transportes", self.transportes())

    def _validar_nombre(self, coleccion: str, nombre: str, id_doc: int | None = None) -> str:
        nombre = nombre.strip()
        if not clave(nombre):
            raise DatosInvalidos("Escribe un nombre con letras o números.")
        otros = self.repo.listar(coleccion)
        if any(clave(o["nombre"]) == clave(nombre) and o["id"] != id_doc for o in otros):
            raise Conflicto(f"Ya existe «{nombre}» (o uno con el mismo nombre sin acentos).")
        if id_doc is not None:
            actual = self.repo.por_id(coleccion, id_doc)
            if actual is None:
                raise NoEncontrado(NO_ENCONTRADO[coleccion])
            if clave(actual["nombre"]) in PROTEGIDAS[coleccion] and clave(nombre) != clave(actual["nombre"]):
                raise Conflicto(
                    f"La app y el sistema experto usan «{actual['nombre']}» como «{clave(actual['nombre'])}»: "
                    "puedes cambiar acentos o mayúsculas, pero no el nombre."
                )
        return nombre

    def _guardar(self, coleccion: str, campos: dict, id_doc: int | None = None) -> dict:
        try:
            doc = self.repo.crear(coleccion, campos) if id_doc is None else self.repo.actualizar(coleccion, id_doc, campos)
        except DuplicateKeyError:
            raise Conflicto(f"Ya hubo un registro borrado llamado «{campos['nombre']}»: créalo de nuevo en lugar de renombrar.") from None
        if doc is None:
            raise NoEncontrado(NO_ENCONTRADO[coleccion])
        doc = {**doc, "clave": clave(doc["nombre"])}
        return self._con_protegida(coleccion, [doc])[0]

    def guardar_categoria(self, datos: dict, id_categoria: int | None = None) -> dict:
        nombre = self._validar_nombre("categorias", datos["nombre"], id_categoria)
        descripcion = (datos.get("descripcion") or "").strip() or None
        return {"descripcion": None} | self._guardar("categorias", {"nombre": nombre, "descripcion": descripcion}, id_categoria)

    def guardar_transporte(self, datos: dict, id_transporte: int | None = None) -> dict:
        nombre = self._validar_nombre("transportes", datos["nombre"], id_transporte)
        return self._guardar("transportes", {"nombre": nombre}, id_transporte)

    def _borrar(self, coleccion: str, id_doc: int) -> None:
        actual = self.repo.por_id(coleccion, id_doc)
        if actual is None:
            raise NoEncontrado(NO_ENCONTRADO[coleccion])
        if clave(actual["nombre"]) in PROTEGIDAS[coleccion]:
            raise Conflicto(f"«{actual['nombre']}» la usan la app y el sistema experto: no se puede borrar.")
        if coleccion == "categorias" and (n := self.repo.lugares_con_categoria(id_doc)) > 0:
            raise Conflicto(f"Hay {n} lugar(es) con esta categoría: cámbialos de categoría antes de borrarla.")
        self.repo.borrar(coleccion, id_doc)

    def borrar_categoria(self, id_categoria: int) -> None:
        self._borrar("categorias", id_categoria)

    def borrar_transporte(self, id_transporte: int) -> None:
        self._borrar("transportes", id_transporte)
