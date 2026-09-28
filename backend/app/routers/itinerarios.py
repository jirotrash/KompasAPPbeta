from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.esquemas.itinerarios import PeticionPlan, PlanGuardado, RespuestaPlanes
from app.ia.motor import recomendar
from app.modelos import Categoria, Plan, Transporte, Usuario
from app.seguridad import get_usuario_actual
from app.servicios import consultas
from app.servicios.geo import ZONA, ahora_mexico, esta_dentro_de_zona

router = APIRouter(prefix="/api", tags=["Itinerarios (sistema experto)"])

# BACKEND.md §4: contexto → no_acompanantes
ACOMPANANTES = {"solo": 0, "pareja": 1, "amigos": 3, "familia": 3}


@router.post("/itinerarios", response_model=RespuestaPlanes)
def crear_itinerarios(peticion: PeticionPlan, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_actual)):
    """Botón **Crear mi plan** 🔒: carga los lugares, llama al sistema experto (`app.ia.motor.recomendar`),
    guarda el plan en `planes` y regresa hasta 2 planes (equilibrado y rápido) con explicación, más los
    lugares descartados con la regla que los descartó. Sin datos suficientes: `planes = []` y `aviso`."""
    if not esta_dentro_de_zona(peticion.origen.model_dump()):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, f"El punto de partida está fuera de la zona piloto ({ZONA['nombre']})."
        )

    # Se busca antes de llamar al motor: si faltan en la BD, es un error de datos y no se debe responder a medias
    categoria = consultas.por_clave(db, Categoria, peticion.intereses[0])
    transporte = consultas.por_clave(db, Transporte, peticion.movilidad[0])
    if categoria is None or transporte is None:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Faltan categorías o transportes en la base de datos. Carga database/datos_desarrollo.sql.",
        )

    solicitud = peticion.model_dump()
    lugares = consultas.lugares_como_dicts(db)
    if lugares:
        respuesta = recomendar(solicitud, lugares)
    else:
        aviso = "No tenemos información suficiente: aún no hay lugares registrados en la zona."
        respuesta = {"datos_suficientes": False, "mensaje": aviso, "aviso": aviso, "planes": [], "descartados": []}

    hora, minuto = (int(x) for x in peticion.hora_salida.split(":"))
    db.add(
        Plan(
            id_usuario=usuario.id_usuario,
            no_acompanantes=ACOMPANANTES[peticion.contexto],
            tiempo_disponible=round(peticion.tiempo_horas * 60),
            id_categoria=categoria.id_categoria,
            id_transporte=transporte.id_transporte,
            fecha_plan=datetime.combine(ahora_mexico().date(), datetime.min.time()).replace(hour=hora, minute=minuto),
        )
    )
    db.commit()
    return respuesta


@router.get("/planes", response_model=list[PlanGuardado])
def mis_planes(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_actual)):
    """Planes que ha creado el usuario 🔒 (tabla `planes`), del más reciente al más antiguo."""
    consulta = (
        select(Plan)
        .where(Plan.id_usuario == usuario.id_usuario, Plan.deleted_at.is_(None))
        .order_by(Plan.id_plan.desc())
    )
    return [
        PlanGuardado(
            id=p.id_plan,
            no_acompanantes=p.no_acompanantes,
            tiempo_disponible=p.tiempo_disponible,
            categoria=p.categoria.nombre,
            transporte=p.transporte.nombre,
            fecha_plan=p.fecha_plan,
            creado_en=p.created_at,
        )
        for p in db.scalars(consulta)
    ]
