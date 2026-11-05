"""Contrato de transporte: API y repositorio reales, base aislada en memoria."""
import mongomock
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modulos.rutas.repositorio import RepositorioRutas
from app.modulos.rutas.router import get_servicio
from app.modulos.rutas.servicio import ServicioRutas
from tests.test_transbordos import DESTINO, ORIGEN, RUTA_1, RUTA_2


@pytest.fixture
def transporte():
    bd = mongomock.MongoClient(tz_aware=True).transporte_aislado
    repo = RepositorioRutas(bd)
    app.dependency_overrides[get_servicio] = lambda: ServicioRutas(repo)
    try:
        with TestClient(app) as cliente:
            yield cliente, repo
    finally:
        app.dependency_overrides.pop(get_servicio, None)


def consultar(cliente, origen, destino):
    r = cliente.get('/api/rutas', params={
        'origen': f"{origen['lat']},{origen['lng']}",
        'destino': f"{destino['lat']},{destino['lng']}",
    })
    assert r.status_code == 200, r.text
    return r.json()


def paradas(trazo):
    return [{"nombre": f"Parada capturada {i}", "ubicacion": {"type": "Point", "coordinates": p}} for i, p in enumerate(trazo)]


@pytest.mark.parametrize('capturadas', [False, True])
def test_distingue_paradas_capturadas_de_puntos_del_trazo(transporte, capturadas):
    cliente, repo = transporte
    trazo = RUTA_1['trazo']
    repo.crear(trazo, 'Línea documentada', paradas(trazo) if capturadas else [])
    bus = consultar(cliente, {'lat': trazo[0][1], 'lng': trazo[0][0]}, {'lat': trazo[-1][1], 'lng': trazo[-1][0]})['alternativas'][0]
    assert bus['modo'] == 'autobus' and bus['paradas_reales'] is capturadas
    assert bus['tramos'][1]['paradas_reales'] is capturadas
    assert bus['tiempos']['espera'] is None and bus['tarifa'] is None
    assert bus['fecha_verificacion'] is None  # capturar una parada no verifica todo el servicio
    assert bus['tiempos']['caminata'] == 0 and bus['caminata_km'] == 0
    assert len(bus['paradas_intermedias']) == len(trazo) - 2
    if not capturadas:
        assert any('puntos del trazo' in a for a in bus['avisos'])


def test_transbordo_conserva_orden_y_caminatas(transporte):
    cliente, repo = transporte
    for ruta in [RUTA_1, RUTA_2]:
        repo.crear(ruta['trazo'], f"Línea {ruta['id']}", paradas(ruta['trazo']))
    bus = consultar(cliente, ORIGEN, DESTINO)['alternativas'][0]
    assert bus['modo'] == 'autobus' and bus['numero_transbordos'] == 1
    assert bus['paradas_reales'] is True
    assert [t['modo'] for t in bus['tramos']] == ['pie', 'autobus', 'pie', 'autobus', 'pie']
    caminatas = [t for t in bus['tramos'] if t['modo'] == 'pie']
    assert bus['caminata_km'] == round(sum(t['distancia_km'] for t in caminatas), 2)
    assert bus['tiempos']['caminata'] == sum(t['duracion_min'] for t in caminatas)
    assert bus['tiempos']['espera'] is None
    assert bus['transbordos'][0]['linea'] == 'Línea 102'
    for t in bus['tramos']:
        if t['modo'] == 'autobus':
            assert t['parada_subida']['km'] < t['parada_bajada']['km']
            assert all(t['parada_subida']['km'] < p['km'] < t['parada_bajada']['km'] for p in t['paradas_intermedias'])


def test_sentido_contrario_no_inventa_autobus(transporte):
    cliente, repo = transporte
    for ruta in [RUTA_1, RUTA_2]:
        repo.crear(ruta['trazo'])
    respuesta = consultar(cliente, DESTINO, ORIGEN)
    assert not respuesta['datos_suficientes']
    assert [a['modo'] for a in respuesta['alternativas']] == ['pie', 'taxi', 'app']


def test_sin_rutas_sigue_ofreciendo_estimaciones_identificadas(transporte):
    cliente, _ = transporte
    datos = consultar(cliente, ORIGEN, DESTINO)
    assert not datos['datos_suficientes'] and 'transporte público' in datos['mensaje']
    assert all(a['fuente'] == 'Estimación por distancia' for a in datos['alternativas'])
    assert all(a['fecha_verificacion'] is None for a in datos['alternativas'])


def test_puntos_invalidos_y_fuera_de_zona(transporte):
    cliente, _ = transporte
    assert cliente.get('/api/rutas', params={'origen': 'NaN,0', 'destino': '19.29,-99.65'}).status_code == 422
    fuera = consultar(cliente, {'lat': 0, 'lng': 0}, DESTINO)
    assert not fuera['datos_suficientes'] and fuera['alternativas'] == []
