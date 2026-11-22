"""Envío de correos por SMTP — patrón Adaptador, igual que Google Places y Ollama.

Se usa para los códigos de recuperación de contraseña. Funciona con cualquier proveedor SMTP
(Gmail con contraseña de aplicación, Outlook, Brevo…): puerto 587 con STARTTLS o 465 con SSL.
Si el servidor no responde o rechaza el acceso se lanza ErrorCorreo (la API responde 503).
"""

import smtplib
from email.message import EmailMessage

from app.nucleo.config import get_settings

TIEMPO_LIMITE_S = 15


class ErrorCorreo(Exception):
    """El servidor SMTP no respondió o rechazó el usuario y la contraseña."""


def configurado() -> bool:
    """Sin SMTP_HOST la API trabaja en modo desarrollo: no envía correos."""
    return bool(get_settings().smtp_host)


def enviar(
    destinatario: str, asunto: str, texto: str, html: str | None = None, imagenes: dict[str, bytes] | None = None
) -> None:
    """`texto` siempre va (clientes sin HTML). `html` puede usar imágenes incrustadas: <img src="cid:logo">
    con imagenes={"logo": bytes_png}."""
    s = get_settings()
    mensaje = EmailMessage()
    mensaje["From"] = s.smtp_remitente or s.smtp_usuario or ""
    mensaje["To"] = destinatario
    mensaje["Subject"] = asunto
    mensaje.set_content(texto)
    if html:
        mensaje.add_alternative(html, subtype="html")
        parte_html = mensaje.get_payload()[-1]
        for nombre, contenido in (imagenes or {}).items():
            parte_html.add_related(contenido, maintype="image", subtype="png", cid=f"<{nombre}>", filename=f"{nombre}.png")
    try:
        if s.smtp_puerto == 465:
            servidor = smtplib.SMTP_SSL(s.smtp_host, s.smtp_puerto, timeout=TIEMPO_LIMITE_S)
        else:
            servidor = smtplib.SMTP(s.smtp_host, s.smtp_puerto, timeout=TIEMPO_LIMITE_S)
            servidor.starttls()
        with servidor:
            if s.smtp_usuario:
                servidor.login(s.smtp_usuario, s.smtp_password or "")
            servidor.send_message(mensaje)
    except (smtplib.SMTPException, OSError) as error:
        raise ErrorCorreo(str(error)) from error
