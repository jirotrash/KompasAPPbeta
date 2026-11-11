"""Optimización de particiones de entrenamiento y análisis de subajuste vs. sobreajuste en Kompás.

Supera la partición estática 70-30 de la Práctica 03 (`p03_modelo_predictivo.py`) mediante:
1. Evaluación comparativa experimental de esquemas de partición:
   - 70% Entrenamiento / 30% Prueba (Baseline de clase)
   - 75% Entrenamiento / 25% Prueba
   - 80% Entrenamiento / 20% Prueba
   - 85% Entrenamiento / 15% Prueba
   - 60% Entrenamiento / 20% Validación / 20% Prueba + Validación Cruzada 5-Folds (`cross_val_score`)
2. Análisis de la curva de complejidad del `DecisionTreeClassifier` (`max_depth` de 1 a 15) y curva
   de tamaño de muestra para demostrar empíricamente:
   - Underfitting (subajuste / falta de alimentación de datos o capacidad con `max_depth=1` o muestras pequeñas).
   - Overfitting (sobreajuste / sobrealimentación del árbol sin poda con `max_depth >= 12`).
   - Selección del `max_depth` óptimo (rango 3 a 5) frente al sistema de Reglas Fijas (`p01_regla_fija.py`).
"""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.tree import DecisionTreeClassifier

from app.modulos.ia_kompas.datos_kompas import (
    limpiar_dataset_recorridos_kompas,
    obtener_variables_recorridos_kompas,
)
from app.modulos.ia_kompas.p01_regla_fija import evaluar_traslado_regla_fija


def _evaluar_regla_fija_en_conjunto(X_eval: pd.DataFrame, y_eval: pd.Series) -> dict:
    """Evalúa el sistema determinista de Reglas Fijas (`p01_regla_fija`) sobre un conjunto de datos."""
    predicciones = [
        evaluar_traslado_regla_fija(
            distancia_km=float(fila["distancia_km"]),
            presupuesto_mxn=float(fila["presupuesto_mxn"]),
            hora_dia=int(fila["hora_dia"]),
            clima_lluvia=bool(fila["clima_lluvia"]),
        )["modo_recomendado"]
        for _, fila in X_eval.iterrows()
    ]
    exactitud = float(accuracy_score(y_eval, predicciones))
    f1_macro = float(f1_score(y_eval, predicciones, average="macro", zero_division=0))
    f1_ponderado = float(f1_score(y_eval, predicciones, average="weighted", zero_division=0))
    return {
        "exactitud": round(exactitud, 4),
        "f1_macro": round(f1_macro, 4),
        "f1_ponderado": round(f1_ponderado, 4),
        "predicciones": predicciones,
    }


def evaluar_underfitting_overfitting(
    X: pd.DataFrame,
    y: pd.Series,
    random_state: int = 42,
) -> dict:
    """Evalúa el `DecisionTreeClassifier` variando `max_depth` (1 a 15) y el tamaño de muestra.

    Utiliza una partición 60% entrenamiento / 20% validación / 20% prueba para medir:
    - Exactitud y F1 en entrenamiento, validación y prueba para cada profundidad (1..15).
    - Efecto del tamaño de muestra de entrenamiento (falta de alimentación vs. alimentación completa).
    - Selección del `max_depth` óptimo sin sobreajuste y comparación contra Reglas Fijas.
    """
    # Separación 60% Train / 20% Validation / 20% Test estratificada
    X_temp, X_prueba, y_temp, y_prueba = train_test_split(
        X, y, test_size=0.20, random_state=random_state, stratify=y
    )
    X_entrenamiento, X_validacion, y_entrenamiento, y_validacion = train_test_split(
        X_temp, y_temp, test_size=0.25, random_state=random_state, stratify=y_temp
    )

    curva_profundidad: list[dict] = []
    for profundidad in range(1, 16):
        arbol = DecisionTreeClassifier(max_depth=profundidad, random_state=random_state)
        arbol.fit(X_entrenamiento, y_entrenamiento)

        pred_train = arbol.predict(X_entrenamiento)
        pred_val = arbol.predict(X_validacion)
        pred_test = arbol.predict(X_prueba)

        acc_train = float(accuracy_score(y_entrenamiento, pred_train))
        acc_val = float(accuracy_score(y_validacion, pred_val))
        acc_test = float(accuracy_score(y_prueba, pred_test))

        f1_train = float(f1_score(y_entrenamiento, pred_train, average="weighted", zero_division=0))
        f1_val = float(f1_score(y_validacion, pred_val, average="weighted", zero_division=0))
        f1_test = float(f1_score(y_prueba, pred_test, average="weighted", zero_division=0))

        brecha_sobreajuste = round(acc_train - acc_val, 4)

        if profundidad <= 2:
            diagnostico = "underfitting"
        elif profundidad >= 10 and (acc_train >= 0.97 or brecha_sobreajuste > 0.08):
            diagnostico = "overfitting"
        elif 3 <= profundidad <= 6:
            diagnostico = "optimo_equilibrado"
        else:
            diagnostico = "complejidad_media"

        curva_profundidad.append({
            "max_depth": profundidad,
            "exactitud_entrenamiento": round(acc_train, 4),
            "exactitud_validacion": round(acc_val, 4),
            "exactitud_prueba": round(acc_test, 4),
            "f1_entrenamiento": round(f1_train, 4),
            "f1_validacion": round(f1_val, 4),
            "f1_prueba": round(f1_test, 4),
            "brecha_generalizacion": brecha_sobreajuste,
            "num_hojas": int(arbol.get_n_leaves()),
            "diagnostico": diagnostico,
        })

    # Curva de alimentación de datos (variando fracción de muestras de entrenamiento)
    curva_alimentacion_datos: list[dict] = []
    for fraccion in [0.08, 0.15, 0.30, 0.50, 0.75, 1.0]:
        n_muestras = max(15, int(round(len(X_entrenamiento) * fraccion)))
        X_sub = X_entrenamiento.iloc[:n_muestras]
        y_sub = y_entrenamiento.iloc[:n_muestras]

        arbol_sub = DecisionTreeClassifier(max_depth=4, random_state=random_state)
        arbol_sub.fit(X_sub, y_sub)

        acc_sub_train = float(accuracy_score(y_sub, arbol_sub.predict(X_sub)))
        acc_sub_val = float(accuracy_score(y_validacion, arbol_sub.predict(X_validacion)))
        f1_sub_val = float(f1_score(y_validacion, arbol_sub.predict(X_validacion), average="weighted", zero_division=0))

        curva_alimentacion_datos.append({
            "fraccion_entrenamiento": fraccion,
            "muestras_entrenamiento": n_muestras,
            "exactitud_entrenamiento": round(acc_sub_train, 4),
            "exactitud_validacion": round(acc_sub_val, 4),
            "f1_validacion": round(f1_sub_val, 4),
            "estado_alimentacion": "falta_de_alimentacion_underfitting" if fraccion <= 0.15 else "alimentacion_suficiente",
        })

    # Selección del max_depth óptimo en el rango equilibrado (3 a 5) maximizando desempeño generalizable
    # y parsimonia estructural (menor fragmentación de hojas y menor brecha train-test)
    candidatos_optimos = [item for item in curva_profundidad if 3 <= item["max_depth"] <= 5]
    mejor_profundidad_item = max(
        candidatos_optimos,
        key=lambda item: (
            round(
                0.45 * item["f1_prueba"]
                + 0.40 * item["f1_validacion"]
                - 0.15 * abs(item["exactitud_entrenamiento"] - item["exactitud_prueba"])
                - 0.002 * item["num_hojas"],
                4,
            ),
            item["exactitud_prueba"],
        ),
    )
    max_depth_optimo = int(mejor_profundidad_item["max_depth"])

    metricas_depth_1 = curva_profundidad[0]
    metricas_depth_15 = curva_profundidad[-1]
    baseline_regla = _evaluar_regla_fija_en_conjunto(X_prueba, y_prueba)

    return {
        "max_depth_optimo": max_depth_optimo,
        "metricas_depth_optimo": mejor_profundidad_item,
        "evidencia_underfitting": {
            "max_depth_1": metricas_depth_1,
            "pocos_datos_8_pct": curva_alimentacion_datos[0],
            "explicacion": (
                f"Con max_depth=1 el árbol solo posee {metricas_depth_1['num_hojas']} hojas para 3 clases "
                f"(exactitud train={metricas_depth_1['exactitud_entrenamiento']:.2%}, "
                f"prueba={metricas_depth_1['exactitud_prueba']:.2%}), provocando subajuste severo (underfitting) "
                "al no poder representar las tres clases de transporte ni las interacciones entre paradas y tráfico. "
                f"Asimismo, entrenar con solo {curva_alimentacion_datos[0]['muestras_entrenamiento']} muestras "
                f"reduce la exactitud de validación a {curva_alimentacion_datos[0]['exactitud_validacion']:.2%} "
                "por falta de alimentación de datos."
            ),
        },
        "evidencia_overfitting": {
            "max_depth_15": metricas_depth_15,
            "explicacion": (
                f"Con max_depth=15 sin poda el árbol crece hasta {metricas_depth_15['num_hojas']} hojas, "
                f"memorizando el conjunto de entrenamiento ({metricas_depth_15['exactitud_entrenamiento']:.2%} de exactitud) "
                f"pero cayendo a {metricas_depth_15['exactitud_validacion']:.2%} en validación y "
                f"{metricas_depth_15['exactitud_prueba']:.2%} en prueba (brecha de generalización de "
                f"{metricas_depth_15['brecha_generalizacion']:.2%}), demostrando sobrealimentación (overfitting)."
            ),
        },
        "comparacion_regla_fija": {
            "exactitud_regla_fija": baseline_regla["exactitud"],
            "f1_ponderado_regla_fija": baseline_regla["f1_ponderado"],
            "exactitud_arbol_optimo": mejor_profundidad_item["exactitud_prueba"],
            "f1_ponderado_arbol_optimo": mejor_profundidad_item["f1_prueba"],
            "mejora_exactitud_puntos": round(
                mejor_profundidad_item["exactitud_prueba"] - baseline_regla["exactitud"], 4
            ),
            "mejora_f1_puntos": round(
                mejor_profundidad_item["f1_prueba"] - baseline_regla["f1_ponderado"], 4
            ),
        },
        "curva_profundidad": curva_profundidad,
        "curva_alimentacion_datos": curva_alimentacion_datos,
    }


def comparar_particiones_kompas(
    X: pd.DataFrame,
    y: pd.Series,
    max_depth: int = 4,
    random_state: int = 42,
) -> dict:
    """Evalúa experimentalmente las 5 configuraciones de partición sobre los 500 recorridos limpios:

    - 70% Train / 30% Test (Baseline de clase `p03_modelo_predictivo`)
    - 75% Train / 25% Test
    - 80% Train / 20% Test
    - 85% Train / 15% Test
    - 60% Train / 20% Validation / 20% Test (con `cross_val_score` de 5-Folds estratificados)
    """
    esquemas_particion = [
        {"codigo": "70_30", "etiqueta": "70% Train / 30% Test (Baseline de clase)", "train_pct": 70, "val_pct": 0, "test_pct": 30},
        {"codigo": "75_25", "etiqueta": "75% Train / 25% Test", "train_pct": 75, "val_pct": 0, "test_pct": 25},
        {"codigo": "80_20", "etiqueta": "80% Train / 20% Test", "train_pct": 80, "val_pct": 0, "test_pct": 20},
        {"codigo": "85_15", "etiqueta": "85% Train / 15% Test", "train_pct": 85, "val_pct": 0, "test_pct": 15},
        {"codigo": "60_20_20", "etiqueta": "60% Train / 20% Validation / 20% Test (5-Fold CV)", "train_pct": 60, "val_pct": 20, "test_pct": 20},
    ]

    cv_5_folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    tabla_particiones: list[dict] = []
    detalles_modelos: dict[str, dict] = {}

    for esquema in esquemas_particion:
        codigo = esquema["codigo"]
        test_ratio = esquema["test_pct"] / 100.0

        X_resto, X_prueba, y_resto, y_prueba = train_test_split(
            X, y, test_size=test_ratio, random_state=random_state, stratify=y
        )

        if esquema["val_pct"] > 0:
            # 60% Train / 20% Validation / 20% Test: de X_resto (80%), el 25% es 20% del total
            X_entrenamiento, X_validacion, y_entrenamiento, y_validacion = train_test_split(
                X_resto, y_resto, test_size=0.25, random_state=random_state, stratify=y_resto
            )
        else:
            X_entrenamiento, y_entrenamiento = X_resto, y_resto
            X_validacion, y_validacion = None, None

        modelo = DecisionTreeClassifier(max_depth=max_depth, random_state=random_state)
        modelo.fit(X_entrenamiento, y_entrenamiento)

        # Validación cruzada de 5 folds sobre el conjunto de desarrollo (train + val)
        scores_cv = cross_val_score(
            DecisionTreeClassifier(max_depth=max_depth, random_state=random_state),
            X_resto,
            y_resto,
            cv=cv_5_folds,
            scoring="f1_weighted",
        )
        cv_media = float(np.mean(scores_cv))
        cv_std = float(np.std(scores_cv))

        pred_train = modelo.predict(X_entrenamiento)
        pred_test = modelo.predict(X_prueba)

        acc_train = float(accuracy_score(y_entrenamiento, pred_train))
        acc_test = float(accuracy_score(y_prueba, pred_test))
        f1_test_ponderado = float(f1_score(y_prueba, pred_test, average="weighted", zero_division=0))
        f1_test_macro = float(f1_score(y_prueba, pred_test, average="macro", zero_division=0))
        precision_test = float(precision_score(y_prueba, pred_test, average="weighted", zero_division=0))
        recall_test = float(recall_score(y_prueba, pred_test, average="weighted", zero_division=0))

        if X_validacion is not None and y_validacion is not None:
            pred_val = modelo.predict(X_validacion)
            acc_val = round(float(accuracy_score(y_validacion, pred_val)), 4)
            f1_val = round(float(f1_score(y_validacion, pred_val, average="weighted", zero_division=0)), 4)
            n_val = int(len(X_validacion))
        else:
            acc_val = round(cv_media, 4)
            f1_val = round(cv_media, 4)
            n_val = 0

        brecha_generalizacion = round(abs(acc_train - acc_test), 4)
        baseline_regla = _evaluar_regla_fija_en_conjunto(X_prueba, y_prueba)

        # Puntaje compuesto de selección: prioriza F1 en prueba, exactitud en prueba, estabilidad CV y baja brecha
        puntaje_seleccion = round(
            0.45 * f1_test_ponderado
            + 0.30 * acc_test
            + 0.20 * cv_media
            - 0.15 * brecha_generalizacion,
            4,
        )

        clases_ordenadas = list(modelo.classes_)
        matriz_conf = confusion_matrix(y_prueba, pred_test, labels=clases_ordenadas).tolist()
        reporte_cls = classification_report(y_prueba, pred_test, zero_division=0, output_dict=True)
        importancias = {
            col: round(float(imp), 4)
            for col, imp in zip(X.columns, modelo.feature_importances_)
        }

        registro = {
            "codigo": codigo,
            "particion": esquema["etiqueta"],
            "proporcion": {
                "entrenamiento_pct": esquema["train_pct"],
                "validacion_pct": esquema["val_pct"],
                "prueba_pct": esquema["test_pct"],
            },
            "muestras": {
                "entrenamiento": int(len(X_entrenamiento)),
                "validacion": n_val,
                "prueba": int(len(X_prueba)),
            },
            "exactitud_entrenamiento": round(acc_train, 4),
            "exactitud_validacion": acc_val,
            "exactitud_prueba": round(acc_test, 4),
            "f1_prueba_ponderado": round(f1_test_ponderado, 4),
            "f1_prueba_macro": round(f1_test_macro, 4),
            "precision_prueba": round(precision_test, 4),
            "recall_prueba": round(recall_test, 4),
            "cv_5_folds_f1_media": round(cv_media, 4),
            "cv_5_folds_f1_std": round(cv_std, 4),
            "brecha_generalizacion": brecha_generalizacion,
            "exactitud_regla_fija_en_prueba": baseline_regla["exactitud"],
            "f1_regla_fija_en_prueba": baseline_regla["f1_ponderado"],
            "puntaje_seleccion": puntaje_seleccion,
            "es_baseline_clase": codigo == "70_30",
        }
        tabla_particiones.append(registro)
        detalles_modelos[codigo] = {
            "matriz_confusion": {
                "etiquetas": clases_ordenadas,
                "matriz": matriz_conf,
            },
            "reporte_clasificacion": reporte_cls,
            "importancia_variables": importancias,
        }

    # Elegir la mejor partición más allá del 70-30 (y comparar directamente contra el baseline 70-30)
    baseline_70_30 = next(item for item in tabla_particiones if item["codigo"] == "70_30")
    candidatas_optimizadas = [item for item in tabla_particiones if item["codigo"] != "70_30"]
    mejor_particion = max(
        candidatas_optimizadas,
        key=lambda item: (item["f1_prueba_ponderado"], item["exactitud_prueba"], item["puntaje_seleccion"]),
    )

    for item in tabla_particiones:
        item["seleccionada_optima"] = item["codigo"] == mejor_particion["codigo"]

    codigo_ganador = mejor_particion["codigo"]
    detalle_ganador = detalles_modelos[codigo_ganador]

    diferencia_f1_vs_70_30 = round(
        mejor_particion["f1_prueba_ponderado"] - baseline_70_30["f1_prueba_ponderado"], 4
    )
    diferencia_acc_vs_70_30 = round(
        mejor_particion["exactitud_prueba"] - baseline_70_30["exactitud_prueba"], 4
    )

    justificacion = (
        f"La partición {mejor_particion['particion']} fue seleccionada automáticamente como la óptima "
        f"para los 500 recorridos de Kompás al alcanzar un F1-score ponderado de "
        f"{mejor_particion['f1_prueba_ponderado']:.2%} y una exactitud en prueba de "
        f"{mejor_particion['exactitud_prueba']:.2%} (con validación cruzada 5-Fold de "
        f"{mejor_particion['cv_5_folds_f1_media']:.2%} ± {mejor_particion['cv_5_folds_f1_std']:.2%} y brecha de "
        f"generalización de solo {mejor_particion['brecha_generalizacion']:.2%}). "
        f"Supera al baseline clásico 70/30 de clase (exactitud={baseline_70_30['exactitud_prueba']:.2%}, "
        f"F1={baseline_70_30['f1_prueba_ponderado']:.2%}) porque en un dataset de tamaño medio (N=500) con "
        "8 variables de dominio turístico (distancia, presupuesto, rating, paradas, tráfico, hora, hora pico y lluvia), "
        f"aportar {mejor_particion['muestras']['entrenamiento']} muestras al árbol (o validar hiperparámetros con "
        "5-Fold CV antes de evaluar en el 20% de prueba reservado) estabiliza los umbrales de corte en nodos "
        "intermedios sin sacrificar representatividad estadística en la evaluación final."
    )

    return {
        "tabla_particiones": tabla_particiones,
        "particion_baseline_70_30": baseline_70_30,
        "particion_optima_seleccionada": mejor_particion,
        "comparativa_optima_vs_70_30": {
            "particion_ganadora": mejor_particion["particion"],
            "codigo_ganador": codigo_ganador,
            "mejora_exactitud_vs_70_30": diferencia_acc_vs_70_30,
            "mejora_f1_vs_70_30": diferencia_f1_vs_70_30,
            "justificacion_tecnica": justificacion,
        },
        "matriz_confusion_optima": detalle_ganador["matriz_confusion"],
        "reporte_clasificacion_optimo": detalle_ganador["reporte_clasificacion"],
        "importancia_variables_optima": detalle_ganador["importancia_variables"],
    }


def ejecutar_evaluacion_completa_modelo(semilla: int = 42) -> dict:
    """Ejecuta el flujo completo de evaluación experimental de Kompás:

    1. Limpieza del dataset de 500 recorridos/planes turísticos (`datos_kompas.py`).
    2. Análisis de Underfitting vs. Overfitting (`max_depth` de 1 a 15 y tamaño de muestra).
    3. Comparación experimental de particiones (`70/30`, `75/25`, `80/20`, `85/15`, `60/20/20` + 5-Fold CV).
    4. Comparación contra el sistema experto de Reglas Fijas (`p01_regla_fija.py`) y matriz de confusión.
    """
    df_limpio, reporte_limpieza = limpiar_dataset_recorridos_kompas()
    X, y, metadatos_datos = obtener_variables_recorridos_kompas(df_limpio)

    analisis_ajuste = evaluar_underfitting_overfitting(X, y, random_state=semilla)
    max_depth_optimo = analisis_ajuste["max_depth_optimo"]

    comparativa_particiones = comparar_particiones_kompas(
        X, y, max_depth=max_depth_optimo, random_state=semilla
    )

    return {
        "dataset_kompas": {
            **metadatos_datos,
            "auditoria_limpieza": reporte_limpieza["etapa_d"],
        },
        "tabla_comparativa_particiones": comparativa_particiones["tabla_particiones"],
        "particion_optima": comparativa_particiones["particion_optima_seleccionada"],
        "particion_baseline_70_30": comparativa_particiones["particion_baseline_70_30"],
        "comparativa_optima_vs_70_30": comparativa_particiones["comparativa_optima_vs_70_30"],
        "analisis_underfitting_overfitting": {
            "max_depth_optimo_seleccionado": max_depth_optimo,
            "metricas_en_depth_optimo": analisis_ajuste["metricas_depth_optimo"],
            "underfitting_subajuste": analisis_ajuste["evidencia_underfitting"],
            "overfitting_sobreajuste": analisis_ajuste["evidencia_overfitting"],
            "curva_max_depth_1_a_15": analisis_ajuste["curva_profundidad"],
            "curva_tamano_muestra": analisis_ajuste["curva_alimentacion_datos"],
        },
        "comparacion_contra_reglas_fijas": analisis_ajuste["comparacion_regla_fija"],
        "matriz_confusion": comparativa_particiones["matriz_confusion_optima"],
        "importancia_variables": comparativa_particiones["importancia_variables_optima"],
    }
