"""Servicios del módulo de IA y Machine Learning (ia_kompas).

- ServicioIAKompas: BFS para escalas, pipeline de datos de 5 etapas, regla fija (baseline) y modelo
  predictivo del medio de transporte.
- ServicioHabitos: destinos probables y resumen de hábitos con el historial real (`historial_rutas`).
"""

from app.modulos.ia_kompas.busqueda_escalas import buscar_ruta_bfs
from app.modulos.ia_kompas.entrenamiento_particiones import ejecutar_evaluacion_completa_modelo
from app.modulos.ia_kompas.habitos import predecir_destinos, resumir_habitos
from app.modulos.ia_kompas.modelo_entrenamiento import obtener_laboratorio_ia
from app.modulos.ia_kompas.modelo_predictivo import obtener_modelo
from app.modulos.ia_kompas.pipeline_datos import ejecutar_pipeline_completo
from app.modulos.ia_kompas.reglas_transporte import evaluar_traslado_regla_fija
from app.modulos.ia_kompas.repositorio import RepositorioHabitos
from app.modulos.rutas.servicio import ServicioRutas, nombre_ruta
from app.nucleo.bd import ahora
from app.nucleo.errores import NoEncontrado


def consejo_clima(clima_lluvia: bool, temperatura: float | None) -> str | None:
    """Consejo según el clima que manda el dispositivo. Sin temperatura no se aconseja por calor o frío."""
    if clima_lluvia:
        return "Lleva paraguas o impermeable."
    if temperatura is None:
        return None
    if temperatura > 26:
        return "Usa bloqueador solar."
    if temperatura < 15:
        return "Lleva suéter o chamarra."
    return None


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
        """Predice el mejor medio de transporte con ML (la lluvia y la hora pico son variables del modelo),
        calcula la ruta BFS y agrega un consejo según el clima.
        """
        # 1. Inferencia del modelo de Machine Learning
        resultado_ml = self._modelo.predecir_traslado(datos)

        # 2. Búsqueda BFS para optimizar número de transbordos/escalas
        origen = datos.get("origen", "Terminal Toluca")
        destino = datos.get("destino", "Centro Metepec")
        resultado_bfs = buscar_ruta_bfs(origen=origen, destino=destino)

        # 3. Consolidación de respuesta
        consejo = consejo_clima(bool(datos.get("clima_lluvia")), datos.get("temperatura"))
        explicacion = resultado_ml["explicacion"] + (f" Consejo: {consejo}" if consejo else "")
        return {
            "modo_recomendado": resultado_ml["modo_recomendado"],
            "confianza": resultado_ml["confianza"],
            "origen_decision": resultado_ml["origen_decision"],
            "tiempo_estimado_min": resultado_ml["tiempo_estimado_min"],
            "ruta_bfs": resultado_bfs if resultado_bfs["encontrado"] else None,
            "comparacion_baseline": resultado_ml["comparacion_baseline"],
            "explicacion": explicacion,
            "consejo_clima": consejo,
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

    def evaluacion_modelo(self) -> dict:
        """Ejecuta el experimento comparativo de particiones (70/30, 75/25, 80/20, 85/15, 60/20/20),
        el análisis de underfitting vs. overfitting (max_depth 1 a 15) y la comparación contra Reglas Fijas
        sobre el dataset limpio de 500 recorridos turísticos de Kompás.
        """
        return ejecutar_evaluacion_completa_modelo()

    def obtener_metricas_laboratorio(self) -> dict:
        """Devuelve el JSON estructurado de métricas para el Laboratorio IA (GET /api/ia/metricas)."""
        return obtener_laboratorio_ia().obtener_metricas()

    def simular_plan_ia(self, datos: dict) -> dict:
        """Simula un plan/traslado con Reglas Fijas, Árbol de Decisión óptimo y BFS (POST /api/ia/simular)."""
        return obtener_laboratorio_ia().simular(datos)




class ServicioHabitos:
    """Aprende de los recorridos que el usuario inició en la app. La ruta se consulta con su servicio."""

    def __init__(self, repo: RepositorioHabitos, rutas: ServicioRutas):
        self.repo = repo
        self.rutas = rutas

    def _con_ruta(self, elemento: dict) -> dict:
        """Agrega nombre y última parada de la ruta. Si la ruta se borró, se dice; no se inventa el nombre."""
        try:
            ruta = self.rutas.detalle(elemento["id_ruta"])
        except NoEncontrado:
            return {**elemento, "nombre": f"Ruta {elemento['id_ruta']} (ya no disponible)", "ultima_parada": None}
        paradas = ruta.get("paradas") or []
        return {**elemento, "nombre": nombre_ruta(ruta), "ultima_parada": paradas[-1]["nombre"] if paradas else None}

    def destinos_probables(self, usuario: dict, hora: int | None = None, dia_semana: int | None = None) -> dict:
        """hora (0-23) y dia_semana (0 = lunes) son los del dispositivo; si no llegan, la hora de Toluca."""
        momento = ahora()
        minuto = momento.minute if hora is None else 0
        hora = momento.hour if hora is None else hora
        dia_semana = momento.weekday() if dia_semana is None else dia_semana
        prediccion = predecir_destinos(self.repo.viajes_del_usuario(usuario["id"]), hora, dia_semana, minuto)
        prediccion["destinos"] = [self._con_ruta(d) for d in prediccion["destinos"]]
        return prediccion

    def mis_habitos(self, usuario: dict) -> dict:
        resumen = resumir_habitos(self.repo.viajes_del_usuario(usuario["id"]))
        resumen["rutas_frecuentes"] = [self._con_ruta(r) for r in resumen["rutas_frecuentes"]]
        return resumen
