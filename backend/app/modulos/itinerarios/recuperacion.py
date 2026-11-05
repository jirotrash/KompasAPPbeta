"""Recupera las mismas paradas, en el mismo orden, con datos actuales y las reglas existentes.

No busca lugares sustitutos ni cambia R01–R20. Un plan que ahora incumple las reglas se
muestra como descartado/pendiente, conservando el registro original del usuario.
"""

from datetime import datetime

from app.compartido.geo import esta_dentro_de_zona
from app.ia.hechos import construir_hechos
from app.ia.motor import evaluar
from app.ia.planificador import armar_itinerario
from app.ia.servicio import BASE, _explicacion, _hhmm, _lugar_app, _reglas, _tramos_app, traducir_solicitud


def reconstruir(peticion: dict, lugares: list[dict], tipo: str, ahora: datetime) -> dict:
    solicitud = traducir_solicitud(peticion, ahora)
    salida = datetime.fromisoformat(solicitud["fecha_hora_salida"])
    itinerario = armar_itinerario(lugares, peticion["origen"], salida, solicitud["movilidad"])
    itinerario.pop("_fin")
    hechos = construir_hechos(solicitud, itinerario, ahora=ahora, zona_validada=esta_dentro_de_zona(peticion["origen"]))
    evaluacion = evaluar(hechos["hechos"], BASE)
    aviso = f"Recorrido revisado para salir hoy a las {peticion['hora_salida']} desde el punto de partida actual."
    advertencias = list(dict.fromkeys([aviso, *hechos["advertencias"], *evaluacion["advertencias"]]))
    respuesta = {
        "datos_suficientes": evaluacion["estado"] == "recomendable",
        "mensaje": None,
        "aviso": " ".join(advertencias),
        "advertencias": advertencias,
        "version_reglas": BASE["version"],
        "planes": [],
        "descartados": [],
    }
    if evaluacion["estado"] != "recomendable":
        respuesta["mensaje"] = "El plan sigue guardado, pero ahora no cumple todas las condiciones para recomendarlo. Revisa los motivos."
        respuesta["descartados"] = [{
            "tipo": tipo, "nombre": " → ".join(l["nombre"] for l in lugares),
            "lugares": [l["nombre"] for l in lugares], "estado": evaluacion["estado"],
            "reglas": _reglas(evaluacion), "datos_faltantes": hechos["datos_faltantes"],
        }]
        return respuesta
    resumen = hechos["resumen"]
    respuesta["planes"] = [{
        "tipo": tipo, "estado": "recomendable", "mejor_opcion": False,
        "puntuacion": evaluacion["puntuacion_preferencias"], "costo": None,
        "rango_costo": {
            "min": resumen["minimo_acreditado_mxn"], "max": resumen["maximo_considerado_mxn"], "moneda": "MXN",
        },
        "duracion_horas": round(resumen["duracion_total_minutos"] / 60, 1),
        "distancia_km": round(sum(t["km"] for t in itinerario["tramos"]), 1),
        "paradas": [
            {"lugar_id": v["place_id"], "nombre": v["nombre"], "llegada_estimada": _hhmm(v["llegada_estimada"]), "lugar": _lugar_app(l)}
            for v, l in zip(itinerario["visitas"], lugares)
        ],
        "tramos": _tramos_app({"lugares": lugares, "itinerario": itinerario}),
        "explicacion": _explicacion(evaluacion["hechos_iniciales"], resumen, solicitud, evaluacion["puntuacion_preferencias"]),
        "reglas_cumplidas": _reglas(evaluacion),
    }]
    return respuesta
