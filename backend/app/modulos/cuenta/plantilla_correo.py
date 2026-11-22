"""Correo del código de recuperación con el mismo diseño que la pantalla de acceso de la app.

Colores de COLORIMETRIA.md (modo claro): fondo #F7F8FA, tarjeta #FFFFFF, borde #E2E6EC, texto #1B1F27,
texto secundario #5B6472, primario #1A62A5, tinte suave #E8F0F8, aviso #DFAB36 / #FDF6E7.
Los correos no admiten hojas de estilo externas: todo va en estilos en línea y tablas.
"""

from functools import lru_cache
from html import escape
from pathlib import Path

LOGO = Path(__file__).resolve().parents[2] / "recursos" / "logo_correo.png"
FUENTE = "-apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"


@lru_cache
def logo() -> bytes:
    return LOGO.read_bytes()


def texto_plano(nombre: str, codigo: str, minutos: int) -> str:
    return (
        f"Hola, {nombre}:\n\n"
        f"Tu código para recuperar tu contraseña de Kompás es:\n\n    {codigo}\n\n"
        f"Vence en {minutos} minutos y solo se puede usar una vez.\n"
        "Si no lo pediste, ignora este correo: tu contraseña no cambia.\n\n"
        "— Equipo Kompás"
    )


def html(nombre: str, codigo: str, minutos: int) -> str:
    nombre = escape(nombre)
    return f"""<!doctype html>
<html lang="es">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Tu código de Kompás</title></head>
<body style="margin:0;padding:0;background:#F7F8FA;">
<div style="display:none;max-height:0;overflow:hidden;">Tu código es {codigo}. Vence en {minutos} minutos.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F7F8FA;padding:32px 16px;">
<tr><td align="center">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;font-family:{FUENTE};">
    <tr><td style="padding:0 4px 20px;">
      <table role="presentation" cellpadding="0" cellspacing="0"><tr>
        <td><img src="cid:logo" width="40" height="40" alt="Kompás" style="display:block;border:0;"></td>
        <td style="padding-left:10px;font-size:18px;font-weight:700;color:#1B1F27;">Kompás App</td>
      </tr></table>
    </td></tr>
    <tr><td style="background:#FFFFFF;border:1px solid #E2E6EC;border-radius:16px;padding:32px 28px;">
      <h1 style="margin:0 0 8px;font-size:24px;line-height:1.25;font-weight:700;color:#1B1F27;text-align:center;">Recupera tu contraseña</h1>
      <p style="margin:0 0 24px;font-size:15px;line-height:1.5;color:#5B6472;text-align:center;">Hola, {nombre}. Escribe este código en la app para crear una contraseña nueva.</p>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
        <td align="center" style="background:#E8F0F8;border-radius:12px;padding:20px 12px;">
          <div style="font-size:13px;font-weight:600;color:#5B6472;margin-bottom:6px;">Código de verificación</div>
          <div style="font-size:34px;line-height:1.2;font-weight:700;letter-spacing:8px;color:#1A62A5;font-family:Consolas,'Courier New',monospace;">{codigo}</div>
        </td>
      </tr></table>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:20px;"><tr>
        <td style="background:#FDF6E7;border:1px solid #DFAB36;border-radius:12px;padding:12px 14px;font-size:14px;line-height:1.45;color:#1B1F27;">
          Vence en <strong>{minutos} minutos</strong> y solo se puede usar una vez.
        </td>
      </tr></table>
      <p style="margin:20px 0 0;font-size:13px;line-height:1.5;color:#5B6472;">Si no pediste este código, ignora este correo: tu contraseña no cambia. Nunca compartas el código con nadie.</p>
    </td></tr>
    <tr><td style="padding:20px 4px 0;font-size:12px;line-height:1.5;color:#5B6472;text-align:center;">
      Kompás · Toluca, Lerma y San Mateo Atenco<br>Este correo se envió automáticamente; no lo respondas.
    </td></tr>
  </table>
</td></tr>
</table>
</body>
</html>"""
