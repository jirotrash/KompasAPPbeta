from fastapi import APIRouter, Depends, Query, Response, status
from pymongo.database import Database

from app.modulos.solicitudes.esquemas import CambioSolicitud, EstadoSolicitud, NuevaSolicitud, SolicitudSalida
from app.modulos.solicitudes.repositorio import RepositorioSolicitudes
from app.modulos.solicitudes.servicio import ServicioSolicitudes
from app.nucleo.bd import get_bd
from app.nucleo.seguridad import get_usuario_actual, requiere_admin

router = APIRouter(prefix="/api/solicitudes-rutas", tags=["Solicitudes de rutas"])
router_admin = APIRouter(
    prefix="/api/admin/solicitudes-rutas", tags=["Administración"], dependencies=[Depends(requiere_admin)]
)


def get_servicio(bd: Database = Depends(get_bd)) -> ServicioSolicitudes:
    return ServicioSolicitudes(RepositorioSolicitudes(bd))


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SolicitudSalida)
def pedir_ruta(
    datos: NuevaSolicitud, servicio: ServicioSolicitudes = Depends(get_servicio), usuario: dict = Depends(get_usuario_actual)
):
    """Pide que se agregue una ruta entre dos puntos 🔒 (la app lo ofrece cuando no encontró camión).
    Queda `pendiente` hasta que el equipo la atienda en el panel. 422 si algún punto está fuera de la zona piloto."""
    return servicio.crear(usuario, datos.model_dump())


@router.get("", response_model=list[SolicitudSalida])
def mis_solicitudes(servicio: ServicioSolicitudes = Depends(get_servicio), usuario: dict = Depends(get_usuario_actual)):
    """Solicitudes del usuario 🔒 con su estado, de la más reciente a la más antigua."""
    return servicio.del_usuario(usuario)


# ─────────────────────────── Panel de administración 🔒 admin ───────────────────────────


@router_admin.get("", response_model=list[SolicitudSalida])
def solicitudes(
    estado: EstadoSolicitud | None = Query(None),
    limite: int = Query(300, ge=1, le=2000),
    servicio: ServicioSolicitudes = Depends(get_servicio),
):
    return servicio.recientes(limite, estado)


@router_admin.patch("/{id_solicitud}", response_model=SolicitudSalida)
def atender(id_solicitud: str, datos: CambioSolicitud, servicio: ServicioSolicitudes = Depends(get_servicio)):
    """Cambia el estado (`atendida` cuando ya se dio de alta la ruta, `descartada` si no procede) y deja una nota."""
    return servicio.actualizar(id_solicitud, datos.model_dump())


@router_admin.delete("/{id_solicitud}", status_code=status.HTTP_204_NO_CONTENT)
def borrar(id_solicitud: str, servicio: ServicioSolicitudes = Depends(get_servicio)):
    servicio.borrar(id_solicitud)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
