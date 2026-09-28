"""Piezas comunes de las respuestas (GeoJSON: [lng, lat])."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Salida(BaseModel):
    """Base de las respuestas: deja pasar campos extra (p. ej. los que agregue el motor de Einar)."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class GeoPunto(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: tuple[float, float] = Field(description="[longitud, latitud]")


class GeoLinea(BaseModel):
    type: Literal["LineString"] = "LineString"
    coordinates: list[tuple[float, float]] = Field(description="[[longitud, latitud], ...]")


class Regla(BaseModel):
    id: str
    descripcion: str | None = None


# La app acepta el id solo ("R1") o con su descripción
ReglaSalida = str | Regla
