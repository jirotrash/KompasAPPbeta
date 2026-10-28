"""Contrato de reportes comunitarios (app/src/types/dominio.ts → Reporte, NuevoReporte, TipoReporte)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.nucleo.esquemas_comunes import GeoPunto, Salida

TipoReporte = Literal["afluencia", "cierre_total", "accidente", "manifestacion"]
NivelAfluencia = Literal["baja", "media", "alta"]


class NuevoReporte(BaseModel):
    tipo: TipoReporte
    nivel_afluencia: NivelAfluencia | None = None
    ubicacion: GeoPunto = Field(description="GeoJSON Point [longitud, latitud]")
    ruta_id: str | None = None
    lugar_id: str | None = None
    observado_en: datetime = Field(description="Cuándo lo vio el usuario (ISO 8601)")
    comentario: str | None = Field(default=None, max_length=500)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tipo": "manifestacion",
                    "ubicacion": {"type": "Point", "coordinates": [-99.625, 19.279]},
                    "observado_en": "2026-10-25T18:00:00-06:00",
                    "comentario": "Bloqueo en Paseo Tollocan",
                }
            ]
        }
    }


class ReporteSalida(Salida):
    id_texto: str = Field(alias="_id", description="ObjectId como texto")
    tipo: TipoReporte
    nivel_afluencia: NivelAfluencia | None = None
    ubicacion: GeoPunto
    ruta_id: str | None = None
    lugar_id: str | None = None
    observado_en: datetime
    vigente_hasta: datetime = Field(description="La calcula la API según el tipo")
    confirmaciones: int
    estado: Literal["pendiente", "verificado", "descartado"]
    comentario: str | None = None


EstadoReporte = Literal["pendiente", "verificado", "descartado"]


class CambioEstadoReporte(BaseModel):
    estado: EstadoReporte


class ReporteAdmin(ReporteSalida):
    id_usuario: int | None = Field(default=None, description="Quién lo reportó")
    vigente: bool = Field(description="vigente_hasta todavía no pasa")
