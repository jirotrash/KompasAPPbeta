from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.esquemas.itinerarios import PeticionPlan, PlanGuardado, RespuestaPlanes
from app.ia.servicio import recomendar
from app.modelos import Categoria, Plan, Transporte, Usuario
from app.seguridad import get_usuario_actual
from app.servicios import consultas, google_places
from app.servicios.geo import ZONA, ahora_mexico, esta_dentro_de_zona
from app.servicios.traslados import radio_km

router = APIRouter(prefix="/api", tags=["Itinerarios (sistema experto)"])

# BACKEND.md §4: contexto → no_acompanantes
ACOMPANANTES = {"solo": 0, "pareja": 1, "amigos": 3, "familia": 3}


@router.post("/itinerarios", response_model=RespuestaPlanes)
def crear_itinerarios(peticion: PeticionPlan, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_actual)):
    """Botón **Crear mi plan** 🔒: busca lugares en Google Places, arma hasta 3 itinerarios y los evalúa con
    el sistema experto de Einar (`app.ia.servicio.recomendar` → `hechos.py` + `evaluar()`). Guarda el plan en
    `planes` y regresa los `recomendable` en `planes` (el de mayor puntuación es `mejor_opcion`) y el resto en
    `descartados` con su estado, reglas y datos faltantes. Si Google no responde: `503` (no se inventan lugares)."""
    origen = peticion.origen.model_dump()
    if not esta_dentro_de_zona(origen):
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

    try:
        lugares = google_places.buscar_para_plan(origen, peticion.intereses, radio_km(peticion.movilidad))
    except google_places.ErrorGooglePlaces as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error
    respuesta = recomendar(peticion.model_dump(), lugares, ahora_mexico())

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
