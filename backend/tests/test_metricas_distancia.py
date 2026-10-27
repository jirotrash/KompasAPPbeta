"""Pruebas de las métricas Euclidiana y Manhattan, sin base de datos ni red."""

import math

from fastapi.testclient import TestClient

from app.ia.metricas_distancia import comparar_distancias, distancia_euclidiana, distancia_manhattan
from app.main import app
from app.compartido.geo import distancia_euclidiana_km, distancia_km, distancia_manhattan_km, distancia_por_calles_km

cliente = TestClient(app)


def test_ejemplo_de_clase_a_1_2_y_b_5_5():
    resultado = comparar_distancias((1, 2), (5, 5))

    assert resultado["euclidiana"] == 5
    assert resultado["manhattan"] == 7
    assert resultado["horizontal"] == 4 and resultado["vertical"] == 3
    assert resultado["esquina"] == {"x": 5, "y": 2}
    assert resultado["pasos"]["euclidiana"].endswith("√25 = 5")
    assert resultado["pasos"]["manhattan"].endswith("4 + 3 = 7")


def test_metricas_no_dependen_del_orden_ni_del_cuadrante():
    assert distancia_euclidiana((5, 1), (0, 4)) == distancia_euclidiana((0, 4), (5, 1)) == math.sqrt(34)
    assert distancia_manhattan((5, 1), (0, 4)) == distancia_manhattan((0, 4), (5, 1)) == 8


def test_puntos_alineados_dan_la_misma_distancia():
    resultado = comparar_distancias((2, 3), (2, 0))

    assert resultado["alineados"] is True
    assert resultado["euclidiana"] == resultado["manhattan"] == 3


def test_en_el_mapa_la_euclidiana_coincide_con_haversine_y_manhattan_es_mayor():
    centro_toluca = {"lat": 19.2926, "lng": -99.6557}
    metepec = {"lat": 19.2520, "lng": -99.6050}

    recta = distancia_km(centro_toluca, metepec)
    assert abs(distancia_euclidiana_km(centro_toluca, metepec) - recta) < 0.02
    assert recta < distancia_manhattan_km(centro_toluca, metepec) <= recta * math.sqrt(2) + 0.01
    assert distancia_por_calles_km(centro_toluca, metepec) == distancia_manhattan_km(centro_toluca, metepec)


def test_endpoint_plano():
    respuesta = cliente.get("/api/distancias/plano", params={"a": "1,2", "b": "5,5"})

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["euclidiana"] == 5 and datos["manhattan"] == 7


def test_endpoint_plano_rechaza_formato_invalido():
    respuesta = cliente.get("/api/distancias/plano", params={"a": "hola", "b": "5,5"})

    assert respuesta.status_code == 422
    assert "x,y" in respuesta.json()["detail"]


def test_endpoint_geo():
    respuesta = cliente.get(
        "/api/distancias/geo", params={"origen": "19.2926,-99.6557", "destino": "19.2520,-99.6050"}
    )

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["manhattan_km"] > datos["linea_recta_km"]
    assert datos["minutos_caminando_calles"] >= datos["minutos_caminando_recta"]
    # Manhattan = tramo este-oeste + tramo norte-sur; la esquina comparte latitud con el origen
    assert abs(datos["este_oeste_km"] + datos["norte_sur_km"] - datos["manhattan_km"]) < 0.01
    assert datos["esquina"] == {"lat": 19.2926, "lng": -99.605}
    assert datos["pasos"]["manhattan"].endswith(" km")
