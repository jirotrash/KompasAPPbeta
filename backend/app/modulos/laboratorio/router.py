"""Endpoints de las demostraciones académicas: búsqueda DFS, métricas de distancia (Euclidiana y Manhattan),
comparativo de búsqueda informada y algoritmo genético (estos dos solo admin, sin pantalla de usuario)."""

from fastapi import APIRouter, Depends, Query
from pymongo.database import Database

from app.modulos.laboratorio.esquemas import (
    ComparacionGeo,
    ComparacionPlano,
    ComparativoBusqueda,
    ParadaCatalogo,
    PeticionGenetico,
    RespuestaDFS,
    RespuestaGenetico,
)
from app.modulos.laboratorio.repositorio import RepositorioBitacora
from app.modulos.laboratorio.servicio import ServicioLaboratorio, punto_plano
from app.nucleo.bd import get_bd
from app.nucleo.parametros import punto_de_consulta
from app.nucleo.seguridad import requiere_admin

router_dfs = APIRouter(prefix="/api/dfs", tags=["Búsqueda DFS (académica)"])
router_distancias = APIRouter(prefix="/api/distancias", tags=["Métricas de distancia (académica)"])
router_busqueda = APIRouter(prefix="/api/busqueda", tags=["Búsqueda informada (académica)"], dependencies=[Depends(requiere_admin)])
router_genetico = APIRouter(prefix="/api/genetico", tags=["Algoritmo genético"], dependencies=[Depends(requiere_admin)])


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


@router_busqueda.get("/comparar", response_model=ComparativoBusqueda)
def comparar_busqueda(
    origen: str = Query(..., description="Identificador de la parada de origen (GET /api/dfs/paradas)"),
    destino: str = Query(..., description="Identificador de la parada de destino"),
    servicio: ServicioLaboratorio = Depends(get_servicio),
) -> dict:
    """🔒 admin. Corre DFS, UCS, voraz (Euclidiana y Manhattan) y A* (Euclidiana y Manhattan) sobre la red del DFS:
    costo (km), nodos explorados, longitud del camino, ¿óptimo? y milisegundos. `heuristicas` muestra en qué
    nodos cada heurística sobreestima el costo real (la Manhattan no es admisible)."""
    return servicio.comparar_busqueda(origen, destino)


@router_genetico.post("/ordenar-paradas", response_model=RespuestaGenetico)
def ordenar_paradas(peticion: PeticionGenetico, servicio: ServicioLaboratorio = Depends(get_servicio)) -> dict:
    """🔒 admin. Ordena las paradas para recorrer la menor distancia (origen fijo, sin regreso) con el algoritmo
    genético: torneo k=3, cruza OX, mutación por intercambio y elitismo 2. Con ≤ 8 paradas compara contra el
    óptimo por fuerza bruta (`brecha_vs_optimo_%`)."""
    return servicio.ordenar_paradas(peticion.model_dump())
