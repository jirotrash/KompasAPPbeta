from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.nucleo.esquemas_comunes import Salida

LIMITE_TEXTO = 2000


class Punto(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class MensajeEntrada(BaseModel):
    texto: str = Field(min_length=1, max_length=LIMITE_TEXTO, description="Máximo 2000 caracteres")
    ubicacion: Punto | None = Field(
        default=None, description='Ubicación actual del usuario para "desde aquí". No se guarda en la base'
    )

    model_config = {"json_schema_extra": {"examples": [{"texto": "¿Cómo llego al Cosmovitral desde aquí?", "ubicacion": {"lat": 19.2926, "lng": -99.6557}}]}}


class EstadoAsistente(BaseModel):
    disponible: bool
    modelo: str
    modelo_instalado: bool = Field(description="false: falta `ollama pull <modelo>`")


class PuntoNombrado(BaseModel):
    nombre: str
    lat: float
    lng: float


class Tarjeta(Salida):
    """Ruta o plan que regresó una herramienta. Las de conversaciones guardadas solo traen la referencia."""

    tipo: Literal["ruta", "plan"]
    titulo: str
    subtitulo: str | None = None
    id_ruta: int | None = None
    id_plan: int | None = None
    origen: PuntoNombrado | None = None
    destino: PuntoNombrado | None = None
    alternativa: dict | None = Field(default=None, description="Mejor opción de GET /api/rutas (solo en la respuesta)")
    plan: dict | None = Field(default=None, description="Plan recomendado de POST /api/itinerarios (solo en la respuesta)")
    destino_texto: str | None = Field(default=None, description="Destino como lo escribió el usuario (tarjetas guardadas)")


class MensajeChat(Salida):
    rol: Literal["usuario", "asistente", "herramienta", "error"]
    contenido: str | None = None
    nombre: str | None = Field(default=None, description="Herramienta que se llamó")
    argumentos: dict | None = None
    resultado_ref: dict | None = None
    duracion_ms: int | None = None
    tarjeta: Tarjeta | None = None
    creado_en: datetime


class RutaConsultada(BaseModel):
    id_ruta: int | None
    origen: str
    destino: str
    transporte: str
    consultado_en: datetime


class ConversacionResumen(BaseModel):
    id: str
    titulo: str | None
    ultimo_mensaje: str | None
    fecha: datetime
    total_mensajes: int


class Conversacion(BaseModel):
    id: str
    titulo: str | None
    modelo: str
    mensajes: list[MensajeChat]
    rutas_consultadas: list[RutaConsultada]
    planes_creados: list[int]
    created_at: datetime
    updated_at: datetime


class RespuestaMensaje(BaseModel):
    conversacion_id: str
    titulo: str | None
    mensaje: MensajeChat
    tarjetas: list[Tarjeta]
    herramientas_usadas: list[str]
