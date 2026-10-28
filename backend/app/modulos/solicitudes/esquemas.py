from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.nucleo.esquemas_comunes import GeoPunto

EstadoSolicitud = Literal["pendiente", "atendida", "descartada"]


class NuevaSolicitud(BaseModel):
    """Lo manda la app cuando "¿Cómo llego?" no encontró camión y la persona pide que se agregue la ruta."""

    origen: GeoPunto = Field(description="GeoJSON Point [longitud, latitud]")
    destino: GeoPunto = Field(description="GeoJSON Point [longitud, latitud]")
    comentario: str | None = Field(default=None, max_length=500, description="Ej. «Tomo la ruta que pasa por Tollocan»")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "origen": {"type": "Point", "coordinates": [-99.511, 19.2847]},
                    "destino": {"type": "Point", "coordinates": [-99.6557, 19.2926]},
                    "comentario": "Hay una combi que va por Tollocan",
                }
            ]
        }
    }


class CambioSolicitud(BaseModel):
    estado: EstadoSolicitud
    nota_admin: str | None = Field(default=None, max_length=500, description="Respuesta o nota interna del equipo")


class SolicitudSalida(BaseModel):
    id: str = Field(description="ObjectId como texto")
    id_usuario: int
    origen: GeoPunto
    destino: GeoPunto
    comentario: str | None
    estado: EstadoSolicitud
    nota_admin: str | None
    creado_en: datetime
    actualizado_en: datetime
