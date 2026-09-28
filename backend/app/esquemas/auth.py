import re
from datetime import date

from pydantic import AliasChoices, BaseModel, Field, field_validator

from app.modelos import Usuario

PATRON_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# BACKEND.md lo llama `correo`; la app manda `email`. Se aceptan los dos.
_CORREO = AliasChoices("correo", "email")


class RegistroEntrada(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    primer_apellido: str = Field(min_length=1, max_length=100)
    segundo_apellido: str | None = Field(default=None, max_length=100)
    correo: str = Field(max_length=100, validation_alias=_CORREO)
    # bcrypt solo usa los primeros 72 bytes
    password: str = Field(min_length=6, max_length=72)
    fecha_nacimiento: date | None = None

    @field_validator("nombre", "primer_apellido", "segundo_apellido")
    @classmethod
    def _sin_espacios(cls, valor: str | None) -> str | None:
        return valor.strip() if valor is not None else None

    @field_validator("nombre", "primer_apellido")
    @classmethod
    def _requerido(cls, valor: str) -> str:
        if not valor:
            raise ValueError("no puede ir vacío")
        return valor

    @field_validator("fecha_nacimiento")
    @classmethod
    def _fecha_posible(cls, valor: date | None) -> date | None:
        hoy = date.today()
        if valor is not None and not (date(hoy.year - 120, 1, 1) <= valor <= hoy):
            raise ValueError("la fecha de nacimiento no puede ser futura ni de hace más de 120 años")
        return valor

    @field_validator("correo")
    @classmethod
    def _correo_valido(cls, valor: str) -> str:
        valor = valor.strip().lower()
        if not PATRON_CORREO.match(valor):
            raise ValueError("el correo no es válido")
        return valor


class LoginEntrada(BaseModel):
    correo: str = Field(max_length=100, validation_alias=_CORREO)
    password: str = Field(max_length=72)

    @field_validator("correo")
    @classmethod
    def _minusculas(cls, valor: str) -> str:
        return valor.strip().lower()


class UsuarioSalida(BaseModel):
    """Campos de la tabla `usuarios` (nunca la contraseña). `email` y `rol` son los que lee la app."""

    id: int
    nombre: str
    primer_apellido: str
    segundo_apellido: str | None
    correo: str
    fecha_nacimiento: date | None
    email: str
    rol: str = Field(description="La base no tiene roles: siempre 'usuario'")

    @classmethod
    def desde_modelo(cls, u: Usuario) -> "UsuarioSalida":
        return cls(
            id=u.id_usuario,
            nombre=u.nombre,
            primer_apellido=u.primer_apellido,
            segundo_apellido=u.segundo_apellido,
            correo=u.correo,
            fecha_nacimiento=u.fecha_nacimiento,
            email=u.correo,
            rol="usuario",
        )


class SesionSalida(BaseModel):
    token: str
    usuario: UsuarioSalida


class ResidenciaEntrada(BaseModel):
    calle: str | None = Field(default=None, max_length=100)
    numero_interior: str | None = Field(default=None, max_length=10)
    numero_exterior: str | None = Field(default=None, max_length=10)
    municipio: str | None = Field(default=None, max_length=100)
    colonia: str | None = Field(default=None, max_length=100)
    estado: str | None = Field(default=None, max_length=100)


class ResidenciaSalida(ResidenciaEntrada):
    id: int
