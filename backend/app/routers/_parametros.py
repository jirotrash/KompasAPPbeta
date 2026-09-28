"""Lectura de coordenadas en parámetros de consulta: "lat,lng" (como manda la app) o lat= y lng=."""

from fastapi import HTTPException, status

from app.servicios.geo import Coordenada, leer_punto


def punto_de_consulta(nombre: str, texto: str | None) -> Coordenada | None:
    if not texto:
        return None
    try:
        return leer_punto(texto)
    except ValueError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, f'"{nombre}" debe tener el formato lat,lng (ej. 19.2926,-99.6557).'
        ) from None


def punto_lat_lng(lat: float | None, lng: float | None) -> Coordenada | None:
    if lat is None and lng is None:
        return None
    if lat is None or lng is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Envía lat y lng juntos.")
    return {"lat": lat, "lng": lng}
