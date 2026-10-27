from fastapi import APIRouter, Depends, Query
from pymongo.database import Database

from app.modulos.laboratorio.repositorio import RepositorioBitacora
from app.modulos.laboratorio.servicio import ServicioLaboratorio
from app.modulos.rutas.esquemas import ArbolRuta, RespuestaAlternativas, RutaSalida
from app.modulos.rutas.repositorio import RepositorioRutas
from app.modulos.rutas.servicio import ServicioRutas
from app.nucleo.bd import get_bd
from app.nucleo.errores import DatosInvalidos
from app.nucleo.parametros import punto_de_consulta
from app.nucleo.seguridad import requiere_admin

router = APIRouter(prefix="/api/rutas", tags=["Rutas"])


def get_servicio(bd: Database = Depends(get_bd)) -> ServicioRutas:
    return ServicioRutas(RepositorioRutas(bd), ServicioLaboratorio(RepositorioBitacora(bd)))


@router.get("", response_model=list[RutaSalida] | RespuestaAlternativas)
def rutas(
    origen: str | None = Query(None, description="lat,lng — solo lo usa la pantalla Buscar de la app"),
    destino: str | None = Query(None, description="lat,lng — solo lo usa la pantalla Buscar de la app"),
    hora: str | None = Query(None, description="HH:MM (se recibe, aún no se usa)"),
    servicio: ServicioRutas = Depends(get_servicio),
):
    """Sin parámetros: lista de rutas `[{id, trazo: [[lng, lat], ...]}]`.

    Con `origen` y `destino` (así llama la app al buscar un destino): opciones en autobús sobre los trazos
    de la colección `rutas` (directas o `tipo: "combinado"` con transbordo, con `parada_subida`,
    `parada_bajada`, `tramo_en_ruta` y `paradas_intermedias`), más a pie y en taxi/app estimadas por
    distancia. Si ninguna ruta conecta, `datos_suficientes` es `false` y no se inventa una ruta."""
    if origen is None and destino is None:
        return servicio.listar()
    if origen is None or destino is None:
        raise DatosInvalidos("Envía origen y destino juntos.")
    return servicio.alternativas(punto_de_consulta("origen", origen), punto_de_consulta("destino", destino))


@router.get("/{id_ruta}", response_model=RutaSalida)
def detalle(id_ruta: int, servicio: ServicioRutas = Depends(get_servicio)):
    """Una ruta con su `trazo` [[lng, lat], ...] para dibujarla en el mapa."""
    return servicio.detalle(id_ruta)


@router.get("/{id_ruta}/arbol", response_model=ArbolRuta, dependencies=[Depends(requiere_admin)])
def arbol(id_ruta: int, servicio: ServicioRutas = Depends(get_servicio)):
    """Árbol binario de paradas de la ruta 🔒 admin (sin pantalla: para pruebas y el manual técnico).
    Si la ruta no tiene paradas capturadas, se usan los puntos de su trazo ("Punto N")."""
    return servicio.arbol(id_ruta)
