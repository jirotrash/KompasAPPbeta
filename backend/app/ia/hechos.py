"""Hechos booleanos de cada lugar (BACKEND.md §7), calculados antes de aplicar las reglas.

# TEMPORAL — Einar reemplaza con sus hechos definitivos.
"""

from app.ia.reglas import APTO_CONTEXTO, ESTANCIA_MIN
from app.servicios.geo import distancia_km
from app.servicios.traslados import permite_taxi, radio_km, tramo


def estancia(lugar: dict) -> int:
    return ESTANCIA_MIN.get(lugar.get("interes") or "", 60)


def datos_suficientes(lugar: dict) -> bool:
    """Tiene coordenadas y categoría."""
    return lugar.get("lat") is not None and lugar.get("lng") is not None and bool(lugar.get("categoria"))


def coincide_intereses(lugar: dict, intereses: list[str]) -> bool:
    return lugar.get("interes") in intereses


def apto_contexto(lugar: dict, contexto: str) -> bool:
    return lugar.get("interes") in APTO_CONTEXTO.get(contexto, set())


def calcular(lugar: dict, solicitud: dict) -> tuple[dict[str, bool], dict]:
    """Regresa los hechos del lugar y datos auxiliares (distancia, traslado desde el origen)."""
    if not datos_suficientes(lugar):
        return {"datos_suficientes": False}, {"km": None, "traslado": None, "minutos": None}

    punto = {"lat": lugar["lat"], "lng": lugar["lng"]}
    movilidad = solicitud["movilidad"]
    km = distancia_km(solicitud["origen"], punto)
    traslado = tramo(solicitud["origen"], punto, movilidad)["duracion_min"]
    minutos = traslado + estancia(lugar)
    hechos = {
        "datos_suficientes": True,
        "coincide_intereses": coincide_intereses(lugar, solicitud["intereses"]),
        "cerca": km <= radio_km(movilidad),
        "solo_a_pie": not permite_taxi(movilidad),
        "apto_contexto": apto_contexto(lugar, solicitud["contexto"]),
        "cabe_en_tiempo": minutos <= solicitud["tiempo_horas"] * 60,
    }
    return hechos, {"km": km, "traslado": traslado, "minutos": minutos}
