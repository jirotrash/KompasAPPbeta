"""Pruebas unitarias para el módulo de IA y Machine Learning (ia_kompas).

Valida:
1. Algoritmo BFS para minimización de escalas (p01_grafo_bfs).
2. Regla fija determinista / baseline heurístico (p01_regla_fija).
3. Pipeline de datos Pandas: calidad, limpieza e imputación (p02_pipeline_datos).
4. Modelo supervisado con partición 70% train / 30% test y evaluación (p03_modelo_predictivo).
5. Endpoints REST de FastAPI (/api/ia/...).
"""

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modulos.ia_kompas.bfs_y_reglas import predecir_con_reglas
from app.modulos.ia_kompas.busqueda_escalas import GRAFO_BASE_KOMPAS, buscar_ruta_bfs
from app.modulos.ia_kompas.datos_kompas import (
    generar_dataset_recorridos_kompas,
    limpiar_dataset_recorridos_kompas,
    obtener_variables_recorridos_kompas,
)
from app.modulos.ia_kompas.datos_y_limpieza import generar_y_limpiar_datos_kompas
from app.modulos.ia_kompas.entrenamiento_particiones import (
    comparar_particiones_kompas,
    ejecutar_evaluacion_completa_modelo,
    evaluar_underfitting_overfitting,
)
from app.modulos.ia_kompas.modelo_entrenamiento import obtener_laboratorio_ia
from app.modulos.ia_kompas.modelo_predictivo import ModeloPredictivoKompás
from app.modulos.ia_kompas.pipeline_datos import (
    etapa_a_analisis_inicial,
    etapa_c_auditoria_calidad,
    etapa_d_limpieza_y_guardado,
    etapa_e_identificacion_variables,
    generar_dataset_crudo_kompas,
)
from app.modulos.ia_kompas.reglas_transporte import evaluar_traslado_regla_fija


@pytest.fixture
def cliente():
    return TestClient(app)


# ----------------------------------------------------------------------
# 1. Pruebas de Búsqueda en Anchura (BFS) - p01_grafo_bfs
# ----------------------------------------------------------------------
def test_bfs_encuentra_ruta_optima_con_minimas_escalas():
    # Terminal Toluca -> Centro Metepec está directamente conectado en GRAFO_BASE_KOMPAS
    resultado = buscar_ruta_bfs(
        grafo=GRAFO_BASE_KOMPAS,
        origen="Terminal Toluca",
        destino="Centro Metepec",
    )
    assert resultado["encontrado"] is True
    assert resultado["ruta_paradas"] == ["Terminal Toluca", "Centro Metepec"]
    assert resultado["num_escalas"] == 0
    assert resultado["saltos_totales"] == 1


def test_bfs_con_escalas_intermedias():
    # Cosmovitral -> Galerias Metepec debe pasar por puntos intermedios
    resultado = buscar_ruta_bfs(
        grafo=GRAFO_BASE_KOMPAS,
        origen="Cosmovitral",
        destino="Galerias Metepec",
    )
    assert resultado["encontrado"] is True
    assert len(resultado["ruta_paradas"]) >= 3
    assert resultado["ruta_paradas"][0] == "Cosmovitral"
    assert resultado["ruta_paradas"][-1] == "Galerias Metepec"
    assert resultado["num_escalas"] == len(resultado["ruta_paradas"]) - 2


def test_bfs_origen_igual_a_destino():
    resultado = buscar_ruta_bfs(
        grafo=GRAFO_BASE_KOMPAS,
        origen="Los Portales",
        destino="Los Portales",
    )
    assert resultado["encontrado"] is True
    assert resultado["ruta_paradas"] == ["Los Portales"]
    assert resultado["num_escalas"] == 0
    assert resultado["saltos_totales"] == 0


def test_bfs_nodo_inexistente():
    resultado = buscar_ruta_bfs(
        grafo=GRAFO_BASE_KOMPAS,
        origen="Lugar Fantasma",
        destino="Cosmovitral",
    )
    assert resultado["encontrado"] is False
    assert resultado["ruta_paradas"] == []


# ----------------------------------------------------------------------
# 2. Pruebas de Regla Fija (Baseline Heurístico) - p01_regla_fija
# ----------------------------------------------------------------------
def test_regla_fija_caminando_distancia_corta_sin_lluvia():
    res = evaluar_traslado_regla_fija(
        distancia_km=1.1,
        presupuesto_mxn=50.0,
        hora_dia=12,
        clima_lluvia=False,
    )
    assert res["modo_recomendado"] == "caminando"
    assert res["regla_activada"] == "R1_CORTA_DISTANCIA_BUEN_CLIMA"


def test_regla_fija_auto_privado_con_lluvia():
    res = evaluar_traslado_regla_fija(
        distancia_km=1.2,
        presupuesto_mxn=120.0,
        hora_dia=14,
        clima_lluvia=True,
    )
    assert res["modo_recomendado"] == "auto_privado"
    assert "CLIMA" in res["regla_activada"]


def test_regla_fija_transporte_publico_distancia_larga_bajo_presupuesto():
    res = evaluar_traslado_regla_fija(
        distancia_km=6.5,
        presupuesto_mxn=30.0,
        hora_dia=11,
        clima_lluvia=False,
    )
    assert res["modo_recomendado"] == "transporte_publico"


# ----------------------------------------------------------------------
# 3. Pruebas del Pipeline de Datos (Pandas) - p02_pipeline_datos
# ----------------------------------------------------------------------
def test_pipeline_datos_genera_audita_y_limpia(tmp_path):
    ruta_crudo = tmp_path / "kompas_crudo_test.csv"
    ruta_limpio = tmp_path / "kompas_limpio_test.csv"

    # Generación
    df_crudo = generar_dataset_crudo_kompas(ruta_csv=ruta_crudo, semilla=123)
    res_a = etapa_a_analisis_inicial(df_crudo)
    assert res_a["filas"] >= 150

    # Auditoría de calidad antes de limpiar (debe detectar nulos y duplicados intencionales)
    res_c = etapa_c_auditoria_calidad(df_crudo)
    assert len(res_c["nulos_por_columna"]) > 0
    assert res_c["filas_completamente_duplicadas"] >= 5

    # Limpieza
    df_limpio = etapa_d_limpieza_y_guardado(df_crudo, ruta_salida=ruta_limpio)
    assert ruta_limpio.exists()

    # Auditoría post-limpieza: 0 nulos en columnas predictoras y 0 duplicados
    assert df_limpio.isnull().sum()["rating_destino"] == 0
    assert df_limpio.isnull().sum()["presupuesto_mxn"] == 0
    assert df_limpio.duplicated().sum() == 0
    assert (df_limpio["distancia_km"] <= 0).sum() == 0

    # Separación formal X e y
    X, y, metadatos = etapa_e_identificacion_variables(df_limpio)
    assert len(X) == len(y)
    assert "distancia_km" in X.columns
    assert len(metadatos["clases_objetivo"]) >= 2


# ----------------------------------------------------------------------
# 4. Pruebas del Modelo Predictivo (70% Train / 30% Test) - p03_modelo_predictivo
# ----------------------------------------------------------------------
def test_modelo_predictivo_entrenamiento_70_30_y_metricas(tmp_path):
    ruta_crudo = tmp_path / "kompas_crudo.csv"
    ruta_limpio = tmp_path / "kompas_limpio.csv"

    df_crudo = generar_dataset_crudo_kompas(ruta_csv=ruta_crudo, semilla=42)
    etapa_d_limpieza_y_guardado(df_crudo, ruta_salida=ruta_limpio)

    modelo = ModeloPredictivoKompás(max_depth=4, random_state=42)
    metricas = modelo.entrenar_y_evaluar(ruta_csv_limpio=ruta_limpio, test_size=0.30)

    # Validar proporción 70% entrenamiento y 30% prueba
    total = metricas["total_muestras"]
    n_train = metricas["muestras_entrenamiento_70_pct"]
    n_test = metricas["muestras_prueba_30_pct"]
    assert n_train + n_test == total
    assert abs((n_test / total) - 0.30) < 0.05  # Aprox 30% test

    # Desempeño
    assert metricas["exactitud_machine_learning"] >= 0.70
    assert "etiquetas" in metricas["matriz_confusion"]

    # Inferencia de nuevo traslado
    prediccion = modelo.predecir_traslado({
        "distancia_km": 1.0,
        "presupuesto_mxn": 50.0,
        "hora_dia": 10,
        "clima_lluvia": False,
        "rating_destino": 4.7,
    })
    assert prediccion["modo_recomendado"] in {"caminando", "transporte_publico", "auto_privado"}
    assert 0.0 <= prediccion["confianza"] <= 1.0
    assert "prediccion_regla_fija" in prediccion["comparacion_baseline"]


# ----------------------------------------------------------------------
# 5. Pruebas de Endpoints de FastAPI (/api/ia/...)
# ----------------------------------------------------------------------
def test_endpoint_pipeline_estado(cliente):
    resp = cliente.get("/api/ia/pipeline-estado")
    assert resp.status_code == 200
    data = resp.json()
    assert "dataset_crudo_filas" in data
    assert "exactitud_modelo_ml" in data
    assert "particion" in data
    assert "entrenamiento_70_pct" in data["particion"]
    assert "prueba_30_pct" in data["particion"]


def test_endpoint_recomendar_traslado(cliente):
    payload = {
        "distancia_km": 1.2,
        "presupuesto_mxn": 60.0,
        "hora_dia": 12,
        "clima_lluvia": False,
        "rating_destino": 4.6,
        "origen": "Terminal Toluca",
        "destino": "Centro Metepec",
    }
    resp = cliente.post("/api/ia/recomendar-traslado", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["modo_recomendado"] in {"caminando", "transporte_publico", "auto_privado"}
    assert data["origen_decision"] == "machine_learning"
    assert data["ruta_bfs"] is not None
    assert data["ruta_bfs"]["origen"] == "Terminal Toluca"
    assert data["ruta_bfs"]["destino"] == "Centro Metepec"


def test_endpoint_ruta_bfs(cliente):
    payload = {
        "origen": "Cosmovitral",
        "destino": "Los Portales",
    }
    resp = cliente.post("/api/ia/ruta-bfs", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["encontrado"] is True
    assert "Cosmovitral" in data["ruta_paradas"]


# ----------------------------------------------------------------------
# 6. Pruebas de Dataset de 500 Recorridos, Optimización de Particiones y Under/Overfitting
# ----------------------------------------------------------------------
def test_dataset_500_recorridos_kompas_y_limpieza(tmp_path):
    ruta_crudo = tmp_path / "recorridos_500_crudo.csv"
    ruta_limpio = tmp_path / "recorridos_500_limpio.csv"
    ruta_revision = tmp_path / "recorridos_500_revision.csv"

    df_crudo = generar_dataset_recorridos_kompas(ruta_csv=ruta_crudo, n_recorridos_limpios=500, semilla=42)
    assert len(df_crudo) > 500
    assert df_crudo["rating_lugar"].isnull().sum() > 0
    assert df_crudo.duplicated().sum() > 0

    df_limpio, reporte = limpiar_dataset_recorridos_kompas(
        df_crudo=df_crudo,
        ruta_crudo=ruta_crudo,
        ruta_limpio=ruta_limpio,
        ruta_revision=ruta_revision,
    )
    assert len(df_limpio) == 500
    assert reporte["etapa_d"]["duplicados_eliminados"] > 0
    assert df_limpio["distancia_km"].between(0.5, 25.0).all()
    assert df_limpio["presupuesto_mxn"].between(20.0, 500.0).all()
    assert df_limpio["rating_lugar"].between(3.0, 5.0).all()
    assert df_limpio["num_paradas"].between(1, 8).all()
    assert df_limpio["trafico_nivel"].between(1, 10).all()
    assert set(df_limpio["modo_optimo"].unique()).issubset({"caminando", "transporte_publico", "auto_privado"})
    assert "plan_viable" in df_limpio.columns


def test_optimizacion_particiones_y_control_under_overfitting(tmp_path):
    ruta_crudo = tmp_path / "recorridos_crudo.csv"
    ruta_limpio = tmp_path / "recorridos_limpio.csv"
    ruta_revision = tmp_path / "recorridos_revision.csv"

    df_crudo = generar_dataset_recorridos_kompas(ruta_csv=ruta_crudo, n_recorridos_limpios=500, semilla=42)
    df_limpio, _ = limpiar_dataset_recorridos_kompas(
        df_crudo=df_crudo,
        ruta_crudo=ruta_crudo,
        ruta_limpio=ruta_limpio,
        ruta_revision=ruta_revision,
    )
    X, y, _ = obtener_variables_recorridos_kompas(df_limpio)

    # 1. Validar análisis de Underfitting vs Overfitting (max_depth 1 a 15)
    ajuste = evaluar_underfitting_overfitting(X, y, random_state=42)
    assert 3 <= ajuste["max_depth_optimo"] <= 5
    assert len(ajuste["curva_profundidad"]) == 15

    depth_1 = ajuste["evidencia_underfitting"]["max_depth_1"]
    depth_optimo = ajuste["metricas_depth_optimo"]
    depth_15 = ajuste["evidencia_overfitting"]["max_depth_15"]

    # Demostración de Underfitting en max_depth=1
    assert depth_1["exactitud_prueba"] < depth_optimo["exactitud_prueba"]
    assert depth_1["diagnostico"] == "underfitting"

    # Demostración de Overfitting en max_depth>=12 (alta exactitud en train pero brecha o caída en val/test)
    assert depth_15["exactitud_entrenamiento"] >= 0.98
    assert depth_15["brecha_generalizacion"] > depth_optimo["brecha_generalizacion"]
    assert depth_15["diagnostico"] == "overfitting"

    # El árbol en max_depth óptimo supera a las Reglas Fijas
    comp_regla = ajuste["comparacion_regla_fija"]
    assert comp_regla["exactitud_arbol_optimo"] > comp_regla["exactitud_regla_fija"]
    assert comp_regla["mejora_exactitud_puntos"] > 0

    # 2. Validar comparador de particiones (70/30, 75/25, 80/20, 85/15, 60/20/20)
    particiones = comparar_particiones_kompas(X, y, max_depth=ajuste["max_depth_optimo"], random_state=42)
    codigos = {item["codigo"] for item in particiones["tabla_particiones"]}
    assert codigos == {"70_30", "75_25", "80_20", "85_15", "60_20_20"}

    optima = particiones["particion_optima_seleccionada"]
    baseline = particiones["particion_baseline_70_30"]
    assert optima["codigo"] != "70_30"
    assert optima["f1_prueba_ponderado"] >= baseline["f1_prueba_ponderado"]
    assert len(particiones["comparativa_optima_vs_70_30"]["justificacion_tecnica"]) > 50


def test_endpoint_evaluacion_modelo(cliente):
    resp = cliente.get("/api/ia/evaluacion-modelo")
    assert resp.status_code == 200
    data = resp.json()

    assert data["dataset_kompas"]["total_muestras"] == 500
    assert len(data["tabla_comparativa_particiones"]) == 5
    assert "particion_optima" in data
    assert "particion_baseline_70_30" in data
    assert "analisis_underfitting_overfitting" in data
    assert "comparacion_contra_reglas_fijas" in data
    assert "matriz_confusion" in data
    assert len(data["matriz_confusion"]["etiquetas"]) == 3


# ----------------------------------------------------------------------
# 7. Pruebas de Laboratorio IA End-to-End (/api/ia/metricas y /api/ia/simular)
# ----------------------------------------------------------------------
def test_datos_y_limpieza_500_planes_y_reglas(tmp_path):
    df_limpio, resumen = generar_y_limpiar_datos_kompas(
        n_registros=500,
        semilla=42,
        ruta_crudo=tmp_path / "planes_crudo.csv",
        ruta_limpio=tmp_path / "planes_limpio.csv",
    )
    assert resumen["registros_iniciales"] > 500
    assert resumen["nulos_imputados"] >= 20
    assert resumen["duplicados_eliminados"] >= 10
    assert resumen["registros_limpios"] == 500
    assert resumen["nulos_restantes"] == 0
    assert set(df_limpio["plan_viable"].unique()) == {0, 1}

    regla_ok = predecir_con_reglas(
        distancia_km=4.0,
        presupuesto_mxn=240.0,
        rating_lugar=4.6,
        num_paradas=3,
        trafico_nivel=4,
    )
    assert regla_ok["plan_viable"] == 1
    assert regla_ok["etiqueta_viabilidad"] == "viable"


def test_endpoint_metricas_laboratorio_ia(cliente):
    resp = cliente.get("/api/ia/metricas")
    assert resp.status_code == 200
    data = resp.json()

    assert data["resumen_limpieza"]["registros_limpios"] == 500
    assert len(data["comparativa_particiones"]) == 5
    codigos = {p["codigo"] for p in data["comparativa_particiones"]}
    assert codigos == {"60_40", "70_30", "75_25", "80_20", "60_20_20"}

    # Verificar que la partición óptima supere el umbral esperado (>= 0.80) y al baseline 70/30
    optima = next(p for p in data["comparativa_particiones"] if p["es_optima"])
    baseline = next(p for p in data["comparativa_particiones"] if p["codigo"] == "70_30")
    assert optima["test_acc"] >= 0.80
    assert optima["test_acc"] >= baseline["test_acc"]
    assert data["comparativa_sistemas"]["exactitud_ml"] > data["comparativa_sistemas"]["exactitud_reglas"]

    # Verificar curva de complejidad en profundidades [1, 2, 3, 4, 5, 8, 12, 15]
    profundidades = [c["max_depth"] for c in data["curva_complejidad"]]
    assert profundidades == [1, 2, 3, 4, 5, 8, 12, 15]
    estados = {c["estado"] for c in data["curva_complejidad"]}
    assert "Underfitting (Subajuste)" in estados
    assert "Buen ajuste" in estados
    assert "Overfitting (Sobreajuste)" in estados


def test_endpoint_simular_ia(cliente):
    payload = {
        "distancia_km": 6.5,
        "presupuesto_mxn": 240.0,
        "rating_lugar": 4.6,
        "num_paradas": 3,
        "trafico_nivel": 5,
        "origen": "Terminal Toluca",
        "destino": "Galerias Metepec",
    }
    resp = cliente.post("/api/ia/simular", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["prediccion_reglas"]["plan_viable"] in {0, 1}
    assert data["prediccion_arbol_ml"]["plan_viable"] in {0, 1}
    assert 0.0 <= data["prediccion_arbol_ml"]["confianza"] <= 1.0
    assert data["ruta_bfs"]["encontrado"] is True
    assert data["ruta_bfs"]["ruta_paradas"][0] == "Terminal Toluca"
    assert data["ruta_bfs"]["ruta_paradas"][-1] == "Galerias Metepec"


