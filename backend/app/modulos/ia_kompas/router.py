"""Router FastAPI para los servicios de Inteligencia Artificial y Machine Learning de Kompás."""

from fastapi import APIRouter, Depends

from app.modulos.ia_kompas.esquemas import (
    EsquemaConsultaRutaBFS,
    EsquemaConsultaTrasladoIA,
    EsquemaEstadoPipeline,
    EsquemaEvaluacionReglaFija,
    EsquemaRespuestaTrasladoIA,
    EsquemaResultadoReglaFija,
    EsquemaResultadoRutaBFS,
)
from app.modulos.ia_kompas.servicio import ServicioIAKompas

router = APIRouter(prefix="/api/ia", tags=["ia_kompas"])


def obtener_servicio_ia() -> ServicioIAKompas:
    return ServicioIAKompas()


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
