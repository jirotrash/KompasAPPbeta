from fastapi import APIRouter, Depends, Query
from pymongo.database import Database

from app.modulos.busquedas.esquemas import BusquedaSalida
from app.modulos.busquedas.repositorio import RepositorioBusquedas
from app.modulos.busquedas.servicio import ServicioBusquedas
from app.nucleo.bd import get_bd
from app.nucleo.seguridad import requiere_admin

router_admin = APIRouter(prefix="/api/admin/busquedas", tags=["Administración"], dependencies=[Depends(requiere_admin)])


def get_servicio(bd: Database = Depends(get_bd)) -> ServicioBusquedas:
    return ServicioBusquedas(RepositorioBusquedas(bd))


@router_admin.get("", response_model=list[BusquedaSalida])
def busquedas(
    sin_autobus: bool = Query(False, description="Solo las que no encontraron camión (rutas que faltan)"),
    limite: int = Query(200, ge=1, le=1000),
    servicio: ServicioBusquedas = Depends(get_servicio),
):
    """Búsquedas de "¿Cómo llego?" 🔒 admin, de la más reciente a la más antigua."""
    return servicio.recientes(limite, sin_autobus)
