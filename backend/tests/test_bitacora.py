"""Las demostraciones académicas dejan un registro en `bitacora_laboratorio` sin cambiar su respuesta."""


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
