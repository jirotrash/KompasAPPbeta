from fastapi import APIRouter, Depends, status
from pymongo.database import Database

from app.modulos.catalogos.repositorio import RepositorioCatalogos
from app.modulos.catalogos.servicio import ServicioCatalogos
from app.modulos.historial.esquemas import NuevoRecorrido, RecorridoSalida
from app.modulos.historial.repositorio import RepositorioHistorial
from app.modulos.historial.servicio import ServicioHistorial
from app.modulos.rutas.repositorio import RepositorioRutas
from app.modulos.rutas.servicio import ServicioRutas
from app.nucleo.bd import get_bd
from app.nucleo.seguridad import get_usuario_actual

router = APIRouter(prefix="/api/historial", tags=["Historial"])


def get_servicio(bd: Database = Depends(get_bd)) -> ServicioHistorial:
    return ServicioHistorial(
        RepositorioHistorial(bd), ServicioRutas(RepositorioRutas(bd)), ServicioCatalogos(RepositorioCatalogos(bd))
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=RecorridoSalida)
def guardar_recorrido(
    datos: NuevoRecorrido, servicio: ServicioHistorial = Depends(get_servicio), usuario: dict = Depends(get_usuario_actual)
):
    """Guarda un recorrido que el usuario inició 🔒 (`tiempo_estimado` en minutos)."""
    return servicio.guardar(usuario, datos.id_ruta, datos.id_transporte, datos.tiempo_estimado)


@router.get("", response_model=list[RecorridoSalida])
def mis_recorridos(servicio: ServicioHistorial = Depends(get_servicio), usuario: dict = Depends(get_usuario_actual)):
    """Recorridos del usuario 🔒, del más reciente al más antiguo."""
    return servicio.del_usuario(usuario)
