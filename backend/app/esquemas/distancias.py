"""Esquemas de respuesta del laboratorio de métricas de distancia (Euclidiana y Manhattan)."""

from pydantic import BaseModel


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
