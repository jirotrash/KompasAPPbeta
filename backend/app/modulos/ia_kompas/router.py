"""Router FastAPI para los servicios de Inteligencia Artificial y Machine Learning de Kompás."""

from fastapi import APIRouter, Depends, Query
from pymongo.database import Database

from app.modulos.ia_kompas.esquemas import (
    EsquemaConsultaRutaBFS,
    EsquemaConsultaTrasladoIA,
    EsquemaDestinosProbables,
    EsquemaEstadoPipeline,
    EsquemaEvaluacionModeloParticiones,
    EsquemaEvaluacionReglaFija,
    EsquemaMetricasLaboratorioIA,
    EsquemaMisHabitos,
    EsquemaPeticionSimulacionIA,
    EsquemaRespuestaSimulacionIA,
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
    return ServicioIAKompas()


def obtener_servicio_habitos(bd: Database = Depends(get_bd)) -> ServicioHabitos:
    return ServicioHabitos(RepositorioHabitos(bd), ServicioRutas(RepositorioRutas(bd)))


@router.get(
    "/destinos-probables",
    response_model=EsquemaDestinosProbables,
    summary="Destinos probables según tus hábitos (historial_rutas) 🔒",
)
def destinos_probables(
    hora: int | None = Query(default=None, ge=0, le=23, description="Hora del dispositivo (0-23)"),
    dia: int | None = Query(default=None, ge=0, le=6, description="Día de la semana del dispositivo (0 = lunes)"),
    servicio: ServicioHabitos = Depends(obtener_servicio_habitos),
    usuario: dict = Depends(get_usuario_actual),
):
    """Aprende de los recorridos que el usuario inició: frecuencia por franja con pocos datos y KNN con
    20 o más. Con menos de 5 recorridos responde `datos_insuficientes` (no se inventa un destino).
    """
    return servicio.destinos_probables(usuario, hora, dia)


@router.get("/mis-habitos", response_model=EsquemaMisHabitos, summary="Resumen de tus recorridos 🔒")
def mis_habitos(
    servicio: ServicioHabitos = Depends(obtener_servicio_habitos),
    usuario: dict = Depends(get_usuario_actual),
):
    """Rutas más usadas, transportes y reparto por franja horaria y día. Solo cuenta; no estima tráfico."""
    return servicio.mis_habitos(usuario)


@router.get(
    "/pipeline-estado",
    response_model=EsquemaEstadoPipeline,
    summary="Estado de Calidad de Datos, Limpieza y Exactitud del Modelo ML",
)
def consultar_estado_pipeline(
    servicio: ServicioIAKompas = Depends(obtener_servicio_ia),
):
    """Ejecuta el pipeline de 5 etapas (p02_a a p02_e) y reporta las métricas de exactitud

    del modelo entrenado con 70% de datos y probado con 30% ciego contra la regla fija.
    """
    return servicio.estado_pipeline()


@router.get(
    "/evaluacion-modelo",
    response_model=EsquemaEvaluacionModeloParticiones,
    summary="Evaluación Experimental de Particiones (70/30 vs 80/20 vs 60/20/20), Underfitting/Overfitting y Reglas Fijas",
)
def consultar_evaluacion_modelo(
    servicio: ServicioIAKompas = Depends(obtener_servicio_ia),
):
    """Evalúa los 500 recorridos limpios de Kompás comparando particiones (70/30, 75/25, 80/20, 85/15, 60/20/20),
    curva de profundidad max_depth (1 a 15) para demostrar subajuste vs. sobreajuste, comparación contra Reglas Fijas
    y matriz de confusión.
    """
    return servicio.evaluacion_modelo()


@router.get(
    "/metricas",
    response_model=EsquemaMetricasLaboratorioIA,
    summary="Métricas del Laboratorio IA: Limpieza (P02), Particiones, Under/Overfitting y Reglas vs ML (P03)",
)
def consultar_metricas_ia(
    servicio: ServicioIAKompas = Depends(obtener_servicio_ia),
):
    """Devuelve el resumen de limpieza de 500 planes, la tabla comparativa de particiones
    (60/40, 70/30, 75/25, 80/20, 60/20/20), la curva de complejidad por max_depth y la matriz de confusión.
    """
    return servicio.obtener_metricas_laboratorio()


@router.post(
    "/simular",
    response_model=EsquemaRespuestaSimulacionIA,
    summary="Simulador Interactivo en Vivo: Reglas Fijas vs Árbol de Decisión Óptimo + Ruta BFS",
)
def simular_prediccion_ia(
    peticion: EsquemaPeticionSimulacionIA,
    servicio: ServicioIAKompas = Depends(obtener_servicio_ia),
):
    """Evalúa en vivo un plan/traslado comparando Reglas Fijas (P01), Árbol de Decisión óptimo (P03) y ruta BFS (P01)."""
    return servicio.simular_plan_ia(peticion.model_dump())




@router.post(
    "/recomendar-traslado",
    response_model=EsquemaRespuestaTrasladoIA,
    summary="Recomendación Inteligente de Transporte (Machine Learning + BFS + Baseline)",
)
def recomendar_traslado(
    consulta: EsquemaConsultaTrasladoIA,
    servicio: ServicioIAKompas = Depends(obtener_servicio_ia),
):
    """Predice el mejor medio de transporte con el modelo supervisado, calcula las escalas mínimas con BFS

    y compara la decisión contra la regla fija determinista.
    """
    return servicio.recomendar_traslado(consulta.model_dump())


@router.post(
    "/ruta-bfs",
    response_model=EsquemaResultadoRutaBFS,
    summary="Búsqueda de Ruta con Menor Número de Escalas (BFS)",
)
def consultar_ruta_bfs(
    consulta: EsquemaConsultaRutaBFS,
    servicio: ServicioIAKompas = Depends(obtener_servicio_ia),
):
    """Encuentra la ruta con el menor número de saltos entre dos paradas del dominio de Kompás."""
    return servicio.ruta_minimas_escalas(
        origen=consulta.origen,
        destino=consulta.destino,
        grafo=consulta.grafo,
    )


@router.post(
    "/regla-fija",
    response_model=EsquemaResultadoReglaFija,
    summary="Evaluación mediante Regla Fija Determinista (Baseline)",
)
def consultar_regla_fija(
    consulta: EsquemaEvaluacionReglaFija,
    servicio: ServicioIAKompas = Depends(obtener_servicio_ia),
):
    """Aplica la heurística fija para determinar la recomendación de transporte estándar."""
    return servicio.baseline_regla_fija(
        distancia_km=consulta.distancia_km,
        presupuesto_mxn=consulta.presupuesto_mxn,
        hora_dia=consulta.hora_dia,
        clima_lluvia=consulta.clima_lluvia,
    )
