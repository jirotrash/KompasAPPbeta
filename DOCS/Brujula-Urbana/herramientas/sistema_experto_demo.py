"""Demostración académica sobre hechos normalizados; no es una API de movilidad.

No consulta servicios, no verifica evidencia externa y no persiste información.
Ejecutar --verificar para comprobar casos y condiciones límite de la inferencia.
"""

import argparse
import json
import sys
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
CARPETA_DATOS = RAIZ / "docs" / "sistema-experto"
# La demo y la API corren el mismo motor: se importa desde backend/app/ia/motor.py
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "backend"))
from app.ia.motor import CRITICOS, ENTRADAS, evaluar, exigir, validar_base  # noqa: E402


def cargar(nombre):
    return json.loads((CARPETA_DATOS / nombre).read_text(encoding="utf-8"))


def verificar(base, datos):
    """Comprobaciones de la especificación; no prueban proveedores ni normalización."""
    total = 0
    cobertura = set()
    comunes = datos["hechos_comunes"]

    def comprobar(cambios, estado, puntos=None):
        nonlocal total
        resultado = evaluar({**comunes, **cambios}, base)
        exigir(resultado["estado"] == estado, f"Estado inesperado con {cambios}.")
        exigir(resultado["puntuacion_preferencias"] == puntos,
               f"Puntuación inesperada con {cambios}.")
        exigir(not {"descartar", "recomendable"} <= set(resultado["hechos_derivados"]),
               "Se derivaron conclusiones contradictorias.")
        cobertura.update(paso["regla_id"] for paso in resultado["traza"])
        total += 1
        return resultado

    for caso in datos["casos"]:
        esperado = caso["esperado"]
        resultado = comprobar(caso["hechos"], esperado["estado"],
                              esperado["puntuacion_preferencias"])
        exigir([p["regla_id"] for p in resultado["traza"]] == esperado["reglas"],
               f"Traza diferente en candidato {caso['candidato_id']}.")

    comprobar({"datos_usuario_validos": False}, "requiere_correccion")
    for nombre in ("modo_disponible", "ruta_calculada", "abierto",
                   "dentro_presupuesto", "cabe_en_tiempo"):
        comprobar({nombre: False}, "descartado")
    for nombre in sorted(CRITICOS - {"control_cierres_habilitado"}):
        comprobar({nombre: None}, "pendiente_verificacion")
    comprobar({"datos_vigentes": False, "abierto": None}, "pendiente_verificacion")
    for valor, estado, puntos in ((True, "descartado", None),
                                  (None, "pendiente_verificacion", None),
                                  (False, "recomendable", 6)):
        comprobar({"control_cierres_habilitado": True, "cierre_vigente": valor}, estado, puntos)
    for valor, estado, puntos in ((False, "descartado", None),
                                  (None, "pendiente_verificacion", None),
                                  (True, "recomendable", 6)):
        comprobar({"requiere_accesibilidad": True, "accesibilidad_verificada": valor}, estado, puntos)
    comprobar({nombre: None for nombre in ("contexto_compatible", "intereses_compatibles",
                                           "poca_caminata", "pocos_transbordos")}, "recomendable", 0)
    comprobar({"abierto": False, "dentro_presupuesto": None}, "descartado")
    comprobar({"datos_usuario_validos": False, "abierto": False}, "requiere_correccion")

    for cambios in ({"abierto": "false"}, {"abierto": 1}, {"recomendable": True},
                    {"datos_criticos_completos": True}, {"cierre_vigente": False},
                    {"control_cierres_habilitado": None}):
        try:
            evaluar({**comunes, **cambios}, base)
        except ValueError:
            total += 1
        else:
            raise ValueError(f"Se admitió entrada inválida: {cambios}.")

    invertida = {**base, "reglas": list(reversed(base["reglas"]))}
    for caso in datos["casos"]:
        entrada = {**comunes, **caso["hechos"]}
        original, alterno = evaluar(entrada, base), evaluar(entrada, invertida)
        for campo in ("estado", "puntuacion_preferencias", "hechos_derivados"):
            exigir(original[campo] == alterno[campo], "El orden cambió el resultado lógico.")
        total += 1
    exigir(cobertura == {r["id"] for r in base["reglas"]}, "Hay reglas sin comprobar.")
    print(f"OK: {total} comprobaciones; {len(cobertura)}/20 reglas activadas al menos una vez.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verificar", action="store_true", help="Comprobar reglas y casos límite")
    parser.add_argument("--json", action="store_true", help="Mostrar la traza completa como JSON")
    argumentos = parser.parse_args()
    base, datos = cargar("reglas.json"), cargar("casos.json")
    validar_base(base)
    exigir(datos["version_reglas"] == base["version"], "Versiones de casos y reglas diferentes.")
    if argumentos.verificar:
        verificar(base, datos)
        return
    resultados = []
    for caso in datos["casos"]:
        resultado = evaluar({**datos["hechos_comunes"], **caso["hechos"]}, base)
        resultados.append({"candidato_id": caso["candidato_id"], **resultado})
    if argumentos.json:
        print(json.dumps({"naturaleza": datos["naturaleza"], "resultados": resultados},
                         ensure_ascii=False, indent=2))
    else:
        print(datos["naturaleza"])
        for resultado in resultados:
            print(f"\n{resultado['candidato_id']}: {resultado['estado']}; "
                  f"preferencias={resultado['puntuacion_preferencias']}")
            for paso in resultado["traza"]:
                print(f"  Ronda {paso['ronda']} / {paso['regla_id']}: {paso['explicacion']}")
            for advertencia in resultado["advertencias"]:
                print(f"  Advertencia: {advertencia}")


if __name__ == "__main__":
    main()
