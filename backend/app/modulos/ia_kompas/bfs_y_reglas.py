"""Búsqueda en Anchura (BFS) y Sistema de Reglas Fijas para planes y traslados en Kompás (Práctica 01).

Integra:
- `buscar_ruta_bfs`: Adaptación de `p01BFS.py` para encontrar la ruta con menor número de escalas
  intermedias entre zonas turísticas del Valle de Toluca.
- `predecir_con_reglas`: Adaptación de `p01reglafija.py` para evaluar con condiciones deterministas
  manuales si un plan/traslado turístico es recomendable (`plan_viable` 0 o 1) y qué medio de
  transporte sugiere.
"""

from app.modulos.ia_kompas.busqueda_escalas import GRAFO_BASE_KOMPAS, buscar_ruta_bfs


def predecir_con_reglas(
    distancia_km: float,
    presupuesto_mxn: float,
    rating_lugar: float = 4.2,
    num_paradas: int = 3,
    trafico_nivel: int = 5,
) -> dict:
    """Evalúa un plan o traslado de Kompás mediante condiciones manuales fijas (`p01reglafija.py`).

    Retorna:
    - `plan_viable`: `1` (recomendable / viable) o `0` (no recomendable / requiere ajuste)
    - `etiqueta_viabilidad`: `'viable'` o `'no_viable'`
    - `modo_recomendado`: `'caminando'`, `'transporte_publico'` o `'auto_privado'`
    - `regla_activada`: identificador de la regla determinista activada
    - `explicacion`: justificación legible para el usuario
    """
    # 1. Regla de transporte determinista
    if distancia_km <= 2.0 and trafico_nivel <= 6 and num_paradas <= 3:
        modo = "caminando"
    elif presupuesto_mxn >= 220.0 and (trafico_nivel >= 7 or distancia_km > 10.0):
        modo = "auto_privado"
    else:
        modo = "transporte_publico"

    # 2. Reglas fijas manuales de viabilidad (baseline heurístico simple que no captura todas las
    # interacciones no lineales entre paradas, tráfico y costo por km que sí aprende el árbol)
    if presupuesto_mxn < 80.0 and num_paradas >= 3:
        return {
            "plan_viable": 0,
            "etiqueta_viabilidad": "no_viable",
            "modo_recomendado": modo,
            "regla_activada": "R1_PRESUPUESTO_INSUFICIENTE_MULTIPLES_PARADAS",
            "explicacion": (
                f"Presupuesto bajo (${presupuesto_mxn:.0f} MXN) para cubrir {num_paradas} paradas turísticas."
            ),
        }

    if distancia_km > 16.0 and trafico_nivel >= 8:
        return {
            "plan_viable": 0,
            "etiqueta_viabilidad": "no_viable",
            "modo_recomendado": modo,
            "regla_activada": "R2_DISTANCIA_LARGA_TRAFICO_SEVERO",
            "explicacion": (
                f"Distancia extensa ({distancia_km:.1f} km) combinada con tráfico alto (nivel {trafico_nivel}/10)."
            ),
        }

    if rating_lugar < 3.4:
        return {
            "plan_viable": 0,
            "etiqueta_viabilidad": "no_viable",
            "modo_recomendado": modo,
            "regla_activada": "R3_CALIFICACION_BAJA_DESTINO",
            "explicacion": f"Calificación promedio del lugar ({rating_lugar:.1f}★) por debajo del umbral recomendado.",
        }

    if presupuesto_mxn >= 180.0:
        return {
            "plan_viable": 1,
            "etiqueta_viabilidad": "viable",
            "modo_recomendado": modo,
            "regla_activada": "R4_PRESUPUESTO_HOLGADO",
            "explicacion": (
                f"Presupuesto amplio (${presupuesto_mxn:.0f} MXN) para recorrer {num_paradas} paradas en {modo}."
            ),
        }

    if distancia_km <= 10.0 and num_paradas <= 4:
        return {
            "plan_viable": 1,
            "etiqueta_viabilidad": "viable",
            "modo_recomendado": modo,
            "regla_activada": "R5_RECORRIDO_COMPACTO_EQUILIBRADO",
            "explicacion": (
                f"Recorrido compacto ({distancia_km:.1f} km y {num_paradas} paradas) viable en {modo}."
            ),
        }

    return {
        "plan_viable": 0,
        "etiqueta_viabilidad": "no_viable",
        "modo_recomendado": modo,
        "regla_activada": "R6_DEFECTO_PRESUPUESTO_AJUSTADO_DISTANCIA_MEDIA",
        "explicacion": (
            f"Presupuesto moderado (${presupuesto_mxn:.0f} MXN) frente a {distancia_km:.1f} km y {num_paradas} paradas."
        ),
    }


__all__ = ["GRAFO_BASE_KOMPAS", "buscar_ruta_bfs", "predecir_con_reglas"]
