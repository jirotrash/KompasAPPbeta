"""Endpoints de las demostraciones académicas: búsqueda DFS y métricas de distancia (Euclidiana y Manhattan)."""

from fastapi import APIRouter, Depends, Query
from pymongo.database import Database

from app.modulos.laboratorio.esquemas import ComparacionGeo, ComparacionPlano, ParadaCatalogo, RespuestaDFS
from app.modulos.laboratorio.repositorio import RepositorioBitacora
from app.modulos.laboratorio.servicio import ServicioLaboratorio, punto_plano
from app.nucleo.bd import get_bd
from app.nucleo.parametros import punto_de_consulta

router_dfs = APIRouter(prefix="/api/dfs", tags=["Búsqueda DFS (académica)"])
router_distancias = APIRouter(prefix="/api/distancias", tags=["Métricas de distancia (académica)"])


def get_servicio(bd: Database = Depends(get_bd)) -> ServicioLaboratorio:
    return ServicioLaboratorio(RepositorioBitacora(bd))


@router_dfs.get("/paradas", response_model=list[ParadaCatalogo])
def listar_paradas() -> list[dict]:
    """Devuelve el catálogo de nodos disponible en el grafo académico."""
    return ServicioLaboratorio.paradas()


@router_dfs.get("/buscar", response_model=RespuestaDFS)
def buscar_rutas_dfs(
    origen: str = Query(..., description="Identificador de la parada de origen"),
    destino: str = Query(..., description="Identificador de la parada de destino"),
    limite_profundidad: int = Query(5, ge=1, le=10, description="Máximo de aristas por camino"),
    servicio: ServicioLaboratorio = Depends(get_servicio),
) -> dict:
    """Ejecuta DFS con control de ciclos, backtracking y límite de profundidad.

    La respuesta siempre identifica esta red como una demostración no operativa.
    """
    return servicio.buscar_dfs(origen, destino, limite_profundidad)


@router_distancias.get("/plano", response_model=ComparacionPlano)
def comparar_en_plano(
    a: str = Query(..., description="Punto A como x,y (ej. 1,2)"),
    b: str = Query(..., description="Punto B como x,y (ej. 5,5)"),
    servicio: ServicioLaboratorio = Depends(get_servicio),
) -> dict:
    """Compara la distancia Euclidiana y la Manhattan entre dos puntos de un plano cartesiano."""
    return servicio.comparar_plano(punto_plano("a", a), punto_plano("b", b))


@router_distancias.get("/geo", response_model=ComparacionGeo)
def comparar_en_mapa(
    origen: str = Query(..., description="lat,lng"),
    destino: str = Query(..., description="lat,lng"),
    servicio: ServicioLaboratorio = Depends(get_servicio),
) -> dict:
    """Las mismas métricas con coordenadas reales, en km sobre un plano local.

    El recorrido Manhattan va primero de este a oeste (sobre la latitud del origen) y luego de norte a sur.
    Kompás estima la distancia por calles con Manhattan.
    """
    return servicio.comparar_geo(punto_de_consulta("origen", origen), punto_de_consulta("destino", destino))
