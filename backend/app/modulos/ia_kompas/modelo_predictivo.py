"""Modelo predictivo de Machine Learning supervisado para recomendación de transporte.

Entrena un DecisionTreeClassifier con partición formal 70% entrenamiento / 30% prueba,
evalúa comparativamente contra el baseline de reglas fijas y realiza inferencia en tiempo real.
(Trazabilidad académica: adaptado de la práctica p03primermodelo).
"""

from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

from app.modulos.ia_kompas.pipeline_datos import (
    COLUMNAS_CARACTERISTICAS,
    RUTA_LIMPIO_DEFECTO,
    ejecutar_pipeline_completo,
    etapa_e_identificacion_variables,
)
from app.modulos.ia_kompas.reglas_transporte import evaluar_traslado_regla_fija

HORAS_PICO_SET = {7, 8, 9, 18, 19, 20}


class ModeloPredictivoKompás:
    """Encapsula el ciclo de vida del clasificador de Machine Learning:

    entrenamiento con 70% de datos, evaluación contra baseline con 30% e inferencia en producción.
    """

    def __init__(self, max_depth: int = 4, random_state: int = 42):
        self.max_depth = max_depth
        self.random_state = random_state
        self.modelo: DecisionTreeClassifier | None = None
        self.clases: list[str] = []
        self.metricas: dict = {}
        self.importancia_variables: dict[str, float] = {}
        self.entrenado: bool = False

    def entrenar_y_evaluar(
        self,
        ruta_csv_limpio: Path | str = RUTA_LIMPIO_DEFECTO,
        test_size: float = 0.30,  # 70% entrenamiento / 30% prueba según requerimiento
    ) -> dict:
        """Entrena el árbol de decisión sobre el 70% de los datos limpios

        y evalúa tanto el modelo de ML como la regla fija sobre el 30% restante de prueba.
        """
        p_limpio = Path(ruta_csv_limpio)
        if not p_limpio.exists():
            ejecutar_pipeline_completo()

        df_limpio = pd.read_csv(p_limpio)
        X, y, _ = etapa_e_identificacion_variables(df_limpio)

        # Partición formal 70% entrenamiento / 30% prueba con estratificación
        X_entrenamiento, X_prueba, y_entrenamiento, y_prueba = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=self.random_state,
            stratify=y,
        )

        # 1. Entrenamiento del clasificador de Machine Learning (fit)
        self.modelo = DecisionTreeClassifier(
            max_depth=self.max_depth,
            random_state=self.random_state,
        )
        self.modelo.fit(X_entrenamiento, y_entrenamiento)
        self.clases = list(self.modelo.classes_)
        self.entrenado = True

        # 2. Inferencia en el conjunto de prueba ciego (predict)
        predicciones_ml = self.modelo.predict(X_prueba)

        # 3. Inferencia de la Regla Fija sobre el mismo conjunto de prueba
        def predecir_fila_regla(fila: pd.Series) -> str:
            res = evaluar_traslado_regla_fija(
                distancia_km=float(fila["distancia_km"]),
                presupuesto_mxn=float(fila["presupuesto_mxn"]),
                hora_dia=int(fila["hora_dia"]),
                clima_lluvia=bool(fila["clima_lluvia"]),
            )
            return res["modo_recomendado"]

        predicciones_regla = X_prueba.apply(predecir_fila_regla, axis=1)

        # 4. Cálculo de exactitud comparativa (accuracy_score)
        exactitud_ml = float(accuracy_score(y_prueba, predicciones_ml))
        exactitud_regla = float(accuracy_score(y_prueba, predicciones_regla))

        # 5. Métricas detalladas: classification_report y matriz de confusión
        reporte_str = classification_report(
            y_prueba,
            predicciones_ml,
            zero_division=0,
            output_dict=True,
        )
        matriz = confusion_matrix(y_prueba, predicciones_ml, labels=self.clases).tolist()

        # 6. Importancia de las variables (feature importances)
        importancias = {
            col: round(float(imp), 4)
            for col, imp in zip(COLUMNAS_CARACTERISTICAS, self.modelo.feature_importances_)
        }
        self.importancia_variables = importancias

        self.metricas = {
            "total_muestras": len(df_limpio),
            "muestras_entrenamiento_70_pct": len(X_entrenamiento),
            "muestras_prueba_30_pct": len(X_prueba),
            "exactitud_machine_learning": round(exactitud_ml, 4),
            "exactitud_regla_fija": round(exactitud_regla, 4),
            "reporte_clasificacion": reporte_str,
            "matriz_confusion": {
                "etiquetas": self.clases,
                "matriz": matriz,
            },
            "importancia_variables": importancias,
        }
        return self.metricas

    def predecir_traslado(self, datos: dict) -> dict:
        """Realiza inferencia en tiempo real para un nuevo traslado en Kompás."""
        if not self.entrenado or self.modelo is None:
            self.entrenar_y_evaluar()

        distancia_km = float(datos.get("distancia_km", 1.0))
        hora_dia = int(datos.get("hora_dia", 12))
        pico_val = datos.get("es_hora_pico")
        if pico_val is None:
            es_hora_pico = 1 if hora_dia in HORAS_PICO_SET else 0
        else:
            es_hora_pico = 1 if pico_val else 0
        presupuesto_mxn = float(datos.get("presupuesto_mxn", 50.0))
        clima_lluvia = int(1 if datos.get("clima_lluvia", False) else 0)
        rating_destino = float(datos.get("rating_destino", 4.5))

        # Vector de características alineado exactamente con COLUMNAS_CARACTERISTICAS
        fila = pd.DataFrame([{
            "distancia_km": distancia_km,
            "hora_dia": hora_dia,
            "es_hora_pico": es_hora_pico,
            "presupuesto_mxn": presupuesto_mxn,
            "clima_lluvia": clima_lluvia,
            "rating_destino": rating_destino,
        }])

        # Predicción y probabilidades
        assert self.modelo is not None
        prediccion_ml = str(self.modelo.predict(fila)[0])
        probabilidades = self.modelo.predict_proba(fila)[0]
        indice_clase = self.clases.index(prediccion_ml)
        confianza = float(round(probabilidades[indice_clase], 3))

        # Comparación contra Regla Fija
        resultado_regla = evaluar_traslado_regla_fija(
            distancia_km=distancia_km,
            presupuesto_mxn=presupuesto_mxn,
            hora_dia=hora_dia,
            clima_lluvia=bool(clima_lluvia),
        )
        prediccion_regla = resultado_regla["modo_recomendado"]
        coinciden = prediccion_ml == prediccion_regla

        # Estimación de duración según el modo predicho
        if prediccion_ml == "caminando":
            duracion_min = int(round(distancia_km * 12.0))
        elif prediccion_ml == "auto_privado":
            duracion_min = int(round(8.0 + distancia_km * 2.5 + (8 if es_hora_pico else 0)))
        else:  # transporte_publico
            duracion_min = int(round(12.0 + distancia_km * 3.8 + (10 if es_hora_pico else 0)))

        explicacion = (
            f"El modelo de Machine Learning recomienda '{prediccion_ml}' con {confianza:.0%} de confianza. "
            f"Distancia: {distancia_km:.1f} km, Presupuesto: ${presupuesto_mxn:.0f} MXN, "
            f"Hora: {hora_dia:02d}:00 {'(hora pico)' if es_hora_pico else ''}, "
            f"Clima: {'lluvioso' if clima_lluvia else 'favorable'}."
        )

        return {
            "modo_recomendado": prediccion_ml,
            "confianza": confianza,
            "origen_decision": "machine_learning",
            "tiempo_estimado_min": max(1, duracion_min),
            "comparacion_baseline": {
                "prediccion_regla_fija": prediccion_regla,
                "regla_activada": resultado_regla["regla_activada"],
                "coinciden": coinciden,
            },
            "explicacion": explicacion,
        }


# Instancia singleton para inferencia en FastAPI
_instancia_modelo: ModeloPredictivoKompás | None = None


def obtener_modelo() -> ModeloPredictivoKompás:
    global _instancia_modelo
    if _instancia_modelo is None:
        _instancia_modelo = ModeloPredictivoKompás()
        _instancia_modelo.entrenar_y_evaluar()
    return _instancia_modelo

