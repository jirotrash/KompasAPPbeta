import pytest

from app.modulos.rutas.repositorio import RepositorioRutas
from tests.conftest import encabezado, registrar

CENTRO_TOLUCA = {"lat": 19.2926, "lng": -99.6557}
TRAZO = [[-99.511, 19.2847], [-99.545, 19.279], [-99.6557, 19.2926]]


def test_catalogos_con_claves_de_la_app(cliente):
    categorias = cliente.get("/api/categorias").json()
    assert {c["clave"] for c in categorias} == {"comer", "cafe", "cultura", "entretenimiento", "aire_libre"}
    transportes = cliente.get("/api/transportes").json()
    assert {t["clave"] for t in transportes} == {"caminando", "transporte_publico", "taxi_app", "combinado"}


def test_lugares_cercanos_ordenados(cliente):
    lugares = cliente.get("/api/lugares", params=CENTRO_TOLUCA).json()
    assert len(lugares) == 10
    distancias = [l["distancia_km"] for l in lugares]
    assert distancias == sorted(distancias)
    primero = lugares[0]
    assert primero["minutos_caminando"] == max(1, round(primero["distancia_km"] * 12))
    assert primero["ubicacion"]["coordinates"] == [primero["lng"], primero["lat"]]
    # La base no tiene estos datos: van en null, no se inventan
    assert primero["horario"] is None and primero["costo_promedio"] is None and primero["calificacion"] is None


def test_lugares_como_los_pide_la_app(cliente):
    lugares = cliente.get("/api/lugares", params={"cerca": "19.2926,-99.6557", "radio_km": 1}).json()
    assert lugares and all(l["distancia_km"] <= 1 for l in lugares)
    assert all(isinstance(l["_id"], str) for l in lugares)


def test_lugares_por_categoria(cliente):
    por_nombre = cliente.get("/api/lugares", params={"categoria": "Café"}).json()
    por_clave = cliente.get("/api/lugares", params={"categoria": "cafe"}).json()
    assert len(por_nombre) == len(por_clave) == 2
    assert all(l["interes"] == "cafe" for l in por_clave)


def test_lugar_inexistente_da_404(cliente):
    assert cliente.get("/api/lugares/99999").status_code == 404
    assert cliente.get("/api/lugares/1").json()["id"] == 1


@pytest.fixture(scope="module")
def id_ruta(bd) -> int:
    """Los datos de desarrollo no traen rutas: se inserta una solo para las pruebas (base kompas_test)."""
    return RepositorioRutas(bd).crear(TRAZO)["id"]


def test_rutas_con_trazo_lng_lat(cliente, id_ruta):
    rutas = cliente.get("/api/rutas").json()
    assert [r["id"] for r in rutas] == [id_ruta]
    ruta = cliente.get(f"/api/rutas/{id_ruta}").json()
    assert ruta["trazo"] == TRAZO
    assert cliente.get("/api/rutas/99999").status_code == 404


def test_alternativas_de_la_pantalla_buscar(cliente, id_ruta):
    # Ninguna ruta pasa cerca del origen: se avisa y solo hay estimaciones a pie y en taxi/app
    datos = cliente.get("/api/rutas", params={"origen": "19.33,-99.60", "destino": "19.2926,-99.6557"}).json()
    assert datos["datos_suficientes"] is False and "transporte público" in datos["mensaje"]
    assert [a["modo"] for a in datos["alternativas"]] == ["pie", "taxi", "app"]

    fuera = cliente.get("/api/rutas", params={"origen": "19.43,-99.13", "destino": "19.2926,-99.6557"}).json()
    assert fuera["alternativas"] == []
    assert cliente.get("/api/rutas", params={"origen": "hola", "destino": "19.2926,-99.6557"}).status_code == 422


def test_opcion_en_autobus_con_subida_y_bajada(cliente, id_ruta):
    """El origen y el destino quedan sobre el trazo de la ruta: aparece la opción directa en autobús."""
    datos = cliente.get("/api/rutas", params={"origen": "19.2847,-99.511", "destino": "19.2926,-99.6557"}).json()
    assert datos["datos_suficientes"] is True and datos["mensaje"] is None
    assert [a["modo"] for a in datos["alternativas"]] == ["autobus", "pie", "taxi", "app"]
    bus = datos["alternativas"][0]
    assert bus["tipo"] == "directo" and bus["id_ruta"] == id_ruta
    # Sin paradas en la base: se usan los puntos del trazo, sin inventar nombres
    assert bus["parada_subida"]["nombre"] == "Punto 1" and bus["parada_bajada"]["nombre"] == "Punto 3"
    assert bus["abordaje"]["nombre"] == "Punto 1" and bus["descenso"]["ubicacion"]["coordinates"] == TRAZO[-1]
    assert bus["tramo_en_ruta"] == TRAZO
    assert [p["nombre"] for p in bus["paradas_intermedias"]] == ["Punto 2"]
    assert bus["tiempos"]["espera"] is None and bus["tarifa"] is None  # no se inventan horarios ni tarifas
    assert [t["modo"] for t in bus["tramos"]] == ["pie", "autobus", "pie"]

    # En sentido contrario al trazo no hay opción en autobús
    vuelta = cliente.get("/api/rutas", params={"origen": "19.2926,-99.6557", "destino": "19.2847,-99.511"}).json()
    assert "autobus" not in [a["modo"] for a in vuelta["alternativas"]]


def test_arbol_de_la_ruta_solo_admin(cliente, id_ruta, token_demo):
    assert cliente.get(f"/api/rutas/{id_ruta}/arbol").status_code == 401
    usuario = encabezado(registrar(cliente, "sin-permiso-arbol@ejemplo.mx")["token"])
    assert cliente.get(f"/api/rutas/{id_ruta}/arbol", headers=usuario).status_code == 403
    arbol = cliente.get(f"/api/rutas/{id_ruta}/arbol", headers=encabezado(token_demo)).json()
    assert arbol["paradas_reales"] is False and arbol["total_nodos"] == 3 and arbol["altura"] == 2
    assert [p["nombre"] for p in arbol["inorden"]] == ["Punto 1", "Punto 2", "Punto 3"]
    assert arbol["raiz"]["parada"]["nombre"] == "Punto 2"


def test_historial(cliente, bd, id_ruta):
    h = encabezado(registrar(cliente, "viajero@ejemplo.mx")["token"])
    id_transporte = bd.transportes.find_one({"nombre": "Caminando"})["_id"]

    assert cliente.get("/api/historial", headers=h).json() == []
    creado = cliente.post("/api/historial", json={"id_ruta": id_ruta, "id_transporte": id_transporte, "tiempo_estimado": 35}, headers=h)
    assert creado.status_code == 201
    assert creado.json()["transporte"] == "Caminando"
    assert len(cliente.get("/api/historial", headers=h).json()) == 1
    otra = {"id_ruta": 99999, "id_transporte": id_transporte, "tiempo_estimado": 5}
    assert cliente.post("/api/historial", json=otra, headers=h).status_code == 404
