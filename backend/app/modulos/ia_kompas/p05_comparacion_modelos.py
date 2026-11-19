"""Modulo de Comparacion de Algoritmos de Machine Learning (Practica 05).

Este modulo implementa el entrenamiento y evaluacion comparativa de tres algoritmos
de clasificacion supervisada para la prediccion del modo de transporte en Kompas:
1. Arbol de Decision (DecisionTreeClassifier)
2. Bosque Aleatorio (RandomForestClassifier)
3. Vecinos mas Cercanos (KNeighborsClassifier)

Compara exactitud, precision, recall, puntuacion F1 y tiempo de inferencia
para fundamentar la seleccion del algoritmo mas idoneo para el backend.
"""

from pathlib import Path
import time
from typing import Any
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier

from app.modulos.ia_kompas.p04_ajuste_modelo import EvaluadorAjusteKompas
from app.modulos.ia_kompas.pipeline_datos import RUTA_LIMPIO_DEFECTO, etapa_e_identificacion_variables


class ComparadorAlgoritmosKompas:
    """Clase para entrenar, contrastar y calificar multiples algoritmos supervisados."""

    def __init__(self, ruta_csv_limpio: Path | str = RUTA_LIMPIO_DEFECTO, semilla: int = 42):
        """Inicializa el comparador con la ruta de datos y semilla.
        
        Que hace:
            Establece la referencia al archivo de datos limpios y la semilla de reproducibilidad.
        Como lo hace:
            Instancia el objeto con las rutas de entrada y crea un evaluador de particion 60/20/20.
        Conexiones:
            Se conecta con EvaluadorAjusteKompas de p04_ajuste_modelo.py para reutilizar la particion.
        """
        self.ruta_csv_limpio = Path(ruta_csv_limpio)
        self.semilla = semilla
        self.evaluador = EvaluadorAjusteKompas(ruta_csv_limpio=self.ruta_csv_limpio, semilla=self.semilla)

    def comparar_tres_algoritmos(self) -> dict[str, Any]:
        """Entrena y compara Arbol de Decision, Bosque Aleatorio y K-Nearest Neighbors.
        
        Que hace:
            Ejecuta un banco de pruebas comparativo entre los 3 clasificadores sobre el mismo
            conjunto de datos de traslados urbanos de Kompas.
        Como lo hace:
            1. Carga los datos limpios y obtiene las particiones 60% entrenamiento, 20% validacion
               y 20% prueba utilizando el metodo particionar_datos_60_20_20.
            2. Configura los tres algoritmos:
               - DecisionTree con max_depth=4.
               - RandomForest con n_estimators=50 y max_depth=5.
               - KNeighborsClassifier con n_neighbors=5 y pesos por distancia.
            3. Para cada algoritmo:
               - Mide el tiempo de entrenamiento en milisegundos con time.perf_counter().
               - Mide el tiempo de prediccion por lote.
               - Calcula la exactitud (accuracy_score), precision ponderada, recall ponderado
                 y puntaje F1 en el conjunto de validacion y prueba.
            4. Ordena los modelos de mayor a menor exactitud en el conjunto de validacion
               y determina el modelo con mejor desempeno global.
        Conexiones:
            Consume los datos procesados de pipeline_datos.py y la particion de p04_ajuste_modelo.py.
            Entrega los resultados a servicio.py y router.py para el endpoint GET /api/ia/comparar-algoritmos.
        """
        df_limpio = pd.read_csv(self.ruta_csv_limpio)
        X, y, _ = etapa_e_identificacion_variables(df_limpio)

        (
            X_entrenamiento,
            X_validacion,
            X_prueba,
            y_entrenamiento,
            y_validacion,
            y_prueba,
        ) = self.evaluador.particionar_datos_60_20_20(X, y)

        modelos = {
            "decision_tree": {
                "nombre": "Arbol de Decision (Decision Tree)",
                "instancia": DecisionTreeClassifier(max_depth=4, random_state=self.semilla),
                "descripcion": "Genera reglas logicas jerarquicas a partir de las caracteristicas de los traslados.",
            },
            "random_forest": {
                "nombre": "Bosque Aleatorio (Random Forest)",
                "instancia": RandomForestClassifier(n_estimators=50, max_depth=5, random_state=self.semilla),
                "descripcion": "Combina multiples arboles de decision aleatorios para mejorar la estabilidad de la prediccion.",
            },
            "k_nearest_neighbors": {
                "nombre": "Vecinos mas Cercanos (K-NN)",
                "instancia": KNeighborsClassifier(n_neighbors=5, weights="distance"),
                "descripcion": "Clasifica segun la distancia euclidiana hacia los traslados historicos mas similares.",
            },
        }

        etiquetas = sorted(pd.Series(y).unique().tolist())
        tabla_comparativa = []
        mejor_clave = None
        mejor_puntaje_val = -1.0

        for clave, meta in modelos.items():
            clf = meta["instancia"]

            # Medir tiempo de entrenamiento
            t0_fit = time.perf_counter()
            clf.fit(X_entrenamiento, y_entrenamiento)
            t_fit_ms = round((time.perf_counter() - t0_fit) * 1000.0, 3)

            # Medir prediccion e inferencia en validacion
            t0_pred = time.perf_counter()
            pred_val = clf.predict(X_validacion)
            t_pred_ms = round((time.perf_counter() - t0_pred) * 1000.0, 3)

            # Prediccion en prueba
            pred_test = clf.predict(X_prueba)

            acc_val = float(accuracy_score(y_validacion, pred_val))
            acc_test = float(accuracy_score(y_prueba, pred_test))
            prec_test = float(precision_score(y_prueba, pred_test, average="weighted", zero_division=0))
            rec_test = float(recall_score(y_prueba, pred_test, average="weighted", zero_division=0))
            f1_test = float(f1_score(y_prueba, pred_test, average="weighted", zero_division=0))

            registro = {
                "clave": clave,
                "nombre": meta["nombre"],
                "descripcion": meta["descripcion"],
                "tiempo_entrenamiento_ms": t_fit_ms,
                "tiempo_inferencia_ms": t_pred_ms,
                "exactitud_validacion": round(acc_val, 4),
                "exactitud_prueba": round(acc_test, 4),
                "precision_prueba": round(prec_test, 4),
                "recall_prueba": round(rec_test, 4),
                "f1_score_prueba": round(f1_test, 4),
                # Matriz de confusion en prueba con un orden de clases comun a los 3 algoritmos
                "matriz_confusion_prueba": confusion_matrix(y_prueba, pred_test, labels=etiquetas).tolist(),
            }

            tabla_comparativa.append(registro)

            if acc_val > mejor_puntaje_val:
                mejor_puntaje_val = acc_val
                mejor_clave = clave

        # Ordenar tabla por exactitud en validacion de forma descendente
        tabla_comparativa.sort(key=lambda item: item["exactitud_validacion"], reverse=True)

        return {
            "total_muestras_evaluadas": len(X),
            "algoritmos_comparados": len(modelos),
            "etiquetas_clases": etiquetas,
            "tabla_comparativa": tabla_comparativa,
            "algoritmo_ganador": {
                "clave": mejor_clave,
                "nombre": modelos[mejor_clave]["nombre"],
                "criterio_seleccion": "Mayor exactitud en el conjunto de validacion y mejor balance de latencia en milisegundos.",
            },
        }

