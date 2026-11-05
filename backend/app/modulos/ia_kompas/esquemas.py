"""Esquemas Pydantic para el módulo de IA y Machine Learning (ia_kompas)."""

from pydantic import BaseModel, ConfigDict, Field


class EsquemaConsultaRutaBFS(BaseModel):
    model_config = ConfigDict(extra="ignore")
    origen: str = Field(..., description="Nombre del lugar o parada de origen en Toluca/Metepec")
    destino: str = Field(..., description="Nombre del lugar o parada de destino")
    grafo: dict[str, list[str]] | None = Field(
        default=None,
        description="Grafo opcional de adyacencia de paradas. Si no se provee, se usa el mapa base de Kompás.",
    )


class EsquemaResultadoRutaBFS(BaseModel):
    model_config = ConfigDict(extra="ignore")
    origen: str
    destino: str
    ruta_paradas: list[str]
    num_escalas: int
    saltos_totales: int
    algoritmo: str = "BFS (Búsqueda en Anchura)"
    encontrado: bool = True


class EsquemaEvaluacionReglaFija(BaseModel):
    model_config = ConfigDict(extra="ignore")
    distancia_km: float = Field(..., ge=0.0, description="Distancia estimada en kilómetros")
    presupuesto_mxn: float = Field(..., ge=0.0, description="Presupuesto disponible en pesos mexicanos")
    hora_dia: int = Field(default=12, ge=0, le=23, description="Hora del día (0-23)")
    clima_lluvia: bool = Field(default=False, description="Indica si hay presencia de lluvia")


class EsquemaResultadoReglaFija(BaseModel):
    model_config = ConfigDict(extra="ignore")
    modo_recomendado: str
    regla_activada: str
    explicacion: str
    metodo: str = "regla_fija"


class EsquemaConsultaTrasladoIA(BaseModel):
    model_config = ConfigDict(extra="ignore")
    distancia_km: float = Field(..., ge=0.0, description="Distancia estimada en km")
    presupuesto_mxn: float = Field(..., ge=0.0, description="Presupuesto disponible en MXN")
    hora_dia: int = Field(default=12, ge=0, le=23, description="Hora del día (0 a 23)")
    es_hora_pico: bool | None = Field(default=None, description="Si es hora pico (se deduce si no se indica)")
    clima_lluvia: bool = Field(default=False, description="Si está lloviendo")
    rating_destino: float = Field(default=4.5, ge=1.0, le=5.0, description="Calificación promedio del destino en Google Places")
    origen: str = Field(default="Origen", description="Punto o lugar de origen")
    destino: str = Field(default="Destino", description="Punto o lugar de destino")


class EsquemaRespuestaTrasladoIA(BaseModel):
    model_config = ConfigDict(extra="ignore")
    modo_recomendado: str
    confianza: float = Field(..., ge=0.0, le=1.0)
    origen_decision: str = Field(..., description="'machine_learning' o 'regla_fija'")
    tiempo_estimado_min: int
    ruta_bfs: EsquemaResultadoRutaBFS | None = None
    comparacion_baseline: dict
    explicacion: str


class EsquemaEstadoPipeline(BaseModel):
    model_config = ConfigDict(extra="ignore")
    dataset_crudo_filas: int
    dataset_limpio_filas: int
    nulos_detectados: dict[str, int]
    duplicados_eliminados: int
    outliers_eliminados: int
    exactitud_modelo_ml: float
    exactitud_regla_fija: float
    particion: dict[str, int]
    importancia_variables: dict[str, float]
