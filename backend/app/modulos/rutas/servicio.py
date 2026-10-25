"""Rutas guardadas y alternativas de la pantalla Buscar (estimaciones por distancia)."""

from app.compartido.geo import (
    ESPERA_TAXI_MIN,
    VELOCIDAD_AUTO_KMH,
    Coordenada,
    distancia_por_calles_km,
    esta_dentro_de_zona,
    minutos_caminando,
    redondear,
)
from app.modulos.rutas.repositorio import RepositorioRutas
from app.nucleo.errores import NoEncontrado

FUENTE_ESTIMACION = "Estimación por distancia"
SIN_AUTOBUS = "No tenemos información suficiente de transporte público para esta ruta."
AVISOS_AUTO = ["El tiempo no considera el tráfico.", "La tarifa la define el proveedor; consúltala en su app o con el conductor."]


class ServicioRutas:
    def __init__(self, repo: RepositorioRutas):
        self.repo = repo

    def listar(self) -> list[dict]:
        return self.repo.listar()

    def detalle(self, id_ruta: int) -> dict:
        ruta = self.repo.por_id(id_ruta)
        if ruta is None:
            raise NoEncontrado("No encontramos esa ruta.")
        return ruta

    def existe(self, id_ruta: int) -> bool:
        return self.repo.por_id(id_ruta) is not None

    def alternativas(self, a: Coordenada, b: Coordenada) -> dict:
        """A pie y en taxi/app estimadas por distancia. Sin líneas de autobús: `datos_suficientes` es false."""
        if not (esta_dentro_de_zona(a) and esta_dentro_de_zona(b)):
            return {
                "datos_suficientes": False,
                "mensaje": "El origen o el destino está fuera de la zona piloto (Toluca, Lerma y San Mateo Atenco).",
                "alternativas": [],
            }

        km = round(distancia_por_calles_km(a, b), 2)
        pie = {
            "id": "pie",
            "modo": "pie",
            "distancia_km": km,
            "tiempos": {"caminata": minutos_caminando(km), "espera": None, "trayecto": None},
            "fuente": FUENTE_ESTIMACION,
            "avisos": ["Trayecto largo para hacerlo a pie."] if km > 4 else [],
        }

        def auto(modo: str) -> dict:
            return {
                "id": modo,
                "modo": modo,
                "distancia_km": km,
                "tiempos": {"caminata": None, "espera": ESPERA_TAXI_MIN, "trayecto": redondear(km / VELOCIDAD_AUTO_KMH * 60)},
                "fuente": FUENTE_ESTIMACION,
                "avisos": AVISOS_AUTO,
            }

        return {"datos_suficientes": False, "mensaje": SIN_AUTOBUS, "alternativas": [pie, auto("taxi"), auto("app")]}
