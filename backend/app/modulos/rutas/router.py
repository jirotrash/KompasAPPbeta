from fastapi import APIRouter, Depends, Query, Response, status
from pymongo.database import Database

from app.modulos.busquedas.repositorio import RepositorioBusquedas
from app.modulos.busquedas.servicio import ServicioBusquedas
from app.modulos.laboratorio.repositorio import RepositorioBitacora
from app.modulos.laboratorio.servicio import ServicioLaboratorio
from app.modulos.rutas.esquemas import ArbolRuta, RespuestaAlternativas, RutaEntrada, RutaSalida
from app.modulos.rutas.repositorio import RepositorioRutas
from app.modulos.rutas.servicio import ServicioRutas
from app.nucleo.bd import get_bd
from app.nucleo.errores import DatosInvalidos
from app.nucleo.parametros import punto_de_consulta
from app.nucleo.seguridad import get_usuario_opcional, requiere_admin

router = APIRouter(prefix="/api/rutas", tags=["Rutas"])
router_admin = APIRouter(prefix="/api/admin/rutas", tags=["Administración"], dependencies=[Depends(requiere_admin)])


def get_servicio(bd: Database = Depends(get_bd)) -> ServicioRutas:
    return ServicioRutas(
        RepositorioRutas(bd), ServicioLaboratorio(RepositorioBitacora(bd)), ServicioBusquedas(RepositorioBusquedas(bd))
    )


@router.get("", response_model=list[RutaSalida] | RespuestaAlternativas)
def rutas(
    origen: str | None = Query(None, description="lat,lng — solo lo usa la pantalla Buscar de la app"),
    destino: str | None = Query(None, description="lat,lng — solo lo usa la pantalla Buscar de la app"),
    hora: str | None = Query(None, description="HH:MM (se recibe, aún no se usa)"),
    servicio: ServicioRutas = Depends(get_servicio),
    usuario: dict | None = Depends(get_usuario_opcional),
):
    """Sin parámetros: lista de rutas `[{id, trazo: [[lng, lat], ...]}]`.

    Con `origen` y `destino` (así llama la app al buscar un destino): opciones en autobús sobre los trazos
    de la colección `rutas` (directas o `tipo: "combinado"` con transbordo, con `parada_subida`,
    `parada_bajada`, `tramo_en_ruta` y `paradas_intermedias`), más a pie y en taxi/app estimadas por
    distancia. Si ninguna ruta conecta, `datos_suficientes` es `false` y no se inventa una ruta.
    La búsqueda se guarda en `busquedas` (con el usuario si manda su token) para el panel."""
    if origen is None and destino is None:
        return servicio.listar()
    if origen is None or destino is None:
        raise DatosInvalidos("Envía origen y destino juntos.")
    return servicio.alternativas(punto_de_consulta("origen", origen), punto_de_consulta("destino", destino), usuario)


@router.get("/{id_ruta}", response_model=RutaSalida)
def detalle(id_ruta: int, servicio: ServicioRutas = Depends(get_servicio)):
    """Una ruta con su `trazo` [[lng, lat], ...] para dibujarla en el mapa."""
    return servicio.detalle(id_ruta)


@router.get("/{id_ruta}/arbol", response_model=ArbolRuta, dependencies=[Depends(requiere_admin)])
def arbol(id_ruta: int, servicio: ServicioRutas = Depends(get_servicio)):
    """Árbol binario de paradas de la ruta 🔒 admin (sin pantalla: para pruebas y el manual técnico).
    Si la ruta no tiene paradas capturadas, se usan los puntos de su trazo ("Punto N")."""
    return servicio.arbol(id_ruta)


# ─────────────────────────── Panel de administración 🔒 admin ───────────────────────────


@router_admin.get("", response_model=list[RutaSalida])
def rutas_admin(servicio: ServicioRutas = Depends(get_servicio)):
    """Todas las rutas con su nombre, trazo y paradas."""
    return servicio.listar()


@router_admin.post("", status_code=status.HTTP_201_CREATED, response_model=RutaSalida)
def crear_ruta(datos: RutaEntrada, servicio: ServicioRutas = Depends(get_servicio)):
    """Da de alta una ruta: nombre, trazo en el sentido en que circula y paradas (opcionales).
    422 si algún punto está fuera de la zona piloto."""
    return servicio.crear(datos.model_dump())


@router_admin.put("/{id_ruta}", response_model=RutaSalida)
def editar_ruta(id_ruta: int, datos: RutaEntrada, servicio: ServicioRutas = Depends(get_servicio)):
    """Reemplaza nombre, trazo y paradas de la ruta."""
    return servicio.actualizar(id_ruta, datos.model_dump())


@router_admin.delete("/{id_ruta}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_ruta(id_ruta: int, servicio: ServicioRutas = Depends(get_servicio)):
    """Borrado lógico: deja de sugerirse en la app; el historial que la usa se conserva."""
    servicio.borrar(id_ruta)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
