"""Pruebas del árbol binario de paradas (sin base de datos)."""

import math

import pytest

from app.ia.arbol_binario import ArbolParadas
from app.ia.trazos import arbol_de_ruta, paradas_de_ruta, proyectar


def paradas(n: int) -> list[dict]:
    return [{"km": float(i), "id": f"p{i}", "nombre": f"Punto {i + 1}", "lat": 19.29, "lng": -99.6 - i / 100} for i in range(n)]


@pytest.mark.parametrize("n", [1, 2, 3, 4, 7, 8, 15, 16, 100])
def test_balanceado_tiene_altura_minima(n):
    arbol = ArbolParadas.construir_balanceado(paradas(n))
    assert arbol.altura() == math.ceil(math.log2(n + 1))
    assert arbol.total_nodos() == n


def test_insertar_en_orden_degenera_en_lista():
    arbol = ArbolParadas()
    for p in paradas(10):
        arbol.insertar(p["km"], p)
    assert arbol.altura() == 10  # por eso se construye balanceado


def test_inorden_regresa_las_paradas_en_orden():
    arbol = ArbolParadas.construir_balanceado(paradas(9))
    assert [n.clave for n in arbol.inorden()] == list(range(9))
    assert arbol.preorden()[0] is arbol.raiz
    assert arbol.postorden()[-1] is arbol.raiz


def test_mas_cercano_encuentra_la_parada_y_su_camino():
    arbol = ArbolParadas.construir_balanceado(paradas(7))  # raíz 3; 1 y 5; hojas 0, 2, 4, 6
    nodo, camino = arbol.mas_cercano(4.4)
    assert nodo.clave == 4
    assert camino == [3, 5, 4]
    nodo, _ = arbol.mas_cercano(4.6)
    assert nodo.clave == 5
    assert arbol.mas_cercano(-3)[0].clave == 0
    assert arbol.mas_cercano(99)[0].clave == 6
    assert arbol.buscar(2).parada["id"] == "p2"
    assert arbol.buscar(2.5) is None


def test_rango_y_diccionario():
    arbol = ArbolParadas.construir_balanceado(paradas(8))
    assert [n.clave for n in arbol.rango(2, 5)] == [2, 3, 4, 5]
    d = arbol.a_dict()
    assert set(d) == {"clave", "parada", "izquierdo", "derecho"}
    resumen = arbol.resumen()
    assert [p["km"] for p in resumen["inorden"]] == list(range(8))
    assert resumen["altura"] == 4


def test_ruta_sin_paradas_usa_puntos_del_trazo_y_cache():
    ruta = {"id": 900, "trazo": [[-99.60, 19.29], [-99.61, 19.29], [-99.62, 19.29]]}
    lista, reales = paradas_de_ruta(ruta)
    assert reales is False
    assert [p["nombre"] for p in lista] == ["Punto 1", "Punto 2", "Punto 3"]
    arbol, _ = arbol_de_ruta(ruta)
    assert arbol_de_ruta(ruta)[0] is arbol  # caché
    cambiada = {**ruta, "trazo": ruta["trazo"] + [[-99.63, 19.29]]}
    assert arbol_de_ruta(cambiada)[0] is not arbol  # se invalida si la ruta cambia
    p = proyectar({"lat": 19.291, "lng": -99.615}, ruta["trazo"])
    assert p["km"] == pytest.approx(1.5 * 1.0506, rel=0.01)
    assert p["distancia_km"] == pytest.approx(0.1106, rel=0.01)
