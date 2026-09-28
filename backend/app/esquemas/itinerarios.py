from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.esquemas.comun import ReglaSalida, Salida
from app.esquemas.lugares import LugarSalida

Contexto = Literal["solo", "pareja", "amigos", "familia"]
Interes = Literal["comer", "cafe", "cultura", "entretenimiento", "aire_libre"]
Movilidad = Literal["caminando", "transporte_publico", "taxi_app", "combinado"]


class Presupuesto(BaseModel):
    min: float = Field(ge=0)
    max: float = Field(ge=0)

    @model_validator(mode="after")
    def _orden(self):
        if self.min > self.max:
            raise ValueError("el presupuesto mínimo no puede ser mayor que el máximo")
        return self


class Punto(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class PeticionPlan(BaseModel):
    """Lo que manda el botón **Crear mi plan** (CONTEXTO.md §6.1)."""

    contexto: Contexto
    presupuesto: Presupuesto = Field(description="Se recibe, pero aún no se evalúa: la base no tiene costos")
    tiempo_horas: float = Field(gt=0, le=24)
    intereses: list[Interes] = Field(min_length=1, description="Al menos uno")
    movilidad: list[Movilidad] = Field(min_length=1, description="Al menos uno")
    origen: Punto
    hora_salida: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$", examples=["18:00"])
    dia: str | None = Field(default=None, description="La app lo manda; aún no se usa (la base no tiene horarios)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "contexto": "pareja",
                    "presupuesto": {"min": 200, "max": 1500},
                    "tiempo_horas": 4,
                    "intereses": ["comer", "cafe", "entretenimiento"],
                    "movilidad": ["caminando", "taxi_app"],
                    "origen": {"lat": 19.2926, "lng": -99.6557},
                    "hora_salida": "18:00",
                }
            ]
        }
    }


class TramoSalida(Salida):
    modo: Literal["pie", "taxi"]
    duracion_min: int = Field(description="Estimación por distancia")
    minutos: int
    distancia_km: float
    desde: str
    hasta: str
    aviso: str | None = None


class ParadaPlan(Salida):
    lugar_id: str
    nombre: str
    llegada_estimada: str = Field(description="HH:MM, estimación")
    lugar: LugarSalida | None = None


class PlanSalida(Salida):
    tipo: Literal["equilibrado", "rapido", "economico"]
    mejor_opcion: bool
    costo: float | None = Field(description="null: la base no tiene costos")
    duracion_horas: float
    distancia_km: float
    paradas: list[ParadaPlan]
    tramos: list[TramoSalida] = []
    explicacion: str
    reglas_cumplidas: list[ReglaSalida]


class Descartado(Salida):
    lugar: LugarSalida
    lugar_id: str
    nombre: str
    reglas: list[ReglaSalida]


class RespuestaPlanes(Salida):
    datos_suficientes: bool
    mensaje: str | None = None
    aviso: str | None = None
    planes: list[PlanSalida]
    descartados: list[Descartado] = []


class PlanGuardado(BaseModel):
    """Fila de la tabla `planes`."""

    id: int
    no_acompanantes: int
    tiempo_disponible: int = Field(description="Minutos")
    categoria: str
    transporte: str
    fecha_plan: datetime | None
    creado_en: datetime | None
