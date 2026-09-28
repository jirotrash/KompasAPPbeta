from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.esquemas.historial import NuevoRecorrido, RecorridoSalida
from app.modelos import HistorialRuta, Transporte, Usuario
from app.seguridad import get_usuario_actual
from app.servicios import consultas

router = APIRouter(prefix="/api/historial", tags=["Historial"])


def _salida(h: HistorialRuta) -> RecorridoSalida:
    return RecorridoSalida(
        id=h.id_historial,
        id_ruta=h.id_ruta,
        id_transporte=h.id_transporte,
        transporte=h.transporte.nombre,
        tiempo_estimado=h.tiempo_estimado,
        creado_en=h.created_at,
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=RecorridoSalida)
def guardar_recorrido(datos: NuevoRecorrido, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_actual)):
    """Guarda un recorrido que el usuario inició 🔒 (`tiempo_estimado` en minutos)."""
    if consultas.ruta_por_id(db, datos.id_ruta) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No encontramos esa ruta.")
    transporte = db.get(Transporte, datos.id_transporte)
    if transporte is None or transporte.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No encontramos ese medio de transporte.")

    recorrido = HistorialRuta(
        id_usuario=usuario.id_usuario,
        id_ruta=datos.id_ruta,
        id_transporte=datos.id_transporte,
        tiempo_estimado=datos.tiempo_estimado,
    )
    db.add(recorrido)
    db.commit()
    db.refresh(recorrido)
    return _salida(recorrido)


@router.get("", response_model=list[RecorridoSalida])
def mis_recorridos(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_actual)):
    """Recorridos del usuario 🔒, del más reciente al más antiguo."""
    consulta = (
        select(HistorialRuta)
        .where(HistorialRuta.id_usuario == usuario.id_usuario, HistorialRuta.deleted_at.is_(None))
        .order_by(HistorialRuta.id_historial.desc())
    )
    return [_salida(h) for h in db.scalars(consulta)]
