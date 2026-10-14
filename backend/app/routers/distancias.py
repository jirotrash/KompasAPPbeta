"""Endpoints del laboratorio de métricas de distancia (Euclidiana y Manhattan)."""

import math

from fastapi import APIRouter, HTTPException, Query, status

from app.esquemas.distancias import ComparacionGeo, ComparacionPlano
from app.ia.metricas_distancia import Punto, comparar_distancias
from app.routers._parametros import punto_de_consulta
from app.servicios.geo import (
    distancia_euclidiana_km,
    distancia_km,
    distancia_manhattan_km,
    minutos_caminando,
)

router = APIRouter(prefix="/api/distancias", tags=["Métricas de distancia (académica)"])


def punto_plano(nombre: str, texto: str) -> Punto:
    """Convierte "x,y" en un punto del plano cartesiano."""
    try:
        x, y = (float(parte) for parte in texto.split(","))
        if not (math.isfinite(x) and math.isfinite(y)):
            raise ValueError
    except ValueError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, f'"{nombre}" debe tener el formato x,y (ej. 1,2).'
        ) from None
    return (x, y)


@router.get("/plano", response_model=ComparacionPlano)
def comparar_en_plano(
    a: str = Query(..., description="Punto A como x,y (ej. 1,2)"),
    b: str = Query(..., description="Punto B como x,y (ej. 5,5)"),
) -> dict:
    """Compara la distancia Euclidiana y la Manhattan entre dos puntos de un plano cartesiano."""
    return comparar_distancias(punto_plano("a", a), punto_plano("b", b))


@router.get("/geo", response_model=ComparacionGeo)
def comparar_en_mapa(
    origen: str = Query(..., description="lat,lng"),
    destino: str = Query(..., description="lat,lng"),
) -> dict:
    """Las mismas métricas con coordenadas reales. Kompás estima la distancia por calles con Manhattan."""
    a = punto_de_consulta("origen", origen)
    b = punto_de_consulta("destino", destino)
    manhattan = distancia_manhattan_km(a, b)
    recta = distancia_km(a, b)
    return {
        "linea_recta_km": round(recta, 2),
        "euclidiana_km": round(distancia_euclidiana_km(a, b), 2),
        "manhattan_km": round(manhattan, 2),
        "minutos_caminando_recta": minutos_caminando(recta),
        "minutos_caminando_calles": minutos_caminando(manhattan),
        "nota": "Kompás usa la distancia Manhattan para estimar trayectos por calles.",
    }
