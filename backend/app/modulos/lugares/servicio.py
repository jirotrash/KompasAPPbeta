"""Lugares para "Cerca de ti" y el buscador. El filtro por distancia y el orden se hacen aquí (en Python)."""

from app.compartido.geo import ZONA, Coordenada, distancia_km, esta_dentro_de_zona, minutos_caminando
from app.compartido.texto import clave
from app.modulos.catalogos.servicio import ServicioCatalogos
from app.modulos.lugares.repositorio import RepositorioLugares
from app.nucleo.errores import DatosInvalidos, NoEncontrado


class ServicioLugares:
    def __init__(self, repo: RepositorioLugares, catalogos: ServicioCatalogos | None = None):
        self.repo = repo
        self.catalogos = catalogos  # solo lo necesita el panel de administración

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

    # ─────────────────────────── Panel de administración ───────────────────────────

    def _campos(self, datos: dict) -> dict:
        nombre = datos["nombre"].strip()
        if not nombre:
            raise DatosInvalidos("Escribe el nombre del lugar.")
        lng, lat = datos["ubicacion"]["coordinates"]
        if not esta_dentro_de_zona({"lat": lat, "lng": lng}):
            raise DatosInvalidos(f"El lugar está fuera de la zona piloto ({ZONA['nombre']}).")
        categoria = self.catalogos.categoria_por_id(datos["id_categoria"])
        if categoria is None:
            raise NoEncontrado("No encontramos esa categoría.")
        return {
            "nombre": nombre,
            "categoria": {"id": categoria["id"], "nombre": categoria["nombre"]},
            "ubicacion": {"type": "Point", "coordinates": [lng, lat]},
        }

    def crear(self, usuario: dict, datos: dict) -> dict:
        return self.repo.crear({**self._campos(datos), "id_usuario": usuario["id"]})

    def actualizar(self, id_lugar: int, datos: dict) -> dict:
        lugar = self.repo.actualizar(id_lugar, self._campos(datos))
        if lugar is None:
            raise NoEncontrado("No encontramos ese lugar.")
        return lugar

    def borrar(self, id_lugar: int) -> None:
        if not self.repo.borrar(id_lugar):
            raise NoEncontrado("No encontramos ese lugar.")
