"""Reportes comunitarios: la API valida la zona y calcula la vigencia según el tipo (mismos valores que el mock)."""

from datetime import datetime, timedelta

from app.compartido.geo import ZONA, esta_dentro_de_zona
from app.modulos.reportes.repositorio import RepositorioReportes
from app.nucleo.bd import ZONA_HORARIA, ahora
from app.nucleo.errores import DatosInvalidos, NoEncontrado

VIGENCIA_H = {"cierre_total": 6, "accidente": 2, "manifestacion": 3, "afluencia": 1}


def _con_zona(fecha: datetime) -> datetime:
    """Una fecha sin zona horaria se toma como hora de Toluca."""
    return fecha.replace(tzinfo=ZONA_HORARIA) if fecha.tzinfo is None else fecha


class ServicioReportes:
    def __init__(self, repo: RepositorioReportes):
        self.repo = repo

    def crear(self, usuario: dict, datos: dict) -> dict:
        lng, lat = datos["ubicacion"]["coordinates"]
        if not esta_dentro_de_zona({"lat": lat, "lng": lng}):
            raise DatosInvalidos(f"El punto de partida está fuera de la zona piloto ({ZONA['nombre']}).")
        observado = _con_zona(datos["observado_en"])
        return self.repo.crear(
            {
                **datos,
                "ubicacion": {"type": "Point", "coordinates": [lng, lat]},
                "observado_en": observado,
                "vigente_hasta": observado + timedelta(hours=VIGENCIA_H[datos["tipo"]]),
                "comentario": (datos.get("comentario") or "").strip() or None,
                "id_usuario": usuario["id"],
            }
        )

    def vigentes(self, ruta_id: str | None = None) -> list[dict]:
        return self.repo.vigentes(ahora(), ruta_id)

    # ─────────────────────────── Panel de administración ───────────────────────────

    @staticmethod
    def _con_vigencia(reporte: dict) -> dict:
        return {**reporte, "vigente": reporte["vigente_hasta"] > ahora()}

    def recientes(self, limite: int, estado: str | None = None) -> list[dict]:
        return [self._con_vigencia(r) for r in self.repo.recientes(limite, estado)]

    def cambiar_estado(self, id_reporte: str, estado: str) -> dict:
        reporte = self.repo.cambiar_estado(id_reporte, estado)
        if reporte is None:
            raise NoEncontrado("No encontramos ese reporte.")
        return self._con_vigencia(reporte)

    def borrar(self, id_reporte: str) -> None:
        if not self.repo.borrar(id_reporte):
            raise NoEncontrado("No encontramos ese reporte.")
