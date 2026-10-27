"""Asistente con LLM local (Ollama): guarda la conversación, llama al modelo con herramientas y regresa
la respuesta con tarjetas de rutas y planes.

Flujo de un mensaje: guardar el mensaje del usuario → system prompt + últimos 12 mensajes → modelo →
(hasta 3 llamadas a herramientas con los servicios existentes) → respuesta final → guardar.
Si Ollama no responde: el mensaje del usuario queda guardado, se anota el error y se lanza 503.
"""

import json
import logging
import time

from app.compartido.geo import Coordenada
from app.externos import ollama
from app.modulos.asistente.herramientas import DEFINICIONES, Herramientas
from app.modulos.asistente.prompt import system_prompt
from app.modulos.asistente.repositorio import RepositorioConversaciones
from app.modulos.itinerarios.servicio import ServicioItinerarios
from app.modulos.lugares.servicio import ServicioLugares
from app.modulos.rutas.servicio import ServicioRutas
from app.nucleo.bd import ahora
from app.nucleo.errores import NoEncontrado, ServicioExterno

log = logging.getLogger(__name__)

NO_DISPONIBLE = "El asistente no está disponible en este momento."
NO_ENCONTRADA = "No encontramos esa conversación."
MENSAJES_AL_MODELO = 12
MAX_HERRAMIENTAS = 3
PALABRAS_TITULO = 6
LARGO_TITULO = 60
SIN_RESPUESTA = "No pude generar una respuesta. ¿Puedes intentarlo con otras palabras?"


def titulo_de(texto: str) -> str:
    """Primeras palabras del primer mensaje (sin llamar al LLM)."""
    palabras = texto.split()
    titulo = " ".join(palabras[:PALABRAS_TITULO])
    if len(palabras) > PALABRAS_TITULO:
        titulo += "…"
    return titulo[:LARGO_TITULO].rstrip("¿?¡! ") or "Conversación"


def tarjeta_guardada(mensaje: dict) -> dict | None:
    """Tarjeta mínima de un mensaje de herramienta guardado (sin datos de Google ni del GPS)."""
    ref = mensaje.get("resultado_ref") or {}
    if ref.get("tipo") == "ruta":
        return {
            "tipo": "ruta",
            "titulo": f"{ref.get('origen')} → {ref.get('destino')}",
            "id_ruta": ref.get("id_ruta"),
            "destino_texto": ref.get("destino"),
        }
    if ref.get("tipo") == "plan" and ref.get("id_plan"):
        return {"tipo": "plan", "titulo": "Plan guardado", "subtitulo": f"Plan #{ref['id_plan']}", "id_plan": ref["id_plan"]}
    return None


class ServicioAsistente:
    def __init__(self, repo: RepositorioConversaciones, lugares: ServicioLugares, rutas: ServicioRutas, itinerarios: ServicioItinerarios):
        self.repo = repo
        self.lugares = lugares
        self.rutas = rutas
        self.itinerarios = itinerarios

    # ───────────── Conversaciones ─────────────

    @staticmethod
    def estado() -> dict:
        return ollama.estado()

    def crear(self, usuario: dict) -> dict:
        return self._salida(self.repo.crear(usuario["id"], ollama.modelo()))

    def listar(self, usuario: dict) -> list[dict]:
        return self.repo.listar(usuario["id"])

    def _propia(self, usuario: dict, id_conversacion: str) -> dict:
        conversacion = self.repo.por_id(id_conversacion, usuario["id"])
        if conversacion is None:
            raise NoEncontrado(NO_ENCONTRADA)
        return conversacion

    def detalle(self, usuario: dict, id_conversacion: str) -> dict:
        return self._salida(self._propia(usuario, id_conversacion))

    def borrar(self, usuario: dict, id_conversacion: str) -> None:
        if not self.repo.borrar(id_conversacion, usuario["id"]):
            raise NoEncontrado(NO_ENCONTRADA)

    @staticmethod
    def _salida(conversacion: dict) -> dict:
        mensajes = [{**m, "tarjeta": tarjeta_guardada(m)} if m.get("rol") == "herramienta" else m for m in conversacion["mensajes"]]
        return {k: v for k, v in conversacion.items() if k != "id_usuario"} | {"mensajes": mensajes}

    # ───────────── Mensajes ─────────────

    @staticmethod
    def _historial(mensajes: list[dict]) -> list[dict]:
        """Últimos 12 mensajes de usuario y asistente en el formato de Ollama, después del system prompt."""
        roles = {"usuario": "user", "asistente": "assistant"}
        visibles = [m for m in mensajes if m.get("rol") in roles and m.get("contenido")]
        return [{"role": "system", "content": system_prompt()}] + [
            {"role": roles[m["rol"]], "content": m["contenido"]} for m in visibles[-MENSAJES_AL_MODELO:]
        ]

    def enviar(self, usuario: dict, id_conversacion: str, texto: str, ubicacion: Coordenada | None) -> dict:
        conversacion = self._propia(usuario, id_conversacion)
        texto = texto.strip()
        titulo = conversacion["titulo"] or titulo_de(texto)
        mensaje_usuario = {"rol": "usuario", "contenido": texto, "creado_en": ahora()}
        self.repo.agregar_mensaje(id_conversacion, mensaje_usuario, titulo if not conversacion["titulo"] else None)

        mensajes = self._historial([*conversacion["mensajes"], mensaje_usuario])
        herramientas = Herramientas(self.lugares, self.rutas, self.itinerarios, usuario, ubicacion)
        tarjetas: list[dict] = []
        usadas: list[str] = []
        inicio = time.perf_counter()
        try:
            contenido = self._conversar(mensajes, herramientas, id_conversacion, tarjetas, usadas)
        except ollama.ErrorOllama as error:
            log.warning("Ollama no respondió: %s", error)
            self.repo.agregar_mensaje(id_conversacion, {"rol": "error", "contenido": NO_DISPONIBLE, "creado_en": ahora()})
            raise ServicioExterno(NO_DISPONIBLE) from error

        respuesta = {
            "rol": "asistente",
            "contenido": contenido or SIN_RESPUESTA,
            "duracion_ms": round((time.perf_counter() - inicio) * 1000),
            "creado_en": ahora(),
        }
        self.repo.agregar_mensaje(id_conversacion, respuesta)
        return {"conversacion_id": id_conversacion, "titulo": titulo, "mensaje": respuesta, "tarjetas": tarjetas, "herramientas_usadas": usadas}

    def _conversar(self, mensajes: list[dict], herramientas: Herramientas, id_conversacion: str, tarjetas: list, usadas: list) -> str:
        """Llama al modelo; si pide herramientas las ejecuta (máximo 3 por mensaje) y le regresa el JSON."""
        definiciones: list[dict] | None = DEFINICIONES
        while True:
            try:
                vuelta = ollama.chat(mensajes, definiciones)
            except ollama.SinHerramientas:
                log.warning("El modelo %s no soporta tools: se responde solo con texto.", ollama.modelo())
                definiciones = None
                continue
            if not vuelta["llamadas"]:
                return vuelta["contenido"]
            mensajes.append({"role": "assistant", "content": vuelta["contenido"], "tool_calls": vuelta["mensaje"].get("tool_calls", [])})
            for llamada in vuelta["llamadas"]:
                if len(usadas) >= MAX_HERRAMIENTAS:
                    resultado_modelo = {"error": "Se alcanzó el máximo de consultas para este mensaje; responde con lo que ya tienes."}
                else:
                    resultado_modelo = self._ejecutar(herramientas, llamada, id_conversacion, tarjetas, usadas)
                mensajes.append({"role": "tool", "tool_name": llamada["nombre"], "content": json.dumps(resultado_modelo, ensure_ascii=False, default=str)})
            if len(usadas) >= MAX_HERRAMIENTAS:
                definiciones = None  # la siguiente vuelta ya no ofrece herramientas: debe contestar

    def _ejecutar(self, herramientas: Herramientas, llamada: dict, id_conversacion: str, tarjetas: list, usadas: list) -> dict:
        nombre, argumentos = llamada["nombre"], llamada["argumentos"]
        usadas.append(nombre)
        resultado = herramientas.ejecutar(nombre, argumentos)
        self.repo.agregar_mensaje(
            id_conversacion,
            {"rol": "herramienta", "nombre": nombre, "argumentos": argumentos, "resultado_ref": resultado.resultado_ref, "creado_en": ahora()},
        )
        if resultado.ruta_consultada:
            self.repo.agregar_ruta(id_conversacion, {**resultado.ruta_consultada, "consultado_en": ahora()})
        if resultado.plan_creado is not None:
            self.repo.agregar_plan(id_conversacion, resultado.plan_creado)
        if resultado.tarjeta:
            tarjetas.append(resultado.tarjeta)
        return resultado.para_modelo
