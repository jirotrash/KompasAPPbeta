"""GET /api/dashboard/* — estadísticas para la web. Todos piden rol admin (403 para un usuario normal)."""

from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from pymongo.database import Database

from app.modulos.catalogos.repositorio import RepositorioCatalogos
from app.modulos.catalogos.servicio import ServicioCatalogos
from app.modulos.dashboard import esquemas
from app.modulos.dashboard.repositorio import RepositorioDashboard
from app.modulos.dashboard.servicio import Rango, ServicioDashboard
from app.nucleo.bd import get_bd
from app.nucleo.seguridad import requiere_admin

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"], dependencies=[Depends(requiere_admin)])


def get_servicio(bd: Database = Depends(get_bd)) -> ServicioDashboard:
    return ServicioDashboard(RepositorioDashboard(bd), ServicioCatalogos(RepositorioCatalogos(bd)))


def get_rango(
    desde: date | None = Query(None, description="YYYY-MM-DD. Por defecto, 30 días antes de `hasta`"),
    hasta: date | None = Query(None, description="YYYY-MM-DD, incluye el día completo. Por defecto, hoy"),
    incluir_demo: bool = Query(True, description="false = no cuenta documentos con demo: true"),
) -> Rango:
    return Rango(desde, hasta, incluir_demo)


@router.get("/kpis", response_model=esquemas.Kpis)
def kpis(rango: Rango = Depends(get_rango), servicio: ServicioDashboard = Depends(get_servicio)):
    """Tarjetas del resumen: usuarios, planes, % con recomendación, recorridos, reportes vigentes y lugares."""
    return servicio.kpis(rango)


@router.get("/series", response_model=esquemas.Series)
def series(
    agrupar: Literal["dia", "semana", "mes"] = Query("dia"),
    rango: Rango = Depends(get_rango),
    servicio: ServicioDashboard = Depends(get_servicio),
):
    """Usuarios nuevos, planes y recorridos por periodo ($dateTrunc); los periodos sin datos van en 0."""
    return servicio.series(rango, agrupar)


@router.get("/planes", response_model=esquemas.Planes)
def planes(rango: Rango = Depends(get_rango), servicio: ServicioDashboard = Depends(get_servicio)):
    """Intereses, movilidad, contexto, histogramas de presupuesto y tiempo, día × hora y perfil por contexto ($facet)."""
    return servicio.planes(rango)


@router.get("/sistema-experto", response_model=esquemas.SistemaExperto)
def sistema_experto(rango: Rango = Depends(get_rango), servicio: ServicioDashboard = Depends(get_servicio)):
    """Cómo decide el sistema experto: estados, reglas más activadas y puntuación por tipo de plan."""
    return servicio.sistema_experto(rango)


@router.get("/movilidad", response_model=esquemas.Movilidad)
def movilidad(rango: Rango = Depends(get_rango), servicio: ServicioDashboard = Depends(get_servicio)):
    """Recorridos por transporte (total, promedio, mínimo y máximo de minutos) y rutas más usadas."""
    return servicio.movilidad(rango)


@router.get("/reportes", response_model=esquemas.Reportes)
def reportes(rango: Rango = Depends(get_rango), servicio: ServicioDashboard = Depends(get_servicio)):
    """Reportes por tipo y estado, vigentes contra vencidos y puntos para el mapa."""
    return servicio.reportes(rango)


@router.get("/lugares", response_model=esquemas.Lugares)
def lugares(rango: Rango = Depends(get_rango), servicio: ServicioDashboard = Depends(get_servicio)):
    """Lugares por categoría y puntos para el mapa (catálogo completo, sin filtro de fechas)."""
    return servicio.lugares(rango)


@router.get("/laboratorio", response_model=esquemas.Laboratorio)
def laboratorio(rango: Rango = Depends(get_rango), servicio: ServicioDashboard = Depends(get_servicio)):
    """Uso de las demostraciones académicas: DFS (nodos vs. límite) y distancias Euclidiana vs. Manhattan."""
    return servicio.laboratorio(rango)
