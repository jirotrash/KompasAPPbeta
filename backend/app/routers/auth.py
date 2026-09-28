"""Cuenta: registro, login, usuario actual y residencia (tablas `usuarios` y `residencia`)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.esquemas.auth import (
    LoginEntrada,
    RegistroEntrada,
    ResidenciaEntrada,
    ResidenciaSalida,
    SesionSalida,
    UsuarioSalida,
)
from app.modelos import Residencia, Usuario
from app.seguridad import crear_token, get_usuario_actual, hash_password, verificar_password
from app.servicios import serializar

router = APIRouter(prefix="/api/auth", tags=["Cuenta"])
router_residencia = APIRouter(prefix="/api/residencia", tags=["Cuenta"])

CORREO_EN_USO = "Ya existe una cuenta con ese correo."


def _sesion(usuario: Usuario) -> SesionSalida:
    return SesionSalida(token=crear_token(usuario.id_usuario), usuario=UsuarioSalida.desde_modelo(usuario))


# BACKEND.md usa /registro; la app (src/services/api.ts) llama a /register. Los dos hacen lo mismo.
@router.post("/registro", status_code=status.HTTP_201_CREATED, response_model=SesionSalida)
@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=SesionSalida, include_in_schema=False)
def registrar(datos: RegistroEntrada, db: Session = Depends(get_db)):
    """Crea la cuenta y regresa la sesión. 409 si el correo ya está registrado."""
    if db.scalar(select(Usuario.id_usuario).where(Usuario.correo == datos.correo)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, CORREO_EN_USO)
    usuario = Usuario(
        nombre=datos.nombre,
        primer_apellido=datos.primer_apellido,
        segundo_apellido=datos.segundo_apellido or None,
        correo=datos.correo,
        password=hash_password(datos.password),
        fecha_nacimiento=datos.fecha_nacimiento,
    )
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:  # dos registros simultáneos con el mismo correo
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, CORREO_EN_USO) from None
    db.refresh(usuario)
    return _sesion(usuario)


@router.post("/login", response_model=SesionSalida)
def login(datos: LoginEntrada, db: Session = Depends(get_db)):
    """401 si el correo o la contraseña no coinciden (no se dice cuál de los dos)."""
    usuario = db.scalar(select(Usuario).where(Usuario.correo == datos.correo, Usuario.deleted_at.is_(None)))
    if usuario is None or not verificar_password(datos.password, usuario.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Correo o contraseña incorrectos.")
    return _sesion(usuario)


@router.get("/yo", response_model=UsuarioSalida)
def yo(usuario: Usuario = Depends(get_usuario_actual)):
    """Usuario de la sesión actual 🔒"""
    return UsuarioSalida.desde_modelo(usuario)


def _residencia_de(db: Session, usuario: Usuario) -> Residencia | None:
    consulta = select(Residencia).where(Residencia.id_usuario == usuario.id_usuario, Residencia.deleted_at.is_(None))
    return db.scalars(consulta.order_by(Residencia.id_residencia)).first()


@router_residencia.get("", response_model=ResidenciaSalida | None)
def ver_residencia(db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_actual)):
    """Residencia del usuario 🔒, o `null` si no la ha registrado."""
    residencia = _residencia_de(db, usuario)
    return serializar.residencia(residencia) if residencia else None


@router_residencia.put("", response_model=ResidenciaSalida)
def guardar_residencia(datos: ResidenciaEntrada, db: Session = Depends(get_db), usuario: Usuario = Depends(get_usuario_actual)):
    """Guarda la residencia del usuario 🔒 (la crea si no existe). Todos los campos son opcionales."""
    residencia = _residencia_de(db, usuario)
    if residencia is None:
        residencia = Residencia(id_usuario=usuario.id_usuario)
        db.add(residencia)
    for campo, valor in datos.model_dump().items():
        setattr(residencia, campo, (valor or "").strip() or None)
    db.commit()
    db.refresh(residencia)
    return serializar.residencia(residencia)
