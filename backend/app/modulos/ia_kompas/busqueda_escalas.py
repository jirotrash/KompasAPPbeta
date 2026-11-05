"""Búsqueda en grafo para minimización de escalas y transbordos en Kompás.

Implementa el algoritmo de Búsqueda en Anchura (BFS) sobre la red de paradas y atractivos
turísticos de Toluca, Metepec, Lerma y San Mateo Atenco utilizando una cola FIFO.
(Trazabilidad académica: adaptado de la práctica p01BFS).
"""

from collections import deque

# Grafo representativo de conectividad turística y de transporte en el Valle de Toluca
GRAFO_BASE_KOMPAS: dict[str, list[str]] = {
    "Terminal Toluca": ["Cosmovitral", "Centro Metepec", "Los Portales"],
    "Cosmovitral": ["Los Portales", "Alameda Central Toluca", "Terminal Toluca"],
    "Los Portales": ["Cosmovitral", "Alameda Central Toluca", "Parque Metropolitano Bicentenario"],
    "Alameda Central Toluca": ["Cosmovitral", "Los Portales", "Estadio Nemesio Diez"],
    "Estadio Nemesio Diez": ["Alameda Central Toluca", "Parque Metropolitano Bicentenario"],
    "Parque Metropolitano Bicentenario": ["Los Portales", "Estadio Nemesio Diez", "Centro Metepec", "Galerias Metepec"],
    "Centro Metepec": ["Terminal Toluca", "Parque Metropolitano Bicentenario", "Galerias Metepec", "Parque Ambiental Bicentenario"],
    "Galerias Metepec": ["Centro Metepec", "Parque Ambiental Bicentenario", "San Mateo Atenco"],
    "Parque Ambiental Bicentenario": ["Centro Metepec", "Galerias Metepec", "Lerma Centro"],
    "San Mateo Atenco": ["Galerias Metepec", "Lerma Centro"],
    "Lerma Centro": ["San Mateo Atenco", "Parque Ambiental Bicentenario", "Plazas Outlet Lerma"],
    "Plazas Outlet Lerma": ["Lerma Centro"],
}


def buscar_ruta_bfs(
    grafo: dict[str, list[str]] | None = None,
    origen: str = "Terminal Toluca",
    destino: str = "Centro Metepec",
) -> dict:
    """Ejecuta una búsqueda en anchura (BFS) para encontrar la ruta con menor número de escalas.

    Args:
        grafo: Diccionario de adyacencia (parada -> lista de paradas conectadas).
               Si es None, utiliza GRAFO_BASE_KOMPAS.
        origen: Nombre del lugar o parada de inicio.
        destino: Nombre del lugar o parada objetivo.

    Returns:
        dict con origen, destino, ruta_paradas, num_escalas, saltos_totales,
        algoritmo y booleano encontrado.
    """
    red = grafo if grafo is not None else GRAFO_BASE_KOMPAS

    if origen not in red or destino not in red:
        return {
            "origen": origen,
            "destino": destino,
            "ruta_paradas": [],
            "num_escalas": 0,
            "saltos_totales": 0,
            "algoritmo": "BFS (Búsqueda en Anchura)",
            "encontrado": False,
        }

    if origen == destino:
        return {
            "origen": origen,
            "destino": destino,
            "ruta_paradas": [origen],
            "num_escalas": 0,
            "saltos_totales": 0,
            "algoritmo": "BFS (Búsqueda en Anchura)",
            "encontrado": True,
        }

    # Cola FIFO de rutas exploradas (primero en entrar, primero en salir)
    cola = deque([[origen]])
    visitados = {origen}

    while cola:
        ruta = cola.popleft()
        nodo_actual = ruta[-1]

        if nodo_actual == destino:
            saltos = max(0, len(ruta) - 1)
            escalas = max(0, len(ruta) - 2)
            return {
                "origen": origen,
                "destino": destino,
                "ruta_paradas": ruta,
                "num_escalas": escalas,
                "saltos_totales": saltos,
                "algoritmo": "BFS (Búsqueda en Anchura)",
                "encontrado": True,
            }

        for vecino in red.get(nodo_actual, []):
            if vecino not in visitados:
                visitados.add(vecino)
                cola.append(ruta + [vecino])

    return {
        "origen": origen,
        "destino": destino,
        "ruta_paradas": [],
        "num_escalas": 0,
        "saltos_totales": 0,
        "algoritmo": "BFS (Búsqueda en Anchura)",
        "encontrado": False,
    }

