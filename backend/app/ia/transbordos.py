# ============================================================
# Transbordos con A*: combinar dos o más rutas de Kompás cuando ninguna sola conecta origen y destino
# ============================================================
# Grafo (se arma con los trazos de la colección `rutas`):
#   nodos   = las paradas de cada ruta (las de la base o, si no hay, los puntos del trazo) + origen + destino
#   aristas = - a lo largo de una ruta, en el sentido del trazo: costo = km × FACTOR_AUTOBUS
#             - a pie entre paradas de rutas distintas, o desde el origen / hacia el destino,
#               si están a ≤ 400 m: costo = km por calles × FACTOR_CAMINATA + PENALIZACION_TRANSBORDO
# Los factores (minutos por km) salen de compartido.traslados.
#
# Búsqueda: A* con heurística Euclidiana en km × FACTOR_AUTOBUS (el modo más rápido del grafo). Como
# ninguna arista cuesta menos que su distancia en línea recta a la velocidad del autobús, h nunca
# sobreestima: es admisible y A* devuelve la combinación de menor costo.
# ============================================================

from typing import Any

from app.compartido.geo import Coordenada, distancia_por_calles_km
from app.compartido.traslados import FACTOR_AUTOBUS, FACTOR_CAMINATA
from app.ia.busqueda_informada import a_estrella, distancia_plano_km
from app.ia.trazos import arbol_de_ruta, huella

RADIO_TRANSBORDO_KM = 0.4
# Parámetro de la búsqueda (en minutos-equivalentes) para preferir menos transbordos. No es un tiempo
# de espera medido y no se suma al tiempo que ve el usuario.
PENALIZACION_TRANSBORDO = 5.0
ORIGEN, DESTINO = "origen", "destino"


def _celda(p: Coordenada) -> tuple[int, int]:
    # ~0.4 km por celda en la zona piloto: los vecinos a ≤ 400 m están en la celda o en las 8 de alrededor
    return int(p["lat"] / 0.0036), int(p["lng"] / 0.0038)


def _caminar(coords: dict[str, Coordenada], a: str, b: str, penalizar: bool = True) -> dict[str, Any] | None:
    # Primero la recta (barata) para descartar; solo si está a ≤ 400 m se calcula la distancia por calles
    if distancia_plano_km(coords[a], coords[b]) > RADIO_TRANSBORDO_KM:
        return None
    km = distancia_por_calles_km(coords[a], coords[b])
    return {"destino": b, "costo": km * FACTOR_CAMINATA + (PENALIZACION_TRANSBORDO if penalizar else 0), "modo": "pie", "km": km}


# SOLO LOCAL (optimización para muchas rutas, p. ej. las del GTFS oficial): la parte del grafo que
# depende solo de las rutas (paradas, tramos en autobús y transbordos a pie) se arma una vez y se
# guarda en memoria; en cada búsqueda solo se agregan el origen y el destino. Si cambia cualquier
# ruta (alta, edición o baja), cambia la firma y el grafo se vuelve a armar.
_BASE: dict[str, Any] = {"firma": None}


def _grafo_de_rutas(rutas: list[dict[str, Any]]) -> tuple[dict, dict, dict, dict]:
    firma = tuple((r["id"], huella(r)) for r in rutas)
    if _BASE["firma"] == firma:
        return _BASE["grafo"], _BASE["coords"], _BASE["info"], _BASE["rejilla"]

    grafo: dict[str, list[dict[str, Any]]] = {}
    coords: dict[str, Coordenada] = {}
    info: dict[str, dict[str, Any]] = {}
    rejilla: dict[tuple[int, int], list[str]] = {}
    for ruta in rutas:
        arbol, _ = arbol_de_ruta(ruta)
        anterior: str | None = None
        for nodo_arbol in arbol.inorden():
            p = nodo_arbol.parada
            nodo = f"{ruta['id']}:{p['id']}"
            coords[nodo] = {"lat": p["lat"], "lng": p["lng"]}
            info[nodo] = {"id_ruta": ruta["id"], "parada": p, "km": nodo_arbol.clave}
            grafo[nodo] = []
            if anterior is not None:
                km = distancia_plano_km(coords[anterior], coords[nodo])
                grafo[anterior].append({"destino": nodo, "costo": km * FACTOR_AUTOBUS, "modo": "autobus", "km": km})
            anterior = nodo
            rejilla.setdefault(_celda(coords[nodo]), []).append(nodo)

    # Transbordos a pie entre paradas de rutas distintas
    for nodo, datos in info.items():
        f, c = _celda(coords[nodo])
        for otro in (n for df in (-1, 0, 1) for dc in (-1, 0, 1) for n in rejilla.get((f + df, c + dc), [])):
            if info[otro]["id_ruta"] != datos["id_ruta"] and (arista := _caminar(coords, nodo, otro)):
                grafo[nodo].append(arista)

    _BASE.update(firma=firma, grafo=grafo, coords=coords, info=info, rejilla=rejilla)
    return grafo, coords, info, rejilla


def armar_grafo(rutas: list[dict[str, Any]], origen: Coordenada, destino: Coordenada) -> tuple[dict, dict, dict]:
    """(grafo para busqueda_informada, coordenadas de cada nodo, info de cada nodo {id_ruta, parada, km})."""
    base, coords_base, info, rejilla = _grafo_de_rutas(rutas)
    # Copias superficiales: lo que se agrega para esta búsqueda no toca el grafo guardado
    grafo: dict[str, list[dict[str, Any]]] = {**base, ORIGEN: [], DESTINO: []}
    coords: dict[str, Coordenada] = {**coords_base, ORIGEN: origen, DESTINO: destino}

    def cercanos(p: Coordenada) -> list[str]:
        f, c = _celda(p)
        return [n for df in (-1, 0, 1) for dc in (-1, 0, 1) for n in rejilla.get((f + df, c + dc), [])]

    # Del origen a las paradas cercanas y de las paradas cercanas al destino
    for otro in cercanos(origen):
        if arista := _caminar(coords, ORIGEN, otro):
            grafo[ORIGEN].append(arista)
    for otro in cercanos(destino):
        if arista := _caminar(coords, otro, DESTINO):
            grafo[otro] = [*grafo[otro], arista]
    return grafo, coords, info


def buscar_transbordo(rutas: list[dict[str, Any]], origen: Coordenada, destino: Coordenada) -> dict[str, Any]:
    """A* sobre el grafo de rutas. Regresa {encontrado, tramos, rutas_usadas, nodos_explorados, ms, costo}.

    `tramos`: [{modo: pie | autobus, ...}] en orden. Si no hay combinación posible, encontrado = False
    (no se inventa una ruta).
    """
    grafo, coords, info = armar_grafo(rutas, origen, destino)
    resultado = a_estrella(ORIGEN, DESTINO, "euclidiana", grafo=grafo, coordenadas=coords, escala_h=FACTOR_AUTOBUS, con_traza=False)
    base = {
        "encontrado": False,
        "nodos_explorados": resultado.get("total_nodos_explorados", 0),
        "total_nodos": len(coords),
        "ms": resultado.get("ms", 0),
        "costo": resultado.get("costo_km"),
        "tramos": [],
        "rutas_usadas": [],
    }
    camino = resultado.get("camino") or []
    if not resultado.get("encontrado") or len(camino) < 2:
        return base

    # Agrupa el camino en tramos: caminatas sueltas y viajes continuos en una misma ruta
    tramos: list[dict[str, Any]] = []
    for a, b in zip(camino, camino[1:]):
        arista = next(x for x in grafo[a] if x["destino"] == b)
        if arista["modo"] == "autobus":
            if tramos and tramos[-1]["modo"] == "autobus" and tramos[-1]["id_ruta"] == info[a]["id_ruta"]:
                tramos[-1]["hasta"] = b
                tramos[-1]["km"] += arista["km"]
            else:
                tramos.append({"modo": "autobus", "id_ruta": info[a]["id_ruta"], "desde": a, "hasta": b, "km": arista["km"]})
        else:
            tramos.append({"modo": "pie", "desde": a, "hasta": b, "km": arista["km"]})

    salida = []
    for t in tramos:
        if t["modo"] == "autobus":
            salida.append(
                {
                    "modo": "autobus",
                    "id_ruta": t["id_ruta"],
                    "km_subida": info[t["desde"]]["km"],
                    "km_bajada": info[t["hasta"]]["km"],
                    "km": t["km"],
                }
            )
        else:
            salida.append({"modo": "pie", "km": t["km"], "desde": coords[t["desde"]], "hasta": coords[t["hasta"]]})
    usadas = list(dict.fromkeys(t["id_ruta"] for t in salida if t["modo"] == "autobus"))
    if not usadas:
        # Origen y destino junto a la misma parada: el camino es solo a pie (eso ya es la opción "a pie")
        return base
    return {**base, "encontrado": True, "tramos": salida, "rutas_usadas": usadas}
