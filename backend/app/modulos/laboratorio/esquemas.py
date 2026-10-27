"""Esquemas de las demostraciones académicas: DFS, métricas de distancia, búsqueda informada y genético."""

from pydantic import BaseModel, ConfigDict, Field


class SalidaDFS(BaseModel):
    """Permite serializar los nombres de campo que requiere la respuesta."""

    model_config = ConfigDict(populate_by_name=True)


class ParadaInfo(SalidaDFS):
    nombre: str
    lat: float
    lng: float


class ParadaCatalogo(ParadaInfo):
    id: str


class TramoDFS(SalidaDFS):
    de_: str = Field(alias="de")
    a: str
    linea: str
    modo: str
    tiempo_min: int


class RutaDFS(SalidaDFS):
    paradas: list[str]
    nodos_id: list[str]
    tiempo_total_minutos: int
    numero_transbordos: int
    tramos: list[TramoDFS]


class PasoDFS(SalidaDFS):
    paso: int
    tipo: str
    nodo: str
    hacia: str | None = None
    profundidad: int
    camino: list[str]
    mensaje: str


class RespuestaDFS(SalidaDFS):
    exito: bool
    fuente: str
    datos_verificados: bool
    mensaje: str | None = None
    aviso: str | None = None
    origen: ParadaInfo | None = None
    destino: ParadaInfo | None = None
    limite_profundidad_aplicado: int | None = None
    orden_exploracion: list[str] = Field(default_factory=list)
    traza: list[PasoDFS] = Field(default_factory=list)
    total_nodos_explorados: int = 0
    total_rutas_encontradas: int = 0
    rutas: list[RutaDFS] = Field(default_factory=list)


# ───────────── Métricas de distancia (Euclidiana y Manhattan) ─────────────


class PuntoPlano(BaseModel):
    x: float
    y: float


class PasosCalculo(BaseModel):
    euclidiana: str
    manhattan: str


class ComparacionPlano(BaseModel):
    a: PuntoPlano
    b: PuntoPlano
    esquina: PuntoPlano
    horizontal: float
    vertical: float
    euclidiana: float
    manhattan: float
    diferencia: float
    alineados: bool
    pasos: PasosCalculo


class PuntoGeo(BaseModel):
    lat: float
    lng: float


class ComparacionGeo(BaseModel):
    origen: PuntoGeo
    destino: PuntoGeo
    esquina: PuntoGeo
    este_oeste_km: float
    norte_sur_km: float
    linea_recta_km: float
    euclidiana_km: float
    manhattan_km: float
    diferencia_km: float
    minutos_caminando_recta: int
    minutos_caminando_calles: int
    pasos: PasosCalculo
    nota: str


# ───────────── Búsqueda informada (comparativo) ─────────────


class FilaComparativo(BaseModel):
    algoritmo: str = Field(description="dfs | costo_uniforme | voraz | a_estrella")
    nombre: str
    heuristica: str | None
    es_admisible: bool | None = Field(description="Propiedad teórica de la heurística (None en DFS)")
    costo_km: float | None
    nodos_explorados: int
    longitud_camino: int = Field(description="Número de aristas del camino")
    optimo: bool = Field(description="Mismo costo que UCS")
    ms: float
    camino: list[str]
    paradas: list[str]


class Sobreestimacion(BaseModel):
    nodo: str
    h: float
    h_real: float = Field(description="Costo mínimo real al destino (h*)")
    exceso_km: float


class DatosHeuristica(BaseModel):
    es_admisible: bool
    nodos_sobreestimados: list[Sobreestimacion] = Field(description="Nodos donde h(n) > h*(n) en este grafo")


class ComparativoBusqueda(BaseModel):
    exito: bool
    fuente: str
    datos_verificados: bool
    origen: ParadaInfo
    destino: ParadaInfo
    costo_optimo_km: float | None
    alcanzable: bool
    filas: list[FilaComparativo]
    heuristicas: dict[str, DatosHeuristica]


# ───────────── Algoritmo genético ─────────────


class ParadaGenetico(BaseModel):
    nombre: str | None = None
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class PeticionGenetico(BaseModel):
    paradas: list[ParadaGenetico] = Field(min_length=1, max_length=30)
    origen: PuntoGeo | None = Field(default=None, description="Punto fijo de salida (opcional)")
    poblacion: int | None = Field(default=None, ge=2, le=500, description="Por defecto 60")
    generaciones: int | None = Field(default=None, ge=1, le=2000, description="Por defecto 150")
    prob_cruza: float | None = Field(default=None, ge=0, le=1, description="Por defecto 0.9")
    prob_mutacion: float | None = Field(default=None, ge=0, le=1, description="Por defecto 0.2")
    semilla: int | None = Field(default=None, description="Para reproducir el resultado")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "origen": {"lat": 19.2926, "lng": -99.6557},
                    "paradas": [
                        {"nombre": "A", "lat": 19.2890, "lng": -99.6640},
                        {"nombre": "B", "lat": 19.2785, "lng": -99.6455},
                        {"nombre": "C", "lat": 19.2838, "lng": -99.6765},
                        {"nombre": "D", "lat": 19.2740, "lng": -99.6350},
                    ],
                    "semilla": 7,
                }
            ]
        }
    }


class PuntoHistorial(BaseModel):
    generacion: int
    mejor: float = Field(description="Mejor aptitud hasta esa generación")
    promedio: float = Field(description="Aptitud promedio de la población")


class OptimoFuerzaBruta(BaseModel):
    orden: list[int]
    distancia_km: float


class RespuestaGenetico(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    mejor_orden: list[int]
    orden_paradas: list[str]
    distancia_km: float
    distancia_original_km: float
    aptitud: float
    paradas_fuera_de_horario: int
    generacion_mejor: int
    historial: list[PuntoHistorial]
    parametros: dict
    optimo_fuerza_bruta: OptimoFuerzaBruta | None
    brecha_vs_optimo: float | None = Field(alias="brecha_vs_optimo_%")
    ms: float
