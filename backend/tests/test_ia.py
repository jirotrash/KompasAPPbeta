"""Sistema experto de Einar conectado al backend: casos de INTEGRAR_IA.md §4 (sin API, sin BD, sin Google).

Itinerario: 2 visitas a pie (café y restaurante), horario 08:00–22:00, rango de precio 100–180 MXN,
presupuesto 400, 4 horas, en pareja. Reloj fijo para que el resultado sea reproducible.
"""

from datetime import datetime

import pytest

from app.ia.hechos import construir_hechos
from app.ia.motor import cargar_base, evaluar

AHORA = datetime.fromisoformat("2026-09-30T17:59:00-06:00")
HORARIO = {
    "periods": [
        {"open": {"day": dia, "hour": 8, "minute": 0}, "close": {"day": dia, "hour": 22, "minute": 0}} for dia in range(7)
    ]
}
SOLICITUD = {
    "contexto": "pareja",
    "intereses": ["comer", "cafe"],
    "presupuesto_por_persona": 400,
    "tiempo_minutos": 240,
    "movilidad": ["caminando"],
    "fecha_hora_salida": "2026-09-30T18:00:00-06:00",
    "incluir_regreso": False,
}


def itinerario(rango_precio: dict | None) -> dict:
    visita = {"horario": HORARIO, "rango_precio": rango_precio, "consultado_en": "2026-09-30T17:59:00-06:00"}
    return {
        "visitas": [
            {**visita, "place_id": "cafe", "nombre": "Café", "categoria": "cafe", "llegada_estimada": "2026-09-30T18:12:00-06:00"},
            {**visita, "place_id": "restaurante", "nombre": "Restaurante", "categoria": "comer", "llegada_estimada": "2026-09-30T19:00:00-06:00"},
        ],
        "tramos": [
            {"modo": "caminando", "km": 0.9, "minutos": 12, "estimado": True},
            {"modo": "caminando", "km": 0.5, "minutos": 6, "estimado": True},
        ],
        "regreso_incluido": False,
    }


@pytest.fixture(scope="module")
def base() -> dict:
    return cargar_base()


def evaluar_itinerario(base: dict, rango_precio: dict | None) -> dict:
    resultado = construir_hechos(SOLICITUD, itinerario(rango_precio), ahora=AHORA, zona_validada=True)
    return evaluar(resultado["hechos"], base)


def test_con_rango_de_precio_es_recomendable_con_6_puntos(base):
    evaluacion = evaluar_itinerario(base, {"min": 100, "max": 180, "moneda": "MXN"})
    assert evaluacion["estado"] == "recomendable"
    assert evaluacion["puntuacion_preferencias"] == 6
    assert [paso["regla_id"] for paso in evaluacion["traza"]] == ["R11", "R13", "R15", "R16", "R17", "R18", "R19", "R20"]


def test_sin_rango_de_precio_queda_pendiente_de_verificacion(base):
    evaluacion = evaluar_itinerario(base, None)
    assert evaluacion["estado"] == "pendiente_verificacion"
    assert evaluacion["puntuacion_preferencias"] is None
    assert [paso["regla_id"] for paso in evaluacion["traza"]] == ["R09", "R11", "R13"]
