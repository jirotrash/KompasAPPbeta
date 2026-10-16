"""Endpoints del laboratorio de métricas de distancia (Euclidiana y Manhattan)."""

import math

from fastapi import APIRouter, HTTPException, Query, status

from app.esquemas.distancias import ComparacionGeo, ComparacionPlano
from app.ia.metricas_distancia import Punto, comparar_distancias, fmt
from app.routers._parametros import punto_de_consulta
from app.servicios.geo import (
    desglose_manhattan_km,
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
    """Las mismas métricas con coordenadas reales, en km sobre un plano local.

    El recorrido Manhattan va primero de este a oeste (sobre la latitud del origen) y luego de norte a sur.
    Kompás estima la distancia por calles con Manhattan.
    """
    a = punto_de_consulta("origen", origen)
    b = punto_de_consulta("destino", destino)
    este_oeste, norte_sur = desglose_manhattan_km(a, b)
    euclidiana = distancia_euclidiana_km(a, b)
    manhattan = distancia_manhattan_km(a, b)
    recta = distancia_km(a, b)
    return {
        "origen": a,
        "destino": b,
        "esquina": {"lat": a["lat"], "lng": b["lng"]},
        "este_oeste_km": round(este_oeste, 3),
        "norte_sur_km": round(norte_sur, 3),
        "linea_recta_km": round(recta, 3),
        "euclidiana_km": round(euclidiana, 3),
        "manhattan_km": round(manhattan, 3),
        "diferencia_km": round(manhattan - euclidiana, 3),
        "minutos_caminando_recta": minutos_caminando(recta),
        "minutos_caminando_calles": minutos_caminando(manhattan),
        "pasos": {
            "euclidiana": f"√({fmt(este_oeste)}² + {fmt(norte_sur)}²) = "
            f"√({fmt(este_oeste**2)} + {fmt(norte_sur**2)}) = {fmt(euclidiana)} km",
            "manhattan": f"{fmt(este_oeste)} + {fmt(norte_sur)} = {fmt(manhattan)} km",
        },
        "nota": "Kompás usa la distancia Manhattan para estimar trayectos por calles.",
    }
