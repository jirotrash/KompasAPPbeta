"""Herramientas que el LLM puede llamar (tool calling de Ollama). Cada una usa los servicios que ya existen.

Al modelo solo se le regresa JSON con datos de Kompás (y de Google, con su fuente); nunca se le pide
inventar. Un origen o destino escrito se ubica en la colección `lugares` y, si no está, con Google Places
(Text Search). Si no se encuentra, se le dice al modelo que no se encontró.
"""

import inspect
from datetime import datetime
from typing import Any

from app.compartido.geo import Coordenada, esta_dentro_de_zona, hora_actual
from app.compartido.texto import INTERESES, clave
from app.externos import google_places
from app.modulos.itinerarios.servicio import ServicioItinerarios
from app.modulos.lugares.servicio import ServicioLugares
from app.modulos.rutas.servicio import ServicioRutas
from app.nucleo.errores import ErrorNegocio

CONTEXTOS = ["solo", "pareja", "amigos", "familia"]
MOVILIDADES = ["caminando", "transporte_publico", "taxi_app", "combinado"]
MODOS_DE_MEDIO = {"caminando": {"pie"}, "transporte_publico": {"autobus"}, "taxi_app": {"taxi", "app"}, "combinado": {"pie", "autobus", "taxi", "app"}}
AQUI = {"", "aqui", "aca", "mi ubicacion", "mi posicion", "donde estoy", "mi casa", "ubicacion actual", "desde aqui"}

DEFINICIONES = [
    {
        "type": "function",
        "function": {
            "name": "buscar_lugares",
            "description": "Busca lugares en Toluca, Lerma y San Mateo Atenco por nombre o tipo (cafés, museos, parques...).",
            "parameters": {
                "type": "object",
                "properties": {
                    "texto": {"type": "string", "description": "Lo que busca el usuario, p. ej. 'café' o 'Cosmovitral'"},
                    "categoria": {"type": "string", "enum": list(INTERESES), "description": "Opcional"},
                },
                "required": ["texto"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "como_llegar",
            "description": "Opciones para ir de un origen a un destino (autobús si hay ruta registrada, a pie y taxi/app), con tiempos estimados.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origen": {"type": "string", "description": "Lugar de salida; 'mi ubicación' si no se menciona"},
                    "destino": {"type": "string", "description": "Lugar al que quiere llegar"},
                    "medios": {"type": "array", "items": {"type": "string", "enum": MOVILIDADES}, "description": "Opcional"},
                },
                "required": ["origen", "destino"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "armar_salida",
            "description": "Arma y guarda un plan de salida con el sistema experto de Kompás (lugares reales cerca del usuario).",
            "parameters": {
                "type": "object",
                "properties": {
                    "contexto": {"type": "string", "enum": CONTEXTOS, "description": "Con quién va"},
                    "presupuesto": {"type": "number", "description": "Presupuesto máximo por persona en pesos"},
                    "tiempo": {"type": "number", "description": "Horas disponibles"},
                    "intereses": {"type": "array", "items": {"type": "string", "enum": list(INTERESES)}},
                    "hora_salida": {"type": "string", "description": "HH:MM (24 h); si no la dice, la hora actual"},
                    "movilidad": {"type": "array", "items": {"type": "string", "enum": MOVILIDADES}, "description": "Opcional"},
                },
                "required": ["contexto", "presupuesto", "tiempo", "intereses"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mis_planes",
            "description": "Planes que el usuario ha guardado en Kompás.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def _texto(valor: Any) -> str:
    return str(valor).strip() if valor is not None else ""


def _lista(valor: Any, permitidos: list[str] | tuple[str, ...]) -> list[str]:
    """El modelo a veces manda un texto en lugar de una lista o valores con acentos: se normalizan."""
    if isinstance(valor, str):
        valor = [v for v in valor.replace(";", ",").split(",")]
    if not isinstance(valor, list):
        return []
    salida = []
    for v in valor:
        c = clave(_texto(v))
        if c in permitidos and c not in salida:
            salida.append(c)
    return salida


def _numero(valor: Any) -> float | None:
    try:
        n = float(str(valor).replace("$", "").replace(",", "").split()[0])
    except (ValueError, IndexError):
        return None
    return n if n > 0 else None


class Resultado:
    """Lo que produce una herramienta: JSON para el modelo + lo que se guarda y lo que ve la app."""

    def __init__(self, para_modelo: dict, resultado_ref: dict | None = None, tarjeta: dict | None = None):
        self.para_modelo = para_modelo
        self.resultado_ref = resultado_ref
        self.tarjeta = tarjeta
        self.ruta_consultada: dict | None = None
        self.plan_creado: int | None = None


class Herramientas:
    def __init__(self, lugares: ServicioLugares, rutas: ServicioRutas, itinerarios: ServicioItinerarios, usuario: dict, ubicacion: Coordenada | None):
        self.lugares = lugares
        self.rutas = rutas
        self.itinerarios = itinerarios
        self.usuario = usuario
        self.ubicacion = ubicacion

    def ejecutar(self, nombre: str, argumentos: dict) -> Resultado:
        funcion = {
            "buscar_lugares": self.buscar_lugares,
            "como_llegar": self.como_llegar,
            "armar_salida": self.armar_salida,
            "mis_planes": self.mis_planes,
        }.get(nombre)
        if funcion is None:
            return Resultado({"error": f"La herramienta {nombre} no existe."})
        try:
            permitidos = inspect.signature(funcion).parameters
            return funcion(**{k: v for k, v in argumentos.items() if k in permitidos})
        except ErrorNegocio as error:
            return Resultado({"error": error.mensaje})

    # ───────────── Ubicar un texto ─────────────

    def _ubicar(self, texto: str) -> dict | None:
        """{nombre, lat, lng, fuente} del texto, o None si no se encuentra (no se inventan coordenadas)."""
        normal = clave(texto).replace("_", " ")
        if normal in AQUI or normal.startswith("mi ubicacion"):
            return {"nombre": "Tu ubicación", **self.ubicacion, "fuente": "GPS"} if self.ubicacion else None
        propios = self._buscar_propios(texto)
        if propios:
            l = propios[0]
            return {"nombre": l["nombre"], "lat": l["lat"], "lng": l["lng"], "fuente": "Kompás"}
        try:
            google = google_places.buscar_texto(texto, maximo=1)
        except google_places.ErrorGooglePlaces:
            google = []
        if google and esta_dentro_de_zona(google[0]):
            g = google[0]
            return {"nombre": g["nombre"], "lat": g["lat"], "lng": g["lng"], "fuente": "Google"}
        return None

    def _buscar_propios(self, texto: str, categoria: str | None = None) -> list[dict]:
        palabras = [p for p in clave(texto).split("_") if len(p) > 2]
        lista = self.lugares.buscar(self.ubicacion, None, categoria)
        if not palabras:
            return lista
        return [l for l in lista if all(p in clave(l["nombre"]) or p in (l.get("interes") or "") for p in palabras)]

    # ───────────── Herramientas ─────────────

    def buscar_lugares(self, texto: Any = "", categoria: Any = None) -> Resultado:
        categoria = (_lista([categoria], INTERESES) or [None])[0] if categoria else None
        propios = self._buscar_propios(_texto(texto), categoria)[:5]
        lista = [
            {"nombre": l["nombre"], "categoria": l["categoria"], "distancia_km": l.get("distancia_km"), "fuente": "Kompás"} for l in propios
        ]
        if not lista and _texto(texto):
            try:
                lista = [{"nombre": g["nombre"], "fuente": "Google"} for g in google_places.buscar_texto(_texto(texto))]
            except google_places.ErrorGooglePlaces:
                pass
        if not lista:
            return Resultado({"lugares": [], "mensaje": "No encontré lugares con esa búsqueda en la zona."}, {"tipo": "lugares", "total": 0})
        return Resultado({"lugares": lista, "nota": "distancia_km es en línea recta desde el usuario"}, {"tipo": "lugares", "total": len(lista)})

    def como_llegar(self, origen: Any = "", destino: Any = "", medios: Any = None) -> Resultado:
        texto_origen, texto_destino = _texto(origen) or "mi ubicación", _texto(destino)
        if not texto_destino:
            return Resultado({"error": "Falta el destino."})
        a, b = self._ubicar(texto_origen), self._ubicar(texto_destino)
        faltan = [t for t, p in ((texto_origen, a), (texto_destino, b)) if p is None]
        if faltan:
            return Resultado({"error": f"No encontré {', '.join(faltan)} en Toluca, Lerma o San Mateo Atenco.", "no_inventar": True})

        respuesta = self.rutas.alternativas({"lat": a["lat"], "lng": a["lng"]}, {"lat": b["lat"], "lng": b["lng"]})
        permitidos = set().union(*(MODOS_DE_MEDIO[m] for m in _lista(medios, MOVILIDADES))) if _lista(medios, MOVILIDADES) else None
        opciones = [o for o in respuesta["alternativas"] if permitidos is None or o["modo"] in permitidos] or respuesta["alternativas"]
        resumen = [
            {
                "modo": o["modo"],
                "linea": o.get("linea"),
                "con_transbordo": o.get("tipo") == "combinado",
                "sube_en": (o.get("parada_subida") or {}).get("nombre"),
                "baja_en": (o.get("parada_bajada") or {}).get("nombre"),
                "minutos_estimados": sum(v or 0 for v in o["tiempos"].values()),
                "espera_conocida": o["tiempos"].get("espera") is not None,
                "distancia_km": o.get("distancia_km"),
                "avisos": o.get("avisos", []),
            }
            for o in opciones
        ]
        mejor = opciones[0] if opciones else None
        nombre_a, nombre_b = a["nombre"], b["nombre"]
        resultado = Resultado(
            {
                "origen": nombre_a,
                "destino": nombre_b,
                "hay_transporte_publico_registrado": respuesta["datos_suficientes"],
                "mensaje": respuesta.get("mensaje"),
                "opciones": resumen,
                "fuente_ubicacion": [a["fuente"], b["fuente"]],
            },
            # Se guardan los textos que escribió el usuario, no datos de Google ni su ubicación
            {"tipo": "ruta", "id_ruta": mejor.get("id_ruta") if mejor else None, "origen": texto_origen, "destino": texto_destino},
            {
                "tipo": "ruta",
                "titulo": f"{nombre_a} → {nombre_b}",
                "subtitulo": (mejor.get("linea") or mejor["modo"]) if mejor else None,
                "id_ruta": mejor.get("id_ruta") if mejor else None,
                "origen": {"nombre": nombre_a, "lat": a["lat"], "lng": a["lng"]},
                "destino": {"nombre": nombre_b, "lat": b["lat"], "lng": b["lng"]},
                "alternativa": mejor,
            },
        )
        if mejor:
            resultado.ruta_consultada = {
                "id_ruta": mejor.get("id_ruta"),
                "origen": texto_origen,
                "destino": texto_destino,
                "transporte": {"pie": "caminando", "autobus": "autobus", "taxi": "taxi_app", "app": "taxi_app"}[mejor["modo"]],
            }
        return resultado

    def armar_salida(
        self, contexto: Any = None, presupuesto: Any = None, tiempo: Any = None, intereses: Any = None, hora_salida: Any = None, movilidad: Any = None
    ) -> Resultado:
        if self.ubicacion is None:
            return Resultado({"error": "Necesito la ubicación del usuario para buscar lugares cercanos."})
        ctx = clave(_texto(contexto))
        maximo, horas = _numero(presupuesto), _numero(tiempo)
        lista = _lista(intereses, INTERESES)
        faltan = [n for n, v in (("contexto", ctx in CONTEXTOS), ("presupuesto", maximo), ("tiempo", horas), ("intereses", lista)) if not v]
        if faltan:
            return Resultado({"error": f"Faltan datos para armar la salida: {', '.join(faltan)}. Pregúntaselos al usuario."})
        hora = _texto(hora_salida)
        try:
            datetime.strptime(hora, "%H:%M")
        except ValueError:
            hora = hora_actual()
        peticion = {
            "contexto": ctx,
            "presupuesto": {"min": 0, "max": maximo},
            "tiempo_horas": min(horas, 24),
            "intereses": lista,
            "movilidad": _lista(movilidad, MOVILIDADES) or ["caminando"],
            "origen": dict(self.ubicacion),
            "hora_salida": hora,
        }
        respuesta, id_plan = self.itinerarios.crear_y_guardar(self.usuario, peticion, origen_solicitud="asistente")
        planes = respuesta["planes"]
        resultado = Resultado(
            {
                "planes": [
                    {
                        "tipo": p["tipo"],
                        "paradas": [f"{x['nombre']} (llegada estimada {x['llegada_estimada']})" for x in p["paradas"]],
                        "duracion_horas_estimada": p["duracion_horas"],
                        "distancia_km": p["distancia_km"],
                        "explicacion": p["explicacion"],
                    }
                    for p in planes
                ],
                "mensaje": respuesta.get("mensaje"),
                "aviso": respuesta.get("aviso"),
                "plan_guardado": id_plan,
            },
            {"tipo": "plan", "id_plan": id_plan},
            {
                "tipo": "plan",
                "titulo": "Tu plan de salida",
                "subtitulo": " → ".join(x["nombre"] for x in planes[0]["paradas"]) if planes else "Sin planes recomendables",
                "id_plan": id_plan,
                "plan": planes[0] if planes else None,
            },
        )
        resultado.plan_creado = id_plan
        return resultado

    def mis_planes(self) -> Resultado:
        planes = self.itinerarios.del_usuario(self.usuario)[:10]
        lista = [
            {
                "id": p["id"],
                "interes_principal": p["categoria"],
                "transporte": p["transporte"],
                "tiempo_disponible_min": p["tiempo_disponible"],
                "fecha": p["fecha_plan"].strftime("%d/%m/%Y %H:%M") if p["fecha_plan"] else None,
            }
            for p in planes
        ]
        return Resultado({"planes": lista, "total": len(lista)}, {"tipo": "planes", "total": len(lista)})
