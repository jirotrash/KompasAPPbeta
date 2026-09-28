"""Contraseñas con bcrypt y sesiones con JWT (Authorization: Bearer <token>)."""

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.modelos import Usuario

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


def _no_autorizado(mensaje: str) -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, detail=mensaje, headers={"WWW-Authenticate": "Bearer"})


def get_usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    """Dependencia de los endpoints 🔒: regresa el usuario del token o responde 401."""
    if credenciales is None:
        raise _no_autorizado("Inicia sesión para continuar.")
    try:
        datos = jwt.decode(credenciales.credentials, get_settings().jwt_secret, algorithms=[ALGORITMO])
        id_usuario = int(datos["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise _no_autorizado("Tu sesión expiró o no es válida. Inicia sesión de nuevo.") from None

    usuario = db.get(Usuario, id_usuario)
    if usuario is None or usuario.deleted_at is not None:
        raise _no_autorizado("Tu cuenta ya no está disponible. Inicia sesión de nuevo.")
    return usuario
