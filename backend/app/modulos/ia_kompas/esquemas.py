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
    temperatura: float | None = Field(default=None, ge=-20.0, le=50.0, description="Temperatura en °C (del dispositivo)")
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
    consejo_clima: str | None = None


class EsquemaDestinoProbable(BaseModel):
    id_ruta: int
    nombre: str = Field(..., description="Nombre de la ruta (o 'Ruta N' si no tiene nombre)")
    ultima_parada: str | None = Field(default=None, description="Última parada capturada de la ruta, si la hay")
    probabilidad: float = Field(..., ge=0.0, le=1.0, description="Estimación según tus hábitos")
    viajes: int = Field(..., description="Veces que has tomado esta ruta")
    hora_habitual: str = Field(..., description="Mediana de la hora en que sueles tomarla (HH:MM)")


class EsquemaDestinosProbables(BaseModel):
    estado: str = Field(..., description="'ok' o 'datos_insuficientes'")
    metodo: str | None = Field(default=None, description="'frecuencia_franja' o 'knn'")
    hora_consulta: int
    dia_consulta: str
    franja: str
    viajes_analizados: int
    minimo_viajes: int
    destinos: list[EsquemaDestinoProbable]
    exactitud_validacion: float | None = Field(default=None, description="Leave-one-out del KNN")
    exactitud_baseline: float | None = Field(default=None, description="Leave-one-out de 'ruta más frecuente'")
    explicacion: str
    aviso: str


class EsquemaRutaFrecuente(BaseModel):
    id_ruta: int
    nombre: str
    ultima_parada: str | None = None
    viajes: int


class EsquemaMisHabitos(BaseModel):
    total_viajes: int
    rutas_frecuentes: list[EsquemaRutaFrecuente]
    transportes: dict[str, int]
    por_franja: dict[str, int]
    por_dia: dict[str, int]


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


class EsquemaEvaluacionModeloParticiones(BaseModel):
    model_config = ConfigDict(extra="ignore")
    dataset_kompas: dict
    tabla_comparativa_particiones: list[dict]
    particion_optima: dict
    particion_baseline_70_30: dict
    comparativa_optima_vs_70_30: dict
    analisis_underfitting_overfitting: dict
    comparacion_contra_reglas_fijas: dict
    matriz_confusion: dict
    importancia_variables: dict[str, float]


class EsquemaMetricasLaboratorioIA(BaseModel):
    model_config = ConfigDict(extra="ignore")
    resumen_limpieza: dict
    particion_optima: str
    max_depth_optimo: int
    comparativa_particiones: list[dict]
    curva_complejidad: list[dict]
    comparativa_sistemas: dict


class EsquemaPeticionSimulacionIA(BaseModel):
    model_config = ConfigDict(extra="ignore")
    distancia_km: float = Field(default=5.0, ge=0.1, le=50.0, description="Distancia del recorrido en km")
    presupuesto_mxn: float = Field(default=180.0, ge=0.0, le=5000.0, description="Presupuesto en MXN")
    rating_lugar: float = Field(default=4.5, ge=1.0, le=5.0, description="Rating del lugar (3.0 a 5.0)")
    num_paradas: int = Field(default=3, ge=1, le=15, description="Número de paradas del plan")
    trafico_nivel: int = Field(default=5, ge=1, le=10, description="Nivel de tráfico (1 a 10)")
    origen: str = Field(default="Terminal Toluca", description="Zona turística de origen para BFS")
    destino: str = Field(default="Galerias Metepec", description="Zona turística de destino para BFS")


class EsquemaRespuestaSimulacionIA(BaseModel):
    model_config = ConfigDict(extra="ignore")
    entrada: dict
    prediccion_reglas: dict
    prediccion_arbol_ml: dict
    coinciden_sistemas: bool
    ruta_bfs: EsquemaResultadoRutaBFS


