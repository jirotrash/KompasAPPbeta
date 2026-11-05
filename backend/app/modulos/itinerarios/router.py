from fastapi import APIRouter, Depends, Query, status
from pymongo.database import Database

from app.modulos.catalogos.repositorio import RepositorioCatalogos
from app.modulos.catalogos.servicio import ServicioCatalogos
from app.modulos.itinerarios.esquemas import CambioPlan, PeticionPlan, PlanGuardado, PlanRecuperado, RecuperarPlan, RespuestaPlanes
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
def mis_planes(
    limite: int = Query(50, ge=1, le=100), antes_de: int | None = Query(None, gt=0),
    servicio: ServicioItinerarios = Depends(get_servicio), usuario: dict = Depends(get_usuario_actual),
):
    """Planes que ha creado el usuario 🔒 (colección `planes`), del más reciente al más antiguo."""
    return servicio.del_usuario(usuario, limite, antes_de)


@router.get("/planes/{id_plan}", response_model=PlanGuardado)
def detalle_plan(id_plan: int, servicio: ServicioItinerarios = Depends(get_servicio), usuario: dict = Depends(get_usuario_actual)):
    """Detalle propio. Los planes anteriores siguen disponibles como resumen."""
    return servicio.detalle(usuario, id_plan)


@router.patch("/planes/{id_plan}", response_model=PlanGuardado)
def cambiar_plan(
    id_plan: int, datos: CambioPlan,
    servicio: ServicioItinerarios = Depends(get_servicio), usuario: dict = Depends(get_usuario_actual),
):
    """Selecciona una alternativa, renombra o marca como realizado. Nunca acepta lugares enviados por el cliente."""
    return servicio.actualizar(usuario, id_plan, datos.model_dump(exclude_unset=True))


@router.delete("/planes/{id_plan}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_plan(id_plan: int, servicio: ServicioItinerarios = Depends(get_servicio), usuario: dict = Depends(get_usuario_actual)):
    """Borrado lógico del plan propio; conserva el documento en la base."""
    servicio.borrar(usuario, id_plan)


@router.post("/planes/{id_plan}/recuperar", response_model=PlanRecuperado)
def recuperar_plan(
    id_plan: int, datos: RecuperarPlan,
    servicio: ServicioItinerarios = Depends(get_servicio), usuario: dict = Depends(get_usuario_actual),
):
    """Reconsulta las mismas paradas y evalúa el recorrido desde el origen actual; no crea otro plan."""
    return servicio.recuperar(usuario, id_plan, datos.model_dump())
