from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.esquemas.catalogos import CategoriaSalida, TransporteSalida
from app.modelos import Categoria, Transporte
from app.servicios.serializar import clave

router = APIRouter(prefix="/api", tags=["Catálogos"])


@router.get("/categorias", response_model=list[CategoriaSalida])
def categorias(db: Session = Depends(get_db)):
    """Categorías de lugares. `clave` es el interés que usa la app (se deriva del nombre)."""
    filas = db.scalars(select(Categoria).where(Categoria.deleted_at.is_(None)).order_by(Categoria.id_categoria))
    return [CategoriaSalida(id=c.id_categoria, nombre=c.nombre, descripcion=c.descripcion, clave=clave(c.nombre)) for c in filas]


@router.get("/transportes", response_model=list[TransporteSalida])
def transportes(db: Session = Depends(get_db)):
    """Medios de movilidad. `clave` es el valor que usa la app (se deriva del nombre)."""
    filas = db.scalars(select(Transporte).where(Transporte.deleted_at.is_(None)).order_by(Transporte.id_transporte))
    return [TransporteSalida(id=t.id_transporte, nombre=t.nombre, clave=clave(t.nombre)) for t in filas]
