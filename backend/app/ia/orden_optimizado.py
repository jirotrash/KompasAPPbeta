"""Orden de las paradas de cada plan con el algoritmo genético, DESPUÉS de recomendar().

No cambia lo que decide el sistema experto: mismos lugares, mismo estado, puntuación, reglas y
explicación. Solo se cambia el orden de visita si:
  1. el genético encuentra un recorrido más corto,
  2. no deja más paradas fuera de horario que el orden original, y
  3. el itinerario reordenado sigue siendo `recomendable` para construir_hechos() + evaluar() de Einar.
Con una sola parada no se ejecuta.
"""

from datetime import datetime
from typing import Any

from app.compartido.geo import esta_dentro_de_zona
from app.ia import planificador
from app.ia.algoritmo_genetico import ordenar_paradas
from app.ia.hechos import construir_hechos
from app.ia.motor import evaluar
from app.ia.servicio import BASE, _hhmm, _lugar_app, _tramos_app, traducir_solicitud

# Semilla fija: la misma petición regresa siempre el mismo orden
SEMILLA = 2026


def _ordenar_plan(plan: dict, lugares: list[dict], solicitud: dict, solicitud_app: dict, ahora: datetime) -> dict[str, Any]:
    origen = {"lat": solicitud_app["origen"]["lat"], "lng": solicitud_app["origen"]["lng"]}
    salida = datetime.fromisoformat(solicitud["fecha_hora_salida"])
    ga = ordenar_paradas(
        [{"lat": l["lat"], "lng": l["lng"], "horario": l.get("horario"), "categoria": l["categoria"]} for l in lugares],
        origen,
        salida,
        solicitud["movilidad"],
        semilla=SEMILLA,
    )
    original = list(range(len(lugares)))
    aplicado = False
    if ga["mejor_orden"] != original and ga["distancia_km"] < ga["distancia_original_km"] - 1e-9:
        nuevos = [lugares[i] for i in ga["mejor_orden"]]
        itinerario = planificador.armar_itinerario(nuevos, origen, salida, solicitud["movilidad"])
        itinerario.pop("_fin")
        r = construir_hechos(solicitud, itinerario, ahora=ahora, zona_validada=esta_dentro_de_zona(origen))
        if evaluar(r["hechos"], BASE)["estado"] == "recomendable":
            plan["paradas"] = [
                {"lugar_id": v["place_id"], "nombre": v["nombre"], "llegada_estimada": _hhmm(v["llegada_estimada"]), "lugar": _lugar_app(l)}
                for v, l in zip(itinerario["visitas"], nuevos)
            ]
            plan["tramos"] = _tramos_app({"lugares": nuevos, "itinerario": itinerario})
            plan["distancia_km"] = round(sum(t["km"] for t in itinerario["tramos"]), 1)
            plan["duracion_horas"] = round(r["resumen"]["duracion_total_minutos"] / 60, 1)
            aplicado = True

    despues = ga["distancia_km"] if aplicado else ga["distancia_original_km"]
    plan["orden_optimizado"] = {
        "distancia_antes_km": round(ga["distancia_original_km"], 2),
        "distancia_despues_km": round(despues, 2),
        "generaciones": ga["parametros"]["generaciones"],
        "generacion_mejor": ga["generacion_mejor"],
        "aplicado": aplicado,
    }
    return {
        "origen": "itinerario",
        "tipo_plan": plan["tipo"],
        "paradas": len(lugares),
        "km_antes": round(ga["distancia_original_km"], 3),
        "km_despues": round(despues, 3),
        "aplicado": aplicado,
        "generaciones": ga["parametros"]["generaciones"],
        "generacion_mejor": ga["generacion_mejor"],
        "brecha_vs_optimo_pct": ga["brecha_vs_optimo_%"],
        "historial_mejor": [h["mejor"] for h in ga["historial"]],
        "historial_promedio": [h["promedio"] for h in ga["historial"]],
        "ms": ga["ms"],
    }


def optimizar_orden(respuesta: dict, solicitud_app: dict, lugares_google: list[dict], ahora: datetime) -> list[dict]:
    """Reordena en su lugar las paradas de cada plan de `respuesta`. Regresa un registro por ejecución."""
    por_id = {l["place_id"]: l for l in lugares_google}
    solicitud = traducir_solicitud(solicitud_app, ahora)
    ejecuciones = []
    for plan in respuesta["planes"]:
        lugares = [por_id[p["lugar_id"]] for p in plan["paradas"] if p["lugar_id"] in por_id]
        if len(lugares) < 2 or len(lugares) != len(plan["paradas"]):
            continue
        ejecuciones.append(_ordenar_plan(plan, lugares, solicitud, solicitud_app, ahora))
    return ejecuciones
