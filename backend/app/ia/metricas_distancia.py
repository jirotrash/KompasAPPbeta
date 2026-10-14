# ============================================================
# Métricas de distancia para Kompás: Euclidiana y Manhattan
# ============================================================
# Euclidiana: línea recta entre dos puntos      d = √(Δx² + Δy²)
# Manhattan:  recorrido por "cuadras" en ángulo recto   d = |Δx| + |Δy|
#
# Se usan en dos lugares:
# 1. Laboratorio académico (/api/distancias/plano y la pantalla "Distancias" de la app):
#    el usuario coloca dos puntos en un plano cartesiano y se comparan ambas métricas.
# 2. Cálculo real de Kompás (servicios/geo.py): la distancia por calles se estima con
#    Manhattan sobre un plano local en km, en lugar de "línea recta × 1.3".
# ============================================================

import math
from typing import Any

Punto = tuple[float, float]


def fmt(n: float) -> str:
    """5.0 -> '5', 5.8309 -> '5.83'"""
    return f"{round(n, 2):g}"


def distancia_euclidiana(a: Punto, b: Punto) -> float:
    """Distancia en línea recta: √((x2 - x1)² + (y2 - y1)²)."""
    return math.hypot(b[0] - a[0], b[1] - a[1])


def distancia_manhattan(a: Punto, b: Punto) -> float:
    """Distancia por cuadras: |x2 - x1| + |y2 - y1|."""
    return abs(b[0] - a[0]) + abs(b[1] - a[1])


def comparar_distancias(a: Punto, b: Punto) -> dict[str, Any]:
    """Compara ambas métricas entre A y B y explica el cálculo paso a paso."""
    dx = abs(b[0] - a[0])
    dy = abs(b[1] - a[1])
    euclidiana = distancia_euclidiana(a, b)
    manhattan = distancia_manhattan(a, b)

    # Se registró cada cálculo con los valores sustituidos para mostrarlo en la app
    paso_euclidiana = (
        f"√(({fmt(b[0])} - {fmt(a[0])})² + ({fmt(b[1])} - {fmt(a[1])})²) = "
        f"√({fmt(dx**2)} + {fmt(dy**2)}) = √{fmt(dx**2 + dy**2)} = {fmt(euclidiana)}"
    )
    paso_manhattan = (
        f"|{fmt(b[0])} - {fmt(a[0])}| + |{fmt(b[1])} - {fmt(a[1])}| = "
        f"{fmt(dx)} + {fmt(dy)} = {fmt(manhattan)}"
    )

    return {
        "a": {"x": a[0], "y": a[1]},
        "b": {"x": b[0], "y": b[1]},
        # El camino Manhattan va primero en horizontal y luego en vertical
        "esquina": {"x": b[0], "y": a[1]},
        "horizontal": round(dx, 4),
        "vertical": round(dy, 4),
        "euclidiana": round(euclidiana, 4),
        "manhattan": round(manhattan, 4),
        "diferencia": round(manhattan - euclidiana, 4),
        "alineados": dx == 0 or dy == 0,
        "pasos": {"euclidiana": paso_euclidiana, "manhattan": paso_manhattan},
    }
