"""Endpoints de la demostración académica de búsqueda DFS."""

from fastapi import APIRouter, Query

from app.esquemas.dfs import ParadaCatalogo, RespuestaDFS
from app.ia.busqueda_dfs import PARADAS_KOMPAS, planificar_rutas_dfs

router = APIRouter(prefix="/api/dfs", tags=["Búsqueda DFS (académica)"])


@router.get("/paradas", response_model=list[ParadaCatalogo])
def listar_paradas() -> list[dict]:
    """Devuelve el catálogo de nodos disponible en el grafo académico."""
    return [{"id": clave, **info} for clave, info in PARADAS_KOMPAS.items()]


@router.get("/buscar", response_model=RespuestaDFS)
def buscar_rutas_dfs(
    origen: str = Query(..., description="Identificador de la parada de origen"),
    destino: str = Query(..., description="Identificador de la parada de destino"),
    limite_profundidad: int = Query(5, ge=1, le=10, description="Máximo de aristas por camino"),
) -> dict:
    """Ejecuta DFS con control de ciclos, backtracking y límite de profundidad.

    La respuesta siempre identifica esta red como una demostración no operativa.
    """
    return planificar_rutas_dfs(origen, destino, limite_profundidad)
