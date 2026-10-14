# ============================================================
# Modulo de Busqueda DFS para la Red de Transporte Kompas
# ============================================================
# Se implemento el algoritmo de busqueda en profundidad (DFS) adaptado a la red
# de transporte del Valle de Toluca, incorporando control de ciclos, profundidad maxima,
# registro del orden de exploracion y calculo de todas las rutas viables.
# ============================================================

from typing import Any

# Esta red sirve exclusivamente como material académico para demostrar DFS. Sus
# conexiones y tiempos no están verificados, por lo que no se mezcla con /api/rutas.
FUENTE_RED_DFS = "Red académica de demostración (sin verificación operativa)"

# Se definieron las estaciones y paradas clave del corredor piloto de Kompás con coordenadas [lat, lng]
PARADAS_KOMPAS = {
    "TerminalToluca": {"nombre": "Terminal de Autobuses de Toluca", "lat": 19.2785, "lng": -99.6455},
    "CentroToluca": {"nombre": "Centro Historico de Toluca", "lat": 19.2926, "lng": -99.6557},
    "PinoSuarez": {"nombre": "Av. Pino Suarez y Las Torres", "lat": 19.2740, "lng": -99.6350},
    "CiudadUniversitaria": {"nombre": "Ciudad Universitaria UAEMex", "lat": 19.2838, "lng": -99.6765},
    "ParqueAlameda": {"nombre": "Alameda Central de Toluca", "lat": 19.2890, "lng": -99.6640},
    "GaleriasMetepec": {"nombre": "Galerias Metepec", "lat": 19.2550, "lng": -99.6280},
    "CentroMetepec": {"nombre": "Centro Magico de Metepec", "lat": 19.2520, "lng": -99.6050},
    "Tecnologico": {"nombre": "Instituto Tecnologico de Toluca", "lat": 19.2580, "lng": -99.5850},
    "PlazaSendero": {"nombre": "Plaza Sendero Lerma", "lat": 19.2890, "lng": -99.5350},
}

# Se definio el grafo de conexiones de transporte con presencia de ciclos
# Ciclos incluidos para demostrar la robustez del algoritmo:
# Circuito 1: TerminalToluca -> CentroToluca -> PinoSuarez -> TerminalToluca
# Circuito 2: GaleriasMetepec -> CentroMetepec -> Tecnologico -> GaleriasMetepec
GRAFO_TRANSPORTE = {
    "TerminalToluca": [
        {"destino": "CentroToluca", "linea": "Linea 1 Centro", "tiempo_min": 15, "modo": "autobus"},
        {"destino": "PinoSuarez", "linea": "Linea 2 Periferica", "tiempo_min": 12, "modo": "autobus"},
        {"destino": "CiudadUniversitaria", "linea": "Linea 5 Universitaria", "tiempo_min": 20, "modo": "autobus"},
    ],
    "CentroToluca": [
        {"destino": "PinoSuarez", "linea": "Linea 2 Periferica", "tiempo_min": 10, "modo": "autobus"},
        {"destino": "GaleriasMetepec", "linea": "Linea 3 Intermunicipal", "tiempo_min": 22, "modo": "autobus"},
        {"destino": "ParqueAlameda", "linea": "Linea 1 Centro", "tiempo_min": 8, "modo": "autobus"},
    ],
    "PinoSuarez": [
        {"destino": "TerminalToluca", "linea": "Linea 2 Periferica (Retorno)", "tiempo_min": 12, "modo": "autobus"},
        {"destino": "CentroMetepec", "linea": "Linea 4 Metepec Directo", "tiempo_min": 18, "modo": "autobus"},
    ],
    "CiudadUniversitaria": [
        {"destino": "ParqueAlameda", "linea": "Linea 5 Universitaria", "tiempo_min": 14, "modo": "autobus"},
        {"destino": "CentroToluca", "linea": "Linea 1 Centro", "tiempo_min": 16, "modo": "autobus"},
    ],
    "ParqueAlameda": [
        {"destino": "CentroMetepec", "linea": "Linea 3 Intermunicipal", "tiempo_min": 20, "modo": "autobus"},
        {"destino": "PlazaSendero", "linea": "Linea 7 Expreso Oriente", "tiempo_min": 28, "modo": "autobus"},
    ],
    "GaleriasMetepec": [
        {"destino": "CentroMetepec", "linea": "Linea 4 Metepec Directo", "tiempo_min": 10, "modo": "autobus"},
        {"destino": "Tecnologico", "linea": "Linea 6 Tecnologico", "tiempo_min": 14, "modo": "autobus"},
        {"destino": "TerminalToluca", "linea": "Linea 3 Intermunicipal (Retorno)", "tiempo_min": 25, "modo": "autobus"},
    ],
    "CentroMetepec": [
        {"destino": "Tecnologico", "linea": "Linea 6 Tecnologico", "tiempo_min": 12, "modo": "autobus"},
        {"destino": "PlazaSendero", "linea": "Linea 7 Expreso Oriente", "tiempo_min": 24, "modo": "autobus"},
    ],
    "Tecnologico": [
        {"destino": "GaleriasMetepec", "linea": "Linea 6 Tecnologico (Retorno)", "tiempo_min": 14, "modo": "autobus"},
        {"destino": "PlazaSendero", "linea": "Linea 8 Sendero", "tiempo_min": 16, "modo": "autobus"},
    ],
    "PlazaSendero": [],
}


def busqueda_dfs_transporte(
    grafo: dict[str, list[dict[str, Any]]],
    actual: str,
    objetivo: str,
    limite_profundidad: int = 5,
    camino_actual: list[str] | None = None,
    orden_exploracion: list[str] | None = None,
    todas_las_rutas: list[list[str]] | None = None,
    traza: list[dict[str, Any]] | None = None,
) -> tuple[list[list[str]], list[str], list[dict[str, Any]]]:
    """Ejecuta la busqueda en profundidad (DFS) en el grafo de transporte.

    Requisitos cubiertos:
    - 2.1 Orden de exploracion: se registra cada estado en 'orden_exploracion'.
    - 2.2 Control de ciclos: se evita visitar nodos que ya estan en 'camino_actual'.
    - 2.3 Todas las rutas: no se detiene en la primera solucion; aplica backtracking para hallar todas.
    - 2.4 Limite de profundidad: restringe la exploracion si se excede 'limite_profundidad'.
    """
    if camino_actual is None:
        camino_actual = [actual]
        orden_exploracion = []
        todas_las_rutas = []
        traza = []

    def registrar(tipo: str, mensaje: str, hacia: str | None = None) -> None:
        traza.append(
            {
                "paso": len(traza) + 1,
                "tipo": tipo,
                "nodo": actual,
                "hacia": hacia,
                "profundidad": len(camino_actual) - 1,
                "camino": list(camino_actual),
                "mensaje": mensaje,
            }
        )

    # 2.1 Se registro el orden secuencial de exploracion de los nodos
    orden_exploracion.append(actual)
    registrar("visita", "DFS visita el nodo.")

    # 2.3 Si se llego al objetivo, se almacena una copia del camino encontrado
    if actual == objetivo:
        todas_las_rutas.append(list(camino_actual))
        registrar("objetivo", "DFS alcanza el destino y guarda el camino.")
        return todas_las_rutas, orden_exploracion, traza

    # 2.4 Se detiene la expansión al alcanzar el máximo de aristas permitido.
    # El objetivo se evalúa antes para aceptar una ruta que llega justo al límite.
    if len(camino_actual) - 1 >= limite_profundidad:
        registrar("limite", "DFS no expande este nodo porque alcanzó la profundidad máxima.")
        return todas_las_rutas, orden_exploracion, traza

    # 2.2 Se exploraron los vecinos comprobando que no esten en el camino para evitar ciclos infinitos
    conexiones = grafo.get(actual, [])
    for conexion in conexiones:
        vecino = conexion["destino"]
        if vecino not in camino_actual:
            registrar("avanza", "DFS profundiza por una conexión no visitada en el camino actual.", vecino)
            camino_actual.append(vecino)
            busqueda_dfs_transporte(
                grafo,
                vecino,
                objetivo,
                limite_profundidad,
                camino_actual,
                orden_exploracion,
                todas_las_rutas,
                traza,
            )
            # Se efectuo backtracking retirando el ultimo nodo para explorar ramas alternativas
            camino_actual.pop()
            registrar("retroceso", "DFS retrocede para explorar otra alternativa.", vecino)
        else:
            registrar("ciclo_evitado", "DFS no sigue esta conexión porque produciría un ciclo.", vecino)

    return todas_las_rutas, orden_exploracion, traza


def calcular_detalle_ruta(camino: list[str]) -> dict[str, Any]:
    """Calcula tiempo acumulado, transbordos y trazo para una ruta obtenida por DFS."""
    tiempo_total = 0
    tramos = []
    lineas_usadas = []

    for i in range(len(camino) - 1):
        origen = camino[i]
        destino = camino[i + 1]
        conexion = next(c for c in GRAFO_TRANSPORTE[origen] if c["destino"] == destino)
        tiempo_total += conexion["tiempo_min"]
        lineas_usadas.append(conexion["linea"])
        tramos.append(
            {
                "de": PARADAS_KOMPAS[origen]["nombre"],
                "a": PARADAS_KOMPAS[destino]["nombre"],
                "linea": conexion["linea"],
                "modo": conexion["modo"],
                "tiempo_min": conexion["tiempo_min"],
            }
        )

    # Se contabilizaron transbordos cuando cambia la linea entre tramos consecutivos
    transbordos = sum(1 for i in range(len(lineas_usadas) - 1) if lineas_usadas[i] != lineas_usadas[i + 1])

    return {
        "paradas": [PARADAS_KOMPAS[nodo]["nombre"] for nodo in camino],
        "nodos_id": camino,
        "tiempo_total_minutos": tiempo_total,
        "numero_transbordos": transbordos,
        "tramos": tramos,
    }


def planificar_rutas_dfs(origen_id: str, destino_id: str, limite_profundidad: int = 5) -> dict[str, Any]:
    """Servicio de alto nivel para invocar DFS desde endpoints o modulos del backend."""
    if origen_id not in PARADAS_KOMPAS or destino_id not in PARADAS_KOMPAS:
        return {
            "exito": False,
            "mensaje": "El origen o destino indicado no se encuentra en el catalogo de paradas de Kompas.",
            "fuente": FUENTE_RED_DFS,
            "datos_verificados": False,
            "orden_exploracion": [],
            "rutas": [],
        }

    rutas_ids, exploracion, traza = busqueda_dfs_transporte(
        GRAFO_TRANSPORTE, origen_id, destino_id, limite_profundidad=limite_profundidad
    )

    detalles = [calcular_detalle_ruta(r) for r in rutas_ids]

    return {
        "exito": True,
        "fuente": FUENTE_RED_DFS,
        "datos_verificados": False,
        "aviso": "Los resultados son una demostración académica de DFS y no una recomendación de transporte real.",
        "origen": PARADAS_KOMPAS[origen_id],
        "destino": PARADAS_KOMPAS[destino_id],
        "limite_profundidad_aplicado": limite_profundidad,
        "orden_exploracion": exploracion,
        "traza": traza,
        "total_nodos_explorados": len(exploracion),
        "total_rutas_encontradas": len(detalles),
        "rutas": detalles,
    }
