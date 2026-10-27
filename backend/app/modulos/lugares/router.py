from fastapi import APIRouter, Depends, Query
from pymongo.database import Database

from app.modulos.lugares.esquemas import LugarSalida
from app.modulos.lugares.repositorio import RepositorioLugares
from app.modulos.lugares.servicio import ServicioLugares
from app.nucleo.bd import get_bd
from app.nucleo.parametros import punto_de_consulta, punto_lat_lng

router = APIRouter(prefix="/api/lugares", tags=["Lugares"])


def get_servicio(bd: Database = Depends(get_bd)) -> ServicioLugares:
    return ServicioLugares(RepositorioLugares(bd))


@router.get("", response_model=list[LugarSalida])
def buscar_lugares(
    lat: float | None = Query(None, ge=-90, le=90),
    lng: float | None = Query(None, ge=-180, le=180),
    cerca: str | None = Query(None, description="lat,lng en un solo parámetro (así lo manda la app)", examples=["19.2926,-99.6557"]),
    radio_km: float | None = Query(None, gt=0, description="Sin radio se regresan todos, ordenados por distancia"),
    categoria: str | None = Query(None, description="Nombre (Café) o valor de la app (cafe)"),
    servicio: ServicioLugares = Depends(get_servicio),
):
    """Lugares para "Cerca de ti" y el buscador, ordenados por distancia si se manda la ubicación.
    `minutos_caminando` es una estimación (≈ 12 min por km). Horario, costo, calificación y foto van
    en `null` porque la base todavía no los tiene."""
    origen = punto_lat_lng(lat, lng) or punto_de_consulta("cerca", cerca)
    return servicio.buscar(origen, radio_km, categoria)


@router.get("/{id_lugar}", response_model=LugarSalida)
def detalle_lugar(id_lugar: int, servicio: ServicioLugares = Depends(get_servicio)):
    return servicio.detalle(id_lugar)
