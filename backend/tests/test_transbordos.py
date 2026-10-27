"""A* para transbordos con dos rutas de prueba que se cruzan (sin base de datos)."""

from app.ia.transbordos import buscar_transbordo


def linea(desde: tuple[float, float], hasta: tuple[float, float], puntos: int = 11) -> list[list[float]]:
    """Trazo recto de prueba [[lng, lat], ...] con `puntos` puntos."""
    return [[desde[0] + (hasta[0] - desde[0]) * i / (puntos - 1), desde[1] + (hasta[1] - desde[1]) * i / (puntos - 1)] for i in range(puntos)]


# Ruta 1: de oeste a este sobre la latitud 19.29. Ruta 2: de sur a norte sobre la longitud -99.60.
RUTA_1 = {"id": 101, "trazo": linea((-99.65, 19.29), (-99.55, 19.29))}
RUTA_2 = {"id": 102, "trazo": linea((-99.60, 19.24), (-99.60, 19.34))}
ORIGEN = {"lat": 19.2905, "lng": -99.6495}  # junto al inicio de la ruta 1
DESTINO = {"lat": 19.3395, "lng": -99.6005}  # junto al final de la ruta 2


def test_origen_y_destino_solo_se_conectan_con_transbordo():
    r = buscar_transbordo([RUTA_1, RUTA_2], ORIGEN, DESTINO)
    assert r["encontrado"] is True
    assert r["rutas_usadas"] == [101, 102]
    modos = [t["modo"] for t in r["tramos"]]
    assert modos == ["pie", "autobus", "pie", "autobus", "pie"]
    primera, segunda = r["tramos"][1], r["tramos"][3]
    assert primera["km_subida"] < primera["km_bajada"] and segunda["km_subida"] < segunda["km_bajada"]
    assert r["nodos_explorados"] > 0


def test_con_una_sola_ruta_no_hay_combinacion():
    r = buscar_transbordo([RUTA_1], ORIGEN, DESTINO)
    assert r["encontrado"] is False and r["tramos"] == []


def test_respeta_el_sentido_del_trazo():
    # Al revés (del final de la ruta 2 al inicio de la ruta 1) no hay forma de ir en el sentido de los trazos
    r = buscar_transbordo([RUTA_1, RUTA_2], DESTINO, ORIGEN)
    assert r["encontrado"] is False
