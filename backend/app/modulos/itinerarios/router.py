from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.modulos.catalogos.repositorio import RepositorioCatalogos
from app.modulos.catalogos.servicio import ServicioCatalogos
from app.modulos.itinerarios.esquemas import PeticionPlan, PlanGuardado, RespuestaPlanes
from app.modulos.itinerarios.repositorio import RepositorioPlanes
from app.modulos.itinerarios.servicio import ServicioItinerarios
from app.modulos.laboratorio.repositorio import RepositorioBitacora
from app.modulos.laboratorio.servicio import ServicioLaboratorio
from app.nucleo.bd import get_bd
from app.nucleo.seguridad import get_usuario_actual

router = APIRouter(prefix="/api", tags=["Itinerarios (sistema experto)"])


def get_servicio(bd: Database = Depends(get_bd)) -> ServicioItinerarios:
    return ServicioItinerarios(
        RepositorioPlanes(bd), ServicioCatalogos(RepositorioCatalogos(bd)), ServicioLaboratorio(RepositorioBitacora(bd))
    )


@router.post("/itinerarios", response_model=RespuestaPlanes)
def crear_itinerarios(
    peticion: PeticionPlan, servicio: ServicioItinerarios = Depends(get_servicio), usuario: dict = Depends(get_usuario_actual)
):
    """Botón **Crear mi plan** 🔒: busca lugares en Google Places, arma hasta 3 itinerarios y los evalúa con
    el sistema experto de Einar (`app.ia.servicio.recomendar` → `hechos.py` + `evaluar()`). Guarda el plan en
    `planes` y regresa los `recomendable` en `planes` (el de mayor puntuación es `mejor_opcion`) y el resto en
    `descartados` con su estado, reglas y datos faltantes. Las paradas de cada plan llegan en el orden más corto
(`orden_optimizado` trae los km antes y después). Si Google no responde: `503` (no se inventan lugares)."""
    return servicio.crear(usuario, peticion.model_dump())


@router.get("/planes", response_model=list[PlanGuardado])
def mis_planes(servicio: ServicioItinerarios = Depends(get_servicio), usuario: dict = Depends(get_usuario_actual)):
    """Planes que ha creado el usuario 🔒 (colección `planes`), del más reciente al más antiguo."""
    return servicio.del_usuario(usuario)
