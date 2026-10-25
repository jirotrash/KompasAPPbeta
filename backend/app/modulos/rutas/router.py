from fastapi import APIRouter, Depends, Query
from pymongo.database import Database

from app.modulos.rutas.esquemas import RespuestaAlternativas, RutaSalida
from app.modulos.rutas.repositorio import RepositorioRutas
from app.modulos.rutas.servicio import ServicioRutas
from app.nucleo.bd import get_bd
from app.nucleo.errores import DatosInvalidos
from app.nucleo.parametros import punto_de_consulta

router = APIRouter(prefix="/api/rutas", tags=["Rutas"])


def get_servicio(bd: Database = Depends(get_bd)) -> ServicioRutas:
    return ServicioRutas(RepositorioRutas(bd))


@router.get("", response_model=list[RutaSalida] | RespuestaAlternativas)
def rutas(
    origen: str | None = Query(None, description="lat,lng — solo lo usa la pantalla Buscar de la app"),
    destino: str | None = Query(None, description="lat,lng — solo lo usa la pantalla Buscar de la app"),
    hora: str | None = Query(None, description="HH:MM (se recibe, aún no se usa)"),
    servicio: ServicioRutas = Depends(get_servicio),
):
    """Sin parámetros: lista de rutas `[{id, trazo: [[lng, lat], ...]}]`.

    Con `origen` y `destino` (así llama la app al buscar un destino): alternativas a pie y en
    taxi/app estimadas por distancia. No hay alternativas en autobús porque la base todavía no tiene
    líneas ni paradas, así que `datos_suficientes` es `false`."""
    if origen is None and destino is None:
        return servicio.listar()
    if origen is None or destino is None:
        raise DatosInvalidos("Envía origen y destino juntos.")
    return servicio.alternativas(punto_de_consulta("origen", origen), punto_de_consulta("destino", destino))


@router.get("/{id_ruta}", response_model=RutaSalida)
def detalle(id_ruta: int, servicio: ServicioRutas = Depends(get_servicio)):
    """Una ruta con su `trazo` [[lng, lat], ...] para dibujarla en el mapa."""
    return servicio.detalle(id_ruta)
