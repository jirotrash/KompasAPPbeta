"""Pruebas de UCS, voraz y A* sobre la red académica del DFS (sin base de datos ni red)."""

import itertools

import pytest

from app.ia.busqueda_dfs import PARADAS_KOMPAS
from app.ia.busqueda_informada import a_estrella, comparar_algoritmos, costo_uniforme, voraz

PARES = [(o, d) for o, d in itertools.permutations(PARADAS_KOMPAS, 2) if costo_uniforme(o, d, con_traza=False)["encontrado"]]


@pytest.mark.parametrize(("origen", "destino"), PARES)
def test_a_estrella_euclidiana_da_el_mismo_costo_que_ucs(origen, destino):
    ucs = costo_uniforme(origen, destino)
    a = a_estrella(origen, destino, "euclidiana")
    assert a["costo_km"] == pytest.approx(ucs["costo_km"])
    assert a["es_admisible"] is True
    # A* con una heurística admisible y consistente no explora más que UCS
    assert a["total_nodos_explorados"] <= ucs["total_nodos_explorados"]


def test_voraz_explora_menos_o_igual_que_ucs():
    ucs = costo_uniforme("TerminalToluca", "PlazaSendero")
    for heuristica in ("euclidiana", "manhattan"):
        assert voraz("TerminalToluca", "PlazaSendero", heuristica)["total_nodos_explorados"] <= ucs["total_nodos_explorados"]


def test_origen_igual_a_destino_regresa_un_camino_de_un_nodo():
    for resultado in (
        costo_uniforme("CentroToluca", "CentroToluca"),
        voraz("CentroToluca", "CentroToluca"),
        a_estrella("CentroToluca", "CentroToluca", "manhattan"),
    ):
        assert resultado["camino"] == ["CentroToluca"]
        assert resultado["costo_km"] == 0
        assert resultado["longitud_camino"] == 0


def test_traza_con_g_h_f_y_frontera_ordenada():
    r = a_estrella("TerminalToluca", "PlazaSendero", "euclidiana")
    assert r["traza"][0]["nodo"] == "TerminalToluca" and r["traza"][-1]["tipo"] == "objetivo"
    for paso in r["traza"]:
        assert paso["f"] == pytest.approx(paso["g"] + paso["h"], abs=1e-3)
        fs = [fila["f"] for fila in paso["frontera"]]
        assert fs == sorted(fs)
    assert r["rutas"][0]["nodos_id"] == r["camino"]  # misma forma que el DFS
    assert r["datos_verificados"] is False


def test_manhattan_no_es_admisible_y_se_ve_con_datos():
    r = comparar_algoritmos("TerminalToluca", "PlazaSendero")
    filas = {(f["algoritmo"], f["heuristica"]): f for f in r["filas"]}
    assert filas[("a_estrella", "euclidiana")]["optimo"] is True
    assert filas[("a_estrella", "manhattan")]["optimo"] is False
    assert filas[("a_estrella", "manhattan")]["costo_km"] > r["costo_optimo_km"]
    assert r["heuristicas"]["euclidiana"]["nodos_sobreestimados"] == []
    assert r["heuristicas"]["manhattan"]["nodos_sobreestimados"]
    assert {f["algoritmo"] for f in r["filas"]} == {"dfs", "costo_uniforme", "voraz", "a_estrella"}


def test_nodo_desconocido():
    assert a_estrella("Narnia", "CentroToluca")["exito"] is False
    assert comparar_algoritmos("Narnia", "CentroToluca")["exito"] is False
