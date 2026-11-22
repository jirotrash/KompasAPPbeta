"""Errores de negocio. Los servicios los lanzan sin conocer HTTP; aquí se traducen a respuestas JSON.

La app muestra `detail` tal cual, así que los mensajes deben quedarse idénticos.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pymongo.errors import ServerSelectionTimeoutError


class ErrorNegocio(Exception):
    codigo_http = 400

    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje


class NoEncontrado(ErrorNegocio):
    codigo_http = 404


class Conflicto(ErrorNegocio):
    codigo_http = 409  # correo ya registrado


class NoAutorizado(ErrorNegocio):
    codigo_http = 401


class Prohibido(ErrorNegocio):
    codigo_http = 403  # dashboard sin rol admin


class DatosInvalidos(ErrorNegocio):
    codigo_http = 422  # fuera de la zona piloto, parámetros mal formados


class ServicioExterno(ErrorNegocio):
    codigo_http = 503  # Google Places no responde


class ErrorDeDatos(ErrorNegocio):
    codigo_http = 500  # faltan catálogos en la base


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ErrorNegocio)
    async def _manejar(_: Request, exc: ErrorNegocio) -> JSONResponse:
        encabezados = {"WWW-Authenticate": "Bearer"} if isinstance(exc, NoAutorizado) else None
        return JSONResponse(status_code=exc.codigo_http, content={"detail": exc.mensaje}, headers=encabezados)

    @app.exception_handler(ServerSelectionTimeoutError)
    async def _base_no_responde(_: Request, __: ServerSelectionTimeoutError) -> JSONResponse:
        """MongoDB apagado o inaccesible: 503 con mensaje (un 500 sin CORS la app lo lee como 'sin conexión')."""
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "La base de datos del servidor no responde. Intenta de nuevo en unos minutos."},
        )

    @app.exception_handler(RequestValidationError)
    async def error_de_validacion(_: Request, exc: RequestValidationError) -> JSONResponse:
        """La app solo muestra `detail` si es texto, así que se resume la lista de errores de Pydantic."""
        mensajes = []
        for error in exc.errors():
            campo = ".".join(str(parte) for parte in error["loc"] if parte != "body")
            mensajes.append(f"{campo}: {error['msg']}" if campo else error["msg"])
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": "Revisa los datos enviados. " + "; ".join(mensajes)},
        )
