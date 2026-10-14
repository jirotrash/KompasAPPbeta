"""Esquemas de respuesta para la demostración académica de búsqueda DFS."""

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
