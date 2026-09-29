"""Arma hasta 3 itinerarios candidatos (equilibrado, rápido, cercano) con lugares de Google Places.

Solo ORGANIZA datos con el formato que espera hechos.py (INTEGRAR_IA.md §3). No decide si un plan es
recomendable: eso lo hacen construir_hechos() y evaluar() de Einar.

- Distancias y minutos son ESTIMADOS por coordenadas (haversine × 1.3; a pie ≈ 12 min/km).
- No hay tramos en autobús: si el usuario solo eligió transporte público, el tramo va sin minutos
  (no se inventa el tiempo) y el motor lo deja pendiente de verificación.
- Se prefieren lugares con priceRange y regularOpeningHours: sin ellos el candidato queda pendiente.
"""

from collections.abc import Callable
from datetime import datetime, timedelta

from app.ia.hechos import CONTEXTOS_CATEGORIAS, ESTANCIAS_MINUTOS, visita_en_horario
from app.servicios.geo import FACTOR_CALLES, distancia_km, minutos_caminando, minutos_en_auto
from app.servicios.traslados import DISTANCIA_CORTA_KM

MIN_VISITAS = 2
MAX_VISITAS = 3


def modos_permitidos(movilidad: list[str]) -> set[str]:
    """Modos con los que el MVP puede estimar un tramo (a pie o taxi/app)."""
    modos = set(movilidad)
    if "combinado" in modos:
        modos |= {"caminando", "taxi_app"}
    return modos & {"caminando", "taxi_app"}


def tramo(a: dict, b: dict, movilidad: list[str]) -> dict:
    """Tramo para hechos.py: {modo, km, minutos, estimado}. A pie si es cerca o si no eligió taxi."""
    km = round(distancia_km(a, b) * FACTOR_CALLES, 2)
    permitidos = modos_permitidos(movilidad)
    if "caminando" in permitidos and (km <= DISTANCIA_CORTA_KM or "taxi_app" not in permitidos):
        return {"modo": "caminando", "km": km, "minutos": minutos_caminando(km), "estimado": True}
    if "taxi_app" in permitidos:
        # Sin costo_por_persona: no hay tarifa real de una plataforma (el presupuesto queda desconocido)
        return {"modo": "taxi_app", "km": km, "minutos": minutos_en_auto(km), "estimado": True}
    # Solo transporte público: no hay líneas ni paradas verificadas, no se inventan minutos
    return {"modo": "transporte_publico", "km": km, "minutos": None, "estimado": True}


def armar_itinerario(lugares: list[dict], origen: dict, salida: datetime, movilidad: list[str]) -> dict:
    """Secuencia origen → lugares con llegadas coherentes: llegada = salida anterior + traslado."""
    reloj: datetime | None = salida
    anterior = origen
    visitas, tramos = [], []
    for lugar in lugares:
        t = tramo(anterior, lugar, movilidad)
        tramos.append(t)
        llegada = reloj + timedelta(minutes=t["minutos"]) if reloj is not None and t["minutos"] is not None else None
        visitas.append(
            {
                "place_id": lugar["place_id"],
                "nombre": lugar["nombre"],
                "categoria": lugar["categoria"],
                "llegada_estimada": llegada.isoformat() if llegada else None,
                "horario": lugar.get("horario"),
                "nivel_precio": lugar.get("nivel_precio"),
                "rango_precio": lugar.get("rango_precio"),
                "consultado_en": lugar["consultado_en"],
                # estancia_minutos se omite: hechos.py usa su tabla por categoría
            }
        )
        reloj = llegada + timedelta(minutes=ESTANCIAS_MINUTOS[lugar["categoria"]]) if llegada else None
        anterior = lugar
    return {"visitas": visitas, "tramos": tramos, "regreso_incluido": False, "_fin": reloj}


def _viable(itinerario: dict, salida: datetime, tiempo_minutos: float, presupuesto: float) -> bool:
    """Filtro previo para no proponer lo que ya se sabe que falla (el motor hace la evaluación real)."""
    ultima = itinerario["visitas"][-1]
    fin = itinerario["_fin"]
    if fin is not None:
        if (fin - salida).total_seconds() / 60 > tiempo_minutos:
            return False
        estancia = ESTANCIAS_MINUTOS[ultima["categoria"]]
        if visita_en_horario(ultima["horario"], ultima["llegada_estimada"], estancia) is False:
            return False  # se sabe que está cerrado durante la visita
    minimos = [v["rango_precio"]["min"] for v in itinerario["visitas"] if v["rango_precio"] and v["rango_precio"]["min"] is not None]
    return sum(minimos) <= presupuesto


def _puntaje(lugar: dict, solicitud: dict) -> float:
    datos_completos = bool(lugar.get("rango_precio")) and bool(lugar.get("horario"))
    return (
        (2 if datos_completos else 0)
        + (2 if lugar["categoria"] in solicitud["intereses"] else 0)
        + (1 if lugar["categoria"] in CONTEXTOS_CATEGORIAS.get(solicitud["contexto"], ()) else 0)
        + (lugar.get("calificacion") or 0) / 5
    )


def _elegir(
    pool: list[dict], orden: Callable[[dict, dict], float], maximo: int, variedad: bool,
    solicitud: dict, origen: dict, salida: datetime,
) -> list[dict]:
    """Agrega lugares uno por uno (el primero viable según `orden`) hasta `maximo`."""
    elegidos: list[dict] = []
    while len(elegidos) < maximo:
        posicion = elegidos[-1] if elegidos else origen
        categorias = {l["categoria"] for l in elegidos}
        opciones = [l for l in pool if l not in elegidos and not (variedad and l["categoria"] in categorias)]
        for lugar in sorted(opciones, key=lambda l: orden(l, posicion)):
            prueba = armar_itinerario([*elegidos, lugar], origen, salida, solicitud["movilidad"])
            if _viable(prueba, salida, solicitud["tiempo_minutos"], solicitud["presupuesto_por_persona"]):
                elegidos.append(lugar)
                break
        else:
            break
    return elegidos if len(elegidos) >= MIN_VISITAS else []


def armar_candidatos(solicitud: dict, origen: dict, lugares: list[dict], salida: datetime) -> list[dict]:
    """Hasta 3 candidatos distintos: [{tipo, lugares, itinerario}] (itinerario con el formato de hechos.py)."""
    pool = [l for l in lugares if l.get("categoria") in ESTANCIAS_MINUTOS]
    estrategias = [
        # equilibrado: mejores datos, intereses y contexto, con categorías distintas
        ("equilibrado", lambda l, _p: -_puntaje(l, solicitud), MAX_VISITAS, True),
        # rápido: estancias cortas y cerca de donde se está
        ("rapido", lambda l, p: ESTANCIAS_MINUTOS[l["categoria"]] + distancia_km(p, l) * 12, MIN_VISITAS, False),
        # cercano: siempre el siguiente lugar más cercano
        ("cercano", lambda l, p: distancia_km(p, l), MAX_VISITAS, False),
    ]
    candidatos, vistos = [], set()
    for tipo, orden, maximo, variedad in estrategias:
        elegidos = _elegir(pool, orden, maximo, variedad, solicitud, origen, salida)
        clave = frozenset(l["place_id"] for l in elegidos)
        if not elegidos or clave in vistos:
            continue
        vistos.add(clave)
        itinerario = armar_itinerario(elegidos, origen, salida, solicitud["movilidad"])
        itinerario.pop("_fin")
        candidatos.append({"tipo": tipo, "lugares": elegidos, "itinerario": itinerario})
    return candidatos
