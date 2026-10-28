from fastapi import APIRouter, Depends, Response, status
from pymongo.database import Database

from app.modulos.catalogos.esquemas import (
    CategoriaAdmin,
    CategoriaEntrada,
    CategoriaSalida,
    TransporteAdmin,
    TransporteEntrada,
    TransporteSalida,
)
from app.modulos.catalogos.repositorio import RepositorioCatalogos
from app.modulos.catalogos.servicio import ServicioCatalogos
from app.nucleo.bd import get_bd
from app.nucleo.seguridad import requiere_admin

router = APIRouter(prefix="/api", tags=["Catálogos"])
router_admin = APIRouter(prefix="/api/admin", tags=["Administración"], dependencies=[Depends(requiere_admin)])


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


# ─────────────────────────── Panel de administración 🔒 admin ───────────────────────────
# `protegida: true` = la usan la app y el sistema experto: no se borra ni cambia de clave (409).


@router_admin.get("/categorias", response_model=list[CategoriaAdmin])
def categorias_admin(servicio: ServicioCatalogos = Depends(get_servicio)):
    return servicio.categorias_admin()


@router_admin.post("/categorias", status_code=status.HTTP_201_CREATED, response_model=CategoriaAdmin)
def crear_categoria(datos: CategoriaEntrada, servicio: ServicioCatalogos = Depends(get_servicio)):
    return servicio.guardar_categoria(datos.model_dump())


@router_admin.put("/categorias/{id_categoria}", response_model=CategoriaAdmin)
def editar_categoria(id_categoria: int, datos: CategoriaEntrada, servicio: ServicioCatalogos = Depends(get_servicio)):
    """El nuevo nombre también se copia a los lugares de esa categoría."""
    return servicio.guardar_categoria(datos.model_dump(), id_categoria)


@router_admin.delete("/categorias/{id_categoria}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_categoria(id_categoria: int, servicio: ServicioCatalogos = Depends(get_servicio)):
    """409 si está protegida o si todavía hay lugares con esa categoría."""
    servicio.borrar_categoria(id_categoria)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router_admin.get("/transportes", response_model=list[TransporteAdmin])
def transportes_admin(servicio: ServicioCatalogos = Depends(get_servicio)):
    return servicio.transportes_admin()


@router_admin.post("/transportes", status_code=status.HTTP_201_CREATED, response_model=TransporteAdmin)
def crear_transporte(datos: TransporteEntrada, servicio: ServicioCatalogos = Depends(get_servicio)):
    return servicio.guardar_transporte(datos.model_dump())


@router_admin.put("/transportes/{id_transporte}", response_model=TransporteAdmin)
def editar_transporte(id_transporte: int, datos: TransporteEntrada, servicio: ServicioCatalogos = Depends(get_servicio)):
    return servicio.guardar_transporte(datos.model_dump(), id_transporte)


@router_admin.delete("/transportes/{id_transporte}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_transporte(id_transporte: int, servicio: ServicioCatalogos = Depends(get_servicio)):
    """409 si está protegido. El historial que lo usa se conserva."""
    servicio.borrar_transporte(id_transporte)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
