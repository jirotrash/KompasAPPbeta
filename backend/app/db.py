"""Conexión a MySQL (esquema `kompas`) con SQLAlchemy 2.0."""

from collections.abc import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

engine = create_engine(
    get_settings().database_url,
    pool_pre_ping=True,  # evita "MySQL server has gone away" tras horas sin uso
    pool_recycle=3600,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base de los modelos de app/modelos.py."""


def get_db() -> Iterator[Session]:
    """Una sesión por petición: `db: Session = Depends(get_db)`."""
    with SessionLocal() as db:
        yield db


def bd_disponible() -> bool:
    try:
        with engine.connect() as conexion:
            conexion.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
