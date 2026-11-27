"""SOLO LOCAL (no subir al repo): "Cerca de ti" con lugares reales de Google Places (New).

GET /api/lugares usa esto cuando la app manda su ubicación y hay GOOGLE_MAPS_API_KEY.
Si Google falla, el router regresa los lugares de la base como antes (la app no se rompe).

- Solo pide campos básicos (id, nombre, ubicación, tipos): es la tarifa más barata de Nearby Search.
- Una consulta por interés (máx. 4 lugares cada una) para que salgan de varias categorías.
- Guarda las respuestas 10 minutos en memoria: Inicio, Mapa y Buscar no vuelven a cobrar.
- No se guarda nada en la base (condiciones de Google).
"""

import time
import zlib

import httpx

from app.compartido.geo import distancia_km, geo_punto, minutos_caminando
from app.externos.google_places import TIEMPO_LIMITE_S, TIPOS_POR_INTERES, URL_CERCANOS, ErrorGooglePlaces
from app.nucleo.config import get_settings

CAMPOS_BASICOS = "places.id,places.displayName,places.location"
NOMBRES = {
    "comer": "Comer",
    "cafe": "Café",
    "cultura": "Cultura",
    "entretenimiento": "Entretenimiento",
    "aire_libre": "Aire libre",
}
RADIO_M = 3000
POR_INTERES = 4
CACHE_S = 600

_cache: dict[tuple, tuple[float, list[dict]]] = {}


def _consultar(cliente: httpx.Client, encabezados: dict, origen: dict, interes: str, maximo: int) -> list[dict]:
    ajustes = get_settings()
    cuerpo = {
        "includedTypes": TIPOS_POR_INTERES[interes],
        "maxResultCount": maximo,
        "rankPreference": "DISTANCE",
        "languageCode": ajustes.google_idioma,
        "regionCode": ajustes.google_region,
        "locationRestriction": {
            "circle": {"center": {"latitude": origen["lat"], "longitude": origen["lng"]}, "radius": RADIO_M}
        },
    }
    try:
        respuesta = cliente.post(URL_CERCANOS, json=cuerpo, headers=encabezados)
    except httpx.HTTPError as error:
        raise ErrorGooglePlaces("No se pudo conectar con Google Places.") from error
    if respuesta.status_code != 200:
        raise ErrorGooglePlaces(f"Google Places respondió con error {respuesta.status_code}.")

    lugares = []
    for place in respuesta.json().get("places", []):
        ubicacion = place.get("location") or {}
        lat, lng = ubicacion.get("latitude"), ubicacion.get("longitude")
        if place.get("id") is None or lat is None or lng is None:
            continue
        km = distancia_km(origen, {"lat": lat, "lng": lng})
        lugares.append({
            "_id": place["id"],
            "id": zlib.crc32(place["id"].encode()),  # la app usa _id; el int solo cumple con el esquema
            "nombre": (place.get("displayName") or {}).get("text") or "Lugar sin nombre",
            "lat": lat,
            "lng": lng,
            "ubicacion": geo_punto(lat, lng),
            "categoria": NOMBRES[interes],
            "id_categoria": None,
            "interes": interes,
            "distancia_km": round(km, 2),
            "minutos_caminando": minutos_caminando(km),
            "horario": None,
            "costo_promedio": None,
            "calificacion": None,
            "afluencia": None,
            "foto_url": None,
            "contextos": [],
            "fuente": "Google",
        })
    return lugares


def cercanos(origen: dict, interes: str | None = None) -> list[dict]:
    """Lugares reales cerca del origen, ordenados por distancia. Lanza ErrorGooglePlaces si no se puede."""
    ajustes = get_settings()
    if not ajustes.google_maps_api_key:
        raise ErrorGooglePlaces("Falta GOOGLE_MAPS_API_KEY.")

    llave = (round(origen["lat"], 3), round(origen["lng"], 3), interes)  # ~100 m
    guardado = _cache.get(llave)
    if guardado and time.monotonic() - guardado[0] < CACHE_S:
        return [dict(l) for l in guardado[1]]

    encabezados = {
        "X-Goog-Api-Key": ajustes.google_maps_api_key,
        "X-Goog-FieldMask": CAMPOS_BASICOS,
        "Content-Type": "application/json",
    }
    intereses = [interes] if interes else list(TIPOS_POR_INTERES)
    maximo = 15 if interes else POR_INTERES
    vistos: dict[str, dict] = {}
    with httpx.Client(timeout=TIEMPO_LIMITE_S) as cliente:
        for i in intereses:
            for lugar in _consultar(cliente, encabezados, origen, i, maximo):
                vistos.setdefault(lugar["_id"], lugar)

    lugares = sorted(vistos.values(), key=lambda l: l["distancia_km"])
    _cache[llave] = (time.monotonic(), lugares)
    return [dict(l) for l in lugares]
