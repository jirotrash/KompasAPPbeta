from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.esquemas.lugares import LugarSalida
from app.routers._parametros import punto_de_consulta, punto_lat_lng
from app.servicios import consultas, serializar
from app.servicios.geo import distancia_km, minutos_caminando

router = APIRouter(prefix="/api/lugares", tags=["Lugares"])


@router.get("", response_model=list[LugarSalida])
def buscar_lugares(
    lat: float | None = Query(None, ge=-90, le=90),
    lng: float | None = Query(None, ge=-180, le=180),
    cerca: str | None = Query(None, description="lat,lng en un solo parámetro (así lo manda la app)", examples=["19.2926,-99.6557"]),
    radio_km: float | None = Query(None, gt=0, description="Sin radio se regresan todos, ordenados por distancia"),
    categoria: str | None = Query(None, description="Nombre (Café) o valor de la app (cafe)"),
    db: Session = Depends(get_db),
):
    """Lugares para "Cerca de ti" y el buscador, ordenados por distancia si se manda la ubicación.
    `minutos_caminando` es una estimación (≈ 12 min por km). Horario, costo, calificación y foto van
    en `null` porque la base todavía no los tiene."""
    origen = punto_lat_lng(lat, lng) or punto_de_consulta("cerca", cerca)
    lugares = consultas.lugares_como_dicts(db)

    if categoria:
        buscada = serializar.clave(categoria)
        lugares = [l for l in lugares if l["categoria"] and serializar.clave(l["categoria"]) == buscada]
    if origen:
        for l in lugares:
            km = distancia_km(origen, {"lat": l["lat"], "lng": l["lng"]})
            l["distancia_km"] = round(km, 2)
            l["minutos_caminando"] = minutos_caminando(km)
        if radio_km:
            lugares = [l for l in lugares if l["distancia_km"] <= radio_km]
        lugares.sort(key=lambda l: l["distancia_km"])
    return lugares


@router.get("/{id_lugar}", response_model=LugarSalida)
def detalle_lugar(id_lugar: int, db: Session = Depends(get_db)):
    lugar = consultas.lugar_por_id(db, id_lugar)
    if lugar is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No encontramos ese lugar.")
    return serializar.lugar(lugar)
