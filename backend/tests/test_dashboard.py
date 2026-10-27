import pytest

from app.nucleo.bd import ahora, siguiente_id
from tests.conftest import encabezado, registrar

ENDPOINTS = {
    "kpis": {
        "usuarios_totales", "usuarios_nuevos", "planes", "porcentaje_con_recomendacion", "recorridos",
        "tiempo_promedio_recorrido_min", "reportes_vigentes", "lugares",
    },
    "series": {"serie", "planes_por_interes"},
    "planes": {"por_interes", "por_movilidad", "por_contexto", "presupuesto", "tiempo_disponible", "dia_hora", "interes_por_contexto"},
    "sistema-experto": {"por_estado", "reglas_top", "puntuacion_por_tipo", "sin_datos_suficientes", "por_version"},
    "movilidad": {"por_transporte", "rutas_top", "paradas_uso"},
    "reportes": {"por_tipo_estado", "vigentes_vs_vencidos", "puntos"},
    "lugares": {"por_categoria", "puntos"},
    "laboratorio": {
        "dfs_puntos", "dfs_pares_top", "distancias_puntos",
        "busqueda_algoritmos", "genetico_convergencia", "genetico_ahorro", "transbordos",
    },
    "asistente": {"por_dia", "herramientas", "tiempo_respuesta", "errores", "planes_por_origen"},
}


@pytest.fixture
def plan_demo(bd):
    """Un plan con demo: true creado hoy (se borra al terminar la prueba)."""
    momento = ahora()
    doc = {
        "_id": siguiente_id(bd, "planes"),
        "id_usuario": 1,
        "contexto": "familia",
        "no_acompanantes": 3,
        "presupuesto": {"min": 100, "max": 450},
        "tiempo_disponible": 180,
        "intereses": ["aire_libre"],
        "movilidad": ["caminando"],
        "categoria": {"id": 5, "nombre": "Aire libre"},
        "transporte": {"id": 1, "nombre": "Caminando"},
        "hora_salida": "11:00",
        "fecha_plan": momento.replace(hour=11, minute=0),
        "evaluacion": {
            "version_reglas": "0.1.0",
            "datos_suficientes": True,
            "candidatos": [{"tipo": "equilibrado", "estado": "recomendable", "puntuacion": 4, "reglas": ["R15", "R16"]}],
        },
        "demo": True,
        "created_at": momento,
        "updated_at": momento,
        "deleted_at": None,
    }
    bd.planes.insert_one(doc)
    yield doc
    bd.planes.delete_one({"_id": doc["_id"]})


def test_sin_token_da_401_y_usuario_normal_403(cliente):
    assert cliente.get("/api/dashboard/kpis").status_code == 401
    h = encabezado(registrar(cliente, "curioso@ejemplo.mx")["token"])
    for endpoint in ENDPOINTS:
        respuesta = cliente.get(f"/api/dashboard/{endpoint}", headers=h)
        assert respuesta.status_code == 403
        assert respuesta.json()["detail"] == "Solo un administrador puede ver el dashboard."


def test_el_demo_es_admin(cliente, token_demo):
    assert cliente.get("/api/auth/yo", headers=encabezado(token_demo)).json()["rol"] == "admin"


@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_cada_endpoint_regresa_sus_llaves(cliente, token_demo, endpoint):
    respuesta = cliente.get(f"/api/dashboard/{endpoint}", headers=encabezado(token_demo))
    assert respuesta.status_code == 200, respuesta.text
    datos = respuesta.json()
    assert ENDPOINTS[endpoint] <= set(datos)
    assert {"periodo", "incluye_demo"} <= set(datos)


def test_incluir_demo_false_no_cuenta_documentos_demo(cliente, token_demo, plan_demo):
    h = encabezado(token_demo)
    con_demo = cliente.get("/api/dashboard/kpis", headers=h).json()
    sin_demo = cliente.get("/api/dashboard/kpis", params={"incluir_demo": "false"}, headers=h).json()
    assert con_demo["planes"] == sin_demo["planes"] + 1
    assert con_demo["incluye_demo"] is True and sin_demo["incluye_demo"] is False

    planes = cliente.get("/api/dashboard/planes", params={"incluir_demo": "false"}, headers=h).json()
    assert {"contexto": "familia", "total": 0} in planes["por_contexto"]


def test_dias_sin_datos_aparecen_con_cero(cliente, token_demo):
    params = {"desde": "2020-01-01", "hasta": "2020-01-05", "agrupar": "dia"}
    datos = cliente.get("/api/dashboard/series", params=params, headers=encabezado(token_demo)).json()
    assert [p["fecha"] for p in datos["serie"]] == [f"2020-01-0{d}" for d in range(1, 6)]
    assert all(p["usuarios"] == p["planes"] == p["recorridos"] == 0 for p in datos["serie"])
    assert all(p["comer"] == 0 for p in datos["planes_por_interes"])


def test_planes_rellena_categorias_y_mapa_de_calor(cliente, token_demo):
    datos = cliente.get("/api/dashboard/planes", headers=encabezado(token_demo)).json()
    assert {i["interes"] for i in datos["por_interes"]} == {"comer", "cafe", "cultura", "entretenimiento", "aire_libre"}
    assert len(datos["dia_hora"]) == 7 * 24
    assert len(datos["presupuesto"]) == 7 and len(datos["tiempo_disponible"]) == 7


def test_reglas_con_descripcion(cliente, token_demo, plan_demo):
    datos = cliente.get("/api/dashboard/sistema-experto", headers=encabezado(token_demo)).json()
    assert datos["reglas_top"] and all(r["descripcion"] for r in datos["reglas_top"])


def test_rango_invertido_da_422(cliente, token_demo):
    respuesta = cliente.get("/api/dashboard/kpis", params={"desde": "2026-10-10", "hasta": "2026-10-01"}, headers=encabezado(token_demo))
    assert respuesta.status_code == 422


def test_laboratorio_con_busqueda_y_genetico(cliente, token_demo):
    h = encabezado(token_demo)
    cliente.get("/api/busqueda/comparar", params={"origen": "TerminalToluca", "destino": "PlazaSendero"}, headers=h)
    cuerpo = {"paradas": [{"lat": 19.289, "lng": -99.664}, {"lat": 19.2785, "lng": -99.6455}, {"lat": 19.2838, "lng": -99.6765}], "generaciones": 10}
    cliente.post("/api/genetico/ordenar-paradas", json=cuerpo, headers=h)
    datos = cliente.get("/api/dashboard/laboratorio", headers=h).json()
    etiquetas = [a["etiqueta"] for a in datos["busqueda_algoritmos"]]
    assert etiquetas[:6] == ["DFS", "UCS", "Voraz (Euclidiana)", "Voraz (Manhattan)", "A* (Euclidiana)", "A* (Manhattan)"]
    a_euclidiana = datos["busqueda_algoritmos"][4]
    assert a_euclidiana["porcentaje_optimo"] == 100 and a_euclidiana["razon_vs_optimo"] == 1
    assert datos["genetico_convergencia"][0]["generacion"] == 1
    assert all(p["mejor"] >= p["promedio"] for p in datos["genetico_convergencia"])


def test_asistente_sin_contenido_de_mensajes(cliente, bd, token_demo):
    from app.nucleo.bd import ahora

    momento = ahora()
    bd.conversaciones.insert_one(
        {
            "id_usuario": 1,
            "titulo": "Secreto",
            "modelo": "llama3.2:3b",
            "mensajes": [
                {"rol": "usuario", "contenido": "texto privado", "creado_en": momento},
                {"rol": "herramienta", "nombre": "como_llegar", "argumentos": {}, "resultado_ref": None, "creado_en": momento},
                {"rol": "asistente", "contenido": "respuesta", "duracion_ms": 1000, "creado_en": momento},
                {"rol": "usuario", "contenido": "otro", "creado_en": momento},
                {"rol": "error", "contenido": "El asistente no está disponible en este momento.", "creado_en": momento},
            ],
            "rutas_consultadas": [],
            "planes_creados": [],
            "created_at": momento,
            "updated_at": momento,
            "deleted_at": None,
        }
    )
    respuesta = cliente.get("/api/dashboard/asistente", headers=encabezado(token_demo))
    assert respuesta.status_code == 200, respuesta.text
    datos = respuesta.json()
    assert "texto privado" not in respuesta.text and "Secreto" not in respuesta.text
    hoy = datos["por_dia"][-1]
    assert hoy["conversaciones"] >= 1 and hoy["mensajes"] >= 2
    assert {"herramienta": "como_llegar", "total": 1} in datos["herramientas"] or datos["herramientas"][0]["total"] >= 1
    assert datos["errores"]["errores"] >= 1 and 0 < datos["errores"]["porcentaje_error"] <= 100
    assert datos["tiempo_respuesta"]["p90_ms"] is not None
    assert [o["origen"] for o in datos["planes_por_origen"]] == ["planificador", "asistente"]


def test_percentil():
    from app.modulos.dashboard.servicio import percentil

    assert percentil([], 90) is None
    assert percentil([10], 90) == 10
    assert percentil(list(range(1, 11)), 90) == 9.1
