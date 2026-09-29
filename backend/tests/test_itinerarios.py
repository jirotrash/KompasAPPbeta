import pytest

from app.servicios import google_places
from app.servicios.geo import ahora_mexico
from tests.conftest import encabezado, registrar

PETICION = {
    "contexto": "pareja",
    "presupuesto": {"min": 200, "max": 1500},
    "tiempo_horas": 4,
    "intereses": ["comer", "cafe", "cultura"],
    "movilidad": ["caminando", "taxi_app"],
    "origen": {"lat": 19.2926, "lng": -99.6557},
    "hora_salida": "18:00",
}

# Abierto siempre (representación 24/7 de Google) para que la prueba no dependa de la hora en que corre
ABIERTO_SIEMPRE = {"periods": [{"open": {"day": 0, "hour": 0, "minute": 0}}]}


def lugar_google(place_id: str, nombre: str, categoria: str, lat: float, lng: float, con_precio: bool = True) -> dict:
    """Lugar con la forma que regresa google_places.buscar_para_plan (datos simulados, no reales)."""
    return {
        "place_id": place_id,
        "nombre": nombre,
        "categoria": categoria,
        "lat": lat,
        "lng": lng,
        "tipos": [],
        "horario": ABIERTO_SIEMPRE,
        "nivel_precio": "PRICE_LEVEL_MODERATE",
        "rango_precio": {"min": 100, "max": 180, "moneda": "MXN"} if con_precio else None,
        "calificacion": 4.5,
        "total_resenas": 120,
        "fuente": "Google",
        "consultado_en": ahora_mexico().isoformat(),
    }


@pytest.fixture
def google(monkeypatch):
    """Sustituye la consulta a Google Places: la prueba decide qué lugares "regresa"."""
    respuesta: dict = {"lugares": []}

    def falso(origen, intereses, radio_km):
        if isinstance(respuesta["lugares"], Exception):
            raise respuesta["lugares"]
        return respuesta["lugares"]

    monkeypatch.setattr(google_places, "buscar_para_plan", falso)
    return respuesta


def test_requiere_sesion(cliente):
    assert cliente.post("/api/itinerarios", json=PETICION).status_code == 401
    assert cliente.get("/api/planes").status_code == 401


def test_origen_fuera_de_zona_da_422(cliente, token_demo):
    peticion = {**PETICION, "origen": {"lat": 19.43, "lng": -99.13}}
    respuesta = cliente.post("/api/itinerarios", json=peticion, headers=encabezado(token_demo))
    assert respuesta.status_code == 422
    assert "zona piloto" in respuesta.json()["detail"]


def test_crea_planes_con_el_motor_de_einar_y_los_guarda(cliente, google):
    google["lugares"] = [
        # El más cercano no trae precio: el plan "cercano" queda pendiente de verificación
        lugar_google("sin-precio", "Fonda sin precio", "comer", 19.2927, -99.6558, con_precio=False),
        lugar_google("cafe", "Café de prueba", "cafe", 19.2935, -99.6570),
        lugar_google("restaurante", "Restaurante de prueba", "comer", 19.2905, -99.6530),
        lugar_google("museo", "Museo de prueba", "cultura", 19.2950, -99.6590),
    ]
    h = encabezado(registrar(cliente, "planeador@ejemplo.mx")["token"])
    respuesta = cliente.post("/api/itinerarios", json=PETICION, headers=h)
    assert respuesta.status_code == 200, respuesta.text
    datos = respuesta.json()

    assert datos["datos_suficientes"] is True
    assert datos["version_reglas"] == "0.1.0"
    assert "cierres" in datos["aviso"]  # R13: esta versión no verifica cierres
    assert datos["planes"][0]["mejor_opcion"] is True
    puntuaciones = [p["puntuacion"] for p in datos["planes"]]
    assert puntuaciones == sorted(puntuaciones, reverse=True)
    for plan in datos["planes"]:
        assert plan["estado"] == "recomendable" and plan["costo"] is None
        assert "R16" in [r["id"] for r in plan["reglas_cumplidas"]]
        assert plan["explicacion"]
        assert len(plan["tramos"]) == len(plan["paradas"]) >= 2
        assert all(t["modo"] in ("pie", "taxi") and t["estimado"] for t in plan["tramos"])
        assert plan["duracion_horas"] <= PETICION["tiempo_horas"]

    assert any(d["estado"] == "pendiente_verificacion" and d["datos_faltantes"] for d in datos["descartados"])

    guardados = cliente.get("/api/planes", headers=h).json()
    assert len(guardados) == 1
    assert guardados[0]["no_acompanantes"] == 1 and guardados[0]["tiempo_disponible"] == 240
    assert guardados[0]["categoria"] == "Comer" and guardados[0]["transporte"] == "Caminando"
    assert guardados[0]["fecha_plan"].endswith("18:00:00")


def test_sin_lugares_suficientes_no_inventa_planes(cliente, token_demo, google):
    google["lugares"] = [lugar_google("cafe", "Café de prueba", "cafe", 19.2935, -99.6570)]
    datos = cliente.post("/api/itinerarios", json=PETICION, headers=encabezado(token_demo)).json()
    assert datos["planes"] == [] and datos["datos_suficientes"] is False
    assert "No tenemos información suficiente" in datos["aviso"]


def test_google_no_disponible_da_503(cliente, token_demo, google):
    google["lugares"] = google_places.ErrorGooglePlaces("Se agotó la cuota de Google Places; intenta más tarde.")
    respuesta = cliente.post("/api/itinerarios", json=PETICION, headers=encabezado(token_demo))
    assert respuesta.status_code == 503
    assert "Google Places" in respuesta.json()["detail"]


def test_peticion_invalida(cliente, token_demo):
    peticion = {**PETICION, "intereses": [], "hora_salida": "25:00"}
    respuesta = cliente.post("/api/itinerarios", json=peticion, headers=encabezado(token_demo))
    assert respuesta.status_code == 422
    assert isinstance(respuesta.json()["detail"], str)
