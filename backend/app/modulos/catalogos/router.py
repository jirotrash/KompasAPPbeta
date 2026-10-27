from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.modulos.catalogos.esquemas import CategoriaSalida, TransporteSalida
from app.modulos.catalogos.repositorio import RepositorioCatalogos
from app.modulos.catalogos.servicio import ServicioCatalogos
from app.nucleo.bd import get_bd

router = APIRouter(prefix="/api", tags=["Catálogos"])


def get_servicio(bd: Database = Depends(get_bd)) -> ServicioCatalogos:
    return ServicioCatalogos(RepositorioCatalogos(bd))


@router.get("/categorias", response_model=list[CategoriaSalida])
def categorias(servicio: ServicioCatalogos = Depends(get_servicio)):
    """Categorías de lugares. `clave` es el interés que usa la app (se deriva del nombre)."""
    return servicio.categorias()


@router.get("/transportes", response_model=list[TransporteSalida])
def transportes(servicio: ServicioCatalogos = Depends(get_servicio)):
    """Medios de movilidad. `clave` es el valor que usa la app (se deriva del nombre)."""
    return servicio.transportes()
