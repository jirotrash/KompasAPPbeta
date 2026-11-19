"""Router FastAPI para los servicios de Inteligencia Artificial y Machine Learning de Kompas."""

from fastapi import APIRouter, Depends, Query
from pymongo.database import Database

from app.modulos.ia_kompas.esquemas import (
    EsquemaConsultaRutaBFS,
    EsquemaConsultaSecuenciaCNN1D,
    EsquemaConsultaTrasladoIA,
    EsquemaConsultaRecomendacionIntegral,
    EsquemaDestinosProbables,
    EsquemaEstadoPipeline,
    EsquemaEvaluacionReglaFija,
    EsquemaMisHabitos,
    EsquemaRespuestaTrasladoIA,
    EsquemaResultadoReglaFija,
    EsquemaResultadoRutaBFS,
)
from app.modulos.ia_kompas.repositorio import RepositorioHabitos
from app.modulos.ia_kompas.servicio import ServicioHabitos, ServicioIAKompas
from app.modulos.rutas.repositorio import RepositorioRutas
from app.modulos.rutas.servicio import ServicioRutas
from app.nucleo.bd import get_bd
from app.nucleo.seguridad import get_usuario_actual

router = APIRouter(prefix="/api/ia", tags=["ia_kompas"])


def obtener_servicio_ia() -> ServicioIAKompas:
    """Proveedor de dependencia para el orquestador ServicioIAKompas."""
    return ServicioIAKompas()


def obtener_servicio_habitos(bd: Database = Depends(get_bd)) -> ServicioHabitos:
    """Proveedor de dependencia para ServicioHabitos con conexion a base de datos."""
    return ServicioHabitos(RepositorioHabitos(bd), ServicioRutas(RepositorioRutas(bd)))


@router.get(
    "/destinos-probables",
    response_model=EsquemaDestinosProbables,
    summary="Destinos probables segun tus habitos (historial_rutas) [Autenticado]",
)
def destinos_probables(
    hora: int | None = Query(default=None, ge=0, le=23, description="Hora del dispositivo (0-23)"),
    dia: int | None = Query(default=None, ge=0, le=6, description="Dia de la semana del dispositivo (0 = lunes)"),
    servicio: ServicioHabitos = Depends(obtener_servicio_habitos),
    usuario: dict = Depends(get_usuario_actual),
):
    """Aprende de los recorridos que el usuario inicio en la app."""
    return servicio.destinos_probables(usuario, hora, dia)


@router.get("/mis-habitos", response_model=EsquemaMisHabitos, summary="Resumen de tus recorridos [Autenticado]")
def mis_habitos(
    servicio: ServicioHabitos = Depends(obtener_servicio_habitos),
    usuario: dict = Depends(get_usuario_actual),
):
    """Rutas mas usadas, transportes y reparto por franja horaria y dia."""
    return servicio.mis_habitos(usuario)


@router.get(
    "/pipeline-estado",
    response_model=EsquemaEstadoPipeline,
    summary="Estado de Calidad de Datos, Limpieza y Exactitud del Modelo ML (P02 y P03)",
)
def consultar_estado_pipeline(
    servicio: ServicioIAKompas = Depends(obtener_servicio_ia),
):
    """Ejecuta el pipeline de 5 etapas (p02_a a p02_e) y reporta metricas de exactitud."""
    return servicio.estado_pipeline()


@router.get(
    "/diagnostico-ajuste",
    summary="Diagnostico de Ajuste del Modelo: Particion 60/20/20, Overfitting y Underfitting (Practica 04)",
)
def diagnostico_ajuste(
    servicio: ServicioIAKompas = Depends(obtener_servicio_ia),
):
    """Evalua la division formal en 60% entrenamiento, 20% validacion y 20% prueba ciego,
    contrastando arboles con profundidad 1 (subajuste), 4 (ajuste adecuado) y libre (sobreajuste).
    """
    return servicio.diagnostico_ajuste_p04()


@router.get(
    "/comparar-algoritmos",
    summary="Comparacion de Algoritmos Supervisados: Arbol vs Bosque vs KNN (Practica 05)",
)
def comparar_algoritmos(
    servicio: ServicioIAKompas = Depends(obtener_servicio_ia),
):
    """Entrena y califica Arbol de Decision, Random Forest y K-Nearest Neighbors
    midiendo exactitud, precision, recall, F1-score y tiempo de respuesta en milisegundos.
    """
    return servicio.comparar_algoritmos_p05()


@router.get(
    "/optimizar-hiperparametros",
    summary="Optimizacion de Hiperparametros y Validacion Cruzada con 5 Pliegues (Practica 06)",
)
def optimizar_hiperparametros(
    servicio: ServicioIAKompas = Depends(obtener_servicio_ia),
):
    """Ejecuta busqueda en rejilla (GridSearchCV) con validacion cruzada estratificada (5-Fold)
    para encontrar la configuracion optima de max_depth, n_estimators y min_samples_split.
    """
    return servicio.optimizar_hiperparametros_p06()


@router.get(
    "/segmentacion-viajeros",
    summary="Segmentacion de Perfiles de Movilidad mediante K-Means (Practica 07)",
)
def segmentacion_viajeros(
    k: int | None = Query(default=None, ge=2, le=8, description="Numero opcional de clusters a forzar"),
    servicio: ServicioIAKompas = Depends(obtener_servicio_ia),
):
    """Aplica K-Means no supervisado sobre variables de distancia, hora, duracion y presupuesto.
    Evalua el Coeficiente de Silueta e Inercia (Metodo del Codo) para descubrir perfiles de viajeros.
    """
    return servicio.segmentar_viajeros_p07(k=k)


@router.get(
    "/auditoria-clusters",
    summary="Auditoria Avanzada de Clusters, Estabilidad ARI y Deteccion de Anomalias (Practica 08)",
)
def auditoria_clusters(
    servicio: ServicioIAKompas = Depends(obtener_servicio_ia),
):
    """Compara inicializaciones (k-means++ vs random) y escaladores (StandardScaler vs MinMaxScaler),
    mide la estabilidad del agrupamiento con Adjusted Rand Index, detecta viajes atipicos en el
    percentil 95 y persiste los perfiles en la coleccion perfiles_viajeros de MongoDB.
    """
    return servicio.auditar_clusters_p08()


@router.get(
    "/proyeccion-pca",
    summary="Reduccion de Dimensionalidad a 2D mediante PCA (Practica 09)",
)
def proyeccion_pca(
    k: int = Query(default=3, ge=2, le=6, description="Numero de clusters a proyectar"),
    servicio: ServicioIAKompas = Depends(obtener_servicio_ia),
):
    """Reduce el espacio multivariado de movilidad a 2 componentes principales (PC1 y PC2)
    calculando la varianza explicada y entregando coordenadas para visualizacion bidimensional.
    """
    return servicio.proyeccion_pca_p09(k=k)


@router.post(
    "/recomendar-traslado",
    response_model=EsquemaRespuestaTrasladoIA,
    summary="Recomendacion Inteligente de Transporte (Machine Learning + BFS + Baseline)",
)
def recomendar_traslado(
    consulta: EsquemaConsultaTrasladoIA,
    servicio: ServicioIAKompas = Depends(obtener_servicio_ia),
):
    """Predice el mejor medio de transporte con el modelo supervisado, calcula las escalas minimas con BFS
    y compara la decision contra la regla fija determinista.
    """
    return servicio.recomendar_traslado(consulta.model_dump())


@router.post(
    "/ruta-bfs",
    response_model=EsquemaResultadoRutaBFS,
    summary="Busqueda de Ruta con Menor Numero de Escalas (BFS)",
)
def consultar_ruta_bfs(
    consulta: EsquemaConsultaRutaBFS,
    servicio: ServicioIAKompas = Depends(obtener_servicio_ia),
):
    """Encuentra la ruta con el menor numero de saltos entre dos paradas del dominio de Kompas."""
    return servicio.ruta_minimas_escalas(
        origen=consulta.origen,
        destino=consulta.destino,
        grafo=consulta.grafo,
    )


@router.post(
    "/regla-fija",
    response_model=EsquemaResultadoReglaFija,
    summary="Evaluacion mediante Regla Fija Determinista (Baseline)",
)
def consultar_regla_fija(
    consulta: EsquemaEvaluacionReglaFija,
    servicio: ServicioIAKompas = Depends(obtener_servicio_ia),
):
    """Aplica la heuristica fija para determinar la recomendacion de transporte estandar."""
    return servicio.baseline_regla_fija(
        distancia_km=consulta.distancia_km,
        presupuesto_mxn=consulta.presupuesto_mxn,
        hora_dia=consulta.hora_dia,
        clima_lluvia=consulta.clima_lluvia,
    )


@router.post(
    "/motor-recomendacion-integral",
    summary="Motor Multimodelo de Recomendacion y Persistencia en Atlas (Practica 14 y 15)",
)
def motor_recomendacion_integral(
    consulta: EsquemaConsultaRecomendacionIntegral,
    servicio: ServicioIAKompas = Depends(obtener_servicio_ia),
):
    """Orquesta simultaneamente Random Forest, K-Means (4 perfiles) y PCA (2D)
    generando directivas de movilidad y persistiendo la evaluacion en MongoDB Atlas.
    """
    return servicio.evaluar_motor_recomendaciones_p14(consulta.model_dump())


@router.get(
    "/analitica/reporte-clusters",
    summary="Estadisticas y Metricas por Perfil de Viajero en MongoDB Atlas (Practica 16)",
)
def analitica_reporte_clusters(
    servicio: ServicioIAKompas = Depends(obtener_servicio_ia),
):
    """Ejecuta el pipeline de agregacion ($group) sobre las evaluaciones historicas
    para reportar volumen, confianza y costos por perfil.
    """
    return servicio.analitica_clusters_p16()


@router.get(
    "/analitica/horas-pico",
    summary="Analisis de Demanda y Concentracion Horaria (Practica 16)",
)
def analitica_horas_pico(
    servicio: ServicioIAKompas = Depends(obtener_servicio_ia),
):
    """Agrupa las solicitudes por hora del dia identificando picos y modos predilectos."""
    return servicio.analitica_horas_pico_p16()


@router.post(
    "/deep-learning/clasificar-congestion",
    summary="Clasificacion de Congestion en Tramos con Red CNN 1D en PyTorch (Practica 24)",
)
def clasificar_congestion_cnn1d(
    consulta: EsquemaConsultaSecuenciaCNN1D,
    servicio: ServicioIAKompas = Depends(obtener_servicio_ia),
):
    """Procesa una secuencia de tramos consecutivos (velocidad, duracion, ocupacion)
    con una red convolucional 1D para diagnosticar el nivel de congestion.
    """
    return servicio.clasificar_congestion_cnn1d_p24(consulta.secuencia)


@router.get(
    "/deep-learning/comparar-modelos",
    summary="Benchmark Formal: Machine Learning Clasico vs Deep Learning CNN 1D (Practica 25)",
)
def comparar_modelos_dl(
    servicio: ServicioIAKompas = Depends(obtener_servicio_ia),
):
    """Compara Decision Tree, Random Forest y CNN 1D en exactitud, F1 y latencia en ms."""
    return servicio.comparar_ml_vs_dl_p25()


@router.post(
    "/deep-learning/predecir-eta",
    summary="Prediccion Continua de Tiempo Estimado de Llegada (ETA) con CNN 1D (Practica 27)",
)
def predecir_eta_cnn1d(
    consulta: EsquemaConsultaSecuenciaCNN1D,
    servicio: ServicioIAKompas = Depends(obtener_servicio_ia),
):
    """Estima los minutos continuos restantes del viaje con la red CNN 1D de regresion."""
    return servicio.estimar_eta_cnn1d_p27(consulta.secuencia)

