"""Geometría de los trazos de la colección `rutas` (GeoJSON [[lng, lat], ...]) para el árbol y A*.

Funciones puras: km acumulado de cada punto, proyección de un punto sobre el trazo y las paradas de
una ruta. Las distancias se miden en el plano local en km de busqueda_informada (centrado en Toluca).
"""

import hashlib
import json
from typing import Any

from app.compartido.geo import Coordenada
from app.ia.arbol_binario import ArbolParadas
from app.ia.busqueda_informada import a_km, distancia_plano_km


def punto(par: list[float] | tuple[float, float]) -> Coordenada:
    return {"lat": par[1], "lng": par[0]}


def km_acumulados(trazo: list[list[float]]) -> list[float]:
    """km desde el inicio de la ruta hasta cada punto del trazo."""
    acumulado = [0.0]
    for a, b in zip(trazo, trazo[1:]):
        acumulado.append(acumulado[-1] + distancia_plano_km(punto(a), punto(b)))
    return acumulado


def proyectar(p: Coordenada, trazo: list[list[float]], acumulado: list[float] | None = None) -> dict[str, Any]:
    """Punto del trazo más cercano a `p`: {km (desde el inicio), distancia_km (de p al trazo), lat, lng}."""
    acumulado = acumulado or km_acumulados(trazo)
    px, py = a_km(p)
    mejor: dict[str, Any] | None = None
    if len(trazo) == 1:
        c = punto(trazo[0])
        return {"km": 0.0, "distancia_km": distancia_plano_km(p, c), **c}
    for i, (a, b) in enumerate(zip(trazo, trazo[1:])):
        ax, ay = a_km(punto(a))
        bx, by = a_km(punto(b))
        dx, dy = bx - ax, by - ay
        largo2 = dx * dx + dy * dy
        t = 0.0 if largo2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / largo2))
        qx, qy = ax + t * dx, ay + t * dy
        d = ((px - qx) ** 2 + (py - qy) ** 2) ** 0.5
        if mejor is None or d < mejor["distancia_km"]:
            mejor = {
                "km": acumulado[i] + t * (acumulado[i + 1] - acumulado[i]),
                "distancia_km": d,
                "lng": a[0] + t * (b[0] - a[0]),
                "lat": a[1] + t * (b[1] - a[1]),
            }
    assert mejor is not None
    return mejor


def paradas_de_ruta(ruta: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    """(paradas ordenadas por km, son_reales).

    Si la ruta trae `paradas` en la base ([{nombre, ubicacion: {coordinates: [lng, lat]}}]) se usan esas,
    proyectadas sobre el trazo. Si no, cada punto del trazo es una parada "Punto N" (no se inventan
    nombres) y son_reales = False.
    """
    trazo = ruta["trazo"]
    acumulado = km_acumulados(trazo)
    reales = ruta.get("paradas") or []
    if reales:
        salida = []
        for i, p in enumerate(reales):
            lng, lat = p["ubicacion"]["coordinates"]
            km = proyectar({"lat": lat, "lng": lng}, trazo, acumulado)["km"]
            salida.append({"km": km, "id": p.get("id", f"{ruta['id']}-{i + 1}"), "nombre": p["nombre"], "lat": lat, "lng": lng})
        return sorted(salida, key=lambda p: p["km"]), True
    return [
        {"km": km, "id": f"{ruta['id']}-{i + 1}", "nombre": f"Punto {i + 1}", "lat": par[1], "lng": par[0]}
        for i, (par, km) in enumerate(zip(trazo, acumulado))
    ], False


def huella(ruta: dict[str, Any]) -> str:
    """Identifica el contenido de la ruta: si el trazo o las paradas cambian, cambia la huella."""
    datos = json.dumps([ruta["trazo"], ruta.get("paradas") or []], sort_keys=True, default=str)
    return hashlib.sha1(datos.encode()).hexdigest()


# Árboles ya construidos: {id_ruta: (huella, árbol, paradas_reales)}. Se invalida si cambia la huella.
_CACHE: dict[Any, tuple[str, ArbolParadas, bool]] = {}


def arbol_de_ruta(ruta: dict[str, Any]) -> tuple[ArbolParadas, bool]:
    """Árbol balanceado de las paradas de la ruta, construido una vez y guardado en memoria."""
    firma = huella(ruta)
    guardado = _CACHE.get(ruta["id"])
    if guardado and guardado[0] == firma:
        return guardado[1], guardado[2]
    paradas, reales = paradas_de_ruta(ruta)
    arbol = ArbolParadas.construir_balanceado(paradas)
    _CACHE[ruta["id"]] = (firma, arbol, reales)
    return arbol, reales


def tramo_del_trazo(trazo: list[list[float]], desde_km: float, hasta_km: float) -> list[list[float]]:
    """Puntos del trazo entre dos km (incluye los puntos de corte), como [[lng, lat], ...]."""
    acumulado = km_acumulados(trazo)

    def en(km: float) -> list[float]:
        for i in range(len(trazo) - 1):
            if acumulado[i] <= km <= acumulado[i + 1]:
                largo = acumulado[i + 1] - acumulado[i]
                t = 0.0 if largo == 0 else (km - acumulado[i]) / largo
                a, b = trazo[i], trazo[i + 1]
                return [a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])]
        return list(trazo[-1])

    medio = [list(p) for p, km in zip(trazo, acumulado) if desde_km < km < hasta_km]
    return [en(desde_km), *medio, en(hasta_km)]
