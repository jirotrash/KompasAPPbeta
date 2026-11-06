"""Destinos probables a partir del historial REAL del usuario (colección `historial_rutas`).

Cero datos aleatorios: cada viaje es un recorrido que el usuario inició en la app (id_ruta + created_at).
La hora y el día salen de `created_at` (hora de Toluca); el destino es la ruta que tomó.

- Menos de MIN_VIAJES: no se predice; se dice que faltan datos (regla 1 de CONTEXTO.md).
- De MIN_VIAJES a UMBRAL_KNN - 1: frecuencia por franja horaria y tipo de día, suavizada hacia la
  frecuencia general del usuario (Laplace / estimador bayesiano simple).
- Desde UMBRAL_KNN: KNeighborsClassifier (scikit-learn) sobre la hora y el día codificados en círculo
  (las 23:00 quedan cerca de las 00:00 y el domingo cerca del lunes). Se valida con leave-one-out contra
  el baseline "siempre la ruta más frecuente", igual que p03 se compara contra la regla fija.

Las probabilidades son estimaciones de hábito, no datos verificados.
"""

import math
from collections import Counter
from datetime import datetime
from statistics import median

import numpy as np
from sklearn.model_selection import LeaveOneOut, cross_val_score
from sklearn.neighbors import KNeighborsClassifier

MIN_VIAJES = 5
UMBRAL_KNN = 20
VECINOS_MAX = 7
MAX_DESTINOS = 3
SUAVIZADO = 1.0
FRANJAS = (("madrugada", 0, 5), ("manana", 6, 11), ("tarde", 12, 18), ("noche", 19, 23))
DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
AVISO = "Estimación a partir de tus recorridos guardados en Kompás; no es un dato verificado."


def franja_horaria(hora: int) -> str:
    return next(nombre for nombre, desde, hasta in FRANJAS if desde <= hora <= hasta)


def es_laborable(dia_semana: int) -> bool:
    """dia_semana: 0 = lunes … 6 = domingo (datetime.weekday())."""
    return dia_semana < 5


def caracteristicas(hora_decimal: float, dia_semana: int) -> list[float]:
    """Vector X: hora y día en círculo (seno, coseno) + si es día laborable."""
    angulo_hora = 2 * math.pi * hora_decimal / 24
    angulo_dia = 2 * math.pi * dia_semana / 7
    return [
        math.sin(angulo_hora),
        math.cos(angulo_hora),
        math.sin(angulo_dia),
        math.cos(angulo_dia),
        1.0 if es_laborable(dia_semana) else 0.0,
    ]


def _hora_decimal(momento: datetime) -> float:
    return momento.hour + momento.minute / 60


def _formato_hora(minutos: float) -> str:
    minutos = round(minutos)
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def _probabilidades_por_frecuencia(viajes: list[dict], hora: int, dia_semana: int) -> dict[int, float]:
    """P(ruta | franja, tipo de día) = (c_franja(ruta) + α·P(ruta)) / (N_franja + α)."""
    global_ = Counter(v["id_ruta"] for v in viajes)
    total = len(viajes)
    franja, laborable = franja_horaria(hora), es_laborable(dia_semana)
    parecidos = [
        v for v in viajes
        if franja_horaria(v["momento"].hour) == franja and es_laborable(v["momento"].weekday()) == laborable
    ]
    en_franja = Counter(v["id_ruta"] for v in parecidos)
    return {
        id_ruta: (en_franja[id_ruta] + SUAVIZADO * conteo / total) / (len(parecidos) + SUAVIZADO)
        for id_ruta, conteo in global_.items()
    }


def _modelo_knn(viajes: list[dict]) -> tuple[KNeighborsClassifier, np.ndarray, np.ndarray]:
    X = np.array([caracteristicas(_hora_decimal(v["momento"]), v["momento"].weekday()) for v in viajes])
    y = np.array([v["id_ruta"] for v in viajes])
    modelo = KNeighborsClassifier(n_neighbors=min(VECINOS_MAX, len(viajes)), weights="distance")
    modelo.fit(X, y)
    return modelo, X, y


def _validar_knn(X: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Exactitud leave-one-out del KNN y del baseline (ruta más frecuente del resto de los viajes)."""
    vecinos = min(VECINOS_MAX, len(y) - 1)
    exactitud_knn = float(
        cross_val_score(KNeighborsClassifier(n_neighbors=vecinos, weights="distance"), X, y, cv=LeaveOneOut()).mean()
    )
    aciertos_baseline = 0
    for i in range(len(y)):
        resto = Counter(np.delete(y, i).tolist())
        aciertos_baseline += int(resto.most_common(1)[0][0] == y[i])
    return round(exactitud_knn, 3), round(aciertos_baseline / len(y), 3)


def predecir_destinos(viajes: list[dict], hora: int, dia_semana: int, minuto: int = 0) -> dict:
    """viajes: [{id_ruta, momento: datetime}] del usuario. Regresa los destinos más probables a esa hora."""
    base = {
        "hora_consulta": hora,
        "dia_consulta": DIAS[dia_semana],
        "franja": franja_horaria(hora),
        "viajes_analizados": len(viajes),
        "minimo_viajes": MIN_VIAJES,
        "exactitud_validacion": None,
        "exactitud_baseline": None,
        "aviso": AVISO,
    }
    if len(viajes) < MIN_VIAJES:
        return {
            **base,
            "estado": "datos_insuficientes",
            "metodo": None,
            "destinos": [],
            "explicacion": (
                f"Aún no hay suficientes recorridos para aprender tus hábitos: llevas {len(viajes)} "
                f"y se necesitan al menos {MIN_VIAJES}."
            ),
        }

    if len(viajes) < UMBRAL_KNN:
        metodo = "frecuencia_franja"
        probabilidades = _probabilidades_por_frecuencia(viajes, hora, dia_semana)
        explicacion = (
            f"Con {len(viajes)} recorridos se usa la frecuencia de cada ruta en la franja de la "
            f"{base['franja']} en días {'laborables' if es_laborable(dia_semana) else 'de fin de semana'}."
        )
    else:
        metodo = "knn"
        modelo, X, y = _modelo_knn(viajes)
        fila = np.array([caracteristicas(hora + minuto / 60, dia_semana)])
        probabilidades = {int(c): float(p) for c, p in zip(modelo.classes_, modelo.predict_proba(fila)[0])}
        base["exactitud_validacion"], base["exactitud_baseline"] = _validar_knn(X, y)
        explicacion = (
            f"Un modelo KNN entrenado con tus {len(viajes)} recorridos compara la hora y el día de hoy con tus "
            f"viajes anteriores. Exactitud en validación: {base['exactitud_validacion']:.0%} "
            f"(baseline 'ruta más frecuente': {base['exactitud_baseline']:.0%})."
        )

    conteos = Counter(v["id_ruta"] for v in viajes)
    minutos = {}
    for v in viajes:
        minutos.setdefault(v["id_ruta"], []).append(v["momento"].hour * 60 + v["momento"].minute)
    mejores = sorted(probabilidades.items(), key=lambda par: (-par[1], -conteos[par[0]]))
    destinos = [
        {
            "id_ruta": id_ruta,
            "probabilidad": round(prob, 3),
            "viajes": conteos[id_ruta],
            "hora_habitual": _formato_hora(median(minutos[id_ruta])),
        }
        for id_ruta, prob in mejores[:MAX_DESTINOS]
        if prob > 0
    ]
    return {**base, "estado": "ok", "metodo": metodo, "destinos": destinos, "explicacion": explicacion}


def resumir_habitos(viajes: list[dict]) -> dict:
    """viajes: [{id_ruta, transporte, momento}]. Solo cuenta lo que hay en el historial; no estima tráfico."""
    if not viajes:
        return {"total_viajes": 0, "rutas_frecuentes": [], "transportes": {}, "por_franja": {}, "por_dia": {}}
    rutas = Counter(v["id_ruta"] for v in viajes)
    return {
        "total_viajes": len(viajes),
        "rutas_frecuentes": [{"id_ruta": r, "viajes": c} for r, c in rutas.most_common(5)],
        "transportes": dict(Counter(v["transporte"] for v in viajes).most_common()),
        "por_franja": {f: n for f, n in Counter(franja_horaria(v["momento"].hour) for v in viajes).items()},
        "por_dia": {DIAS[d]: n for d, n in sorted(Counter(v["momento"].weekday() for v in viajes).items())},
    }
