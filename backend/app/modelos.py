"""Modelos SQLAlchemy de las 8 tablas del esquema `kompas`, tal como están en el dump de Sebas.

El esquema NO se modifica desde el backend (BACKEND.md §0). Si hace falta una columna, se habla con Sebas.
Borrado lógico: toda consulta filtra `deleted_at IS NULL`; "eliminar" = poner fecha en `deleted_at`.
"""

import re
from datetime import date, datetime

from sqlalchemy import TIMESTAMP, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.expression import FunctionElement
from sqlalchemy.types import TypeDecorator, UserDefinedType

from app.db import Base

# ─────────────────────── LINESTRING (SRID 4326) ↔ [[lng, lat], ...] ───────────────────────
# MySQL 8 con SRID 4326 usa por defecto el orden latitud-longitud; MariaDB guarda x, y tal cual.
# Se pide siempre longitud-latitud (como GeoJSON) según el motor al que se conecte.


class _TextoWKT(TypeDecorator):
    """Resultado de ST_AsText: 'LINESTRING(-99.49 19.28, ...)' → [[-99.49, 19.28], ...]"""

    impl = String
    cache_ok = True

    def process_result_value(self, wkt, dialect):
        if wkt is None:
            return None
        if isinstance(wkt, bytes):
            wkt = wkt.decode()
        cuerpo = re.search(r"\((.*)\)", wkt).group(1)
        return [[float(n) for n in par.split()] for par in cuerpo.split(",")]


class _WKTaGeometria(FunctionElement):
    inherit_cache = True


class _GeometriaAWKT(FunctionElement):
    type = _TextoWKT()
    inherit_cache = True


@compiles(_WKTaGeometria)
def _compilar_wkt_a_geometria(elemento, compilador, **kw):
    wkt = compilador.process(elemento.clauses, **kw)
    if getattr(compilador.dialect, "is_mariadb", False):
        return f"ST_GeomFromText({wkt}, 4326)"
    return f"ST_GeomFromText({wkt}, 4326, 'axis-order=long-lat')"


@compiles(_GeometriaAWKT)
def _compilar_geometria_a_wkt(elemento, compilador, **kw):
    columna = compilador.process(elemento.clauses, **kw)
    if getattr(compilador.dialect, "is_mariadb", False):
        return f"ST_AsText({columna})"
    return f"ST_AsText({columna}, 'axis-order=long-lat')"


class LineaGeo(UserDefinedType):
    """Columna LINESTRING que en Python se maneja como lista de pares [lng, lat]."""

    cache_ok = True

    def get_col_spec(self, **kw):
        return "LINESTRING"

    def bind_expression(self, valor):
        return _WKTaGeometria(valor)

    def column_expression(self, columna):
        return _GeometriaAWKT(columna)

    def bind_processor(self, dialect):
        def procesar(coordenadas):
            if coordenadas is None:
                return None
            return "LINESTRING(" + ", ".join(f"{lng} {lat}" for lng, lat in coordenadas) + ")"

        return procesar


# ─────────────────────────────── Columnas comunes ───────────────────────────────


class ConTiempos:
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())
    deleted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, default=None)


# ─────────────────────────────── Usuarios y residencia ──────────────────────────


class Usuario(ConTiempos, Base):
    __tablename__ = "usuarios"

    id_usuario: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    primer_apellido: Mapped[str] = mapped_column(String(100))
    segundo_apellido: Mapped[str | None] = mapped_column(String(100))
    correo: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(255))  # hash bcrypt, nunca texto plano
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date)


class Residencia(ConTiempos, Base):
    __tablename__ = "residencia"

    id_residencia: Mapped[int] = mapped_column(Integer, primary_key=True)
    calle: Mapped[str | None] = mapped_column(String(100))
    numero_interior: Mapped[str | None] = mapped_column(String(10))
    numero_exterior: Mapped[str | None] = mapped_column(String(10))
    municipio: Mapped[str | None] = mapped_column(String(100))
    colonia: Mapped[str | None] = mapped_column(String(100))
    estado: Mapped[str | None] = mapped_column(String(100))
    id_usuario: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id_usuario"))


# ─────────────────────────────────── Catálogos ──────────────────────────────────


class Categoria(ConTiempos, Base):
    __tablename__ = "categorias"

    id_categoria: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text)


class Transporte(ConTiempos, Base):
    __tablename__ = "transportes"

    id_transporte: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)


# ──────────────────────────────────── Lugares ───────────────────────────────────


class Lugar(ConTiempos, Base):
    __tablename__ = "lugares_de_interes"

    id_lugar: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    longitud: Mapped[float] = mapped_column(Numeric(11, 8, asdecimal=False))
    latitud: Mapped[float] = mapped_column(Numeric(10, 8, asdecimal=False))
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuarios.id_usuario"))  # quien registró el lugar
    id_cat: Mapped[int] = mapped_column(ForeignKey("categorias.id_categoria"))

    categoria: Mapped[Categoria] = relationship(lazy="joined")


# ──────────────────────────────── Rutas e historial ─────────────────────────────


class Ruta(ConTiempos, Base):
    __tablename__ = "rutas"

    id_ruta: Mapped[int] = mapped_column(Integer, primary_key=True)
    ruta: Mapped[list[list[float]]] = mapped_column(LineaGeo)  # trazo [[lng, lat], ...]


class HistorialRuta(ConTiempos, Base):
    __tablename__ = "historial_rutas"

    id_historial: Mapped[int] = mapped_column(Integer, primary_key=True)
    tiempo_estimado: Mapped[int] = mapped_column(Integer)  # minutos
    id_ruta: Mapped[int] = mapped_column(ForeignKey("rutas.id_ruta"))
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuarios.id_usuario"))
    id_transporte: Mapped[int] = mapped_column(ForeignKey("transportes.id_transporte"))

    transporte: Mapped[Transporte] = relationship(lazy="joined")


# ──────────────────────────────────── Planes ────────────────────────────────────


class Plan(ConTiempos, Base):
    __tablename__ = "planes"

    id_plan: Mapped[int] = mapped_column(Integer, primary_key=True)
    no_acompanantes: Mapped[int] = mapped_column(Integer, server_default="0")
    tiempo_disponible: Mapped[int] = mapped_column(Integer)  # minutos
    id_transporte: Mapped[int] = mapped_column(ForeignKey("transportes.id_transporte"))
    id_categoria: Mapped[int] = mapped_column(ForeignKey("categorias.id_categoria"))
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuarios.id_usuario"))
    fecha_plan: Mapped[datetime | None] = mapped_column(DateTime)

    categoria: Mapped[Categoria] = relationship(lazy="joined")
    transporte: Mapped[Transporte] = relationship(lazy="joined")
