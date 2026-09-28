"""Consultas que comparten varios routers. Todas filtran el borrado lógico (deleted_at IS NULL)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import modelos
from app.servicios import serializar


def lugares_como_dicts(db: Session) -> list[dict]:
    consulta = select(modelos.Lugar).where(modelos.Lugar.deleted_at.is_(None)).order_by(modelos.Lugar.id_lugar)
    return [serializar.lugar(l) for l in db.scalars(consulta)]


def lugar_por_id(db: Session, id_lugar: int) -> modelos.Lugar | None:
    l = db.get(modelos.Lugar, id_lugar)
    return l if l is not None and l.deleted_at is None else None


def rutas(db: Session) -> list[modelos.Ruta]:
    consulta = select(modelos.Ruta).where(modelos.Ruta.deleted_at.is_(None)).order_by(modelos.Ruta.id_ruta)
    return list(db.scalars(consulta))


def ruta_por_id(db: Session, id_ruta: int) -> modelos.Ruta | None:
    r = db.get(modelos.Ruta, id_ruta)
    return r if r is not None and r.deleted_at is None else None


def por_clave(db: Session, modelo: type[modelos.Categoria] | type[modelos.Transporte], valor: str):
    """Busca en un catálogo por el valor de la app ("cafe" → fila "Café")."""
    filas = db.scalars(select(modelo).where(modelo.deleted_at.is_(None)))
    return next((f for f in filas if serializar.clave(f.nombre) == valor), None)
