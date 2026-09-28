from typing import Literal

from pydantic import Field

from app.esquemas.comun import Salida


class RutaSalida(Salida):
    id: int
    id_texto: str = Field(alias="_id")
    trazo: list[tuple[float, float]] = Field(description="[[longitud, latitud], ...]")


class Tiempos(Salida):
    caminata: int | None
    espera: int | None
    trayecto: int | None


class Alternativa(Salida):
    id: str
    modo: Literal["pie", "taxi", "app"]
    tiempos: Tiempos
    distancia_km: float
    fuente: str
    fecha_verificacion: None = None
    avisos: list[str] = []


class RespuestaAlternativas(Salida):
    """Lo que espera la pantalla Buscar de la app (GET /api/rutas?origen=&destino=)."""

    datos_suficientes: bool
    mensaje: str | None = None
    alternativas: list[Alternativa]
