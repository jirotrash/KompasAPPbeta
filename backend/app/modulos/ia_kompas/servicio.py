"""Servicios del modulo de IA y Machine Learning (ia_kompas).

- ServicioIAKompas: Orquestador general que integra:
  * P01: Busqueda BFS para escalas y reglas fijas heuristicas.
  * P02: Pipeline de datos ETL/EDA en 5 etapas.
  * P03: Modelo predictivo basico de transporte (70/30).
  * P04: Diagnostico de sobreajuste y subajuste con particion 60/20/20.
  * P05: Comparacion de algoritmos supervisados (Tree vs Forest vs KNN).
  * P06: Optimizacion de hiperparametros con GridSearchCV y 5-Fold Cross Validation.
  * P07: Segmentacion no supervisada de perfiles de viajeros con K-Means.
  * P08: Auditoria avanzada de clusters, estabilidad ARI, anomalias y MongoDB.
  * P09: Reduccion de dimensionalidad 2D con PCA.
- ServicioHabitos: Destinos probables y resumen de habitos con el historial real de rutas.
"""

from typing import Any
from app.modulos.ia_kompas.busqueda_escalas import buscar_ruta_bfs
from app.modulos.ia_kompas.habitos import predecir_destinos, resumir_habitos
from app.modulos.ia_kompas.modelo_predictivo import obtener_modelo
from app.modulos.ia_kompas.p04_ajuste_modelo import EvaluadorAjusteKompas
from app.modulos.ia_kompas.p05_comparacion_modelos import ComparadorAlgoritmosKompas
from app.modulos.ia_kompas.p06_optimizacion_hiperparametros import OptimizadorHiperparametrosKompas
from app.modulos.ia_kompas.p07_segmentacion_viajeros import SegmentadorViajerosKompas
from app.modulos.ia_kompas.p08_clusters_avanzado import AuditorClustersKompas
from app.modulos.ia_kompas.p09_reduccion_pca import ReductorDimensionalidadPCA
from app.modulos.ia_kompas.p14_motor_recomendaciones import MotorRecomendacionesKompas
from app.modulos.ia_kompas.p16_consultas_analiticas import AnaliticaAtlasKompas
from app.modulos.ia_kompas.p24_red_cnn1d_clasificacion import ClasificadorCongestionCNN1D
from app.modulos.ia_kompas.p25_comparacion_modelos_dl import ComparadorMLvsDLKompas
from app.modulos.ia_kompas.p27_red_cnn1d_eta_regresion import RegresorETACNN1D
from app.modulos.ia_kompas.pipeline_datos import ejecutar_pipeline_completo
from app.modulos.ia_kompas.reglas_transporte import evaluar_traslado_regla_fija
from app.modulos.ia_kompas.repositorio import RepositorioHabitos
from app.modulos.rutas.servicio import ServicioRutas, nombre_ruta
from app.nucleo.bd import ahora
from app.nucleo.errores import NoEncontrado


def consejo_clima(clima_lluvia: bool, temperatura: float | None) -> str | None:
    """Consejo segun el clima que manda el dispositivo. Sin temperatura no se aconseja por calor o frio."""
    if clima_lluvia:
        return "Lleva paraguas o impermeable."
    if temperatura is None:
        return None
    if temperatura > 26:
        return "Usa bloqueador solar."
    if temperatura < 15:
        return "Lleva sueter o chamarra."
    return None


class ServicioIAKompas:
    """Orquestador central de servicios inteligentes para el backend de Kompas."""

    def __init__(self):
        """Inicializa los componentes de IA y Machine Learning.
        
        Que hace:
            Instancia el modelo supervisado por defecto y los evaluadores avanzados.
        Como lo hace:
            Carga la instancia singleton de modelo predictivo y crea evaluadores para P04 a P09.
        Conexiones:
            Conecta con modelo_predictivo, p04_ajuste_modelo, p05_comparacion_modelos,
            p06_optimizacion_hiperparametros, p07_segmentacion_viajeros, p08_clusters_avanzado
            y p09_reduccion_pca.
        """
        self._modelo = obtener_modelo()
        self._evaluador_ajuste = EvaluadorAjusteKompas()
        self._comparador_algoritmos = ComparadorAlgoritmosKompas()
        self._optimizador = OptimizadorHiperparametrosKompas()
        self._segmentador = SegmentadorViajerosKompas()
        self._auditor_clusters = AuditorClustersKompas()
        self._reductor_pca = ReductorDimensionalidadPCA()

    def estado_pipeline(self) -> dict:
        """Ejecuta y resume las 5 etapas del pipeline de datos y las metricas de ML."""
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

    def diagnostico_ajuste_p04(self) -> dict[str, Any]:
        """Ejecuta el diagnostico de subajuste y sobreajuste con particion 60/20/20 (Practica 04).
        
        Que hace:
            Compara la exactitud de arboles con profundidad 1, 4 y libre sobre los 3 conjuntos de datos.
        Como lo hace:
            Invoca ejecutar_diagnostico_completo() del evaluador de ajuste.
        Conexiones:
            Conecta con p04_ajuste_modelo.py y se expone en router.py en GET /api/ia/diagnostico-ajuste.
        """
        return self._evaluador_ajuste.ejecutar_diagnostico_completo()

    def comparar_algoritmos_p05(self) -> dict[str, Any]:
        """Compara Arbol de Decision, Bosque Aleatorio y KNN (Practica 05).
        
        Que hace:
            Entrena y evalua los 3 algoritmos supervisados sobre los traslados de Kompas.
        Como lo hace:
            Invoca comparar_tres_algoritmos() midiendo tiempos de latencia y metricas de clasificacion.
        Conexiones:
            Conecta con p05_comparacion_modelos.py y se expone en router.py en GET /api/ia/comparar-algoritmos.
        """
        return self._comparador_algoritmos.comparar_tres_algoritmos()

    def optimizar_hiperparametros_p06(self) -> dict[str, Any]:
        """Ajusta sistematicamente hiperparametros mediante GridSearchCV y 5 pliegues (Practica 06).
        
        Que hace:
            Busca la mejor combinacion de profundidad, criterio y numero de arboles.
        Como lo hace:
            Invoca ejecutar_optimizacion_completa() de p06_optimizacion_hiperparametros.py.
        Conexiones:
            Conecta con p06_optimizacion_hiperparametros.py y se expone en GET /api/ia/optimizar-hiperparametros.
        """
        return self._optimizador.ejecutar_optimizacion_completa()

    def segmentar_viajeros_p07(self, k: int | None = None) -> dict[str, Any]:
        """Segmenta los perfiles de movilidad mediante K-Means no supervisado (Practica 07).
        
        Que hace:
            Agrupa los traslados en perfiles representativos fundamentando K con el metodo del codo y silueta.
        Como lo hace:
            Invoca ejecutar_segmentacion_completa() del segmentador.
        Conexiones:
            Conecta con p07_segmentacion_viajeros.py y se expone en GET /api/ia/segmentacion-viajeros.
        """
        return self._segmentador.ejecutar_segmentacion_completa(k=k)

    def auditar_clusters_p08(self) -> dict[str, Any]:
        """Ejecuta la auditoria avanzada de clusters, estabilidad ARI y anomalias (Practica 08).
        
        Que hace:
            Compara inicializaciones, escaladores, calcula el indice ARI, detecta anomalias y guarda en MongoDB.
        Como lo hace:
            Invoca ejecutar_auditoria_completa() de AuditorClustersKompas.
        Conexiones:
            Conecta con p08_clusters_avanzado.py y bd.py (MongoDB). Expuesto en GET /api/ia/auditoria-clusters.
        """
        return self._auditor_clusters.ejecutar_auditoria_completa()

    def proyeccion_pca_p09(self, k: int = 3) -> dict[str, Any]:
        """Reduce la dimensionalidad a 2 componentes principales (Practica 09).
        
        Que hace:
            Calcula PC1 y PC2 para proyectar en un plano bidimensional los viajes y clusters de K-Means.
        Como lo hace:
            Invoca ejecutar_pca_con_clusters(k=k) del reductor PCA.
        Conexiones:
            Conecta con p09_reduccion_pca.py y se expone en GET /api/ia/proyeccion-pca.
        """
        return self._reductor_pca.ejecutar_pca_con_clusters(k=k)

    def recomendar_traslado(self, datos: dict) -> dict:
        """Predice el mejor medio de transporte con ML, calcula la ruta BFS y agrega consejo climatico."""
        # 1. Inferencia del modelo de Machine Learning
        resultado_ml = self._modelo.predecir_traslado(datos)

        # 2. Busqueda BFS para optimizar numero de transbordos/escalas
        origen = datos.get("origen", "Terminal Toluca")
        destino = datos.get("destino", "Centro Metepec")
        resultado_bfs = buscar_ruta_bfs(origen=origen, destino=destino)

        # 3. Consolidacion de respuesta
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

    def evaluar_motor_recomendaciones_p14(self, datos_traslado: dict[str, Any], persistir_atlas: bool = True) -> dict[str, Any]:
        """Ejecuta el motor integrado (Random Forest + K-Means + PCA) y persiste en Atlas."""
        motor = MotorRecomendacionesKompas()
        resultado = motor.evaluar_traslado_integral(datos_traslado)
        if persistir_atlas:
            try:
                analitica = AnaliticaAtlasKompas()
                res_atlas = analitica.guardar_evaluacion({"datos_entrada": datos_traslado, **resultado})
                resultado["persistencia_atlas"] = res_atlas
            except Exception as e:
                resultado["persistencia_atlas"] = {"estado": "ERROR_O_OFFLINE", "detalle": str(e)}
        return resultado

    def analitica_clusters_p16(self) -> list[dict[str, Any]]:
        """Obtiene las estadisticas agregadas por cluster desde MongoDB Atlas."""
        analitica = AnaliticaAtlasKompas()
        return analitica.estadisticas_por_cluster()

    def analitica_horas_pico_p16(self) -> list[dict[str, Any]]:
        """Obtiene el resumen de concentracion de viajes por hora."""
        analitica = AnaliticaAtlasKompas()
        return analitica.resumen_horas_pico_congestion()

    def clasificar_congestion_cnn1d_p24(self, secuencia: list[list[float]]) -> dict[str, Any]:
        """Clasifica el nivel de congestion de tramos con la CNN 1D en PyTorch."""
        clasificador = ClasificadorCongestionCNN1D()
        return clasificador.inferir_secuencia_en_caliente(secuencia)

    def comparar_ml_vs_dl_p25(self) -> dict[str, Any]:
        """Ejecuta el benchmark formal de Random Forest vs CNN 1D."""
        comparador = ComparadorMLvsDLKompas()
        return comparador.ejecutar_comparativa_completa()

    def estimar_eta_cnn1d_p27(self, secuencia: list[list[float]]) -> dict[str, Any]:
        """Estima el tiempo continuo de arribo (ETA) en minutos con la CNN 1D regresora."""
        regresor = RegresorETACNN1D()
        return regresor.estimar_eta_en_caliente(secuencia)

    def ruta_minimas_escalas(self, origen: str, destino: str, grafo: dict[str, list[str]] | None = None) -> dict:
        """Invoca directamente el buscador BFS."""
        return buscar_ruta_bfs(grafo=grafo, origen=origen, destino=destino)

    def baseline_regla_fija(
        self, distancia_km: float, presupuesto_mxn: float, hora_dia: int = 12, clima_lluvia: bool = False
    ) -> dict:
        """Invoca directamente la regla determinista heuristica."""
        return evaluar_traslado_regla_fija(
            distancia_km=distancia_km,
            presupuesto_mxn=presupuesto_mxn,
            hora_dia=hora_dia,
            clima_lluvia=clima_lluvia,
        )


class ServicioHabitos:
    """Aprende de los recorridos que el usuario inicio en la app. La ruta se consulta con su servicio."""

    def __init__(self, repo: RepositorioHabitos, rutas: ServicioRutas):
        self.repo = repo
        self.rutas = rutas

    def _con_ruta(self, elemento: dict) -> dict:
        """Agrega nombre y ultima parada de la ruta. Si la ruta se borro, se dice; no se inventa el nombre."""
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
