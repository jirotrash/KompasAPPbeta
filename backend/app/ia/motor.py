"""Motor de inferencia del sistema experto (Einar).

Código movido SIN CAMBIOS desde herramientas/sistema_experto_demo.py para que la demo y la API
ejecuten exactamente la misma lógica. Las reglas R01–R20 se leen de docs/sistema-experto/reglas.json.

    from app.ia.motor import cargar_base, evaluar
    base = cargar_base()                 # una sola vez al iniciar
    resultado = evaluar(hechos, base)    # estado, puntuación, traza y advertencias
"""

import json
from pathlib import Path

# backend/app/ia/motor.py → raíz del repositorio → DOCS/Brujula-Urbana/docs/sistema-experto
CARPETA_REGLAS = Path(__file__).resolve().parents[3] / "DOCS" / "Brujula-Urbana" / "docs" / "sistema-experto"

ENTRADAS = {
    "datos_usuario_validos", "modo_disponible", "ruta_calculada", "abierto",
    "dentro_presupuesto", "cabe_en_tiempo", "requiere_accesibilidad",
    "accesibilidad_verificada", "control_cierres_habilitado", "cierre_vigente",
    "datos_vigentes", "contexto_compatible", "intereses_compatibles",
    "poca_caminata", "pocos_transbordos",
}
CRITICOS = {
    "datos_usuario_validos", "modo_disponible", "ruta_calculada", "abierto",
    "dentro_presupuesto", "cabe_en_tiempo", "requiere_accesibilidad",
    "control_cierres_habilitado", "datos_vigentes",
}
DERIVADOS = {
    "requiere_correccion", "descartar", "pendiente_verificacion",
    "accesibilidad_resuelta", "cierres_resueltos", "advertir_sin_cobertura_cierres",
    "viabilidad_base", "recomendable", "priorizar_contexto", "priorizar_intereses",
    "priorizar_caminata", "priorizar_transbordos",
}


def exigir(condicion, mensaje):
    if not condicion:
        raise ValueError(mensaje)


def validar_base(base):
    reglas = base["reglas"]
    exigir(len(reglas) == 20, "La versión 0.1.0 debe contener 20 reglas.")
    exigir({r["id"] for r in reglas} == {f"R{i:02}" for i in range(1, 21)},
           "Identificadores de regla ausentes o repetidos.")
    conocidos = ENTRADAS | DERIVADOS | {"datos_criticos_completos"}
    for regla in reglas:
        exigir(bool(regla["si"]) and bool(regla["entonces"]), "Regla vacía.")
        for nombre, valor in regla["si"].items():
            exigir(nombre in conocidos and type(valor) is bool,
                   f"Antecedente inválido: {regla['id']} / {nombre}.")
            exigir(nombre not in DERIVADOS or valor is True,
                   "No se permite negar un hecho derivado ausente.")
        exigir(set(regla["entonces"]) <= DERIVADOS, "Conclusión no declarada.")
        exigir(bool(regla["explicacion"]), "Falta explicación de una regla.")
    for nombre, peso in base["pesos_preferencias"].items():
        exigir(nombre in DERIVADOS and type(peso) is int and peso >= 0,
               "Peso de preferencia inválido.")


def evaluar(entrada, base):
    """Devuelve estado, preferencias y traza, sin alterar entrada ni base."""
    exigir(isinstance(entrada, dict), "La entrada debe ser un objeto de hechos.")
    exigir(set(entrada) <= ENTRADAS, "Hay hechos no permitidos o derivados inyectados.")
    exigir(all(v is None or type(v) is bool for v in entrada.values()),
           "Solo se admiten booleanos y null; 0, 1 y cadenas no son booleanos.")
    iniciales = {nombre: entrada.get(nombre) for nombre in sorted(ENTRADAS)}
    exigir(type(iniciales["control_cierres_habilitado"]) is bool,
           "Debe especificarse si el control de cierres está habilitado.")
    exigir(iniciales["control_cierres_habilitado"] or iniciales["cierre_vigente"] is None,
           "Con control deshabilitado, cierre_vigente debe ser null.")

    requeridos = set(CRITICOS)
    if iniciales["requiere_accesibilidad"] is True:
        requeridos.add("accesibilidad_verificada")
    if iniciales["control_cierres_habilitado"] is True:
        requeridos.add("cierre_vigente")
    iniciales["datos_criticos_completos"] = all(
        iniciales[nombre] is not None for nombre in requeridos
    )

    hechos = dict(iniciales)
    activadas = set()
    traza = []
    ronda = 0
    while True:
        aplicables = [
            regla for regla in base["reglas"]
            if regla["id"] not in activadas
            and all(hechos.get(nombre) is valor for nombre, valor in regla["si"].items())
        ]
        if not aplicables:
            break
        ronda += 1
        for regla in aplicables:
            activadas.add(regla["id"])
            for conclusion in regla["entonces"]:
                hechos[conclusion] = True
            traza.append({"ronda": ronda, "regla_id": regla["id"],
                          "conclusiones": list(regla["entonces"]),
                          "explicacion": regla["explicacion"]})

    derivados = {nombre for nombre in DERIVADOS if hechos.get(nombre) is True}
    if "requiere_correccion" in derivados:
        estado = "requiere_correccion"
    elif "descartar" in derivados:
        estado = "descartado"
    elif "pendiente_verificacion" in derivados:
        estado = "pendiente_verificacion"
    elif "recomendable" in derivados:
        estado = "recomendable"
    else:
        estado = "pendiente_verificacion"
    puntos = None
    if estado == "recomendable":
        puntos = sum(peso for nombre, peso in base["pesos_preferencias"].items()
                     if nombre in derivados)
    return {
        "version_reglas": base["version"], "estado": estado,
        "puntuacion_preferencias": puntos, "hechos_iniciales": iniciales,
        "hechos_derivados": sorted(derivados), "traza": traza,
        "advertencias": (["Esta versión no verifica cierres mediante una fuente integrada."]
                         if "advertir_sin_cobertura_cierres" in derivados else []),
    }


def cargar_base(carpeta: Path = CARPETA_REGLAS) -> dict:
    """Lee docs/sistema-experto/reglas.json y lo valida con validar_base() de Einar."""
    base = json.loads((carpeta / "reglas.json").read_text(encoding="utf-8"))
    validar_base(base)
    return base
