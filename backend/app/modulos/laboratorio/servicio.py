"""Demostraciones académicas: envuelve `app.ia.busqueda_dfs`, `app.ia.metricas_distancia`,
`app.ia.busqueda_informada` y `app.ia.algoritmo_genetico` sin cambiar su respuesta.

Después de calcular, deja un registro en la bitácora para el dashboard. Si la escritura falla, la
respuesta se devuelve igual (solo se registra un aviso).
"""

import logging
import math

from app.compartido.geo import (
    Coordenada,
    desglose_manhattan_km,
    distancia_euclidiana_km,
    distancia_km,
    distancia_manhattan_km,
    minutos_caminando,
)
from app.ia.algoritmo_genetico import ordenar_paradas
from app.ia.busqueda_dfs import PARADAS_KOMPAS, planificar_rutas_dfs
from app.ia.busqueda_informada import comparar_algoritmos
from app.ia.metricas_distancia import Punto, comparar_distancias, fmt
from app.modulos.laboratorio.repositorio import RepositorioBitacora
from app.nucleo.errores import DatosInvalidos, NoEncontrado

log = logging.getLogger(__name__)


def punto_plano(nombre: str, texto: str) -> Punto:
    """Convierte "x,y" en un punto del plano cartesiano."""
    try:
        x, y = (float(parte) for parte in texto.split(","))
        if not (math.isfinite(x) and math.isfinite(y)):
            raise ValueError
    except ValueError:
        raise DatosInvalidos(f'"{nombre}" debe tener el formato x,y (ej. 1,2).') from None
    return (x, y)


class ServicioLaboratorio:
    def __init__(self, bitacora: RepositorioBitacora):
        self.bitacora = bitacora

    def registrar(self, tipo: str, datos: dict) -> None:
        """Escribe en la bitácora sin romper nunca la respuesta (la usan también rutas e itinerarios)."""
        try:
            self.bitacora.registrar(tipo, datos)
        except Exception as error:  # noqa: BLE001 — la bitácora nunca debe romper la demostración
            log.warning("No se pudo escribir en bitacora_laboratorio: %s", error)

    @staticmethod
    def paradas() -> list[dict]:
        return [{"id": clave, **info} for clave, info in PARADAS_KOMPAS.items()]

    def buscar_dfs(self, origen: str, destino: str, limite_profundidad: int) -> dict:
        resultado = planificar_rutas_dfs(origen, destino, limite_profundidad)
        self.registrar(
            "dfs",
            {
                "origen": origen,
                "destino": destino,
                "limite_profundidad": limite_profundidad,
                "exito": resultado.get("exito", False),
                "total_nodos_explorados": resultado.get("total_nodos_explorados", 0),
                "total_rutas": resultado.get("total_rutas_encontradas", 0),
                "profundidad_maxima": max((p["profundidad"] for p in resultado.get("traza", [])), default=0),
            },
        )
        return resultado

    def comparar_plano(self, a: Punto, b: Punto) -> dict:
        resultado = comparar_distancias(a, b)
        self.registrar("distancia", {"modo": "plano", "euclidiana": resultado["euclidiana"], "manhattan": resultado["manhattan"]})
        return resultado

    def comparar_geo(self, a: Coordenada, b: Coordenada) -> dict:
        este_oeste, norte_sur = desglose_manhattan_km(a, b)
        euclidiana = distancia_euclidiana_km(a, b)
        manhattan = distancia_manhattan_km(a, b)
        recta = distancia_km(a, b)
        resultado = {
            "origen": a,
            "destino": b,
            "esquina": {"lat": a["lat"], "lng": b["lng"]},
            "este_oeste_km": round(este_oeste, 3),
            "norte_sur_km": round(norte_sur, 3),
            "linea_recta_km": round(recta, 3),
            "euclidiana_km": round(euclidiana, 3),
            "manhattan_km": round(manhattan, 3),
            "diferencia_km": round(manhattan - euclidiana, 3),
            "minutos_caminando_recta": minutos_caminando(recta),
            "minutos_caminando_calles": minutos_caminando(manhattan),
            "pasos": {
                "euclidiana": f"√({fmt(este_oeste)}² + {fmt(norte_sur)}²) = "
                f"√({fmt(este_oeste**2)} + {fmt(norte_sur**2)}) = {fmt(euclidiana)} km",
                "manhattan": f"{fmt(este_oeste)} + {fmt(norte_sur)} = {fmt(manhattan)} km",
            },
            "nota": "Kompás usa la distancia Manhattan para estimar trayectos por calles.",
        }
        self.registrar(
            "distancia", {"modo": "geo", "euclidiana": resultado["euclidiana_km"], "manhattan": resultado["manhattan_km"]}
        )
        return resultado

    def comparar_busqueda(self, origen: str, destino: str) -> dict:
        """DFS, UCS, voraz y A* sobre la red académica (tabla comparativa)."""
        resultado = comparar_algoritmos(origen, destino)
        if not resultado["exito"]:
            raise NoEncontrado(resultado["mensaje"])
        campos = ("algoritmo", "heuristica", "costo_km", "nodos_explorados", "longitud_camino", "optimo", "ms")
        self.registrar(
            "busqueda",
            {
                "origen": origen,
                "destino": destino,
                "costo_optimo_km": resultado["costo_optimo_km"],
                "algoritmos": [{k: f[k] for k in campos} for f in resultado["filas"]],
            },
        )
        return resultado

    def ordenar_paradas(self, peticion: dict) -> dict:
        """Ejecuta el genético con los parámetros que elija el administrador."""
        paradas = peticion["paradas"]
        parametros = {k: peticion.get(k) for k in ("poblacion", "generaciones", "prob_cruza", "prob_mutacion", "semilla")}
        try:
            resultado = ordenar_paradas(paradas, peticion.get("origen"), None, None, **parametros)
        except ValueError as error:
            raise DatosInvalidos(str(error)) from None
        resultado["orden_paradas"] = [paradas[i].get("nombre") or f"Parada {i + 1}" for i in resultado["mejor_orden"]]
        self.registrar(
            "genetico",
            {
                "origen": "endpoint",
                "paradas": len(paradas),
                "km_antes": resultado["distancia_original_km"],
                "km_despues": resultado["distancia_km"],
                "aplicado": resultado["mejor_orden"] != list(range(len(paradas))),
                "generaciones": resultado["parametros"]["generaciones"],
                "generacion_mejor": resultado["generacion_mejor"],
                "brecha_vs_optimo_pct": resultado["brecha_vs_optimo_%"],
                "historial_mejor": [h["mejor"] for h in resultado["historial"]],
                "historial_promedio": [h["promedio"] for h in resultado["historial"]],
                "ms": resultado["ms"],
            },
        )
        return resultado
