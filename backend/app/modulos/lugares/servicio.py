"""Lugares para "Cerca de ti" y el buscador. El filtro por distancia y el orden se hacen aquí (en Python)."""

from app.compartido.geo import Coordenada, distancia_km, minutos_caminando
from app.compartido.texto import clave
from app.modulos.lugares.repositorio import RepositorioLugares
from app.nucleo.errores import NoEncontrado


class ServicioLugares:
    def __init__(self, repo: RepositorioLugares):
        self.repo = repo

    def buscar(self, origen: Coordenada | None, radio_km: float | None, categoria: str | None) -> list[dict]:
        lugares = self.repo.listar()
        if categoria:
            buscada = clave(categoria)
            lugares = [l for l in lugares if l["categoria"] and clave(l["categoria"]) == buscada]
        if origen:
            for l in lugares:
                km = distancia_km(origen, {"lat": l["lat"], "lng": l["lng"]})
                l["distancia_km"] = round(km, 2)
                l["minutos_caminando"] = minutos_caminando(km)
            if radio_km:
                lugares = [l for l in lugares if l["distancia_km"] <= radio_km]
            lugares.sort(key=lambda l: l["distancia_km"])
        return lugares

    def detalle(self, id_lugar: int) -> dict:
        lugar = self.repo.por_id(id_lugar)
        if lugar is None:
            raise NoEncontrado("No encontramos ese lugar.")
        return lugar
