from fastapi import APIRouter, Depends, Query, status
from pymongo.database import Database

from app.modulos.reportes.esquemas import NuevoReporte, ReporteSalida
from app.modulos.reportes.repositorio import RepositorioReportes
from app.modulos.reportes.servicio import ServicioReportes
from app.nucleo.bd import get_bd
from app.nucleo.seguridad import get_usuario_actual

router = APIRouter(prefix="/api/reportes", tags=["Reportes"])


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
