"""Reglas SI … ENTONCES … del sistema experto (lógica proposicional).

# TEMPORAL — Einar define las reglas definitivas (meta: 15–20).
Cada regla es una conjunción de literales ("hecho" o "¬hecho") que concluye un hecho nuevo.
Solo se usan hechos que se pueden calcular con la base actual: horario y presupuesto NO se
evalúan hasta que la base tenga esos datos (BACKEND.md §10).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Regla:
    id: str
    si: tuple[str, ...]  # literales: "cerca", "¬cerca"
    entonces: str
    motivo: str = ""  # texto para el usuario cuando la regla descarta (acepta {contexto}, {minutos}…)

    @property
    def descripcion(self) -> str:
        return f"{' ∧ '.join(self.si)} → {self.entonces}"


# Reglas que se evalúan por lugar
REGLAS_LUGAR: list[Regla] = [
    Regla("R1", ("coincide_intereses", "cerca"), "candidato"),
    Regla("R2", ("candidato", "apto_contexto"), "recomendable"),
    Regla("R3", ("recomendable", "cabe_en_tiempo"), "incluir_en_plan"),
    Regla("R4", ("datos_suficientes", "¬cerca", "¬solo_a_pie"), "descartar", "Queda lejos para tu forma de moverte"),
    Regla("R5", ("¬datos_suficientes",), "descartar", "No tenemos información suficiente de este lugar"),
    Regla("R7", ("datos_suficientes", "solo_a_pie", "¬cerca"), "descartar", "Queda a más de 2 km para ir caminando"),
    Regla("R8", ("datos_suficientes", "¬coincide_intereses"), "descartar", "No coincide con los intereses que elegiste"),
    Regla("R9", ("candidato", "¬apto_contexto"), "descartar", 'No es un lugar típico para ir en plan "{contexto}"'),
    Regla("R10", ("recomendable", "¬cabe_en_tiempo"), "descartar", "No alcanza el tiempo: requiere ~{minutos} min"),
]

# Regla sobre toda la solicitud
R6 = Regla("R6", ("¬hay_candidatos",), "avisar_sin_informacion")

# Reglas que eligen cómo hacer cada tramo del plan
REGLAS_TRAMO: list[Regla] = [
    Regla("R11", ("caminando", "distancia_corta"), "ir_a_pie"),
    Regla("R12", ("taxi_app", "¬distancia_corta"), "ir_en_taxi"),
    Regla("R13", ("¬taxi_app",), "ir_a_pie"),
    Regla("R14", ("taxi_app", "¬caminando"), "ir_en_taxi"),
]

REGLAS = {r.id: r for r in [*REGLAS_LUGAR, R6, *REGLAS_TRAMO]}

# Categoría adecuada para cada contexto (TEMPORAL — tabla fija que Einar ajusta)
APTO_CONTEXTO: dict[str, set[str]] = {
    "solo": {"comer", "cafe", "cultura", "entretenimiento", "aire_libre"},
    "pareja": {"comer", "cafe", "cultura", "entretenimiento", "aire_libre"},
    "amigos": {"comer", "cafe", "entretenimiento", "aire_libre"},
    "familia": {"comer", "cultura", "entretenimiento", "aire_libre"},
}

# Minutos que se pasan en cada tipo de lugar (supuesto del prototipo)
ESTANCIA_MIN: dict[str, int] = {"comer": 90, "cafe": 60, "cultura": 90, "entretenimiento": 120, "aire_libre": 60}

MIN_CANDIDATOS = 2  # hay_candidatos: al menos 2 lugares recomendables


def como_salida(regla: Regla, **datos) -> dict:
    """{"id": "R4", "descripcion": "Queda lejos para tu forma de moverte"} (o la fórmula si no descarta)."""
    return {"id": regla.id, "descripcion": regla.motivo.format(**datos) if regla.motivo else regla.descripcion}


def encadenar(hechos: dict[str, bool], reglas: list[Regla]) -> list[Regla]:
    """Encadenamiento hacia adelante: aplica reglas hasta que no se derive nada nuevo.
    Modifica `hechos` con las conclusiones y regresa las reglas que se dispararon, en orden."""

    def cumple(literal: str) -> bool:
        return not hechos.get(literal[1:], False) if literal.startswith("¬") else hechos.get(literal, False)

    disparadas: list[Regla] = []
    hubo_cambios = True
    while hubo_cambios:
        hubo_cambios = False
        for regla in reglas:
            if regla not in disparadas and all(cumple(l) for l in regla.si):
                hechos[regla.entonces] = True
                disparadas.append(regla)
                hubo_cambios = True
    return disparadas
