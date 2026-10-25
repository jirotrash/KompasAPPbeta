from datetime import datetime

from pydantic import BaseModel, Field


class NuevoRecorrido(BaseModel):
    id_ruta: int
    id_transporte: int
    tiempo_estimado: int = Field(gt=0, le=24 * 60, description="Minutos (estimación)")


class RecorridoSalida(BaseModel):
    id: int
    id_ruta: int
    id_transporte: int
    transporte: str
    tiempo_estimado: int
    creado_en: datetime | None
