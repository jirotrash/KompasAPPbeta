"""Servicio orquestador del módulo de IA y Machine Learning (ia_kompas).

Conecta la búsqueda en anchura (BFS) para escalas, el pipeline de datos de 5 etapas,
la regla heurística baseline y el modelo predictivo supervisado.
"""

from app.modulos.ia_kompas.busqueda_escalas import buscar_ruta_bfs
from app.modulos.ia_kompas.modelo_predictivo import obtener_modelo
from app.modulos.ia_kompas.pipeline_datos import ejecutar_pipeline_completo
from app.modulos.ia_kompas.reglas_transporte import evaluar_traslado_regla_fija


class ServicioIAKompas:
    """Orquestador de servicios inteligentes para Kompás."""

    def __init__(self):
        self._modelo = obtener_modelo()

    def estado_pipeline(self) -> dict:
        """Ejecuta y resume las 5 etapas del pipeline de datos y las métricas de ML."""
        reporte_pipeline = ejecutar_pipeline_completo()
        metricas_ml = self._modelo.entrenar_y_evaluar()

        return {
            "dataset_crudo_filas": reporte_pipeline["etapa_a"]["filas"],
            "dataset_limpio_filas": reporte_pipeline["etapa_d"]["filas_limpias"],
            "nulos_detectados": reporte_pipeline["etapa_c"]["nulos_por_columna"],
            "duplicados_eliminados": reporte_pipeline["etapa_c"]["filas_completamente_duplicadas"],
            "outliers_eliminados": (
                reporte_pipeline["etapa_c"]["outliers_detectados"]["distancia_menor_o_igual_a_cero"]
                + reporte_pipeline["etapa_c"]["outliers_detectados"]["rating_fuera_de_rango_1_a_5"]
            ),
            "exactitud_modelo_ml": metricas_ml["exactitud_machine_learning"],
            "exactitud_regla_fija": metricas_ml["exactitud_regla_fija"],
            "particion": {
                "entrenamiento_70_pct": metricas_ml["muestras_entrenamiento_70_pct"],
                "prueba_30_pct": metricas_ml["muestras_prueba_30_pct"],
            },
            "importancia_variables": metricas_ml["importancia_variables"],
        }

    def recomendar_traslado(self, datos: dict) -> dict:
        """Predice el mejor medio de transporte con ML, calcula la ruta BFS y evalúa la regla fija."""
        # 1. Inferencia del modelo de Machine Learning
        resultado_ml = self._modelo.predecir_traslado(datos)

        # 2. Búsqueda BFS para optimizar número de transbordos/escalas
        origen = datos.get("origen", "Terminal Toluca")
        destino = datos.get("destino", "Centro Metepec")
        resultado_bfs = buscar_ruta_bfs(origen=origen, destino=destino)

        # 3. Consolidación de respuesta
        return {
            "modo_recomendado": resultado_ml["modo_recomendado"],
            "confianza": resultado_ml["confianza"],
            "origen_decision": resultado_ml["origen_decision"],
            "tiempo_estimado_min": resultado_ml["tiempo_estimado_min"],
            "ruta_bfs": resultado_bfs if resultado_bfs["encontrado"] else None,
            "comparacion_baseline": resultado_ml["comparacion_baseline"],
            "explicacion": resultado_ml["explicacion"],
        }

    def ruta_minimas_escalas(self, origen: str, destino: str, grafo: dict[str, list[str]] | None = None) -> dict:
        """Invoca directamente el buscador BFS."""
        return buscar_ruta_bfs(grafo=grafo, origen=origen, destino=destino)

    def baseline_regla_fija(
        self, distancia_km: float, presupuesto_mxn: float, hora_dia: int = 12, clima_lluvia: bool = False
    ) -> dict:
        """Invoca directamente la regla determinista heurística."""
        return evaluar_traslado_regla_fija(
            distancia_km=distancia_km,
            presupuesto_mxn=presupuesto_mxn,
            hora_dia=hora_dia,
            clima_lluvia=clima_lluvia,
        )
