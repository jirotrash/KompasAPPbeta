from fastapi import APIRouter, Depends, Response, status
from pymongo.database import Database

from app.modulos.asistente.esquemas import Conversacion, ConversacionResumen, EstadoAsistente, MensajeEntrada, RespuestaMensaje
from app.modulos.asistente.repositorio import RepositorioConversaciones
from app.modulos.asistente.servicio import ServicioAsistente
from app.modulos.catalogos.repositorio import RepositorioCatalogos
from app.modulos.catalogos.servicio import ServicioCatalogos
from app.modulos.itinerarios.repositorio import RepositorioPlanes
from app.modulos.itinerarios.servicio import ServicioItinerarios
from app.modulos.laboratorio.repositorio import RepositorioBitacora
from app.modulos.laboratorio.servicio import ServicioLaboratorio
from app.modulos.lugares.repositorio import RepositorioLugares
from app.modulos.lugares.servicio import ServicioLugares
from app.modulos.rutas.repositorio import RepositorioRutas
from app.modulos.rutas.servicio import ServicioRutas
from app.nucleo.bd import get_bd
from app.nucleo.seguridad import get_usuario_actual

router = APIRouter(prefix="/api/asistente", tags=["Asistente (Ollama)"])


def get_servicio(bd: Database = Depends(get_bd)) -> ServicioAsistente:
    bitacora = ServicioLaboratorio(RepositorioBitacora(bd))
    return ServicioAsistente(
        RepositorioConversaciones(bd),
        ServicioLugares(RepositorioLugares(bd)),
        ServicioRutas(RepositorioRutas(bd), bitacora),
        ServicioItinerarios(RepositorioPlanes(bd), ServicioCatalogos(RepositorioCatalogos(bd)), bitacora),
    )


@router.get("/estado", response_model=EstadoAsistente)
def estado(_: dict = Depends(get_usuario_actual)):
    """🔒 Hace ping a Ollama. `disponible` es false si Ollama no está abierto o no tiene el modelo."""
    return ServicioAsistente.estado()


@router.post("/conversaciones", response_model=Conversacion, status_code=status.HTTP_201_CREATED)
def crear(servicio: ServicioAsistente = Depends(get_servicio), usuario: dict = Depends(get_usuario_actual)):
    """🔒 Crea una conversación vacía."""
    return servicio.crear(usuario)


@router.get("/conversaciones", response_model=list[ConversacionResumen])
def listar(servicio: ServicioAsistente = Depends(get_servicio), usuario: dict = Depends(get_usuario_actual)):
    """🔒 Conversaciones del usuario, de la más reciente a la más antigua."""
    return servicio.listar(usuario)


@router.get("/conversaciones/{id_conversacion}", response_model=Conversacion)
def detalle(id_conversacion: str, servicio: ServicioAsistente = Depends(get_servicio), usuario: dict = Depends(get_usuario_actual)):
    """🔒 Conversación completa. La de otro usuario responde 404 (no se revela que existe)."""
    return servicio.detalle(usuario, id_conversacion)


@router.post("/conversaciones/{id_conversacion}/mensajes", response_model=RespuestaMensaje)
def enviar(
    id_conversacion: str,
    mensaje: MensajeEntrada,
    servicio: ServicioAsistente = Depends(get_servicio),
    usuario: dict = Depends(get_usuario_actual),
):
    """🔒 Guarda el mensaje, llama al modelo con herramientas (lugares, rutas, itinerarios, mis planes) y
    regresa la respuesta con tarjetas de rutas y planes. Máximo 2000 caracteres (422). Si Ollama no
    responde: 503 y el mensaje del usuario queda guardado."""
    ubicacion = mensaje.ubicacion.model_dump() if mensaje.ubicacion else None
    return servicio.enviar(usuario, id_conversacion, mensaje.texto, ubicacion)


@router.delete("/conversaciones/{id_conversacion}", status_code=status.HTTP_204_NO_CONTENT)
def borrar(id_conversacion: str, servicio: ServicioAsistente = Depends(get_servicio), usuario: dict = Depends(get_usuario_actual)):
    """🔒 Borrado lógico (`deleted_at`)."""
    servicio.borrar(usuario, id_conversacion)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
