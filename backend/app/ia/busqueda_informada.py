# ============================================================
# Búsqueda informada para Kompás: costo uniforme (UCS), voraz y A*
# ============================================================
# Reutiliza la red académica de busqueda_dfs.py (GRAFO_TRANSPORTE y PARADAS_KOMPAS): no la copia.
#
#   UCS:   f(n) = g(n)          expande siempre el nodo con menor costo acumulado
#   Voraz: f(n) = h(n)          primero el mejor: el nodo que "parece" más cerca del destino
#   A*:    f(n) = g(n) + h(n)   costo acumulado + estimación de lo que falta
#
# g(n): suma de los costos de las aristas desde el origen. El costo de una arista es la distancia en
#       km entre sus dos nodos (los tiempos `tiempo_min` del grafo no se usan: no están verificados y
#       están en otra unidad). Si una arista trae `costo`, se usa ese valor.
# h(n): distancia del nodo n al destino con distancia_euclidiana o distancia_manhattan de
#       metricas_distancia.py, sobre coordenadas convertidas a km con una proyección local
#       equirectangular centrada en Toluca:
#           x = (lng - lng₀) · 111.320 · cos(lat₀)      y = (lat - lat₀) · 110.574
#       con (lat₀, lng₀) = Centro de Toluca. En la zona piloto la diferencia con haversine es < 0.1 %.
#
# Admisibilidad: la Euclidiana nunca sobreestima la distancia real (la línea recta es el camino más
# corto posible), así que A* con Euclidiana encuentra el camino óptimo. La Manhattan puede
# sobreestimar (|Δx| + |Δy| ≥ √(Δx² + Δy²)), así que no es admisible y A* puede devolver un camino
# que no es el óptimo. comparar_algoritmos() lo muestra con datos.
# ============================================================

import heapq
import math
import time
from collections.abc import Callable
from typing import Any

from app.compartido.geo import Coordenada, a_plano_km
from app.ia.busqueda_dfs import FUENTE_RED_DFS, GRAFO_TRANSPORTE, PARADAS_KOMPAS, calcular_detalle_ruta, planificar_rutas_dfs
from app.ia.metricas_distancia import distancia_euclidiana, distancia_manhattan

Grafo = dict[str, list[dict[str, Any]]]

# Centro de Toluca (el mismo punto de referencia que usa la app en src/constants/zona.ts)
REFERENCIA_TOLUCA: Coordenada = {"lat": 19.2926, "lng": -99.6557}

HEURISTICAS: dict[str, Callable[[tuple[float, float], tuple[float, float]], float]] = {
    "euclidiana": distancia_euclidiana,
    "manhattan": distancia_manhattan,
}
# Propiedad teórica de cada heurística (ver encabezado)
ADMISIBLE = {"euclidiana": True, "manhattan": False}
NOMBRES = {"costo_uniforme": "Costo uniforme (UCS)", "voraz": "Voraz (primero el mejor)", "a_estrella": "A*"}
MENSAJE_NODO_DESCONOCIDO = "El origen o destino indicado no se encuentra en el catalogo de paradas de Kompas."


def a_km(p: Coordenada) -> tuple[float, float]:
    """lat/lng → (x, y) en km sobre el plano local centrado en Toluca."""
    return a_plano_km(p, REFERENCIA_TOLUCA)


def distancia_plano_km(a: Coordenada, b: Coordenada) -> float:
    """Distancia en km entre dos coordenadas en el plano local (la que usa g(n))."""
    return distancia_euclidiana(a_km(a), a_km(b))


def coordenadas_red_dfs() -> dict[str, Coordenada]:
    return {nodo: {"lat": p["lat"], "lng": p["lng"]} for nodo, p in PARADAS_KOMPAS.items()}


def _r(x: float) -> float:
    return round(x, 4)


def _buscar(
    algoritmo: str,
    origen: str,
    destino: str,
    heuristica: str | None,
    grafo: Grafo,
    coordenadas: dict[str, Coordenada],
    escala_h: float,
    con_traza: bool,
) -> dict[str, Any]:
    """Búsqueda en grafo con cola de prioridad. `algoritmo`: costo_uniforme | voraz | a_estrella."""
    if heuristica is not None and heuristica not in HEURISTICAS:
        raise ValueError(f"Heurística desconocida: {heuristica}")
    if origen not in coordenadas or destino not in coordenadas:
        return {"exito": False, "mensaje": MENSAJE_NODO_DESCONOCIDO, "algoritmo": algoritmo, "heuristica": heuristica}

    destino_km = a_km(coordenadas[destino])
    medir = HEURISTICAS.get(heuristica or "")

    def h(nodo: str) -> float:
        return escala_h * medir(a_km(coordenadas[nodo]), destino_km) if medir else 0.0

    def f(g: float, hn: float) -> float:
        return {"costo_uniforme": g, "voraz": hn, "a_estrella": g + hn}[algoritmo]

    def costo(a: str, arista: dict[str, Any]) -> float:
        if arista.get("costo") is not None:
            return float(arista["costo"])
        return distancia_plano_km(coordenadas[a], coordenadas[arista["destino"]])

    inicio = time.perf_counter()
    g: dict[str, float] = {origen: 0.0}
    padre: dict[str, str | None] = {origen: None}
    contador = 0  # desempate estable: a igual f, el que entró primero
    frontera: list[tuple[float, int, str]] = [(f(0.0, h(origen)), contador, origen)]
    explorados: set[str] = set()
    orden: list[str] = []
    traza: list[dict[str, Any]] = []
    encontrado = False

    while frontera:
        _, _, nodo = heapq.heappop(frontera)
        if nodo in explorados:
            continue  # entrada vieja: el nodo ya salió con un costo menor
        explorados.add(nodo)
        orden.append(nodo)
        paso: dict[str, Any] = {"paso": len(orden), "nodo": nodo, "g": _r(g[nodo]), "h": _r(h(nodo)), "f": _r(f(g[nodo], h(nodo)))}
        if nodo == destino:
            encontrado = True
            if con_traza:
                traza.append({**paso, "tipo": "objetivo", "expandidos": [], "frontera": _frontera(frontera, explorados, g, h, f)})
            break

        expandidos = []
        for arista in grafo.get(nodo, []):
            vecino = arista["destino"]
            if vecino in explorados or vecino not in coordenadas:
                continue
            g_nuevo = g[nodo] + costo(nodo, arista)
            # Voraz no reabre nodos ya descubiertos; UCS y A* sí, si encuentran un camino más barato
            mejora = vecino not in g if algoritmo == "voraz" else g_nuevo < g.get(vecino, math.inf)
            if mejora:
                g[vecino] = g_nuevo
                padre[vecino] = nodo
                contador += 1
                heapq.heappush(frontera, (f(g_nuevo, h(vecino)), contador, vecino))
                expandidos.append(vecino)
        if con_traza:
            traza.append({**paso, "tipo": "expande", "expandidos": expandidos, "frontera": _frontera(frontera, explorados, g, h, f)})

    camino: list[str] = []
    if encontrado:
        actual: str | None = destino
        while actual is not None:
            camino.append(actual)
            actual = padre[actual]
        camino.reverse()

    return {
        "exito": True,
        "encontrado": encontrado,
        "algoritmo": algoritmo,
        "nombre": NOMBRES[algoritmo],
        "heuristica": heuristica,
        "es_admisible": ADMISIBLE[heuristica] if heuristica else True,
        "camino": camino,
        "costo_km": _r(g[destino]) if encontrado else None,
        "longitud_camino": max(0, len(camino) - 1),
        "orden_exploracion": orden,
        "traza": traza,
        "total_nodos_explorados": len(orden),
        "ms": round((time.perf_counter() - inicio) * 1000, 3),
    }


def _frontera(frontera, explorados, g, h, f) -> list[dict[str, Any]]:
    """Frontera ordenada por f (cada nodo una vez, con su mejor entrada), para mostrarla como tabla."""
    vistos: set[str] = set()
    filas = []
    for _, _, nodo in sorted(frontera):
        if nodo in explorados or nodo in vistos:
            continue
        vistos.add(nodo)
        filas.append({"nodo": nodo, "g": _r(g[nodo]), "h": _r(h(nodo)), "f": _r(f(g[nodo], h(nodo)))})
    return filas


def _con_red_dfs(resultado: dict[str, Any], origen: str, destino: str) -> dict[str, Any]:
    """Agrega los datos de la red académica (nombres y tramos) con la misma forma que el DFS."""
    resultado.update({"fuente": FUENTE_RED_DFS, "datos_verificados": False})
    if not resultado["exito"]:
        resultado.update({"orden_exploracion": [], "rutas": []})
        return resultado
    resultado["origen"] = PARADAS_KOMPAS[origen]
    resultado["destino"] = PARADAS_KOMPAS[destino]
    resultado["paradas"] = [PARADAS_KOMPAS[n]["nombre"] for n in resultado["camino"]]
    resultado["rutas"] = [calcular_detalle_ruta(resultado["camino"])] if resultado["camino"] else []
    resultado["total_rutas_encontradas"] = len(resultado["rutas"])
    return resultado


def costo_uniforme(
    origen: str, destino: str, *, grafo: Grafo | None = None, coordenadas: dict[str, Coordenada] | None = None, con_traza: bool = True
) -> dict[str, Any]:
    """UCS: f(n) = g(n). Sin grafo, usa la red académica del DFS."""
    if grafo is None:
        return _con_red_dfs(_buscar("costo_uniforme", origen, destino, None, GRAFO_TRANSPORTE, coordenadas_red_dfs(), 1.0, con_traza), origen, destino)
    return _buscar("costo_uniforme", origen, destino, None, grafo, coordenadas or {}, 1.0, con_traza)


def voraz(
    origen: str,
    destino: str,
    heuristica: str = "euclidiana",
    *,
    grafo: Grafo | None = None,
    coordenadas: dict[str, Coordenada] | None = None,
    escala_h: float = 1.0,
    con_traza: bool = True,
) -> dict[str, Any]:
    """Primero el mejor: f(n) = h(n)."""
    if grafo is None:
        return _con_red_dfs(_buscar("voraz", origen, destino, heuristica, GRAFO_TRANSPORTE, coordenadas_red_dfs(), 1.0, con_traza), origen, destino)
    return _buscar("voraz", origen, destino, heuristica, grafo, coordenadas or {}, escala_h, con_traza)


def a_estrella(
    origen: str,
    destino: str,
    heuristica: str = "euclidiana",
    *,
    grafo: Grafo | None = None,
    coordenadas: dict[str, Coordenada] | None = None,
    escala_h: float = 1.0,
    con_traza: bool = True,
) -> dict[str, Any]:
    """A*: f(n) = g(n) + h(n). `escala_h` convierte h a la unidad de los costos (p. ej. km → minutos)."""
    if grafo is None:
        return _con_red_dfs(_buscar("a_estrella", origen, destino, heuristica, GRAFO_TRANSPORTE, coordenadas_red_dfs(), 1.0, con_traza), origen, destino)
    return _buscar("a_estrella", origen, destino, heuristica, grafo, coordenadas or {}, escala_h, con_traza)


def costo_real_al_destino(destino: str, grafo: Grafo = GRAFO_TRANSPORTE, coordenadas: dict[str, Coordenada] | None = None) -> dict[str, float]:
    """h*(n): costo mínimo real de cada nodo al destino (Dijkstra sobre el grafo invertido)."""
    coordenadas = coordenadas or coordenadas_red_dfs()
    inverso: dict[str, list[tuple[str, float]]] = {}
    for a, aristas in grafo.items():
        for arista in aristas:
            c = arista.get("costo")
            c = float(c) if c is not None else distancia_plano_km(coordenadas[a], coordenadas[arista["destino"]])
            inverso.setdefault(arista["destino"], []).append((a, c))
    real = {destino: 0.0}
    cola = [(0.0, destino)]
    while cola:
        d, nodo = heapq.heappop(cola)
        if d > real.get(nodo, math.inf):
            continue
        for anterior, c in inverso.get(nodo, []):
            if d + c < real.get(anterior, math.inf):
                real[anterior] = d + c
                heapq.heappush(cola, (d + c, anterior))
    return real


def _primer_camino_dfs(origen: str, destino: str) -> dict[str, Any]:
    inicio = time.perf_counter()
    # Límite = número de aristas máximo de un camino simple: DFS encuentra todos los caminos
    r = planificar_rutas_dfs(origen, destino, limite_profundidad=len(PARADAS_KOMPAS) - 1)
    ms = round((time.perf_counter() - inicio) * 1000, 3)
    coords = coordenadas_red_dfs()

    def km(camino: list[str]) -> float:
        return sum(distancia_plano_km(coords[a], coords[b]) for a, b in zip(camino, camino[1:]))

    caminos = [ruta["nodos_id"] for ruta in r.get("rutas", [])]
    primero = caminos[0] if caminos else []
    return {
        "algoritmo": "dfs",
        "nombre": "DFS (profundidad)",
        "heuristica": None,
        "es_admisible": None,
        "camino": primero,
        "costo_km": _r(km(primero)) if primero else None,
        "longitud_camino": max(0, len(primero) - 1),
        "total_nodos_explorados": r.get("total_nodos_explorados", 0),
        "total_rutas_encontradas": len(caminos),
        "mejor_costo_km": _r(min(km(c) for c in caminos)) if caminos else None,
        "ms": ms,
    }


def comparar_algoritmos(origen: str, destino: str) -> dict[str, Any]:
    """DFS, UCS, voraz (2 heurísticas) y A* (2 heurísticas) sobre la red académica, en una tabla."""
    if origen not in PARADAS_KOMPAS or destino not in PARADAS_KOMPAS:
        return {"exito": False, "mensaje": MENSAJE_NODO_DESCONOCIDO, "fuente": FUENTE_RED_DFS, "datos_verificados": False, "filas": []}

    ucs = costo_uniforme(origen, destino, con_traza=False)
    corridas = [_primer_camino_dfs(origen, destino), ucs]
    for nombre in HEURISTICAS:
        corridas.append(voraz(origen, destino, nombre, con_traza=False))
    for nombre in HEURISTICAS:
        corridas.append(a_estrella(origen, destino, nombre, con_traza=False))

    optimo = ucs["costo_km"]
    filas = [
        {
            "algoritmo": c["algoritmo"],
            "nombre": c["nombre"],
            "heuristica": c["heuristica"],
            "es_admisible": c["es_admisible"],
            "costo_km": c["costo_km"],
            "nodos_explorados": c["total_nodos_explorados"],
            "longitud_camino": c["longitud_camino"],
            "optimo": c["costo_km"] is not None and optimo is not None and math.isclose(c["costo_km"], optimo, abs_tol=1e-6),
            "ms": c["ms"],
            "camino": c["camino"],
            "paradas": [PARADAS_KOMPAS[n]["nombre"] for n in c["camino"]],
        }
        for c in corridas
    ]

    # Datos de admisibilidad: ¿en qué nodos h(n) supera al costo real h*(n)?
    real = costo_real_al_destino(destino)
    coords = coordenadas_red_dfs()
    destino_km = a_km(coords[destino])
    heuristicas = {}
    for nombre, medir in HEURISTICAS.items():
        excesos = []
        for nodo, h_real in real.items():
            hn = medir(a_km(coords[nodo]), destino_km)
            if hn > h_real + 1e-9:
                excesos.append({"nodo": nodo, "h": _r(hn), "h_real": _r(h_real), "exceso_km": _r(hn - h_real)})
        heuristicas[nombre] = {
            "es_admisible": ADMISIBLE[nombre],
            "nodos_sobreestimados": sorted(excesos, key=lambda e: -e["exceso_km"]),
        }

    return {
        "exito": True,
        "fuente": FUENTE_RED_DFS,
        "datos_verificados": False,
        "origen": PARADAS_KOMPAS[origen],
        "destino": PARADAS_KOMPAS[destino],
        "costo_optimo_km": optimo,
        "alcanzable": optimo is not None,
        "filas": filas,
        "heuristicas": heuristicas,
    }
