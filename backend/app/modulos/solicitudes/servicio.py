"""Solicitudes de rutas que faltan: la persona las pide desde la app y el equipo las atiende en el panel."""

from app.compartido.geo import ZONA, esta_dentro_de_zona
from app.modulos.solicitudes.repositorio import RepositorioSolicitudes
from app.nucleo.errores import DatosInvalidos, NoEncontrado


def _punto(geo: dict) -> dict:
    lng, lat = geo["coordinates"]
    return {"lat": lat, "lng": lng}


class ServicioSolicitudes:
    def __init__(self, repo: RepositorioSolicitudes):
        self.repo = repo

    def crear(self, usuario: dict, datos: dict) -> dict:
        if not (esta_dentro_de_zona(_punto(datos["origen"])) and esta_dentro_de_zona(_punto(datos["destino"]))):
            raise DatosInvalidos(f"El origen o el destino está fuera de la zona piloto ({ZONA['nombre']}).")
        return self.repo.crear(
            {
                "id_usuario": usuario["id"],
                "origen": {"type": "Point", "coordinates": list(datos["origen"]["coordinates"])},
                "destino": {"type": "Point", "coordinates": list(datos["destino"]["coordinates"])},
                "comentario": (datos.get("comentario") or "").strip() or None,
            }
        )

    def del_usuario(self, usuario: dict) -> list[dict]:
        return self.repo.del_usuario(usuario["id"])

    def recientes(self, limite: int, estado: str | None = None) -> list[dict]:
        return self.repo.recientes(limite, estado)

    def actualizar(self, id_solicitud: str, datos: dict) -> dict:
        campos = {"estado": datos["estado"], "nota_admin": (datos.get("nota_admin") or "").strip() or None}
        solicitud = self.repo.actualizar(id_solicitud, campos)
        if solicitud is None:
            raise NoEncontrado("No encontramos esa solicitud.")
        return solicitud

    def borrar(self, id_solicitud: str) -> None:
        if not self.repo.borrar(id_solicitud):
            raise NoEncontrado("No encontramos esa solicitud.")
