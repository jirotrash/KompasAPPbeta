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


def test_requiere_sesion(cliente):
    assert cliente.post("/api/itinerarios", json=PETICION).status_code == 401
    assert cliente.get("/api/planes").status_code == 401


def test_origen_fuera_de_zona_da_422(cliente, token_demo):
    peticion = {**PETICION, "origen": {"lat": 19.43, "lng": -99.13}}
    respuesta = cliente.post("/api/itinerarios", json=peticion, headers=encabezado(token_demo))
    assert respuesta.status_code == 422
    assert "zona piloto" in respuesta.json()["detail"]


def test_crea_planes_con_explicacion_y_los_guarda(cliente):
    h = encabezado(registrar(cliente, "planeador@ejemplo.mx")["token"])
    respuesta = cliente.post("/api/itinerarios", json=PETICION, headers=h)
    assert respuesta.status_code == 200, respuesta.text
    datos = respuesta.json()

    assert datos["datos_suficientes"] is True
    assert "costos ni horarios" in datos["aviso"]
    assert 1 <= len(datos["planes"]) <= 2
    assert [p["mejor_opcion"] for p in datos["planes"]][0] is True
    for plan in datos["planes"]:
        assert plan["costo"] is None  # la base no tiene costos
        assert plan["explicacion"] and plan["reglas_cumplidas"]
        assert len(plan["tramos"]) == len(plan["paradas"])
        assert all(t["modo"] in ("pie", "taxi") for t in plan["tramos"])
        assert plan["duracion_horas"] <= PETICION["tiempo_horas"]

    # Lo que no es de sus intereses se descarta con la regla correspondiente
    descartes = {d["nombre"]: [r["id"] for r in d["reglas"]] for d in datos["descartados"]}
    assert "R8" in descartes["Parque de ejemplo · Toluca"]

    guardados = cliente.get("/api/planes", headers=h).json()
    assert len(guardados) == 1
    assert guardados[0]["no_acompanantes"] == 1 and guardados[0]["tiempo_disponible"] == 240
    assert guardados[0]["categoria"] == "Comer" and guardados[0]["transporte"] == "Caminando"
    assert guardados[0]["fecha_plan"].endswith("18:00:00")


def test_sin_candidatos_no_inventa_planes(cliente, token_demo):
    # Caminando desde Lerma solo hay un café cerca: no alcanza para armar un plan
    peticion = {**PETICION, "intereses": ["cafe"], "movilidad": ["caminando"], "origen": {"lat": 19.285, "lng": -99.5115}}
    datos = cliente.post("/api/itinerarios", json=peticion, headers=encabezado(token_demo)).json()
    assert datos["planes"] == [] and datos["datos_suficientes"] is False
    assert "No tenemos información suficiente" in datos["aviso"]


def test_peticion_invalida(cliente, token_demo):
    peticion = {**PETICION, "intereses": [], "hora_salida": "25:00"}
    respuesta = cliente.post("/api/itinerarios", json=peticion, headers=encabezado(token_demo))
    assert respuesta.status_code == 422
    assert isinstance(respuesta.json()["detail"], str)
