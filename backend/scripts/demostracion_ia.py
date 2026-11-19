"""Script interactivo de consola para demostrar en vivo las Practicas de IA (P04 a P09).

Muestra en pantalla el resumen ejecutivo de cada tecnica de Machine Learning
adaptada al dominio de transporte y turismo de KompasAPPbeta en el Valle de Toluca.
"""

import sys
from pathlib import Path

# Asegurar que el modulo app este en el PYTHONPATH
raiz_backend = Path(__file__).resolve().parent.parent
if str(raiz_backend) not in sys.path:
    sys.path.insert(0, str(raiz_backend))

from app.modulos.ia_kompas.servicio import ServicioIAKompas


def imprimir_encabezado(titulo: str):
    print("\n" + "=" * 70)
    print(f" {titulo}")
    print("=" * 70)


def main():
    print("======================================================================")
    print("   DEMOSTRACION EN VIVO DE MACHINE LEARNING E IA - KOMPAS APP BETA")
    print("======================================================================")

    servicio = ServicioIAKompas()

    # 1. Practica 04: Particion 60/20/20 y Diagnostico de Ajuste
    imprimir_encabezado("PRACTICA 04: PARTICION 60/20/20 Y DIAGNOSTICO DE AJUSTE")
    p4 = servicio.diagnostico_ajuste_p04()
    dist = p4["distribucion_datos"]
    print(f"Total de registros: {dist['total_registros']}")
    print(f"  - Entrenamiento (60%): {dist['entrenamiento_60']}")
    print(f"  - Validacion (20%):    {dist['validacion_20']}")
    print(f"  - Prueba ciega (20%):  {dist['prueba_20']}\n")

    print(f"{'Regimen':<26} | {'Max Depth':<10} | {'Train Acc':<10} | {'Val Acc':<10} | {'Diagnostico'}")
    print("-" * 80)
    for clave, item in p4["comparacion_modelos"].items():
        print(f"{item['nombre_legible']:<26} | {str(item['max_depth']):<10} | {item['exactitud_entrenamiento']:<10.2%} | {item['exactitud_validacion']:<10.2%} | {item['diagnostico'][:30]}...")

    print(f"\nModelo Ganador Seleccionado: {p4['modelo_seleccionado']['nombre']}")
    print(f"Exactitud Final en Prueba Ciega: {p4['modelo_seleccionado']['exactitud_prueba_final']:.2%}")

    # 2. Practica 05: Comparacion de Algoritmos
    imprimir_encabezado("PRACTICA 05: COMPARACION DE ALGORITMOS DE MACHINE LEARNING")
    p5 = servicio.comparar_algoritmos_p05()
    print(f"{'Algoritmo':<30} | {'Exactitud Val':<14} | {'Exactitud Test':<14} | {'Latencia Inferencia'}")
    print("-" * 75)
    for item in p5["tabla_comparativa"]:
        print(f"{item['nombre']:<30} | {item['exactitud_validacion']:<14.2%} | {item['exactitud_prueba']:<14.2%} | {item['tiempo_inferencia_ms']} ms")
    print(f"\nAlgoritmo Ganador: {p5['algoritmo_ganador']['nombre']}")

    # 3. Practica 06: Optimizacion de Hiperparametros
    imprimir_encabezado("PRACTICA 06: OPTIMIZACION CON GRIDSEARCHCV Y 5 PLIEGUES")
    p6 = servicio.optimizar_hiperparametros_p06()
    rec = p6["recomendacion_para_produccion"]
    print(f"Algoritmo Recomendado: {rec['algoritmo']}")
    print(f"Exactitud Promedio (5-Fold CV): {rec['exactitud_esperada']:.2%}")
    print(f"Estabilidad (Desviacion Estandar): +/- {rec['estabilidad_desviacion']:.2%}")
    print(f"Mejores Hiperparametros Encontrados: {rec['hiperparametros_optimos']}")

    # 4. Practica 07: Segmentacion K-Means
    imprimir_encabezado("PRACTICA 07: SEGMENTACION DE VIAJEROS MEDIANTE K-MEANS")
    p7 = servicio.segmentar_viajeros_p07(k=3)
    print(f"Numero de Clusters Evaluado: K = {p7['k_utilizado']}")
    print(f"Coeficiente de Silueta: {p7['coeficiente_silueta_final']} (Inercia: {p7['inercia_final']})\n")
    print("Perfiles de Movilidad Descubiertos:")
    for perf in p7["perfiles_descubiertos"]:
        c = perf["centroide_promedios"]
        print(f"  [Cluster {perf['cluster_id']}] {perf['nombre_perfil']} ({perf['total_viajeros']} viajes, {perf['porcentaje_total']}%)")
        print(f"    - Distancia Media: {c['distancia_km_media']} km | Hora Media: {c['hora_dia_media']} hrs | Presupuesto: ${c['presupuesto_mxn_medio']} MXN | Modo: {c['modo_predilecto']}")

    # 5. Practica 08: Auditoria Avanzada y Anomalias
    imprimir_encabezado("PRACTICA 08: AUDITORIA DE CLUSTERS, ESTABILIDAD Y ANOMALIAS")
    p8 = servicio.auditar_clusters_p08()
    ari = p8["estabilidad_ajuste_ari"]
    anom = p8["auditoria_anomalias"]
    print(f"Estabilidad con Adjusted Rand Index (ARI): {ari['promedio_ari']} ({ari['diagnostico_estabilidad']})")
    print(f"Deteccion de Anomalias (Percentil 95):")
    print(f"  - Umbral de distancia euclidiana: {anom['umbral_distancia_p95']}")
    print(f"  - Viajes anomalos detectados: {anom['total_viajes_anomalos_detectados']}")
    print(f"Persistencia en MongoDB: {p8['persistencia_mongodb']['mensaje']}")

    # 6. Practica 09: Reduccion PCA
    imprimir_encabezado("PRACTICA 09: REDUCCION DE DIMENSIONALIDAD CON PCA (2D)")
    p9 = servicio.proyeccion_pca_p09(k=3)
    print(f"Componentes Principales: 2 (PC1 y PC2)")
    print(f"Varianza Explicada por PC1: {p9['varianza_explicada_pc1']:.2%}")
    print(f"Varianza Explicada por PC2: {p9['varianza_explicada_pc2']:.2%}")
    print(f"Varianza Explicada Acumulada: {p9['varianza_explicada_acumulada']:.2%}")

    print("\n======================================================================")
    print("   TODAS LAS PRACTICAS DE IA SE EJECUTARON CORRECTAMENTE")
    print("======================================================================\n")


if __name__ == "__main__":
    main()

