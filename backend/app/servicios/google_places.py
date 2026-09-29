"""Lugares cercanos desde Google Places API (New) — Nearby Search (BACKEND.md §6).

Se consulta desde el backend (la llave nunca va en la app). Condiciones de Google: no guardar en MySQL
nombres, horarios ni calificaciones; solo se puede conservar el place_id.
Si Google falla o no hay llave, se lanza ErrorGooglePlaces (la API responde 503): no se inventan lugares.
"""

from datetime import datetime

import httpx

from app.config import get_settings
from app.servicios.geo import ahora_mexico

URL_CERCANOS = "https://places.googleapis.com/v1/places:searchNearby"
# Horario, precio y calificación son de la tarifa Enterprise: se piden solo para el planificador
CAMPOS = (
    "places.id,places.displayName,places.location,places.types,places.primaryType,"
    "places.regularOpeningHours,places.priceLevel,places.priceRange,places.rating,places.userRatingCount"
)
RADIO_MAXIMO_KM = 5
RESULTADOS_POR_INTERES = 10
TIEMPO_LIMITE_S = 10

# Categoría de la app → includedTypes de Google (tabla fija de BACKEND.md §6)
TIPOS_POR_INTERES = {
    "comer": ["restaurant"],
    "cafe": ["cafe", "coffee_shop"],
    "cultura": ["museum", "art_gallery", "cultural_center"],
    "entretenimiento": ["movie_theater", "bowling_alley", "amusement_center"],
    "aire_libre": ["park"],
}


class ErrorGooglePlaces(Exception):
    """Google no respondió o no está configurado. El mensaje se muestra tal cual en el 503."""


def _dinero(valor: dict | None) -> float | None:
    """Money de Google ({currencyCode, units, nanos}) → pesos. Solo MXN; otra moneda o sin dato → None."""
    if not isinstance(valor, dict) or valor.get("currencyCode") != "MXN":
        return None
    try:
        return float(valor.get("units", 0)) + int(valor.get("nanos", 0)) / 1e9
    except (TypeError, ValueError):
        return None


def rango_precio(place: dict) -> dict | None:
    """priceRange → {"min", "max", "moneda": "MXN"}. Sin priceRange → None.

    priceLevel ($–$$$$) NO se convierte a pesos (decisión de Einar, INTEGRAR_IA.md §3).
    """
    rango = place.get("priceRange")
    if not isinstance(rango, dict):
        return None
    minimo, maximo = _dinero(rango.get("startPrice")), _dinero(rango.get("endPrice"))
    if minimo is None and maximo is None:
        return None
    return {"min": minimo, "max": maximo, "moneda": "MXN"}


def normalizar(place: dict, categoria: str, consultado_en: datetime) -> dict | None:
    """Respuesta de Google → lugar que usan el planificador y la app. None si le falta ubicación."""
    ubicacion = place.get("location") or {}
    lat, lng = ubicacion.get("latitude"), ubicacion.get("longitude")
    if place.get("id") is None or lat is None or lng is None:
        return None
    return {
        "place_id": place["id"],
        "nombre": (place.get("displayName") or {}).get("text") or "Lugar sin nombre",
        "lat": lat,
        "lng": lng,
        "categoria": categoria,
        "tipos": place.get("types", []),
        # Se pasa directo el objeto de Google (con periods); hechos.py lo interpreta
        "horario": place.get("regularOpeningHours"),
        "nivel_precio": place.get("priceLevel"),
        "rango_precio": rango_precio(place),
        "calificacion": place.get("rating"),
        "total_resenas": place.get("userRatingCount"),
        "fuente": "Google",
        "consultado_en": consultado_en.isoformat(),
    }


def buscar_para_plan(
    origen: dict, intereses: list[str], radio_km: float, *, cliente: httpx.Client | None = None
) -> list[dict]:
    """Lugares cercanos al origen para cada interés de la solicitud (un lugar aparece una sola vez)."""
    ajustes = get_settings()
    if not ajustes.google_maps_api_key:
        raise ErrorGooglePlaces("Falta configurar GOOGLE_MAPS_API_KEY en el servidor: no se pueden buscar lugares.")

    encabezados = {
        "X-Goog-Api-Key": ajustes.google_maps_api_key,
        "X-Goog-FieldMask": CAMPOS,
        "Content-Type": "application/json",
    }
    radio_m = min(radio_km, RADIO_MAXIMO_KM) * 1000
    propio = cliente is None
    cliente = cliente or httpx.Client(timeout=TIEMPO_LIMITE_S)
    lugares: dict[str, dict] = {}
    try:
        for interes in intereses:
            cuerpo = {
                "includedTypes": TIPOS_POR_INTERES[interes],
                "maxResultCount": RESULTADOS_POR_INTERES,
                "rankPreference": "DISTANCE",
                "languageCode": ajustes.google_idioma,
                "regionCode": ajustes.google_region,
                "locationRestriction": {
                    "circle": {"center": {"latitude": origen["lat"], "longitude": origen["lng"]}, "radius": radio_m}
                },
            }
            try:
                respuesta = cliente.post(URL_CERCANOS, json=cuerpo, headers=encabezados)
            except httpx.HTTPError as error:
                raise ErrorGooglePlaces("No se pudo conectar con Google Places; intenta de nuevo en un momento.") from error
            if respuesta.status_code == 429:
                raise ErrorGooglePlaces("Se agotó la cuota de Google Places; intenta más tarde.")
            if respuesta.status_code != 200:
                raise ErrorGooglePlaces(f"Google Places respondió con error {respuesta.status_code}; no se inventan lugares.")
            consultado = ahora_mexico()
            for place in respuesta.json().get("places", []):
                lugar = normalizar(place, interes, consultado)
                if lugar and lugar["place_id"] not in lugares:
                    lugares[lugar["place_id"]] = lugar
    finally:
        if propio:
            cliente.close()
    return list(lugares.values())
