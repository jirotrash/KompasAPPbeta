"""API real + repositorios + motor, con MongoDB en memoria y Google simulado.

No requiere Atlas ni llaves externas. Los validadores BSON se verifican por separado
al aplicar preparar_bd en un MongoDB real: mongomock no ejecuta $jsonSchema.
"""
from copy import deepcopy

import httpx
import mongomock
import pytest
from fastapi.testclient import TestClient

from app.externos import google_places
from app.main import app
from app.nucleo.bd import get_bd
from app.nucleo.config import get_settings
from scripts.preparar_bd import ajustar_contadores, cargar_datos
from tests.conftest import encabezado, registrar
from tests.test_itinerarios import PETICION, lugar_google


@pytest.fixture
def escenario(monkeypatch):
    bd = mongomock.MongoClient(tz_aware=True).kompas_planes_test
    cargar_datos(bd)
    ajustar_contadores(bd)
    bd.usuarios.create_index("correo", unique=True)
    lugares = [
        lugar_google("cafe", "Café externo privado", "cafe", 19.2935, -99.6570),
        lugar_google("restaurante", "Restaurante externo", "comer", 19.2905, -99.6530),
        lugar_google("museo", "Museo externo", "cultura", 19.2950, -99.6590),
    ]
    monkeypatch.setattr(google_places, "buscar_para_plan", lambda *_: deepcopy(lugares))
    monkeypatch.setattr(google_places, "consultar_paradas", lambda refs: [deepcopy(next(l for l in lugares if l["place_id"] == r["place_id"])) for r in refs])
    app.dependency_overrides[get_bd] = lambda: bd
    with TestClient(app) as cliente:
        h = encabezado(registrar(cliente, "propietario@ejemplo.mx")["token"])
        otro = encabezado(registrar(cliente, "otro@ejemplo.mx")["token"])
        respuesta = cliente.post("/api/itinerarios", json=PETICION, headers=h)
        assert respuesta.status_code == 200, respuesta.text
        datos = respuesta.json()
        assert datos["planes"]
        yield cliente, bd, h, otro, datos, lugares
    app.dependency_overrides.pop(get_bd, None)


def elegir(escenario):
    cliente, _, h, _, datos, _ = escenario
    respuesta = cliente.patch(f"/api/planes/{datos['id_plan']}", headers=h, json={"tipo_seleccionado": datos["planes"][0]["tipo"]})
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def test_guarda_referencias_sin_contenido_de_google_ni_gps(escenario):
    cliente, bd, h, _, datos, _ = escenario
    doc = bd.planes.find_one({"_id": datos["id_plan"]})
    assert "origen" not in doc and "Café externo privado" not in str(doc)
    for opcion in doc["opciones_guardadas"]:
        original = next(p for p in datos["planes"] if p["tipo"] == opcion["tipo"])
        assert [p["place_id"] for p in opcion["paradas"]] == [p["lugar_id"] for p in original["paradas"]]
        assert all(set(p) == {"place_id", "categoria"} for p in opcion["paradas"])
    resumen = cliente.get("/api/planes", headers=h).json()[0]
    assert resumen["tiene_detalle"] and resumen["estado_usuario"] == "borrador"
    assert "opciones_guardadas" not in resumen and "id_usuario" not in resumen


def test_elegir_renombrar_realizar_y_recuperar_tras_nueva_sesion(escenario):
    cliente, bd, h, _, datos, _ = escenario
    ruta = f"/api/planes/{datos['id_plan']}"
    elegir(escenario)
    ficha = cliente.patch(ruta, headers=h, json={"titulo": "  Mi salida   de sábado  ", "estado_usuario": "realizado"}).json()
    assert ficha["titulo"] == "Mi salida de sábado" and ficha["estado_usuario"] == "realizado"
    # Otro cliente, sin el estado en memoria de las pantallas.
    with TestClient(app) as nuevo:
        ficha = nuevo.get(ruta, headers=h).json()
        assert ficha["titulo"] == "Mi salida de sábado"
        recuperado = nuevo.post(ruta + "/recuperar", headers=h, json={"origen": PETICION["origen"], "hora_salida": "18:00"})
    assert recuperado.status_code == 200, recuperado.text
    respuesta = recuperado.json()["respuesta"]
    assert respuesta["id_plan"] == datos["id_plan"] and respuesta["planes"]
    guardado = bd.planes.find_one({"_id": datos["id_plan"]})
    refs = next(o for o in guardado["opciones_guardadas"] if o["tipo"] == ficha["tipo_seleccionado"])
    assert [p["lugar_id"] for p in respuesta["planes"][0]["paradas"]] == [p["place_id"] for p in refs["paradas"]]
    assert bd.planes.count_documents({}) == 1  # abrir no duplica el historial
    assert guardado["estado_usuario"] == "realizado"


@pytest.mark.parametrize("metodo,cuerpo,sufijo", [
    ("GET", None, ""), ("PATCH", {"titulo": "Ajeno"}, ""), ("DELETE", None, ""),
    ("POST", {"origen": PETICION["origen"], "hora_salida": "18:00"}, "/recuperar"),
])
def test_aislamiento_entre_usuarios_y_sesion_obligatoria(escenario, metodo, cuerpo, sufijo):
    cliente, _, _, otro, datos, _ = escenario
    ruta = f"/api/planes/{datos['id_plan']}{sufijo}"
    assert cliente.request(metodo, ruta, json=cuerpo, headers=otro).status_code == 404
    assert cliente.request(metodo, ruta, json=cuerpo).status_code == 401
    assert cliente.get("/api/planes", headers=otro).json() == []


@pytest.mark.parametrize("cambio", [{}, {"titulo": "   "}, {"titulo": "x" * 81}, {"titulo": None}, {"id_usuario": 1}, {"estado_usuario": "inventado"}])
def test_rechaza_cambios_invalidos(escenario, cambio):
    cliente, _, h, _, datos, _ = escenario
    assert cliente.patch(f"/api/planes/{datos['id_plan']}", headers=h, json=cambio).status_code == 422


def test_no_realiza_un_plan_sin_seleccionar_y_no_inyecta_paradas(escenario):
    cliente, bd, h, _, datos, _ = escenario
    ruta = f"/api/planes/{datos['id_plan']}"
    assert cliente.patch(ruta, headers=h, json={"estado_usuario": "realizado"}).status_code == 409
    bd.planes.update_one({"_id": datos["id_plan"]}, {"$set": {"opciones_guardadas": []}})
    assert cliente.patch(ruta, headers=h, json={"tipo_seleccionado": "equilibrado"}).status_code == 422


def test_borrado_logico_y_recuperacion_bloqueada(escenario):
    cliente, bd, h, _, datos, _ = escenario
    elegir(escenario)
    ruta = f"/api/planes/{datos['id_plan']}"
    assert cliente.delete(ruta, headers=h).status_code == 204
    assert cliente.get("/api/planes", headers=h).json() == []
    assert bd.planes.find_one({"_id": datos["id_plan"]})["deleted_at"] is not None
    assert cliente.get(ruta, headers=h).status_code == 404
    assert cliente.patch(ruta, headers=h, json={"titulo": "No"}).status_code == 404
    assert cliente.post(ruta + "/recuperar", headers=h, json={"origen": PETICION["origen"], "hora_salida": "18:00"}).status_code == 404


def test_registro_legacy_se_conserva_sin_inventar_detalle(escenario):
    cliente, bd, h, _, datos, _ = escenario
    ruta = f"/api/planes/{datos['id_plan']}"
    bd.planes.update_one({"_id": datos["id_plan"]}, {"$unset": {"opciones_guardadas": "", "titulo": "", "estado_usuario": ""}})
    ficha = cliente.get(ruta, headers=h).json()
    assert ficha["titulo"] == "Plan de salida" and not ficha["tiene_detalle"]
    assert cliente.patch(ruta, headers=h, json={"titulo": "Recuerdo"}).status_code == 200
    assert cliente.post(ruta + "/recuperar", headers=h, json={"origen": PETICION["origen"], "hora_salida": "18:00"}).status_code == 409


def test_precio_actual_se_revalida_y_el_plan_no_se_borra(escenario):
    cliente, bd, h, _, datos, lugares = escenario
    elegir(escenario)
    for lugar in lugares:
        lugar["rango_precio"] = {"min": 5000, "max": 6000, "moneda": "MXN"}
    r = cliente.post(f"/api/planes/{datos['id_plan']}/recuperar", headers=h, json={"origen": PETICION["origen"], "hora_salida": "18:00"})
    assert r.status_code == 200, r.text
    assert not r.json()["respuesta"]["datos_suficientes"] and not r.json()["respuesta"]["planes"]
    assert r.json()["respuesta"]["descartados"]
    assert bd.planes.find_one({"_id": datos["id_plan"]})["estado_usuario"] == "guardado"


def test_error_externo_conserva_el_plan_y_permite_reintentar(escenario, monkeypatch):
    cliente, bd, h, _, datos, _ = escenario
    elegir(escenario)
    def falla(_):
        raise google_places.ErrorGooglePlaces("No se pudo conectar con Google Places.")
    monkeypatch.setattr(google_places, "consultar_paradas", falla)
    r = cliente.post(f"/api/planes/{datos['id_plan']}/recuperar", headers=h, json={"origen": PETICION["origen"], "hora_salida": "18:00"})
    assert r.status_code == 503 and "Google Places" in r.json()["detail"]
    assert bd.planes.find_one({"_id": datos["id_plan"]})["deleted_at"] is None


def test_paginacion_y_origen_invalido(escenario):
    cliente, _, h, _, datos, _ = escenario
    elegir(escenario)
    assert len(cliente.get("/api/planes?limite=1", headers=h).json()) == 1
    assert cliente.get(f"/api/planes?antes_de={datos['id_plan']}", headers=h).json() == []
    assert cliente.get("/api/planes?limite=0", headers=h).status_code == 422
    assert cliente.post(f"/api/planes/{datos['id_plan']}/recuperar", headers=h, json={"origen": {"lat": 0, "lng": 0}, "hora_salida": "18:00"}).status_code == 422


@pytest.mark.parametrize("status,datos", [(404, {}), (429, {}), (200, {"businessStatus": "CLOSED_PERMANENTLY"}), (200, {"businessStatus": "CLOSED_TEMPORARILY"}), (200, {})])
def test_place_details_no_inventa_lugares(status, datos, monkeypatch):
    monkeypatch.setattr(get_settings(), "google_maps_api_key", "llave-de-prueba")
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(status, json=datos))) as cliente:
        with pytest.raises(google_places.ErrorGooglePlaces):
            google_places.consultar_paradas([{"place_id": "lugar", "categoria": "cafe"}], cliente=cliente)


def test_place_details_consulta_ids_ordenados_y_fieldmask(monkeypatch):
    monkeypatch.setattr(get_settings(), "google_maps_api_key", "llave-de-prueba")
    ids = []
    def responder(request):
        ids.append(request.url.path.rsplit("/", 1)[-1])
        assert "places." not in request.headers["X-Goog-FieldMask"]
        assert "businessStatus" in request.headers["X-Goog-FieldMask"]
        return httpx.Response(200, json={"id": ids[-1], "displayName": {"text": "Dato consultado"}, "location": {"latitude": 19.29, "longitude": -99.65}})
    with httpx.Client(transport=httpx.MockTransport(responder)) as cliente:
        lugares = google_places.consultar_paradas([{"place_id": p, "categoria": "cafe"} for p in ["b", "a"]], cliente=cliente)
    assert ids == ["b", "a"] and [l["place_id"] for l in lugares] == ids
