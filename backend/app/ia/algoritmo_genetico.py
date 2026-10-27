# ============================================================
# Algoritmo genético: orden de las paradas de un plan (agente viajero con origen fijo, sin regreso)
# ============================================================
# Cromosoma:  permutación de los índices de las paradas, p. ej. [2, 0, 1] = ir primero a la parada 2.
# Aptitud:    1 / (1 + distancia_total_km + penalización)
#             distancia_total_km = origen → 1.ª parada → … → última (por calles, métrica Manhattan,
#             la misma que usa el planificador). La penalización se suma por cada parada que, con la
#             hora de salida y los tiempos estimados de compartido.traslados, quedaría fuera de su horario.
# Operadores: selección por torneo (k = 3), cruza de orden (OX), mutación por intercambio y elitismo (2).
# Con 8 paradas o menos también se calcula el óptimo por fuerza bruta para medir la brecha.
# ============================================================

import itertools
import math
import random
import time
from datetime import datetime, timedelta
from typing import Any

from app.compartido.geo import Coordenada, distancia_por_calles_km
from app.compartido.traslados import tramo
from app.ia.hechos import ESTANCIAS_MINUTOS, visita_en_horario

PARAMETROS_POR_DEFECTO = {
    "poblacion": 60,
    "generaciones": 150,
    "prob_cruza": 0.9,
    "prob_mutacion": 0.2,
    "torneo_k": 3,
    "elitismo": 2,
    "semilla": None,
}
# km "equivalentes" que se suman por cada parada fuera de horario: más que cualquier recorrido en la zona
PENALIZACION_FUERA_DE_HORARIO_KM = 100.0
MAX_FUERZA_BRUTA = 8


class Evaluador:
    """Distancia y penalización de un orden. Las distancias entre puntos se calculan una sola vez."""

    def __init__(self, paradas: list[dict[str, Any]], origen: Coordenada | None, salida: datetime | None, movilidad: list[str] | None):
        self.paradas = paradas
        self.origen = origen
        self.salida = salida
        self.movilidad = movilidad or ["caminando"]
        puntos = ([origen] if origen else []) + [{"lat": p["lat"], "lng": p["lng"]} for p in paradas]
        self.desfase = 1 if origen else 0
        self.km = [[distancia_por_calles_km(a, b) for b in puntos] for a in puntos]
        self.puntos = puntos
        self._cache: dict[tuple[int, ...], float] = {}

    def distancia(self, orden: list[int]) -> float:
        nodos = ([0] if self.origen else []) + [i + self.desfase for i in orden]
        return sum(self.km[a][b] for a, b in zip(nodos, nodos[1:]))

    def fuera_de_horario(self, orden: list[int]) -> int:
        """Paradas que quedarían cerradas durante la visita (False de hechos.visita_en_horario)."""
        if self.salida is None or self.origen is None:
            return 0
        reloj = self.salida
        anterior = self.origen
        fuera = 0
        for i in orden:
            p = self.paradas[i]
            t = tramo(anterior, {"lat": p["lat"], "lng": p["lng"]}, self.movilidad)
            reloj = reloj + timedelta(minutes=t["minutos"])
            estancia = p.get("estancia_min") or ESTANCIAS_MINUTOS.get(p.get("categoria", ""), 60)
            if p.get("horario") is not None and visita_en_horario(p["horario"], reloj.isoformat(), estancia) is False:
                fuera += 1
            reloj = reloj + timedelta(minutes=estancia)
            anterior = {"lat": p["lat"], "lng": p["lng"]}
        return fuera

    def penalizacion(self, orden: list[int]) -> float:
        return self.fuera_de_horario(orden) * PENALIZACION_FUERA_DE_HORARIO_KM

    def aptitud(self, orden: list[int]) -> float:
        clave = tuple(orden)
        if clave not in self._cache:
            self._cache[clave] = 1 / (1 + self.distancia(orden) + self.penalizacion(orden))
        return self._cache[clave]


def _torneo(poblacion: list[list[int]], aptitudes: list[float], k: int, azar: random.Random) -> list[int]:
    elegidos = azar.sample(range(len(poblacion)), min(k, len(poblacion)))
    return poblacion[max(elegidos, key=lambda i: aptitudes[i])]


def cruza_ox(padre: list[int], madre: list[int], azar: random.Random) -> list[int]:
    """Cruza de orden (OX): copia un segmento del padre y completa con los genes de la madre en su orden."""
    n = len(padre)
    a, b = sorted(azar.sample(range(n), 2)) if n > 1 else (0, 0)
    hijo: list[int | None] = [None] * n
    hijo[a : b + 1] = padre[a : b + 1]
    usados = set(padre[a : b + 1])
    restantes = [g for g in madre[b + 1 :] + madre[: b + 1] if g not in usados]
    posiciones = list(range(b + 1, n)) + list(range(0, a))
    for pos, gen in zip(posiciones, restantes):
        hijo[pos] = gen
    return [g for g in hijo if g is not None]


def mutar_intercambio(orden: list[int], azar: random.Random) -> list[int]:
    """Intercambia dos posiciones al azar."""
    if len(orden) < 2:
        return orden[:]
    i, j = azar.sample(range(len(orden)), 2)
    nuevo = orden[:]
    nuevo[i], nuevo[j] = nuevo[j], nuevo[i]
    return nuevo


def fuerza_bruta(evaluador: Evaluador, n: int) -> tuple[list[int], float]:
    """Mejor orden revisando las n! permutaciones (solo para n ≤ 8)."""
    mejor = max(itertools.permutations(range(n)), key=lambda o: evaluador.aptitud(list(o)))
    return list(mejor), evaluador.aptitud(list(mejor))


def ordenar_paradas(
    paradas: list[dict[str, Any]],
    origen: Coordenada | None = None,
    salida: datetime | None = None,
    movilidad: list[str] | None = None,
    **parametros: Any,
) -> dict[str, Any]:
    """Ejecuta el genético. `paradas`: [{lat, lng, horario?, categoria?, estancia_min?}, ...].

    Regresa mejor orden, distancia, aptitud, generación en que se encontró, historial (mejor y promedio
    de aptitud por generación), parámetros usados y, con ≤ 8 paradas, la brecha contra el óptimo.
    """
    p = {**PARAMETROS_POR_DEFECTO, **{k: v for k, v in parametros.items() if v is not None}}
    if p["poblacion"] < 2 or p["generaciones"] < 1:
        raise ValueError("La población debe ser de al menos 2 y las generaciones de al menos 1.")
    inicio = time.perf_counter()
    azar = random.Random(p["semilla"])
    n = len(paradas)
    evaluador = Evaluador(paradas, origen, salida, movilidad)
    original = list(range(n))

    if n <= 1:
        return {
            "mejor_orden": original,
            "distancia_km": round(evaluador.distancia(original), 4),
            "distancia_original_km": round(evaluador.distancia(original), 4),
            "aptitud": evaluador.aptitud(original),
            "paradas_fuera_de_horario": evaluador.fuera_de_horario(original),
            "generacion_mejor": 0,
            "historial": [],
            "parametros": p,
            "optimo_fuerza_bruta": None,
            "brecha_vs_optimo_%": None,
            "ms": round((time.perf_counter() - inicio) * 1000, 3),
        }

    # Población inicial: el orden original (para no empeorar nunca) + permutaciones al azar
    poblacion = [original[:]] + [azar.sample(original, n) for _ in range(p["poblacion"] - 1)]
    mejor, mejor_aptitud, generacion_mejor = original[:], evaluador.aptitud(original), 0
    historial = []
    factorial_n = math.factorial(n)

    for generacion in range(1, p["generaciones"] + 1):
        aptitudes = [evaluador.aptitud(c) for c in poblacion]
        lider = max(range(len(poblacion)), key=lambda i: aptitudes[i])
        if aptitudes[lider] > mejor_aptitud:
            mejor, mejor_aptitud, generacion_mejor = poblacion[lider][:], aptitudes[lider], generacion
        historial.append({"generacion": generacion, "mejor": mejor_aptitud, "promedio": sum(aptitudes) / len(aptitudes)})

        elite = [poblacion[i][:] for i in sorted(range(len(poblacion)), key=lambda i: -aptitudes[i])[: p["elitismo"]]]
        nueva = elite
        vistos = {tuple(c) for c in elite}
        while len(nueva) < p["poblacion"]:
            padre = _torneo(poblacion, aptitudes, p["torneo_k"], azar)
            madre = _torneo(poblacion, aptitudes, p["torneo_k"], azar)
            hijo = cruza_ox(padre, madre, azar) if azar.random() < p["prob_cruza"] else padre[:]
            if azar.random() < p["prob_mutacion"]:
                hijo = mutar_intercambio(hijo, azar)
            # Diversidad: un hijo repetido se muta (hasta 3 veces) para que la población no se estanque
            intentos = 0
            while tuple(hijo) in vistos and intentos < 3 and len(vistos) < factorial_n:
                hijo = mutar_intercambio(hijo, azar)
                intentos += 1
            vistos.add(tuple(hijo))
            nueva.append(hijo)
        poblacion = nueva

    resultado = {
        "mejor_orden": mejor,
        "distancia_km": round(evaluador.distancia(mejor), 4),
        "distancia_original_km": round(evaluador.distancia(original), 4),
        "aptitud": mejor_aptitud,
        "paradas_fuera_de_horario": evaluador.fuera_de_horario(mejor),
        "generacion_mejor": generacion_mejor,
        "historial": [{**h, "mejor": round(h["mejor"], 6), "promedio": round(h["promedio"], 6)} for h in historial],
        "parametros": p,
        "optimo_fuerza_bruta": None,
        "brecha_vs_optimo_%": None,
    }
    if n <= MAX_FUERZA_BRUTA:
        orden_optimo, aptitud_optima = fuerza_bruta(evaluador, n)
        costo_optimo = 1 / aptitud_optima - 1
        costo_ga = 1 / mejor_aptitud - 1
        resultado["optimo_fuerza_bruta"] = {"orden": orden_optimo, "distancia_km": round(evaluador.distancia(orden_optimo), 4)}
        resultado["brecha_vs_optimo_%"] = round(100 * (costo_ga - costo_optimo) / costo_optimo, 4) if costo_optimo > 0 else 0.0
    resultado["ms"] = round((time.perf_counter() - inicio) * 1000, 3)
    return resultado
