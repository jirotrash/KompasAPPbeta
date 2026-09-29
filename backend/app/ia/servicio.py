"""recomendar(): solicitud de la app + lugares de Google → planes para "Tus planes" (INTEGRAR_IA.md §3).

1. Traduce la solicitud de la app al formato de hechos.py.
2. Valida la zona piloto AQUÍ, en el servidor (nunca se toma del JSON del usuario).
3. El planificador arma hasta 3 itinerarios candidatos.
4. Por cada uno: construir_hechos() → evaluar() de Einar (sin cambiar su lógica).
5. `recomendable` → planes (ordenados por puntuación); el resto → descartados con su estado y motivos.
"""

from datetime import datetime

from app.ia import planificador
from app.ia.hechos import construir_hechos
from app.ia.motor import cargar_base, evaluar
from app.servicios.geo import HORA_MEXICO, esta_dentro_de_zona, geo_punto

# Las reglas R01–R20 se leen y validan una sola vez al iniciar
BASE = cargar_base()

TIPOS = {"equilibrado": "Plan equilibrado", "rapido": "Plan rápido", "cercano": "Plan cercano"}
CATEGORIAS = {"comer": "Comer", "cafe": "Café", "cultura": "Cultura", "entretenimiento": "Entretenimiento", "aire_libre": "Aire libre"}
MODO_APP = {"caminando": "pie", "taxi_app": "taxi", "transporte_publico": "autobus"}
AVISO_TAXI = "El tiempo no considera el tráfico. La tarifa la define el proveedor."
SIN_INFORMACION = (
    "No tenemos información suficiente para recomendar un plan con esos datos. "
    "Revisa los planes pendientes de verificar o prueba con otros intereses, más tiempo u otra forma de moverte."
)


def traducir_solicitud(solicitud_app: dict, ahora: datetime) -> dict:
    """App (POST /api/itinerarios) → solicitud de hechos.py."""
    hora, minuto = (int(x) for x in solicitud_app["hora_salida"].split(":"))
    salida = datetime.combine(ahora.astimezone(HORA_MEXICO).date(), datetime.min.time(), HORA_MEXICO)
    return {
        "contexto": solicitud_app["contexto"],
        "intereses": list(solicitud_app["intereses"]),
        "movilidad": list(solicitud_app["movilidad"]),
        "presupuesto_por_persona": solicitud_app["presupuesto"]["max"],
        "tiempo_minutos": solicitud_app["tiempo_horas"] * 60,
        "fecha_hora_salida": salida.replace(hour=hora, minute=minuto).isoformat(),
        "incluir_regreso": False,  # MVP
    }


def _hhmm(iso: str | None) -> str | None:
    return datetime.fromisoformat(iso).astimezone(HORA_MEXICO).strftime("%H:%M") if iso else None


def _lugar_app(l: dict) -> dict:
    """Lugar de Google con la forma que usa la app (src/types/dominio.ts → Lugar). No se guarda en MySQL."""
    fecha = l["consultado_en"][:10]
    return {
        "_id": l["place_id"],
        "nombre": l["nombre"],
        "lat": l["lat"],
        "lng": l["lng"],
        "ubicacion": geo_punto(l["lat"], l["lng"]),
        "categoria": CATEGORIAS.get(l["categoria"], l["categoria"]),
        "interes": l["categoria"],
        "nivel_precio": l.get("nivel_precio"),
        "rango_precio": l.get("rango_precio"),
        "calificacion": {"valor": l["calificacion"], "fuente": "Google", "fecha": fecha} if l.get("calificacion") else None,
        "total_resenas": l.get("total_resenas"),
        "horario": None,  # el horario de Google lo usa el motor; la app no lo pinta
        "costo_promedio": None,  # Google no da costo exacto
        "afluencia": None,
        "contextos": [],
        "fuente": "Google",
        "consultado_en": l["consultado_en"],
    }


def _tramos_app(candidato: dict, origen_nombre: str = "Tu ubicación") -> list[dict]:
    nombres = [origen_nombre] + [l["nombre"] for l in candidato["lugares"]]
    salida = []
    for i, t in enumerate(candidato["itinerario"]["tramos"]):
        salida.append(
            {
                "modo": MODO_APP[t["modo"]],
                "duracion_min": t["minutos"],
                "minutos": t["minutos"],
                "distancia_km": t["km"],
                "desde": nombres[i],
                "hasta": nombres[i + 1],
                "estimado": True,
                "aviso": AVISO_TAXI if t["modo"] == "taxi_app" else None,
            }
        )
    return salida


def _explicacion(hechos: dict, resumen: dict, solicitud: dict, puntos: int) -> str:
    """Explicación en español a partir de los hechos que sí se cumplieron (no se afirma nada sin dato)."""
    horas = resumen["duracion_total_minutos"] / 60
    partes = [
        "Los lugares abren durante toda la visita",
        f"el rango de precios cabe en tus ${solicitud['presupuesto_por_persona']:,.0f} por persona",
        f"el recorrido estimado (~{horas:.1f} h) cabe en tus {solicitud['tiempo_minutos'] / 60:g} horas",
    ]
    extras = []
    if hechos["contexto_compatible"]:
        extras.append(f"es adecuado para salir en plan {solicitud['contexto']}")
    if hechos["intereses_compatibles"]:
        extras.append("coincide con tus intereses")
    if hechos["poca_caminata"]:
        extras.append(f"camina poco ({resumen['caminata_km']:.1f} km)")
    texto = ", ".join(partes[:-1]) + " y " + partes[-1] + "."
    if extras:
        texto += " Además " + ", ".join(extras) + "."
    return f"{texto} Puntuación de preferencias: {puntos} de 6."


def _reglas(evaluacion: dict) -> list[dict]:
    """Traza del motor → reglas que se cumplieron (id + explicación de Einar), en orden de inferencia."""
    return [{"id": p["regla_id"], "descripcion": p["explicacion"]} for p in evaluacion["traza"]]


def recomendar(solicitud_app: dict, lugares_google: list[dict], ahora: datetime) -> dict:
    """Respuesta para la app: {datos_suficientes, mensaje, aviso, advertencias, version_reglas, planes, descartados}."""
    origen = {"lat": solicitud_app["origen"]["lat"], "lng": solicitud_app["origen"]["lng"]}
    zona_ok = esta_dentro_de_zona(origen)
    solicitud = traducir_solicitud(solicitud_app, ahora)
    salida = datetime.fromisoformat(solicitud["fecha_hora_salida"])
    candidatos = planificador.armar_candidatos(solicitud, origen, lugares_google, salida)

    planes, descartados, advertencias = [], [], []
    for candidato in candidatos:
        r = construir_hechos(solicitud, candidato["itinerario"], ahora=ahora, zona_validada=zona_ok)
        e = evaluar(r["hechos"], BASE)
        advertencias += r["advertencias"] + e["advertencias"]
        nombres = [l["nombre"] for l in candidato["lugares"]]
        if e["estado"] == "recomendable":
            resumen = r["resumen"]
            rango = (
                {"min": resumen["minimo_acreditado_mxn"], "max": resumen["maximo_considerado_mxn"], "moneda": "MXN"}
                if resumen["maximo_considerado_mxn"] is not None
                else None
            )
            planes.append(
                {
                    "tipo": candidato["tipo"],
                    "estado": e["estado"],
                    "mejor_opcion": False,
                    "puntuacion": e["puntuacion_preferencias"],
                    "costo": None,  # Google no da precios exactos
                    "rango_costo": rango,  # estimación por persona, no es una cotización
                    "duracion_horas": round(resumen["duracion_total_minutos"] / 60, 1),
                    "distancia_km": round(sum(t["km"] for t in candidato["itinerario"]["tramos"]), 1),
                    "paradas": [
                        {
                            "lugar_id": v["place_id"],
                            "nombre": v["nombre"],
                            "llegada_estimada": _hhmm(v["llegada_estimada"]),
                            "lugar": _lugar_app(l),
                        }
                        for v, l in zip(candidato["itinerario"]["visitas"], candidato["lugares"])
                    ],
                    "tramos": _tramos_app(candidato),
                    "explicacion": _explicacion(e["hechos_iniciales"], resumen, solicitud, e["puntuacion_preferencias"]),
                    "reglas_cumplidas": _reglas(e),
                }
            )
        else:
            descartados.append(
                {
                    "tipo": candidato["tipo"],
                    "nombre": f"{TIPOS[candidato['tipo']]}: {' → '.join(nombres)}",
                    "lugares": nombres,
                    "estado": e["estado"],
                    "reglas": _reglas(e),
                    "datos_faltantes": r["datos_faltantes"],
                }
            )

    planes.sort(key=lambda p: p["puntuacion"], reverse=True)
    if planes:
        planes[0]["mejor_opcion"] = True
    advertencias = list(dict.fromkeys(advertencias))
    mensaje = None if planes else SIN_INFORMACION
    return {
        "datos_suficientes": bool(planes),
        "mensaje": mensaje,
        "aviso": " ".join(advertencias) or mensaje,
        "advertencias": advertencias,
        "version_reglas": BASE["version"],
        "planes": planes,
        "descartados": descartados,
    }
