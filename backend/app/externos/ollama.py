"""Cliente de Ollama (LLM local en la PC) — patrón Adaptador, igual que Google Places.

La app móvil NUNCA llama a Ollama: todo pasa por la API (módulo asistente).
POST {OLLAMA_URL}/api/chat con stream: false. Si Ollama no responde se lanza ErrorOllama (la API
responde 503). Si el modelo no soporta *tools* se lanza SinHerramientas para reintentar solo con texto.
"""

import json
from typing import Any

import httpx

from app.nucleo.config import get_settings

TIEMPO_LIMITE_S = 60
TIEMPO_ESTADO_S = 3
OPCIONES = {"temperature": 0.3, "num_ctx": 4096}


class ErrorOllama(Exception):
    """Ollama no está abierto, no tiene el modelo o tardó demasiado."""


class SinHerramientas(ErrorOllama):
    """El modelo no soporta tool calling."""


def _url(ruta: str) -> str:
    return get_settings().ollama_url.rstrip("/") + ruta


def modelo() -> str:
    return get_settings().ollama_modelo


def chat(mensajes: list[dict[str, Any]], herramientas: list[dict] | None = None, *, cliente: httpx.Client | None = None) -> dict:
    """Una vuelta de conversación. Regresa {contenido, llamadas: [{nombre, argumentos}], mensaje (crudo)}."""
    cuerpo: dict[str, Any] = {"model": modelo(), "messages": mensajes, "stream": False, "options": OPCIONES}
    if herramientas:
        cuerpo["tools"] = herramientas
    propio = cliente is None
    cliente = cliente or httpx.Client(timeout=TIEMPO_LIMITE_S)
    try:
        respuesta = cliente.post(_url("/api/chat"), json=cuerpo)
    except httpx.HTTPError as error:
        raise ErrorOllama(f"No se pudo conectar con Ollama: {error}") from error
    finally:
        if propio:
            cliente.close()
    if respuesta.status_code == 400 and "does not support tools" in respuesta.text:
        raise SinHerramientas(respuesta.text)
    if respuesta.status_code != 200:
        raise ErrorOllama(f"Ollama respondió {respuesta.status_code}: {respuesta.text[:200]}")
    mensaje = respuesta.json().get("message") or {}
    llamadas = []
    for llamada in mensaje.get("tool_calls") or []:
        funcion = llamada.get("function") or {}
        argumentos = funcion.get("arguments")
        llamadas.append({"nombre": funcion.get("name", ""), "argumentos": argumentos if isinstance(argumentos, dict) else {}})
    contenido = (mensaje.get("content") or "").strip()
    if not llamadas and herramientas and (en_texto := llamada_en_texto(contenido, {h["function"]["name"] for h in herramientas})):
        # Modelos chicos a veces escriben la llamada como JSON en el texto en lugar de usar tool_calls
        llamadas = [en_texto]
        contenido = ""
        mensaje = {**mensaje, "content": "", "tool_calls": [{"function": {"name": en_texto["nombre"], "arguments": en_texto["argumentos"]}}]}
    return {"contenido": contenido, "llamadas": llamadas, "mensaje": mensaje}


def llamada_en_texto(contenido: str, nombres: set[str]) -> dict | None:
    """{"name": "...", "parameters": {...}} (con o sin bloque ```) → {nombre, argumentos}, si es una herramienta conocida."""
    texto = contenido.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    if not (texto.startswith("{") and texto.endswith("}")):
        return None
    try:
        datos = json.loads(texto)
    except ValueError:
        return None
    nombre = datos.get("name") if isinstance(datos, dict) else None
    argumentos = datos.get("parameters", datos.get("arguments", {})) if isinstance(datos, dict) else {}
    if nombre not in nombres or not isinstance(argumentos, dict):
        return None
    # "null" como texto es un valor vacío
    return {"nombre": nombre, "argumentos": {k: v for k, v in argumentos.items() if v not in (None, "null", "")}}


def estado(*, cliente: httpx.Client | None = None) -> dict:
    """{disponible, modelo, modelo_instalado}: hace ping a GET /api/tags."""
    nombre = modelo()
    propio = cliente is None
    cliente = cliente or httpx.Client(timeout=TIEMPO_ESTADO_S)
    try:
        respuesta = cliente.get(_url("/api/tags"))
        modelos = {m.get("name") for m in respuesta.json().get("models", [])} if respuesta.status_code == 200 else set()
        disponible = respuesta.status_code == 200
    except (httpx.HTTPError, ValueError):
        disponible, modelos = False, set()
    finally:
        if propio:
            cliente.close()
    # "llama3.2" y "llama3.2:latest" son el mismo modelo
    instalado = nombre in modelos or f"{nombre}:latest" in modelos
    return {"disponible": disponible and instalado, "modelo": nombre, "modelo_instalado": instalado}
