from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.esquemas.comun import GeoPunto, ReglaSalida, Salida

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
    presupuesto: Presupuesto = Field(description="presupuesto.max es el presupuesto por persona que evalúa el motor")
    tiempo_horas: float = Field(gt=0, le=24)
    intereses: list[Interes] = Field(min_length=1, description="Al menos uno")
    movilidad: list[Movilidad] = Field(min_length=1, description="Al menos uno")
    origen: Punto
    hora_salida: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$", examples=["18:00"])
    dia: str | None = Field(default=None, description="La app lo manda; el servidor usa la fecha de hoy en Toluca")

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
    modo: Literal["pie", "taxi", "autobus"]
    duracion_min: int | None = Field(description="Estimación por distancia; null si no se puede estimar (autobús)")
    minutos: int | None
    distancia_km: float
    desde: str
    hasta: str
    estimado: bool = True
    aviso: str | None = None


class RangoCosto(BaseModel):
    min: float | None
    max: float | None
    moneda: Literal["MXN"] = "MXN"


class LugarPlan(Salida):
    """Lugar de Google Places (no se guarda en MySQL: condiciones de Google)."""

    id_texto: str = Field(alias="_id", description="place_id de Google")
    nombre: str
    lat: float
    lng: float
    ubicacion: GeoPunto
    categoria: str
    interes: str
    nivel_precio: str | None = Field(default=None, description="priceLevel de Google; no se convierte a pesos")
    rango_precio: RangoCosto | None = Field(default=None, description="priceRange de Google, si lo trae")
    fuente: Literal["Google"] = "Google"
    consultado_en: str


class ParadaPlan(Salida):
    lugar_id: str = Field(description="place_id de Google")
    nombre: str
    llegada_estimada: str | None = Field(description="HH:MM, estimación")
    lugar: LugarPlan | None = None


class PlanSalida(Salida):
    tipo: Literal["equilibrado", "rapido", "cercano"]
    estado: Literal["recomendable"] = "recomendable"
    mejor_opcion: bool
    puntuacion: int = Field(ge=0, le=6, description="Puntuación de preferencias del motor de Einar")
    costo: None = Field(default=None, description="null: Google no da precios exactos")
    rango_costo: RangoCosto | None = Field(default=None, description="Suma estimada por persona según priceRange")
    duracion_horas: float
    distancia_km: float
    paradas: list[ParadaPlan]
    tramos: list[TramoSalida] = []
    explicacion: str
    reglas_cumplidas: list[ReglaSalida] = Field(description="Traza del motor: reglas activadas con su explicación")


class Descartado(Salida):
    """Itinerario candidato que el motor no recomendó, con su estado y los motivos."""

    tipo: Literal["equilibrado", "rapido", "cercano"]
    nombre: str
    lugares: list[str]
    estado: Literal["descartado", "pendiente_verificacion", "requiere_correccion"]
    reglas: list[ReglaSalida]
    datos_faltantes: list[str] = []


class RespuestaPlanes(Salida):
    datos_suficientes: bool
    mensaje: str | None = None
    aviso: str | None = None
    advertencias: list[str] = []
    version_reglas: str | None = None
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
