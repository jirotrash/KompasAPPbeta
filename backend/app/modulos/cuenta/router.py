"""Cuenta: registro, login, usuario actual y residencia (colección `usuarios`)."""

from fastapi import APIRouter, Depends, status
from pymongo.database import Database

from app.modulos.cuenta.esquemas import (
    LoginEntrada,
    RegistroEntrada,
    ResidenciaEntrada,
    ResidenciaSalida,
    SesionSalida,
    UsuarioSalida,
)
from app.modulos.cuenta.repositorio import RepositorioCuenta
from app.modulos.cuenta.servicio import ServicioCuenta
from app.nucleo.bd import get_bd
from app.nucleo.seguridad import get_usuario_actual

router = APIRouter(prefix="/api/auth", tags=["Cuenta"])
router_residencia = APIRouter(prefix="/api/residencia", tags=["Cuenta"])


def get_servicio(bd: Database = Depends(get_bd)) -> ServicioCuenta:
    return ServicioCuenta(RepositorioCuenta(bd))


def _sesion(sesion: dict) -> SesionSalida:
    return SesionSalida(token=sesion["token"], usuario=UsuarioSalida.desde_usuario(sesion["usuario"]))


# BACKEND.md usa /registro; la app (src/services/api.ts) llama a /register. Los dos hacen lo mismo.
@router.post("/registro", status_code=status.HTTP_201_CREATED, response_model=SesionSalida)
@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=SesionSalida, include_in_schema=False)
def registrar(datos: RegistroEntrada, servicio: ServicioCuenta = Depends(get_servicio)):
    """Crea la cuenta y regresa la sesión. 409 si el correo ya está registrado."""
    return _sesion(servicio.registrar(datos.model_dump()))


@router.post("/login", response_model=SesionSalida)
def login(datos: LoginEntrada, servicio: ServicioCuenta = Depends(get_servicio)):
    """401 si el correo o la contraseña no coinciden (no se dice cuál de los dos)."""
    return _sesion(servicio.login(datos.correo, datos.password))


@router.get("/yo", response_model=UsuarioSalida)
def yo(usuario: dict = Depends(get_usuario_actual)):
    """Usuario de la sesión actual 🔒"""
    return UsuarioSalida.desde_usuario(usuario)


@router_residencia.get("", response_model=ResidenciaSalida | None)
def ver_residencia(servicio: ServicioCuenta = Depends(get_servicio), usuario: dict = Depends(get_usuario_actual)):
    """Residencia del usuario 🔒, o `null` si no la ha registrado."""
    return servicio.residencia(usuario)


@router_residencia.put("", response_model=ResidenciaSalida)
def guardar_residencia(
    datos: ResidenciaEntrada, servicio: ServicioCuenta = Depends(get_servicio), usuario: dict = Depends(get_usuario_actual)
):
    """Guarda la residencia del usuario 🔒 (la crea si no existe). Todos los campos son opcionales."""
    return servicio.guardar_residencia(usuario, datos.model_dump())
