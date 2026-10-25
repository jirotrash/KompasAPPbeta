"""Recorridos que el usuario inicia. Valida la ruta y el transporte con los servicios de sus módulos."""

from app.modulos.catalogos.servicio import ServicioCatalogos
from app.modulos.historial.repositorio import RepositorioHistorial
from app.modulos.rutas.servicio import ServicioRutas
from app.nucleo.errores import NoEncontrado


class ServicioHistorial:
    def __init__(self, repo: RepositorioHistorial, rutas: ServicioRutas, catalogos: ServicioCatalogos):
        self.repo = repo
        self.rutas = rutas
        self.catalogos = catalogos

    def guardar(self, usuario: dict, id_ruta: int, id_transporte: int, tiempo_estimado: int) -> dict:
        if not self.rutas.existe(id_ruta):
            raise NoEncontrado("No encontramos esa ruta.")
        transporte = self.catalogos.transporte_por_id(id_transporte)
        if transporte is None:
            raise NoEncontrado("No encontramos ese medio de transporte.")
        return self.repo.crear(usuario["id"], id_ruta, transporte, tiempo_estimado)

    def del_usuario(self, usuario: dict) -> list[dict]:
        return self.repo.del_usuario(usuario["id"])
