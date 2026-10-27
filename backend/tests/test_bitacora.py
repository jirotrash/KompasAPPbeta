"""Las demostraciones académicas dejan un registro en `bitacora_laboratorio` sin cambiar su respuesta."""

from tests.conftest import encabezado


def test_busqueda_dfs_deja_registro(cliente, bd):
    antes = bd.bitacora_laboratorio.count_documents({"tipo": "dfs"})
    respuesta = cliente.get("/api/dfs/buscar", params={"origen": "TerminalToluca", "destino": "CentroToluca"})
    assert respuesta.status_code == 200 and respuesta.json()["exito"] is True

    assert bd.bitacora_laboratorio.count_documents({"tipo": "dfs"}) == antes + 1
    registro = bd.bitacora_laboratorio.find_one({"tipo": "dfs"}, sort=[("creado_en", -1)])
    datos = respuesta.json()
    assert registro["origen"] == "TerminalToluca" and registro["destino"] == "CentroToluca"
    assert registro["limite_profundidad"] == 5 and registro["exito"] is True
    assert registro["total_nodos_explorados"] == datos["total_nodos_explorados"]
    assert registro["total_rutas"] == datos["total_rutas_encontradas"]
    assert registro["profundidad_maxima"] >= 1


def test_distancias_dejan_registro(cliente, bd):
    cliente.get("/api/distancias/plano", params={"a": "1,2", "b": "5,5"})
    registro = bd.bitacora_laboratorio.find_one({"tipo": "distancia", "modo": "plano"}, sort=[("creado_en", -1)])
    assert registro["euclidiana"] == 5 and registro["manhattan"] == 7


def test_comparar_busqueda_solo_admin_y_deja_registro(cliente, bd, token_demo):
    params = {"origen": "TerminalToluca", "destino": "PlazaSendero"}
    assert cliente.get("/api/busqueda/comparar", params=params).status_code == 401
    respuesta = cliente.get("/api/busqueda/comparar", params=params, headers=encabezado(token_demo))
    assert respuesta.status_code == 200
    filas = respuesta.json()["filas"]
    assert [(f["algoritmo"], f["heuristica"]) for f in filas] == [
        ("dfs", None),
        ("costo_uniforme", None),
        ("voraz", "euclidiana"),
        ("voraz", "manhattan"),
        ("a_estrella", "euclidiana"),
        ("a_estrella", "manhattan"),
    ]
    registro = bd.bitacora_laboratorio.find_one({"tipo": "busqueda"}, sort=[("creado_en", -1)])
    assert len(registro["algoritmos"]) == 6 and registro["costo_optimo_km"] == respuesta.json()["costo_optimo_km"]
    otro = cliente.get("/api/busqueda/comparar", params={"origen": "X", "destino": "Y"}, headers=encabezado(token_demo))
    assert otro.status_code == 404


def test_genetico_por_endpoint(cliente, bd, token_demo):
    cuerpo = {
        "origen": {"lat": 19.2926, "lng": -99.6557},
        "paradas": [
            {"nombre": "A", "lat": 19.2890, "lng": -99.6640},
            {"nombre": "B", "lat": 19.2785, "lng": -99.6455},
            {"nombre": "C", "lat": 19.2838, "lng": -99.6765},
        ],
        "semilla": 3,
        "generaciones": 40,
    }
    assert cliente.post("/api/genetico/ordenar-paradas", json=cuerpo).status_code == 401
    datos = cliente.post("/api/genetico/ordenar-paradas", json=cuerpo, headers=encabezado(token_demo)).json()
    assert sorted(datos["mejor_orden"]) == [0, 1, 2] and len(datos["historial"]) == 40
    assert datos["brecha_vs_optimo_%"] == 0
    assert datos["parametros"]["poblacion"] == 60
    registro = bd.bitacora_laboratorio.find_one({"tipo": "genetico", "origen": "endpoint"}, sort=[("creado_en", -1)])
    assert len(registro["historial_mejor"]) == 40
