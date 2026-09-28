from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.esquemas.rutas import RespuestaAlternativas, RutaSalida
from app.routers._parametros import punto_de_consulta
from app.servicios import consultas, serializar
from app.servicios.geo import (
    ESPERA_TAXI_MIN,
    FACTOR_CALLES,
    VELOCIDAD_AUTO_KMH,
    distancia_km,
    esta_dentro_de_zona,
    minutos_caminando,
    redondear,
)

router = APIRouter(prefix="/api/rutas", tags=["Rutas"])

FUENTE_ESTIMACION = "Estimación por distancia"
SIN_AUTOBUS = "No tenemos información suficiente de transporte público para esta ruta."
AVISOS_AUTO = ["El tiempo no considera el tráfico.", "La tarifa la define el proveedor; consúltala en su app o con el conductor."]


@router.get("", response_model=list[RutaSalida] | RespuestaAlternativas)
def rutas(
    origen: str | None = Query(None, description="lat,lng — solo lo usa la pantalla Buscar de la app"),
    destino: str | None = Query(None, description="lat,lng — solo lo usa la pantalla Buscar de la app"),
    hora: str | None = Query(None, description="HH:MM (se recibe, aún no se usa)"),
    db: Session = Depends(get_db),
):
    """Sin parámetros: lista de rutas `[{id, trazo: [[lng, lat], ...]}]`.

    Con `origen` y `destino` (así llama la app al buscar un destino): alternativas a pie y en
    taxi/app estimadas por distancia. No hay alternativas en autobús porque la base todavía no tiene
    líneas ni paradas, así que `datos_suficientes` es `false`."""
    if origen is None and destino is None:
        return [serializar.ruta(r) for r in consultas.rutas(db)]
    if origen is None or destino is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Envía origen y destino juntos.")

    a = punto_de_consulta("origen", origen)
    b = punto_de_consulta("destino", destino)
    if not (esta_dentro_de_zona(a) and esta_dentro_de_zona(b)):
        return {
            "datos_suficientes": False,
            "mensaje": "El origen o el destino está fuera de la zona piloto (Toluca, Lerma y San Mateo Atenco).",
            "alternativas": [],
        }

    km = round(distancia_km(a, b) * FACTOR_CALLES, 2)
    pie = {
        "id": "pie",
        "modo": "pie",
        "distancia_km": km,
        "tiempos": {"caminata": minutos_caminando(km), "espera": None, "trayecto": None},
        "fuente": FUENTE_ESTIMACION,
        "avisos": ["Trayecto largo para hacerlo a pie."] if km > 4 else [],
    }

    def auto(modo: str) -> dict:
        return {
            "id": modo,
            "modo": modo,
            "distancia_km": km,
            "tiempos": {"caminata": None, "espera": ESPERA_TAXI_MIN, "trayecto": redondear(km / VELOCIDAD_AUTO_KMH * 60)},
            "fuente": FUENTE_ESTIMACION,
            "avisos": AVISOS_AUTO,
        }

    return {"datos_suficientes": False, "mensaje": SIN_AUTOBUS, "alternativas": [pie, auto("taxi"), auto("app")]}


@router.get("/{id_ruta}", response_model=RutaSalida)
def detalle(id_ruta: int, db: Session = Depends(get_db)):
    """Una ruta con su `trazo` [[lng, lat], ...] para dibujarla en el mapa."""
    ruta = consultas.ruta_por_id(db, id_ruta)
    if ruta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No encontramos esa ruta.")
    return serializar.ruta(ruta)
