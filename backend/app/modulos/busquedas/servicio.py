"""Guarda lo que la gente busca en "¿Cómo llego?". Las búsquedas sin camión le dicen al equipo qué rutas faltan."""

from app.compartido.geo import Coordenada, geo_punto
from app.modulos.busquedas.repositorio import RepositorioBusquedas


class ServicioBusquedas:
    def __init__(self, repo: RepositorioBusquedas):
        self.repo = repo

    def registrar(self, usuario: dict | None, origen: Coordenada, destino: Coordenada, resultado: dict) -> None:
        opciones = resultado["alternativas"]
        buses = [o for o in opciones if o["modo"] == "autobus"]
        pie = next((o for o in opciones if o["modo"] == "pie"), None)
        self.repo.crear(
            {
                "id_usuario": usuario["id"] if usuario else None,
                "origen": geo_punto(origen["lat"], origen["lng"]),
                "destino": geo_punto(destino["lat"], destino["lng"]),
                "datos_suficientes": resultado["datos_suficientes"],
                "opciones_autobus": len(buses),
                "rutas": sorted({i for o in buses for i in o.get("rutas", [])}),
                "distancia_km": pie["distancia_km"] if pie else None,
            }
        )

    def recientes(self, limite: int, solo_sin_autobus: bool) -> list[dict]:
        return self.repo.recientes(limite, solo_sin_autobus)
