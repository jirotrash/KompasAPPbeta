"""Sistema experto de reglas heurísticas base para transporte urbano (baseline determinista).

Evalúa las condiciones del traslado mediante reglas condicionales deterministas de negocio
para actuar como salvaguarda (fallback) y línea base comparativa frente al modelo predictivo.
(Trazabilidad académica: adaptado de la práctica p01reglafija).
"""

HORAS_PICO = {7, 8, 9, 18, 19, 20}


def evaluar_traslado_regla_fija(
    distancia_km: float,
    presupuesto_mxn: float,
    hora_dia: int = 12,
    clima_lluvia: bool = False,
) -> dict:
    """Evalúa las condiciones del traslado mediante reglas fijas deterministas.

    Args:
        distancia_km: Distancia del trayecto en kilómetros.
        presupuesto_mxn: Presupuesto disponible en pesos mexicanos.
        hora_dia: Hora del traslado (0-23).
        clima_lluvia: Booleano indicando si está lloviendo.

    Returns:
        dict con: modo_recomendado, regla_activada, explicacion y metodo="regla_fija".
    """
    es_hora_pico = hora_dia in HORAS_PICO

    # Regla 1: Trayectos cortos con buen clima
    if distancia_km <= 1.5 and not clima_lluvia:
        return {
            "modo_recomendado": "caminando",
            "regla_activada": "R1_CORTA_DISTANCIA_BUEN_CLIMA",
            "explicacion": f"Distancia corta ({distancia_km:.1f} km) y clima sin lluvia: se recomienda caminar por economía y salud.",
            "metodo": "regla_fija",
        }

    # Regla 2: Clima adverso o tráfico pico con presupuesto suficiente
    if clima_lluvia or (es_hora_pico and presupuesto_mxn >= 100.0):
        motivo = "lluvia intensa" if clima_lluvia else "hora pico con alto tráfico"
        return {
            "modo_recomendado": "auto_privado",
            "regla_activada": "R2_CLIMA_O_HORA_PICO_PRESUPUESTO_ALTO",
            "explicacion": f"Condición de {motivo} con presupuesto suficiente (${presupuesto_mxn:.0f} MXN): se recomienda auto privado o taxi.",
            "metodo": "regla_fija",
        }

    # Regla 3: Distancia media con presupuesto limitado
    if distancia_km <= 4.0 and not clima_lluvia and presupuesto_mxn < 40.0:
        return {
            "modo_recomendado": "transporte_publico",
            "regla_activada": "R3_DISTANCIA_MEDIA_PRESUPUESTO_BAJO",
            "explicacion": f"Distancia moderada ({distancia_km:.1f} km) y presupuesto ajustado: transporte público es la opción económica óptima.",
            "metodo": "regla_fija",
        }

    # Regla 4: Distancia superior a caminata con presupuesto moderado
    if distancia_km > 1.5 and presupuesto_mxn < 80.0:
        return {
            "modo_recomendado": "transporte_publico",
            "regla_activada": "R4_DISTANCIA_LARGA_PRESUPUESTO_MODERADO",
            "explicacion": f"Distancia de {distancia_km:.1f} km con presupuesto menor a $80 MXN: el transporte público optimiza el gasto.",
            "metodo": "regla_fija",
        }

    # Regla 5: Fallback por defecto según presupuesto
    if presupuesto_mxn >= 80.0:
        return {
            "modo_recomendado": "auto_privado",
            "regla_activada": "R5_DEFECTO_PRESUPUESTO_CONFORT",
            "explicacion": "Presupuesto adecuado para traslado directo y cómodo en auto privado o taxi.",
            "metodo": "regla_fija",
        }

    return {
        "modo_recomendado": "transporte_publico",
        "regla_activada": "R5_DEFECTO_TRANSPORTE_PUBLICO",
        "explicacion": "Recomendación general estándar en transporte público de la red urbana.",
        "metodo": "regla_fija",
    }

