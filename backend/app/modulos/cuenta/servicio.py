"""Casos de uso de la cuenta: registro, login, residencia y recuperación de contraseña.
bcrypt y JWT viven en nucleo/seguridad.py; el envío de correos en externos/correo.py."""

import hashlib
import hmac
import logging
import secrets
from datetime import timedelta

from app.externos import correo
from app.modulos.cuenta import plantilla_correo
from app.modulos.cuenta.repositorio import RepositorioCuenta
from app.nucleo.bd import ahora
from app.nucleo.config import get_settings
from app.nucleo.errores import Conflicto, ErrorNegocio, NoAutorizado, ServicioExterno
from app.nucleo.seguridad import crear_token, hash_password, verificar_password

log = logging.getLogger(__name__)

CORREO_EN_USO = "Ya existe una cuenta con ese correo."

# Recuperación de contraseña: código de 6 dígitos que vence a los 15 minutos y admite 5 intentos
MINUTOS_VIGENCIA = 15
MAX_INTENTOS = 5
SEGUNDOS_ENTRE_ENVIOS = 60
CODIGO_ENVIADO = "Si el correo está registrado, te enviamos un código de verificación. Revisa también la carpeta de spam."
CODIGO_INVALIDO = "El código no es válido o ya venció. Pide uno nuevo."
DEMASIADOS_INTENTOS = "Demasiados intentos. Pide un código nuevo."


def _hash_codigo(correo_usuario: str, codigo: str) -> str:
    """HMAC con el secreto de la API: en la base nunca queda el código en claro."""
    clave = get_settings().jwt_secret.encode()
    return hmac.new(clave, f"{correo_usuario}:{codigo}".encode(), hashlib.sha256).hexdigest()


def _enviar_codigo(correo_usuario: str, nombre: str, codigo: str) -> None:
    correo.enviar(
        correo_usuario,
        f"{codigo} es tu código de Kompás",
        plantilla_correo.texto_plano(nombre, codigo, MINUTOS_VIGENCIA),
        html=plantilla_correo.html(nombre, codigo, MINUTOS_VIGENCIA),
        imagenes={"logo": plantilla_correo.logo()},
    )


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

    # ─────────────────────────── Recuperación de contraseña ─────────────────────────

    def solicitar_recuperacion(self, correo_usuario: str) -> str:
        """Envía un código al correo. La respuesta es la misma exista o no la cuenta (no revela quién está registrado)."""
        usuario = self.repo.por_correo(correo_usuario)
        if usuario is None:
            return CODIGO_ENVIADO
        previo = self.repo.codigo_recuperacion(correo_usuario)
        if previo and ahora() - previo["creado"] < timedelta(seconds=SEGUNDOS_ENTRE_ENVIOS):
            return CODIGO_ENVIADO  # evita reenvíos seguidos; el código anterior sigue vigente

        codigo = f"{secrets.randbelow(10**6):06d}"
        self.repo.guardar_codigo_recuperacion(
            correo_usuario, _hash_codigo(correo_usuario, codigo), ahora() + timedelta(minutes=MINUTOS_VIGENCIA)
        )
        if not correo.configurado():
            log.warning("MODO DESARROLLO (sin SMTP_HOST): código de recuperación de %s = %s", correo_usuario, codigo)
            return CODIGO_ENVIADO
        try:
            _enviar_codigo(correo_usuario, usuario["nombre"], codigo)
        except correo.ErrorCorreo as error:
            self.repo.borrar_codigo_recuperacion(correo_usuario)
            log.error("No se pudo enviar el código a %s: %s", correo_usuario, error)
            raise ServicioExterno("No se pudo enviar el correo. Intenta de nuevo en unos minutos.") from None
        return CODIGO_ENVIADO

    def verificar_codigo(self, correo_usuario: str, codigo: str) -> None:
        """ErrorNegocio (400) si el código no coincide, venció o se agotaron los intentos."""
        guardado = self.repo.codigo_recuperacion(correo_usuario)
        if guardado is None or guardado["expira"] < ahora():
            raise ErrorNegocio(CODIGO_INVALIDO)
        if guardado["intentos"] >= MAX_INTENTOS:
            self.repo.borrar_codigo_recuperacion(correo_usuario)
            raise ErrorNegocio(DEMASIADOS_INTENTOS)
        if not hmac.compare_digest(guardado["codigo_hash"], _hash_codigo(correo_usuario, codigo)):
            if self.repo.sumar_intento_recuperacion(correo_usuario) >= MAX_INTENTOS:
                self.repo.borrar_codigo_recuperacion(correo_usuario)
                raise ErrorNegocio(DEMASIADOS_INTENTOS)
            raise ErrorNegocio(CODIGO_INVALIDO)

    def restablecer_password(self, correo_usuario: str, codigo: str, password_nueva: str) -> str:
        """Comprueba el código otra vez, cambia la contraseña y borra el código (solo sirve una vez)."""
        self.verificar_codigo(correo_usuario, codigo)
        if not self.repo.cambiar_password(correo_usuario, hash_password(password_nueva)):
            raise ErrorNegocio(CODIGO_INVALIDO)
        self.repo.borrar_codigo_recuperacion(correo_usuario)
        return "Tu contraseña se cambió. Ya puedes iniciar sesión."
