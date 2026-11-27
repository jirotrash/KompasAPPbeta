"""Modulo de Optimizacion de Hiperparametros y Validacion Cruzada (Practica 06).

Este modulo implementa la busqueda automatizada de hiperparametros mediante
GridSearchCV y validacion cruzada estratificada (StratifiedKFold con 5 pliegues).
Permite sustituir los valores configurados manualmente por aquellos que maximizan
estadisticamente el rendimiento y la estabilidad del clasificador de transporte de Kompas.
"""

from pathlib import Path
from typing import Any
import pandas as pd
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

from app.modulos.ia_kompas.pipeline_datos import RUTA_LIMPIO_DEFECTO, etapa_e_identificacion_variables


class OptimizadorHiperparametrosKompas:
    """Clase para la optimizacion sistematica de hiperparametros de modelos predictivos."""

    def __init__(self, ruta_csv_limpio: Path | str = RUTA_LIMPIO_DEFECTO, semilla: int = 42):
        """Inicializa el optimizador con la ruta de datos limpios y la semilla.
        
        Que hace:
            Configura el origen de datos y fija la semilla para la reproducibilidad de los pliegues.
        Como lo hace:
            Guarda la ruta al archivo CSV procesado y define el generador de particiones StratifiedKFold.
        Conexiones:
            Se conecta con pipeline_datos.RUTA_LIMPIO_DEFECTO.
        """
        self.ruta_csv_limpio = Path(ruta_csv_limpio)
        self.semilla = semilla
        self.cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=self.semilla)

    # ALGORITMO: GridSearchCV con 5 pliegues estratificados para elegir los hiperparámetros del árbol.
    #   Se ve en: Dashboard > Machine Learning > 'Optimización con validación cruzada'.
    def optimizar_arbol_decision(self, X: pd.DataFrame, y: pd.Series) -> dict[str, Any]:
        """Ejecuta una busqueda en rejilla (GridSearchCV) para afinar el DecisionTreeClassifier.
        
        Que hace:
            Encuentra la mejor combinacion de profundidad maxima (max_depth), criterio de division
            (criterion) y cantidad minima de muestras para dividir un nodo (min_samples_split).
        Como lo hace:
            1. Define el espacio de hiperparametros:
               - max_depth: [2, 3, 4, 5, 6, 8, None]
               - min_samples_split: [2, 5, 10, 20]
               - criterion: ['gini', 'entropy', 'log_loss']
            2. Configura GridSearchCV evaluando cada combinacion a traves de los 5 pliegues de validacion cruzada.
            3. Ajusta la rejilla sobre los datos y extrae los mejores hiperparametros (best_params_)
               y la mejor puntuacion promedio (best_score_).
            4. Realiza una validacion cruzada adicional para reportar los puntajes individuales de cada pliegue.
        Conexiones:
            Recibe X e y de etapa_e_identificacion_variables.
            Devuelve un reporte detallado para servicio.py y router.py.
        """
        param_grid = {
            "max_depth": [2, 3, 4, 5, 6, 8, None],
            "min_samples_split": [2, 5, 10, 20],
            "criterion": ["gini", "entropy"],
        }

        grid_search = GridSearchCV(
            estimator=DecisionTreeClassifier(random_state=self.semilla),
            param_grid=param_grid,
            cv=self.cv,
            scoring="accuracy",
            n_jobs=-1,
        )

        grid_search.fit(X, y)
        mejor_modelo = grid_search.best_estimator_

        # Puntajes individuales en cada uno de los 5 pliegues
        scores_pliegues = cross_val_score(mejor_modelo, X, y, cv=self.cv, scoring="accuracy")

        return {
            "algoritmo": "DecisionTreeClassifier",
            "mejores_hiperparametros": grid_search.best_params_,
            "exactitud_media_cv": round(float(grid_search.best_score_), 4),
            "desviacion_estandar_cv": round(float(scores_pliegues.std()), 4),
            "puntajes_por_pliegue": [round(float(s), 4) for s in scores_pliegues],
            "total_combinaciones_probadas": len(grid_search.cv_results_["params"]),
        }

    def optimizar_bosque_aleatorio(self, X: pd.DataFrame, y: pd.Series) -> dict[str, Any]:
        """Ajusta los hiperparametros clave del clasificador RandomForestClassifier.
        
        Que hace:
            Explora combinaciones optimas entre el numero de arboles (n_estimators) y su profundidad maxima.
        Como lo hace:
            Aplica GridSearchCV sobre n_estimators [25, 50, 100] y max_depth [3, 4, 5, 7]
            con evaluacion mediante 5 pliegues cruzados estratificados.
        Conexiones:
            Utiliza la misma particion de pliegues estratificada que el arbol de decision.
        """
        param_grid = {
            "n_estimators": [25, 50, 100],
            "max_depth": [3, 4, 5, 7],
            "min_samples_split": [2, 5, 10],
        }

        grid_search = GridSearchCV(
            estimator=RandomForestClassifier(random_state=self.semilla),
            param_grid=param_grid,
            cv=self.cv,
            scoring="accuracy",
            n_jobs=-1,
        )

        grid_search.fit(X, y)
        mejor_modelo = grid_search.best_estimator_

        scores_pliegues = cross_val_score(mejor_modelo, X, y, cv=self.cv, scoring="accuracy")

        return {
            "algoritmo": "RandomForestClassifier",
            "mejores_hiperparametros": grid_search.best_params_,
            "exactitud_media_cv": round(float(grid_search.best_score_), 4),
            "desviacion_estandar_cv": round(float(scores_pliegues.std()), 4),
            "puntajes_por_pliegue": [round(float(s), 4) for s in scores_pliegues],
            "total_combinaciones_probadas": len(grid_search.cv_results_["params"]),
        }

    def ejecutar_optimizacion_completa(self) -> dict[str, Any]:
        """Ejecuta el pipeline completo de optimizacion para los modelos principales de transporte.
        
        Que hace:
            Orquesta la busqueda de hiperparametros para arboles individuales y ensambles de bosques,
            comparando las ganancias de rendimiento frente a configuraciones por defecto.
        Como lo hace:
            Carga los datos limpios, separa variables predictoras y objetivo, y ejecuta
            consecutivamente las optimizaciones de arbol de decision y bosque aleatorio.
        Conexiones:
            Consume RUTA_LIMPIO_DEFECTO de pipeline_datos.py y provee la salida a router.py
            bajo el endpoint GET /api/ia/optimizar-hiperparametros.
        """
        df_limpio = pd.read_csv(self.ruta_csv_limpio)
        X, y, _ = etapa_e_identificacion_variables(df_limpio)

        res_arbol = self.optimizar_arbol_decision(X, y)
        res_bosque = self.optimizar_bosque_aleatorio(X, y)

        mejor_global = (
            res_bosque if res_bosque["exactitud_media_cv"] >= res_arbol["exactitud_media_cv"] else res_arbol
        )

        return {
            "total_registros_utilizados": len(X),
            "esquema_validacion": "Validacion cruzada estratificada (StratifiedKFold con 5 pliegues)",
            "resultados_por_algoritmo": {
                "arbol_decision": res_arbol,
                "bosque_aleatorio": res_bosque,
            },
            "recomendacion_para_produccion": {
                "algoritmo": mejor_global["algoritmo"],
                "hiperparametros_optimos": mejor_global["mejores_hiperparametros"],
                "exactitud_esperada": mejor_global["exactitud_media_cv"],
                "estabilidad_desviacion": mejor_global["desviacion_estandar_cv"],
            },
        }

