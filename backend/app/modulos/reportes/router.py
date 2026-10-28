from fastapi import APIRouter, Depends, Query, Response, status
from pymongo.database import Database

from app.modulos.reportes.esquemas import CambioEstadoReporte, EstadoReporte, NuevoReporte, ReporteAdmin, ReporteSalida
from app.modulos.reportes.repositorio import RepositorioReportes
from app.modulos.reportes.servicio import ServicioReportes
from app.nucleo.bd import get_bd
from app.nucleo.seguridad import get_usuario_actual, requiere_admin

router = APIRouter(prefix="/api/reportes", tags=["Reportes"])
router_admin = APIRouter(prefix="/api/admin/reportes", tags=["Administración"], dependencies=[Depends(requiere_admin)])


def get_servicio(bd: Database = Depends(get_bd)) -> ServicioReportes:
    return ServicioReportes(RepositorioReportes(bd))


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ReporteSalida, response_model_exclude_none=True)
def crear_reporte(
    datos: NuevoReporte, servicio: ServicioReportes = Depends(get_servicio), usuario: dict = Depends(get_usuario_actual)
):
    """Crea un reporte comunitario 🔒. La API calcula `vigente_hasta` según el tipo (cierre total 6 h,
    accidente 2 h, manifestación 3 h, afluencia 1 h) y lo deja `pendiente` con 0 confirmaciones.
    422 si la ubicación está fuera de la zona piloto."""
    return servicio.crear(usuario, datos.model_dump())


@router.get("", response_model=list[ReporteSalida], response_model_exclude_none=True)
def reportes_vigentes(
    ruta_id: str | None = Query(None, description="Solo los de esa ruta"),
    servicio: ServicioReportes = Depends(get_servicio),
):
    """Reportes vigentes (`vigente_hasta` posterior a ahora). Sin `ruta_id`: todos los de la zona."""
    return servicio.vigentes(ruta_id)


# ─────────────────────────── Panel de administración 🔒 admin ───────────────────────────


@router_admin.get("", response_model=list[ReporteAdmin], response_model_exclude_none=True)
def reportes_admin(
    estado: EstadoReporte | None = Query(None),
    limite: int = Query(300, ge=1, le=2000),
    servicio: ServicioReportes = Depends(get_servicio),
):
    """Todos los reportes (vigentes y vencidos), del más reciente al más antiguo."""
    return servicio.recientes(limite, estado)


@router_admin.patch("/{id_reporte}", response_model=ReporteAdmin, response_model_exclude_none=True)
def moderar_reporte(id_reporte: str, datos: CambioEstadoReporte, servicio: ServicioReportes = Depends(get_servicio)):
    """Marca el reporte como `verificado` o `descartado` (o lo regresa a `pendiente`)."""
    return servicio.cambiar_estado(id_reporte, datos.estado)


@router_admin.delete("/{id_reporte}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_reporte(id_reporte: str, servicio: ServicioReportes = Depends(get_servicio)):
    """Lo borra de la base (también deja de contarse en el dashboard). Para conservarlo, márcalo `descartado`."""
    servicio.borrar(id_reporte)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
