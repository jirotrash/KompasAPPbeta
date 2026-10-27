from typing import Literal

from pydantic import BaseModel, Field

from app.nucleo.esquemas_comunes import Salida


class RutaSalida(Salida):
    id: int
    id_texto: str = Field(alias="_id")
    trazo: list[tuple[float, float]] = Field(description="[[longitud, latitud], ...]")


class Tiempos(Salida):
    caminata: int | None
    espera: int | None
    trayecto: int | None


class ParadaRuta(Salida):
    nombre: str = Field(description='Parada real de la base o "Punto N" del trazo (no se inventan nombres)')
    lat: float
    lng: float
    km: float = Field(description="km desde el inicio de la ruta")


class TramoOpcion(Salida):
    """Camina → ruta X → (transbordo) → ruta Y → camina. Los campos de autobús solo vienen en ese modo."""

    modo: Literal["pie", "autobus"]
    distancia_km: float
    duracion_min: int = Field(description="Estimación por distancia")
    id_ruta: int | None = None
    linea: str | None = None
    parada_subida: ParadaRuta | None = None
    parada_bajada: ParadaRuta | None = None
    tramo_en_ruta: list[tuple[float, float]] | None = Field(default=None, description="[[lng, lat], ...] entre subida y bajada")
    paradas_intermedias: list[ParadaRuta] | None = None
    trazo_ruta: list[tuple[float, float]] | None = Field(default=None, description="Trazo completo de la ruta [[lng, lat], ...]")


class Alternativa(Salida):
    id: str
    modo: Literal["pie", "taxi", "app", "autobus"]
    tiempos: Tiempos
    distancia_km: float
    fuente: str
    fecha_verificacion: None = None
    avisos: list[str] = []
    # Solo en las opciones en autobús (campos nuevos, opcionales)
    tipo: Literal["directo", "combinado"] | None = Field(default=None, description="combinado = con transbordo")
    id_ruta: int | None = None
    linea: str | None = None
    parada_subida: ParadaRuta | None = None
    parada_bajada: ParadaRuta | None = None
    tramo_en_ruta: list[tuple[float, float]] | None = Field(default=None, description="[[lng, lat], ...] del tramo en autobús")
    paradas_intermedias: list[ParadaRuta] | None = None
    numero_transbordos: int | None = None
    tramos: list[TramoOpcion] | None = None


class NodoArbol(BaseModel):
    clave: float = Field(description="km acumulado desde el inicio de la ruta")
    parada: dict
    izquierdo: "NodoArbol | None" = None
    derecho: "NodoArbol | None" = None


class ParadaArbol(Salida):
    km: float
    id: str
    nombre: str
    lat: float
    lng: float


class ArbolRuta(BaseModel):
    """GET /api/rutas/{id}/arbol: árbol binario de búsqueda (balanceado) de las paradas de la ruta."""

    id_ruta: int
    nombre: str
    paradas_reales: bool = Field(description='false: no hay paradas capturadas y se usan los puntos del trazo ("Punto N")')
    raiz: NodoArbol | None
    altura: int
    total_nodos: int
    inorden: list[ParadaArbol]
    preorden: list[ParadaArbol]
    postorden: list[ParadaArbol]


class RespuestaAlternativas(Salida):
    """Lo que espera la pantalla Buscar de la app (GET /api/rutas?origen=&destino=)."""

    datos_suficientes: bool
    mensaje: str | None = None
    alternativas: list[Alternativa]
