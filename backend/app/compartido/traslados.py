"""Tramos entre dos puntos: a pie o en taxi/app. Funciones puras (sin BD).

No hay tramos en autobús: la base todavía no tiene líneas ni paradas (BACKEND.md §10).
Todos los tiempos son ESTIMACIONES por distancia.
"""

from app.compartido.geo import MIN_POR_KM_A_PIE, Coordenada, distancia_por_calles_km, minutos_caminando, minutos_en_auto, redondear

DISTANCIA_CORTA_KM = 1.5
RADIO_A_PIE_KM = 2  # BACKEND.md §7: caminando ≈ 2 km
RADIO_TAXI_KM = 8  # taxi/app ≈ 8 km

# Autobús: la misma velocidad que usa la app (src/utils/geo.ts → VELOCIDAD_KMH.autobus).
# Solo para estimar el trayecto sobre un trazo registrado; no incluye la espera (no hay frecuencias).
VELOCIDAD_AUTOBUS_KMH = 18
MIN_POR_KM_AUTOBUS = 60 / VELOCIDAD_AUTOBUS_KMH
# Factores de costo (minutos por km) para la búsqueda de transbordos
FACTOR_CAMINATA = MIN_POR_KM_A_PIE
FACTOR_AUTOBUS = MIN_POR_KM_AUTOBUS


def minutos_en_autobus(km: float) -> int:
    """Trayecto estimado sobre el trazo de la ruta (sin espera ni tráfico)."""
    return max(1, redondear(km * MIN_POR_KM_AUTOBUS))

AVISO_TAXI = "El tiempo no considera el tráfico. La tarifa la define el proveedor."
AVISO_SIN_AUTOBUS = "No tenemos líneas de autobús registradas: este tramo se estima caminando."


def permite_pie(movilidad: list[str]) -> bool:
    # Sin líneas de autobús registradas, "transporte público" solo se puede estimar a pie
    return bool({"caminando", "combinado", "transporte_publico"} & set(movilidad))


def permite_taxi(movilidad: list[str]) -> bool:
    return bool({"taxi_app", "combinado"} & set(movilidad))


def radio_km(movilidad: list[str]) -> float:
    return RADIO_TAXI_KM if permite_taxi(movilidad) else RADIO_A_PIE_KM


def tramo(a: Coordenada, b: Coordenada, movilidad: list[str], desde: str = "", hasta: str = "") -> dict:
    """A pie si es cerca (o si no eligió taxi); en taxi/app si lo eligió y no es cerca."""
    km = distancia_por_calles_km(a, b)
    a_pie = not permite_taxi(movilidad) or (permite_pie(movilidad) and km <= DISTANCIA_CORTA_KM)
    if a_pie:
        minutos = minutos_caminando(km)
        solo_autobus = set(movilidad) == {"transporte_publico"}
        aviso = AVISO_SIN_AUTOBUS if solo_autobus and km > DISTANCIA_CORTA_KM else None
        modo = "pie"
    else:
        minutos = minutos_en_auto(km)
        aviso = AVISO_TAXI
        modo = "taxi"
    return {
        "modo": modo,
        "duracion_min": minutos,
        "minutos": minutos,
        "distancia_km": round(km, 2),
        "desde": desde,
        "hasta": hasta,
        "aviso": aviso,
    }
