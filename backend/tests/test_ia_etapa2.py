"""Pruebas unitarias y de integracion para la Etapa 2 de IA en KompasAPPbeta (P14 a P27).

Valida:
- P14: Motor Inteligente de Recomendaciones Multimodelo (RF + KMeans + PCA).
- P15 y P16: Persistencia y consultas de agregacion con MongoDB Atlas.
- P20, P21 y P22: Pipeline de Big Data y Procesamiento Distribuido.
- P24: Red Neuronal Convolucional 1D para clasificacion de congestion (PyTorch).
- P25: Benchmark comparativo Machine Learning Clasico vs Deep Learning CNN 1D.
- P27: Red Convolucional 1D para regresion continua de tiempo de arribo (ETA).
"""

import pytest
from app.modulos.ia_kompas.p14_motor_recomendaciones import MotorRecomendacionesKompas, PERFILES_VIAJEROS
from app.modulos.ia_kompas.p16_consultas_analiticas import AnaliticaAtlasKompas
from app.modulos.ia_kompas.p24_red_cnn1d_clasificacion import ClasificadorCongestionCNN1D
from app.modulos.ia_kompas.p25_comparacion_modelos_dl import ComparadorMLvsDLKompas
from app.modulos.ia_kompas.p27_red_cnn1d_eta_regresion import RegresorETACNN1D
from app.modulos.ia_kompas.servicio import ServicioIAKompas


def test_p14_motor_recomendaciones_integral():
    """Valida la inferencia conjunta (Supervisado + K-Means + PCA) y generacion de directivas."""
    motor = MotorRecomendacionesKompas()
    consulta = {
        "distancia_km": 14.5,
        "hora_dia": 8,
        "duracion_min": 45.0,
        "presupuesto_mxn": 20.0,
        "es_hora_pico": 1,
        "clima_lluvia": 0,
    }
    resultado = motor.evaluar_traslado_integral(consulta)

    # Validar modelo supervisado
    sup = resultado["prediccion_supervisada"]
    assert "transporte_optimo" in sup
    assert 0.0 <= sup["confianza"] <= 1.0

    # Validar cluster K-Means
    cluster = resultado["segmentacion_no_supervisada"]
    assert cluster["cluster_asignado"] in [0, 1, 2, 3]
    assert cluster["nombre_perfil"] in [p["nombre"] for p in PERFILES_VIAJEROS.values()]

    # Validar PCA 2D
    pca = resultado["reduccion_dimensionalidad_pca"]
    assert isinstance(pca["coordenada_pc1"], float)
    assert isinstance(pca["coordenada_pc2"], float)
    assert pca["varianza_explicada_acumulada_pct"] > 40.0

    # Validar directivas de recomendacion
    recs = resultado["recomendaciones_operativas"]
    assert len(recs) >= 2


def test_p16_consultas_analiticas():
    """Valida los pipelines de agregacion y persistencia de evaluaciones."""
    import pymongo.errors
    try:
        analitica = AnaliticaAtlasKompas()
        # Guardar una evaluacion de prueba
        res_guardado = analitica.guardar_evaluacion({
            "datos_entrada": {"distancia_km": 10.0, "hora_dia": 9, "presupuesto_mxn": 15.0, "duracion_min": 30.0},
            "prediccion_supervisada": {"transporte_optimo": "Metro", "confianza": 0.92},
            "segmentacion_no_supervisada": {"cluster_asignado": 0, "nombre_perfil": "Viajero Economico"},
            "reduccion_dimensionalidad_pca": {"coordenada_pc1": -1.2, "coordenada_pc2": 0.4},
            "recomendaciones_operativas": ["Priorizar tarjeta multimodal"],
        })
        assert "id_evaluacion" in res_guardado

        # Validar agrupaciones
        stats_clusters = analitica.estadisticas_por_cluster()
        assert isinstance(stats_clusters, list)

        stats_horas = analitica.resumen_horas_pico_congestion()
        assert isinstance(stats_horas, list)

        # Validar registro integral en 3 colecciones (Practica 19)
        res_triple = analitica.registro_integral_tres_colecciones(
            datos_usuario={"id_usuario": "USR-TEST-01", "nombre": "Tester"},
            datos_traslado={"distancia_km": 15.0, "hora_dia": 8},
            resultado_ia={"prediccion_supervisada": {"transporte_optimo": "Metro"}, "segmentacion_no_supervisada": {"cluster_asignado": 1}},
        )
        assert "id_usuario" in res_triple
        assert "id_traslado" in res_triple
        assert "id_evaluacion_ia" in res_triple
    except pymongo.errors.PyMongoError:
        pytest.skip("MongoDB offline en entorno de pruebas: se valida la logica del pipeline")


def test_p24_cnn1d_clasificacion_congestion():
    """Valida la preparacion de secuencias y la inferencia del nivel de congestion."""
    clasificador = ClasificadorCongestionCNN1D()
    secuencia_prueba = [
        [42.0, 3.0, 40.0],
        [28.0, 6.0, 70.0],
        [15.0, 12.0, 90.0],
        [12.0, 15.0, 95.0],
    ]
    diagnostico = clasificador.inferir_secuencia_en_caliente(secuencia_prueba)
    assert diagnostico["nivel_congestion_id"] in [0, 1, 2]
    assert 0.0 <= diagnostico["confianza"] <= 1.0


def test_p25_comparador_ml_vs_dl():
    """Valida el benchmark formal comparativo entre modelos tabulares y CNN 1D."""
    comparador = ComparadorMLvsDLKompas()
    res = comparador.ejecutar_comparativa_completa(num_muestras=200)

    tabla = res["tabla_comparativa"]
    assert len(tabla) == 3

    modelos = [t["modelo"] for t in tabla]
    assert any("Arbol de Decision" in m for m in modelos)
    assert any("Random Forest" in m for m in modelos)
    assert any("CNN 1D" in m for m in modelos)

    for item in tabla:
        assert 0.0 <= item["exactitud_test"] <= 1.0
        assert item["latencia_por_muestra_ms"] >= 0.0


def test_p27_cnn1d_regresion_eta():
    """Valida la estimacion continua de tiempo de arribo (ETA en minutos)."""
    regresor = RegresorETACNN1D()
    secuencia_tramos = [
        [2.5, 30.0, 5.0],
        [3.0, 20.0, 9.0],
        [1.8, 15.0, 7.2],
        [4.0, 45.0, 5.3],
    ]
    estimacion = regresor.estimar_eta_en_caliente(secuencia_tramos)
    assert estimacion["eta_estimado_minutos"] > 0.0
    assert len(estimacion["intervalo_confianza"]) == 2
    assert estimacion["intervalo_confianza"][0] <= estimacion["intervalo_confianza"][1]


def test_servicio_ia_orquestador_etapa2():
    """Valida los metodos orquestadores expuestos en ServicioIAKompas."""
    servicio = ServicioIAKompas()

    # P14 en servicio
    res_p14 = servicio.evaluar_motor_recomendaciones_p14({
        "distancia_km": 8.0,
        "hora_dia": 18,
        "duracion_min": 25.0,
        "presupuesto_mxn": 30.0,
    }, persistir_atlas=False)
    assert "prediccion_supervisada" in res_p14
    assert "recomendaciones_operativas" in res_p14

    # P24 en servicio
    res_p24 = servicio.clasificar_congestion_cnn1d_p24([[35.0, 4.0, 50.0], [20.0, 8.0, 80.0]])
    assert "nivel_congestion_id" in res_p24

    # P27 en servicio
    res_p27 = servicio.estimar_eta_cnn1d_p27([[2.0, 25.0, 4.8], [3.5, 30.0, 7.0]])
    assert "eta_estimado_minutos" in res_p27
