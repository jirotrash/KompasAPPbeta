"""Pruebas del algoritmo genético que ordena las paradas de un plan (sin base de datos)."""

import random
from datetime import datetime

from app.compartido.geo import HORA_MEXICO
from app.ia.algoritmo_genetico import cruza_ox, mutar_intercambio, ordenar_paradas

ORIGEN = {"lat": 19.2926, "lng": -99.6557}


def paradas_al_azar(n: int, semilla: int) -> list[dict]:
    azar = random.Random(semilla)
    return [{"lat": 19.25 + azar.random() * 0.08, "lng": -99.68 + azar.random() * 0.1} for _ in range(n)]


def test_con_semilla_fija_es_reproducible():
    paradas = paradas_al_azar(7, 3)
    a = ordenar_paradas(paradas, ORIGEN, semilla=11)
    b = ordenar_paradas(paradas, ORIGEN, semilla=11)
    assert a["mejor_orden"] == b["mejor_orden"]
    assert a["historial"] == b["historial"]
    assert len(a["historial"]) == 150
    assert a["parametros"]["poblacion"] == 60


def test_brecha_contra_fuerza_bruta_menor_a_5_por_ciento():
    for semilla in range(15):
        n = 2 + semilla % 7  # de 2 a 8 paradas
        r = ordenar_paradas(paradas_al_azar(n, semilla), ORIGEN, semilla=semilla)
        assert r["optimo_fuerza_bruta"] is not None
        assert r["brecha_vs_optimo_%"] <= 5
        assert r["distancia_km"] <= r["distancia_original_km"]


def test_el_resultado_siempre_es_una_permutacion_valida():
    for n in (1, 2, 5, 10):
        r = ordenar_paradas(paradas_al_azar(n, n), ORIGEN, semilla=1, generaciones=20)
        assert sorted(r["mejor_orden"]) == list(range(n))
    azar = random.Random(0)
    for _ in range(200):
        padre, madre = azar.sample(range(9), 9), azar.sample(range(9), 9)
        assert sorted(cruza_ox(padre, madre, azar)) == list(range(9))
        assert sorted(mutar_intercambio(padre, azar)) == list(range(9))


def test_penaliza_paradas_fuera_de_horario():
    # La parada cercana solo abre de 19:30 a 23:59: visitarla primero (a las ~18:05) la deja cerrada
    abre_tarde = {"periods": [{"open": {"day": d, "hour": 19, "minute": 30}, "close": {"day": d, "hour": 23, "minute": 59}} for d in range(7)]}
    paradas = [
        {"lat": 19.2930, "lng": -99.6560, "horario": abre_tarde, "categoria": "comer"},
        {"lat": 19.2990, "lng": -99.6400, "categoria": "cultura"},
    ]
    salida = datetime(2026, 10, 27, 18, 0, tzinfo=HORA_MEXICO)
    r = ordenar_paradas(paradas, ORIGEN, salida, ["caminando"], semilla=1)
    assert r["mejor_orden"] == [1, 0]
    assert r["paradas_fuera_de_horario"] == 0
