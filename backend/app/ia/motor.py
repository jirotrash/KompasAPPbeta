"""Motor de inferencia: hechos → encadenamiento hacia adelante → hasta 2 planes con explicación.

# TEMPORAL — Einar reemplaza con el motor de reglas definitivo.
# Basado en src/services/mock/motor.ts de la app, quitando lo que depende de costo u horario
# (la base todavía no tiene esos datos). Lo que Einar debe conservar es el CONTRATO:
#   recomendar(solicitud, lugares) -> {datos_suficientes, mensaje, aviso, planes, descartados}
#   - solicitud: el JSON del planificador (dict)
#   - lugares: dicts con la forma de app/servicios/serializar.py → lugar()
#   - nunca inventar datos: si faltan, planes = [] y un aviso claro
"""

from dataclasses import dataclass, field

from app.ia import hechos as H
from app.ia.reglas import MIN_CANDIDATOS, R6, REGLAS, REGLAS_LUGAR, REGLAS_TRAMO, como_salida, encadenar
from app.servicios.geo import a_hora, a_minutos_del_dia
from app.servicios.traslados import DISTANCIA_CORTA_KM, permite_pie, permite_taxi, tramo

MAX_PARADAS = 3

AVISO_SIN_COSTOS = "Todavía no tenemos costos ni horarios de los lugares; revisa antes de ir."
NOMBRES_INTERES = {"comer": "comer", "cafe": "café", "cultura": "cultura", "entretenimiento": "entretenimiento", "aire_libre": "aire libre"}


@dataclass
class Evaluado:
    lugar: dict
    incluir: bool
    cumplidas: list[str] = field(default_factory=list)
    descartes: list[dict] = field(default_factory=list)
    traslado: int = 0
    km: float = 0


def _punto(lugar: dict) -> dict:
    return {"lat": lugar["lat"], "lng": lugar["lng"]}


def _evaluar(lugar: dict, solicitud: dict) -> Evaluado:
    hechos, datos = H.calcular(lugar, solicitud)
    disparadas = encadenar(hechos, REGLAS_LUGAR)
    ev = Evaluado(lugar=lugar, incluir=hechos.get("incluir_en_plan", False), traslado=datos["traslado"] or 0, km=datos["km"] or 0)
    for regla in disparadas:
        if regla.entonces == "descartar":
            ev.descartes.append(como_salida(regla, contexto=solicitud["contexto"], minutos=datos["minutos"]))
        else:
            ev.cumplidas.append(regla.id)
    return ev


def _reglas_del_tramo(t: dict, movilidad: list[str]) -> list[str]:
    hechos = {
        "caminando": permite_pie(movilidad),
        "taxi_app": permite_taxi(movilidad),
        "distancia_corta": t["distancia_km"] <= DISTANCIA_CORTA_KM,
    }
    return [r.id for r in encadenar(hechos, REGLAS_TRAMO) if (r.entonces == "ir_a_pie") == (t["modo"] == "pie")]


def _armar_plan(seleccion: list[Evaluado], solicitud: dict) -> dict:
    """Secuencia origen → paradas con traslados y horas de llegada ESTIMADAS."""
    minuto = a_minutos_del_dia(solicitud["hora_salida"])
    anterior, nombre_anterior = solicitud["origen"], "Tu ubicación"
    tramos, paradas = [], []
    for ev in seleccion:
        lugar = ev.lugar
        t = tramo(anterior, _punto(lugar), solicitud["movilidad"], nombre_anterior, lugar["nombre"])
        tramos.append(t)
        minuto += t["duracion_min"]
        paradas.append({"lugar_id": lugar["_id"], "nombre": lugar["nombre"], "llegada_estimada": a_hora(minuto), "lugar": lugar})
        minuto += H.estancia(lugar)
        anterior, nombre_anterior = _punto(lugar), lugar["nombre"]
    return {
        "paradas": paradas,
        "tramos": tramos,
        "duracion": minuto - a_minutos_del_dia(solicitud["hora_salida"]),
        "distancia": sum(t["distancia_km"] for t in tramos),
    }


def _seleccionar(orden: list[Evaluado], solicitud: dict, maximo: int, variedad: bool) -> list[Evaluado]:
    """Agrega paradas en el orden dado mientras el recorrido quepa en el tiempo disponible."""
    elegidos: list[Evaluado] = []
    for ev in orden:
        if len(elegidos) == maximo:
            break
        if variedad and any(x.lugar["interes"] == ev.lugar["interes"] for x in elegidos):
            continue
        if _armar_plan([*elegidos, ev], solicitud)["duracion"] <= solicitud["tiempo_horas"] * 60:
            elegidos.append(ev)
    return elegidos


def _explicacion(tipo: str, seleccion: list[Evaluado], plan: dict, solicitud: dict) -> str:
    intereses = sorted({NOMBRES_INTERES.get(e.lugar["interes"], e.lugar["interes"]) for e in seleccion})
    horas = f"{solicitud['tiempo_horas']:g}"
    if tipo == "rapido":
        lejano = max(e.km for e in seleccion)
        texto = f"Lo más cercano: {len(seleccion)} lugares a menos de {lejano:.1f} km, ideal si tienes poco tiempo."
    else:
        texto = (
            f"{len(seleccion)} lugares variados ({', '.join(intereses)}) que coinciden con tus intereses; "
            f"el recorrido estimado (~{plan['duracion'] / 60:.1f} h) cabe en tus {horas} horas."
        )
    return f"{texto} {AVISO_SIN_COSTOS}"


def recomendar(solicitud: dict, lugares: list[dict]) -> dict:
    evaluados = [_evaluar(l, solicitud) for l in lugares]
    incluidos = [e for e in evaluados if e.incluir]
    descartados = [
        {"lugar": e.lugar, "lugar_id": e.lugar["_id"], "nombre": e.lugar["nombre"], "reglas": e.descartes}
        for e in evaluados
        if e.descartes
    ]

    # R6: ¬hay_candidatos → avisar_sin_informacion
    if encadenar({"hay_candidatos": len(incluidos) >= MIN_CANDIDATOS}, [R6]):
        aviso = "No tenemos información suficiente para armar un plan con esos datos. Prueba con otros intereses, más tiempo u otra forma de moverte."
        return {"datos_suficientes": False, "mensaje": aviso, "aviso": aviso, "planes": [], "descartados": descartados}

    por_cercania = sorted(incluidos, key=lambda e: e.traslado)
    propuestas = [
        ("equilibrado", _seleccionar(por_cercania, solicitud, MAX_PARADAS, variedad=True)),
        ("rapido", _seleccionar(por_cercania, solicitud, 2, variedad=False)),
    ]

    vistos: set[tuple[str, ...]] = set()
    planes = []
    for tipo, seleccion in propuestas:
        clave = tuple(sorted(e.lugar["_id"] for e in seleccion))
        if not seleccion or clave in vistos:
            continue
        vistos.add(clave)
        plan = _armar_plan(seleccion, solicitud)
        ids = {i for e in seleccion for i in e.cumplidas}
        ids |= {i for t in plan["tramos"] for i in _reglas_del_tramo(t, solicitud["movilidad"])}
        planes.append(
            {
                "tipo": tipo,
                "mejor_opcion": False,
                "costo": None,  # la base no tiene costos
                "duracion_horas": round(plan["duracion"] / 60, 1),
                "distancia_km": round(plan["distancia"], 1),
                "paradas": plan["paradas"],
                "tramos": plan["tramos"],
                "explicacion": _explicacion(tipo, seleccion, plan, solicitud),
                "reglas_cumplidas": [como_salida(REGLAS[i]) for i in sorted(ids, key=lambda x: int(x[1:]))],
            }
        )

    planes[0]["mejor_opcion"] = True
    return {"datos_suficientes": True, "mensaje": None, "aviso": AVISO_SIN_COSTOS, "planes": planes, "descartados": descartados}
