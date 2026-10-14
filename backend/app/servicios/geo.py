"""Distancias, horas y zona piloto (misma zona que la app: src/constants/zona.ts).

Coordenadas: dict {"lat": .., "lng": ..}. Geometrías GeoJSON: [lng, lat].
Todos los tiempos son ESTIMACIONES calculadas por distancia (por calles = métrica Manhattan).
"""

import math
from datetime import datetime, timedelta, timezone
from typing import TypedDict

from app.ia.metricas_distancia import distancia_euclidiana, distancia_manhattan


class Coordenada(TypedDict):
    lat: float
    lng: float


# México centro no tiene horario de verano desde 2022: UTC-6 fijo (sin depender de tzdata en Windows)
HORA_MEXICO = timezone(timedelta(hours=-6), "America/Mexico_City")

MIN_POR_KM_A_PIE = 12  # BACKEND.md §6: ≈ 12 min por km
VELOCIDAD_AUTO_KMH = 25

# Kilómetros por grado (aproximación local; suficiente para la zona piloto)
KM_POR_GRADO_LAT = 110.574
KM_POR_GRADO_LNG_ECUADOR = 111.320
ESPERA_TAXI_MIN = 5

# Zona piloto PROVISIONAL (rectángulo aproximado); Sebas define los límites definitivos
ZONA = {
    "nombre": "Toluca · Lerma · San Mateo Atenco",
    "limites": {"sur": 19.2, "oeste": -99.76, "norte": 19.42, "este": -99.38},
}


def redondear(x: float) -> int:
    """Como Math.round de JavaScript (0.5 hacia arriba)."""
    return math.floor(x + 0.5)


def distancia_km(a: Coordenada, b: Coordenada) -> float:
    """Distancia en línea recta (haversine)."""
    rad = math.radians
    d_lat = rad(b["lat"] - a["lat"])
    d_lng = rad(b["lng"] - a["lng"])
    h = math.sin(d_lat / 2) ** 2 + math.cos(rad(a["lat"])) * math.cos(rad(b["lat"])) * math.sin(d_lng / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def a_plano_km(p: Coordenada, referencia: Coordenada) -> tuple[float, float]:
    """Proyecta lat/lng a un plano local en km (x = este, y = norte) con origen en `referencia`."""
    km_por_grado_lng = KM_POR_GRADO_LNG_ECUADOR * math.cos(math.radians(referencia["lat"]))
    return (
        (p["lng"] - referencia["lng"]) * km_por_grado_lng,
        (p["lat"] - referencia["lat"]) * KM_POR_GRADO_LAT,
    )


def distancia_euclidiana_km(a: Coordenada, b: Coordenada) -> float:
    """Línea recta sobre el plano local (en la zona piloto coincide con haversine)."""
    return distancia_euclidiana(a_plano_km(a, a), a_plano_km(b, a))


def distancia_manhattan_km(a: Coordenada, b: Coordenada) -> float:
    """Recorrido por cuadras (este-oeste + norte-sur) sobre el plano local."""
    return distancia_manhattan(a_plano_km(a, a), a_plano_km(b, a))


def distancia_por_calles_km(a: Coordenada, b: Coordenada) -> float:
    """Estimación de la distancia por calles: métrica Manhattan.

    Antes se usaba "línea recta × 1.3". En promedio Manhattan mide 4/π ≈ 1.27 veces la línea
    recta, pero ahora depende de la dirección: igual a la recta si el trayecto va derecho
    por una calle y hasta 1.41 veces si va en diagonal a la cuadrícula.
    """
    return distancia_manhattan_km(a, b)


def minutos_caminando(km: float) -> int:
    return max(1, redondear(km * MIN_POR_KM_A_PIE))


def minutos_en_auto(km: float) -> int:
    return redondear(km / VELOCIDAD_AUTO_KMH * 60) + ESPERA_TAXI_MIN


def esta_dentro_de_zona(p: Coordenada) -> bool:
    lim = ZONA["limites"]
    return lim["sur"] <= p["lat"] <= lim["norte"] and lim["oeste"] <= p["lng"] <= lim["este"]


def geo_punto(lat: float, lng: float) -> dict:
    return {"type": "Point", "coordinates": [lng, lat]}


def leer_punto(texto: str) -> Coordenada:
    """Convierte "lat,lng" (parámetro de consulta de la app) en coordenada. ValueError si no es válido."""
    partes = texto.split(",")
    if len(partes) != 2:
        raise ValueError(texto)
    lat, lng = (float(p) for p in partes)
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise ValueError(texto)
    return {"lat": lat, "lng": lng}


# ──────────────────────────────────── Horas ────────────────────────────────────


def a_minutos_del_dia(hhmm: str) -> int:
    h, m = hhmm.split(":")[:2]
    return int(h) * 60 + int(m)


def a_hora(minutos: float) -> str:
    total = redondear(minutos) % 1440
    return f"{total // 60:02d}:{total % 60:02d}"


def ahora_mexico() -> datetime:
    return datetime.now(HORA_MEXICO)


def hora_actual() -> str:
    return ahora_mexico().strftime("%H:%M")
