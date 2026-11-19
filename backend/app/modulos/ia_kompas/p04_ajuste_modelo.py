"""Modulo de Evaluacion de Ajuste de Modelos (Practica 04).

Este modulo implementa la particion metodologica en tres subconjuntos disjuntos:
60% para entrenamiento, 20% para validacion y 20% para prueba final ciega.
Evalua comparativamente tres niveles de complejidad en arboles de decision
para diagnosticar fenomenos de subajuste (underfitting), buen ajuste y sobreajuste (overfitting).
"""

from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

from app.modulos.ia_kompas.pipeline_datos import (
    COLUMNAS_CARACTERISTICAS,
    COLUMNA_OBJETIVO,
    RUTA_LIMPIO_DEFECTO,
    ejecutar_pipeline_completo,
    etapa_e_identificacion_variables,
)


class EvaluadorAjusteKompas:
    """Clase encargada de ejecutar la particion triple y diagnosticar sobreajuste o subajuste."""

    def __init__(self, ruta_csv_limpio: Path | str = RUTA_LIMPIO_DEFECTO, semilla: int = 42):
        """Inicializa el evaluador con la ruta del dataset y la semilla de reproducibilidad.
        
        Que hace:
            Configura los atributos base del evaluador y asegura la semilla para reproducibilidad.
        Como lo hace:
            Guarda la ruta al archivo CSV limpio y fija un entero para reproducir las particiones aleatorias.
        Conexiones:
            Se conecta con pipeline_datos.RUTA_LIMPIO_DEFECTO para acceder al archivo de traslados limpios.
        """
        self.ruta_csv_limpio = Path(ruta_csv_limpio)
        self.semilla = semilla

    def particionar_datos_60_20_20(
        self, X: pd.DataFrame, y: pd.Series
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
        """Divide las matrices de datos en 60% entrenamiento, 20% validacion y 20% prueba.
        
        Que hace:
            Realiza una separacion en tres conjuntos mutuamente excluyentes conservando la
            distribucion de clases mediante estratificacion.
        Como lo hace:
            1. En el primer paso, reserva el 20% del total de observaciones como conjunto de prueba ciega
               utilizando train_test_split con test_size=0.20 y stratify=y. El 80% restante queda como temporal.
            2. En el segundo paso, sobre el 80% temporal aplica test_size=0.25 (puesto que 0.25 * 0.80 = 0.20),
               obteniendo un 20% del total para validacion y el 60% restante (0.75 * 0.80 = 0.60) para entrenamiento.
        Conexiones:
            Recibe la matriz X y el vector y devueltos por etapa_e_identificacion_variables de pipeline_datos.py.
            Entrega los conjuntos a los metodos de entrenamiento y evaluacion.
        """
        # Paso 1: Aislar el conjunto de prueba final (20% del total)
        X_temporal, X_prueba, y_temporal, y_prueba = train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=self.semilla,
            stratify=y,
        )

        # Paso 2: Dividir el 80% restante en entrenamiento (60% del total) y validacion (20% del total)
        X_entrenamiento, X_validacion, y_entrenamiento, y_validacion = train_test_split(
            X_temporal,
            y_temporal,
            test_size=0.25,
            random_state=self.semilla,
            stratify=y_temporal,
        )

        return (
            X_entrenamiento,
            X_validacion,
            X_prueba,
            y_entrenamiento,
            y_validacion,
            y_prueba,
        )

    def curva_complejidad(
        self,
        X_entrenamiento: pd.DataFrame,
        X_validacion: pd.DataFrame,
        X_prueba: pd.DataFrame,
        y_entrenamiento: pd.Series,
        y_validacion: pd.Series,
        y_prueba: pd.Series,
        profundidades: tuple[int | None, ...] = (1, 2, 3, 4, 5, 6, 7, 8, 10, 12, None),
    ) -> list[dict[str, Any]]:
        """Mide la exactitud del arbol en los tres conjuntos para cada profundidad maxima.

        Que hace:
            Construye la curva clasica de complejidad del modelo: a la izquierda (poca profundidad)
            entrenamiento y validacion son bajas (subajuste); a la derecha (profundidad libre)
            entrenamiento tiende a 100% mientras validacion/prueba dejan de mejorar o caen (sobreajuste).
        Como lo hace:
            Entrena un DecisionTreeClassifier por cada valor de max_depth sobre el 60% de entrenamiento
            y calcula accuracy_score en entrenamiento, validacion (20%) y prueba (20%).
        Conexiones:
            Se invoca desde ejecutar_diagnostico_completo y alimenta la grafica
            "Overfitting vs Underfitting" de la seccion Machine Learning del dashboard.
        """
        curva = []
        for profundidad in profundidades:
            modelo = DecisionTreeClassifier(max_depth=profundidad, random_state=self.semilla)
            modelo.fit(X_entrenamiento, y_entrenamiento)
            acc_train = float(accuracy_score(y_entrenamiento, modelo.predict(X_entrenamiento)))
            acc_val = float(accuracy_score(y_validacion, modelo.predict(X_validacion)))
            acc_test = float(accuracy_score(y_prueba, modelo.predict(X_prueba)))
            curva.append(
                {
                    "max_depth": profundidad,
                    "profundidad_real": int(modelo.get_depth()),
                    "exactitud_entrenamiento": round(acc_train, 4),
                    "exactitud_validacion": round(acc_val, 4),
                    "exactitud_prueba": round(acc_test, 4),
                    "brecha_train_val": round(abs(acc_train - acc_val), 4),
                }
            )
        return curva

    def ejecutar_diagnostico_completo(self) -> dict[str, Any]:
        """Entrena y evalua arboles de decision con diferente profundidad para diagnosticar el ajuste.
        
        Que hace:
            Compara tres modelos con hiperparametro max_depth distinto:
            - max_depth = 1: Modelo excesivamente restringido (Subajuste / Underfitting).
            - max_depth = 4: Modelo con profundidad equilibrada (Ajuste adecuado).
            - max_depth = None: Arbol sin restriccion de profundidad (Sobreajuste / Overfitting).
        Como lo hace:
            1. Carga los datos limpios o genera el dataset si no existe.
            2. Realiza la particion 60% / 20% / 20%.
            3. Entrena cada variante de DecisionTreeClassifier con X_entrenamiento.
            4. Calcula la exactitud (accuracy_score) en los tres conjuntos (entrenamiento, validacion y prueba).
            5. Evalua la diferencia (brecha) entre entrenamiento y validacion:
               - Si entrenamiento tiene exactitud muy alta pero validacion cae significativamente, se marca sobreajuste.
               - Si ambas exactitudes son bajas, se marca subajuste.
               - Si son equilibradas y consistentes, se marca ajuste optimo.
            6. Selecciona el mejor modelo basado exclusivamente en el desempeno del conjunto de validacion
               y lo evalua formalmente contra el conjunto de prueba ciego.
        Conexiones:
            Lee datos desde RUTA_LIMPIO_DEFECTO (generado por pipeline_datos.py).
            Devuelve un diccionario estructurado que alimenta el endpoint de la API en router.py y servicio.py.
        """
        if not self.ruta_csv_limpio.exists():
            ejecutar_pipeline_completo()

        df_limpio = pd.read_csv(self.ruta_csv_limpio)
        X, y, _ = etapa_e_identificacion_variables(df_limpio)

        (
            X_entrenamiento,
            X_validacion,
            X_prueba,
            y_entrenamiento,
            y_validacion,
            y_prueba,
        ) = self.particionar_datos_60_20_20(X, y)

        configuraciones = {
            "subajuste_underfitting": {
                "nombre_legible": "Arbol muy simple (Profundidad 1)",
                "max_depth": 1,
            },
            "ajuste_adecuado": {
                "nombre_legible": "Arbol equilibrado (Profundidad 4)",
                "max_depth": 4,
            },
            "sobreajuste_overfitting": {
                "nombre_legible": "Arbol sin limite (Profundidad libre)",
                "max_depth": None,
            },
        }

        resultados_modelos = {}
        mejor_clave = None
        mejor_exactitud_val = -1.0

        for clave, config in configuraciones.items():
            modelo = DecisionTreeClassifier(
                max_depth=config["max_depth"],
                random_state=self.semilla,
            )
            modelo.fit(X_entrenamiento, y_entrenamiento)

            pred_train = modelo.predict(X_entrenamiento)
            pred_val = modelo.predict(X_validacion)
            pred_test = modelo.predict(X_prueba)

            acc_train = float(accuracy_score(y_entrenamiento, pred_train))
            acc_val = float(accuracy_score(y_validacion, pred_val))
            acc_test = float(accuracy_score(y_prueba, pred_test))

            brecha = abs(acc_train - acc_val)

            # Diagnostico teorico de la condicion de aprendizaje
            if acc_train < 0.70 and acc_val < 0.70:
                diagnostico = "Subajuste (Underfitting): El modelo no posee suficiente capacidad para aprender los patrones."
            elif acc_train > 0.95 and brecha > 0.08:
                diagnostico = "Sobreajuste (Overfitting): El arbol memorizo el ruido del entrenamiento y pierde generalizacion."
            else:
                diagnostico = "Ajuste Adecuado: Buena capacidad de generalizacion con desempeno consistente en datos nuevos."

            resultados_modelos[clave] = {
                "nombre_legible": config["nombre_legible"],
                "max_depth": config["max_depth"],
                "exactitud_entrenamiento": round(acc_train, 4),
                "exactitud_validacion": round(acc_val, 4),
                "exactitud_prueba": round(acc_test, 4),
                "brecha_train_val": round(brecha, 4),
                "diagnostico": diagnostico,
            }

            # Seleccion del mejor modelo guiada por el conjunto de validacion
            if acc_val > mejor_exactitud_val:
                mejor_exactitud_val = acc_val
                mejor_clave = clave

        # Evaluacion final del modelo seleccionado sobre el conjunto de prueba
        modelo_ganador = DecisionTreeClassifier(
            max_depth=configuraciones[mejor_clave]["max_depth"],
            random_state=self.semilla,
        )
        modelo_ganador.fit(X_entrenamiento, y_entrenamiento)
        pred_ganador_test = modelo_ganador.predict(X_prueba)

        reporte_clasificacion = classification_report(
            y_prueba,
            pred_ganador_test,
            output_dict=True,
            zero_division=0,
        )

        matriz_conf = confusion_matrix(y_prueba, pred_ganador_test).tolist()

        return {
            "distribucion_datos": {
                "total_registros": len(X),
                "entrenamiento_60": len(X_entrenamiento),
                "validacion_20": len(X_validacion),
                "prueba_20": len(X_prueba),
            },
            "comparacion_modelos": resultados_modelos,
            "curva_complejidad": self.curva_complejidad(
                X_entrenamiento, X_validacion, X_prueba, y_entrenamiento, y_validacion, y_prueba
            ),
            "modelo_seleccionado": {
                "clave": mejor_clave,
                "nombre": configuraciones[mejor_clave]["nombre_legible"],
                "max_depth": configuraciones[mejor_clave]["max_depth"],
                "exactitud_validacion": round(mejor_exactitud_val, 4),
                "exactitud_prueba_final": round(float(accuracy_score(y_prueba, pred_ganador_test)), 4),
            },
            "metricas_prueba_final": {
                "reporte_clasificacion": reporte_clasificacion,
                "matriz_confusion": matriz_conf,
                "etiquetas_clases": list(modelo_ganador.classes_),
            },
        }

