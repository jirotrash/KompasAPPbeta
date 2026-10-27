"""Contraseñas con bcrypt y sesiones con JWT (Authorization: Bearer <token>)."""

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo.database import Database

from app.nucleo.bd import get_bd
from app.nucleo.config import get_settings
from app.nucleo.errores import NoAutorizado, Prohibido

ALGORITMO = "HS256"

_bearer = HTTPBearer(auto_error=False, description="Token que regresan /api/auth/login y /api/auth/register")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verificar_password(password: str, hash_guardado: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hash_guardado.encode())
    except ValueError:  # hash con formato inválido o contraseña de más de 72 bytes
        return False


def crear_token(id_usuario: int) -> str:
    ajustes = get_settings()
    ahora = datetime.now(UTC)
    datos = {"sub": str(id_usuario), "iat": ahora, "exp": ahora + timedelta(minutes=ajustes.jwt_expira_minutos)}
    return jwt.encode(datos, ajustes.jwt_secret, algorithm=ALGORITMO)


def get_usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_bearer),
    bd: Database = Depends(get_bd),
) -> dict:
    """Dependencia de los endpoints 🔒: regresa el usuario del token (dict del dominio) o responde 401."""
    # Import local: el módulo cuenta importa este archivo (crear_token, hash_password)
    from app.modulos.cuenta.repositorio import RepositorioCuenta

    if credenciales is None:
        raise NoAutorizado("Inicia sesión para continuar.")
    try:
        datos = jwt.decode(credenciales.credentials, get_settings().jwt_secret, algorithms=[ALGORITMO])
        id_usuario = int(datos["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise NoAutorizado("Tu sesión expiró o no es válida. Inicia sesión de nuevo.") from None

    usuario = RepositorioCuenta(bd).por_id(id_usuario)
    if usuario is None:
        raise NoAutorizado("Tu cuenta ya no está disponible. Inicia sesión de nuevo.")
    return usuario


def requiere_admin(usuario: dict = Depends(get_usuario_actual)) -> dict:
    if usuario.get("rol") != "admin":
        raise Prohibido("Solo un administrador puede ver el dashboard.")
    return usuario
