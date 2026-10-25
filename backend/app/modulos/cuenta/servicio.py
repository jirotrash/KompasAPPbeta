"""Casos de uso de la cuenta: registro, login y residencia. bcrypt y JWT viven en nucleo/seguridad.py."""

from app.modulos.cuenta.repositorio import RepositorioCuenta
from app.nucleo.errores import Conflicto, NoAutorizado
from app.nucleo.seguridad import crear_token, hash_password, verificar_password

CORREO_EN_USO = "Ya existe una cuenta con ese correo."


class ServicioCuenta:
    def __init__(self, repo: RepositorioCuenta):
        self.repo = repo

    @staticmethod
    def _sesion(usuario: dict) -> dict:
        return {"token": crear_token(usuario["id"]), "usuario": usuario}

    def registrar(self, datos: dict) -> dict:
        """Crea la cuenta y regresa la sesión. Conflicto si el correo ya está registrado."""
        if self.repo.existe_correo(datos["correo"]):
            raise Conflicto(CORREO_EN_USO)
        usuario = self.repo.crear(
            {
                **datos,
                "segundo_apellido": datos.get("segundo_apellido") or None,
                "password": hash_password(datos["password"]),
            }
        )
        if usuario is None:  # dos registros simultáneos con el mismo correo
            raise Conflicto(CORREO_EN_USO)
        return self._sesion(usuario)

    def login(self, correo: str, password: str) -> dict:
        """No se dice si falló el correo o la contraseña."""
        usuario = self.repo.por_correo(correo)
        if usuario is None or not verificar_password(password, usuario["password"]):
            raise NoAutorizado("Correo o contraseña incorrectos.")
        return self._sesion(usuario)

    def residencia(self, usuario: dict) -> dict | None:
        return self.repo.residencia(usuario["id"])

    def guardar_residencia(self, usuario: dict, datos: dict) -> dict:
        campos = {campo: (valor or "").strip() or None for campo, valor in datos.items()}
        return self.repo.guardar_residencia(usuario["id"], campos)
