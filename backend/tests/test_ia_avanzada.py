"""Pruebas unitarias y de integracion para las Practicas de IA Avanzada (P04 a P09).

Verifica el funcionamiento correcto de:
- p04_ajuste_modelo (Particion 60/20/20 y diagnostico de underfitting/overfitting)
- p05_comparacion_modelos (Decision Tree vs Random Forest vs KNN)
- p06_optimizacion_hiperparametros (GridSearchCV con 5-Fold Stratified CV)
- p07_segmentacion_viajeros (K-Means con Silueta y Metodo del Codo)
- p08_clusters_avanzado (Estabilidad ARI, anomalias y persistencia en MongoDB)
- p09_reduccion_pca (Proyeccion a 2 componentes principales)
"""

import pytest
from app.modulos.ia_kompas.p04_ajuste_modelo import EvaluadorAjusteKompas
from app.modulos.ia_kompas.p05_comparacion_modelos import ComparadorAlgoritmosKompas
from app.modulos.ia_kompas.p06_optimizacion_hiperparametros import OptimizadorHiperparametrosKompas
from app.modulos.ia_kompas.p07_segmentacion_viajeros import SegmentadorViajerosKompas
from app.modulos.ia_kompas.p08_clusters_avanzado import AuditorClustersKompas
from app.modulos.ia_kompas.p09_reduccion_pca import ReductorDimensionalidadPCA
from app.modulos.ia_kompas.servicio import ServicioIAKompas


def test_p04_particion_y_diagnostico_ajuste():
    """Valida la particion 60/20/20 y la identificacion de overfitting y underfitting."""
    evaluador = EvaluadorAjusteKompas()
    res = evaluador.ejecutar_diagnostico_completo()

    dist = res["distribucion_datos"]
    total = dist["total_registros"]
    assert dist["entrenamiento_60"] + dist["validacion_20"] + dist["prueba_20"] == total

    # Validar presencia de los 3 regimenes de ajuste
    comp = res["comparacion_modelos"]
    assert "subajuste_underfitting" in comp
    assert "ajuste_adecuado" in comp
    assert "sobreajuste_overfitting" in comp

    # El arbol libre debe tener 100% de exactitud o cercana en entrenamiento
    assert comp["sobreajuste_overfitting"]["exactitud_entrenamiento"] >= 0.95

    # Debe existir un modelo ganador seleccionado
    assert res["modelo_seleccionado"]["clave"] is not None


def test_p05_comparacion_algoritmos():
    """Valida el benchmark comparativo entre Decision Tree, Random Forest y KNN."""
    comparador = ComparadorAlgoritmosKompas()
    res = comparador.comparar_tres_algoritmos()

    assert res["algoritmos_comparados"] == 3
    tabla = res["tabla_comparativa"]
    assert len(tabla) == 3

    claves = [m["clave"] for m in tabla]
    assert "decision_tree" in claves
    assert "random_forest" in claves
    assert "k_nearest_neighbors" in claves

    for item in tabla:
        assert item["exactitud_prueba"] > 0.60
        assert item["tiempo_inferencia_ms"] >= 0.0


def test_p06_optimizacion_hiperparametros():
    """Valida la busqueda en rejilla con 5 pliegues estratificados."""
    optimizador = OptimizadorHiperparametrosKompas()
    res = optimizador.ejecutar_optimizacion_completa()

    assert "arbol_decision" in res["resultados_por_algoritmo"]
    assert "bosque_aleatorio" in res["resultados_por_algoritmo"]

    arbol_opt = res["resultados_por_algoritmo"]["arbol_decision"]
    assert "max_depth" in arbol_opt["mejores_hiperparametros"]
    assert arbol_opt["exactitud_media_cv"] > 0.70
    assert len(arbol_opt["puntajes_por_pliegue"]) == 5


def test_p07_segmentacion_viajeros():
    """Valida la agrupacion K-Means y el calculo de Silueta e Inercia."""
    segmentador = SegmentadorViajerosKompas()
    res = segmentador.ejecutar_segmentacion_completa(k=3)

    assert res["k_utilizado"] == 3
    assert res["coeficiente_silueta_final"] > 0.20
    assert len(res["perfiles_descubiertos"]) == 3

    for perfil in res["perfiles_descubiertos"]:
        assert "distancia_km_media" in perfil["centroide_promedios"]
        assert perfil["total_viajeros"] > 0


def test_p08_auditoria_clusters_y_anomalias():
    """Valida estabilidad ARI, deteccion de anomalias en percentil 95 y persistencia."""
    auditor = AuditorClustersKompas()
    res = auditor.ejecutar_auditoria_completa()

    # Comparaciones tecnicas
    assert "kmeans_plus_plus" in res["comparacion_inicializaciones"]
    assert "standard_scaler" in res["comparacion_escaladores"]
    assert "promedio_ari" in res["estabilidad_ajuste_ari"]

    # Anomalias
    anomalias = res["auditoria_anomalias"]
    assert anomalias["total_viajes_anomalos_detectados"] > 0
    assert anomalias["umbral_distancia_p95"] > 0.0


def test_p09_reduccion_pca():
    """Valida la proyeccion 2D con PCA y la varianza explicada acumulada."""
    reductor = ReductorDimensionalidadPCA()
    res = reductor.ejecutar_pca_con_clusters(k=3)

    assert res["componentes_principales"] == 2
    assert res["varianza_explicada_acumulada"] > 0.50
    assert len(res["centroides_en_pca"]) == 3
    assert len(res["muestra_puntos_2d"]) > 0


def test_servicio_ia_endpoints_avanzados():
    """Valida la orquestacion central a traves de ServicioIAKompas."""
    servicio = ServicioIAKompas()

    r4 = servicio.diagnostico_ajuste_p04()
    assert "modelo_seleccionado" in r4

    r5 = servicio.comparar_algoritmos_p05()
    assert "algoritmo_ganador" in r5

    r6 = servicio.optimizar_hiperparametros_p06()
    assert "recomendacion_para_produccion" in r6

    r7 = servicio.segmentar_viajeros_p07(k=3)
    assert len(r7["perfiles_descubiertos"]) == 3

    r8 = servicio.auditar_clusters_p08()
    assert "auditoria_anomalias" in r8

    r9 = servicio.proyeccion_pca_p09(k=3)
    assert r9["componentes_principales"] == 2
