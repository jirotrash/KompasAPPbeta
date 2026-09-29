"""Convierte solicitud e itinerario en hechos para las reglas R01–R20.

Contrato de IA.md: recibe datos normalizados por el backend, sin consultar
Google, MySQL ni FastAPI. Los datos desconocidos conservan el valor None.
Ejecutar este archivo con --ejemplo para probarlo sin servicios externos.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, TypedDict
from unicodedata import combining, normalize
from zoneinfo import ZoneInfo

Hecho = bool | None

# Son duraciones de planificación, no horarios ni tiempos observados.
ESTANCIAS_MINUTOS = {
    "comer": 60, "cafe": 40, "cultura": 60,
    "entretenimiento": 90, "aire_libre": 60,
}
CONTEXTOS_CATEGORIAS = {
    "solo": frozenset({"cafe", "cultura", "aire_libre"}),
    "pareja": frozenset({"comer", "cafe", "cultura", "aire_libre"}),
    "amigos": frozenset({"comer", "cafe", "entretenimiento", "aire_libre"}),
    "familia": frozenset({"comer", "cultura", "entretenimiento", "aire_libre"}),
}
MODOS = {"caminando", "taxi_app", "transporte_publico", "combinado"}


@dataclass(frozen=True)
class PoliticaHechos:
    """Decisiones del servidor; no se reciben de la app como hechos."""

    aceptar_rutas_estimadas: bool = True
    vigencia_minutos: int = 15
    limite_caminata_km: float = 2.0
    zona_horaria: str = "America/Mexico_City"

    def __post_init__(self):
        if type(self.aceptar_rutas_estimadas) is not bool:
            raise ValueError("aceptar_rutas_estimadas debe ser booleano.")
        if type(self.vigencia_minutos) is not int or self.vigencia_minutos <= 0:
            raise ValueError("vigencia_minutos debe ser un entero positivo.")
        if _numero(self.limite_caminata_km) is None:
            raise ValueError("limite_caminata_km debe ser finito y no negativo.")
        ZoneInfo(self.zona_horaria)


class ResultadoHechos(TypedDict):
    hechos: dict[str, Hecho]
    advertencias: list[str]
    datos_faltantes: list[str]
    errores_solicitud: list[str]
    resumen: dict[str, Any]


def _numero(valor: Any) -> Decimal | None:
    """No admite cadenas, booleanos, negativos, NaN ni infinito."""
    if type(valor) not in (int, float, Decimal):
        return None
    try:
        numero = Decimal(str(valor))
    except InvalidOperation:
        return None
    return numero if numero.is_finite() and numero >= 0 else None


def _fecha(valor: Any) -> datetime | None:
    try:
        fecha = valor if isinstance(valor, datetime) else datetime.fromisoformat(valor)
        return fecha if fecha.tzinfo is not None and fecha.utcoffset() is not None else None
    except (TypeError, ValueError):
        return None


def _etiqueta(valor: Any) -> str | None:
    if not isinstance(valor, str):
        return None
    texto = "".join(c for c in normalize("NFKD", valor) if not combining(c))
    return "_".join(texto.lower().replace("/", " ").split())


def _etiquetas(valor: Any) -> list[str] | None:
    if not isinstance(valor, list) or not valor:
        return None
    etiquetas = [_etiqueta(v) for v in valor]
    return etiquetas if all(etiquetas) else None


def _todos(valores: list[Hecho]) -> Hecho:
    if any(v is False for v in valores):
        return False
    return True if valores and all(v is True for v in valores) else None


def _vigente(consulta: Any, ahora: datetime, minutos: int) -> Hecho:
    fecha = _fecha(consulta)
    if fecha is None:
        return None
    edad = (ahora - fecha).total_seconds()
    if edad < 0:
        return None
    return edad <= minutos * 60


def _minuto_hora(valor: Any, *, cierre: bool = False) -> int | None:
    if not isinstance(valor, str) or len(valor) != 5 or valor[2] != ":":
        return None
    if not (valor[:2].isdigit() and valor[3:].isdigit()):
        return None
    hora, minuto = int(valor[:2]), int(valor[3:])
    if cierre and hora == 24 and minuto == 0:
        return 1440
    return hora * 60 + minuto if 0 <= hora <= 23 and 0 <= minuto <= 59 else None


def _dia(valor: Any) -> bool:
    return type(valor) is int and 0 <= valor <= 6


def _periodos(horario: Any) -> list[tuple[int, int]] | None:
    """Semana de Google: domingo=0. None es desconocido; [] es cerrado.

    Acepta la lista normalizada de IA.md o un objeto OpeningHours con periods.
    No interpreta weekdayDescriptions ni confunde openNow con una visita futura.
    """
    google = isinstance(horario, Mapping)
    filas = horario.get("periods") if google else horario
    if not isinstance(filas, list):
        return None
    periodos = []
    for fila in filas:
        if not isinstance(fila, Mapping):
            return None
        if google:
            apertura, cierre = fila.get("open"), fila.get("close")
            if not isinstance(apertura, Mapping) or not _dia(apertura.get("day")):
                return None
            puntos = [apertura] + ([cierre] if isinstance(cierre, Mapping) else [])
            for punto in puntos:
                if "date" in punto or punto.get("truncated") is True:
                    return None  # No convertir excepciones fechadas en una semana recurrente.
                if not _dia(punto.get("day")):
                    return None
                for nombre, limite in (("hour", 23), ("minute", 59)):
                    valor = punto.get(nombre, 0)
                    if type(valor) is not int or not 0 <= valor <= limite:
                        return None
            inicio = apertura["day"] * 1440 + apertura.get("hour", 0) * 60 + apertura.get("minute", 0)
            if cierre is None:
                # Representación documentada de abierto 24/7.
                return [(0, 10080)] if inicio == 0 and len(filas) == 1 else None
            if not isinstance(cierre, Mapping):
                return None
            fin = cierre["day"] * 1440 + cierre.get("hour", 0) * 60 + cierre.get("minute", 0)
            if fin == inicio:
                return None
            if fin < inicio:
                fin += 10080
        else:
            dia = fila.get("dia")
            abre = _minuto_hora(fila.get("abre"))
            cierra = _minuto_hora(fila.get("cierra"), cierre=True)
            if not _dia(dia) or abre is None or cierra is None:
                return None
            inicio = dia * 1440 + abre
            if "dia_cierre" in fila:
                if not _dia(fila["dia_cierre"]):
                    return None
                fin = fila["dia_cierre"] * 1440 + cierra
                if fin == inicio:
                    return None
                if fin < inicio:
                    fin += 10080
            else:
                if cierra == abre:
                    return None  # 08:00–08:00 no demuestra apertura de 24 horas.
                fin = dia * 1440 + cierra + (1440 if cierra < abre else 0)
        periodos.append((inicio, fin))
    return periodos


def visita_en_horario(horario: Any, llegada: Any, estancia_minutos: Any,
                      zona_horaria: str = "America/Mexico_City") -> Hecho:
    """Comprueba toda la visita, incluidos horarios partidos y medianoche."""
    fecha, estancia = _fecha(llegada), _numero(estancia_minutos)
    periodos = _periodos(horario)
    if fecha is None or estancia is None or estancia <= 0 or periodos is None:
        return None
    if not periodos:
        return False
    if periodos == [(0, 10080)]:
        return True
    fecha = fecha.astimezone(ZoneInfo(zona_horaria))
    domingo = fecha.replace(hour=0, minute=0, second=0, microsecond=0)
    domingo -= timedelta(days=(fecha.weekday() + 1) % 7)
    intervalos = sorted(
        (domingo + timedelta(minutes=inicio, days=desfase),
         domingo + timedelta(minutes=fin, days=desfase))
        for inicio, fin in periodos for desfase in (-7, 0, 7)
    )
    unidos: list[tuple[datetime, datetime]] = []
    for inicio, fin in intervalos:
        if unidos and inicio <= unidos[-1][1]:
            unidos[-1] = (unidos[-1][0], max(unidos[-1][1], fin))
        else:
            unidos.append((inicio, fin))
    try:
        salida = fecha + timedelta(minutes=float(estancia))
    except OverflowError:
        return None
    return any(inicio <= fecha and salida <= fin for inicio, fin in unidos)


def _rango(valor: Any) -> tuple[Decimal | None, Decimal | None]:
    if not isinstance(valor, Mapping) or valor.get("moneda") != "MXN":
        return None, None
    minimo, maximo = _numero(valor.get("min")), _numero(valor.get("max"))
    if any(valor.get(k) is not None and _numero(valor[k]) is None for k in ("min", "max")):
        return None, None
    if minimo is not None and maximo is not None and minimo > maximo:
        return None, None
    return minimo, maximo


def _validar_solicitud(solicitud: Mapping, hechos: dict[str, Hecho]) -> list[str]:
    errores = []
    if _etiqueta(solicitud.get("contexto")) not in CONTEXTOS_CATEGORIAS:
        errores.append("contexto debe ser solo, pareja, amigos o familia.")
    intereses = _etiquetas(solicitud.get("intereses"))
    movilidad = _etiquetas(solicitud.get("movilidad"))
    if intereses is None or not set(intereses) <= ESTANCIAS_MINUTOS.keys():
        errores.append("intereses debe contener categorías reconocidas.")
    if movilidad is None or not set(movilidad) <= MODOS:
        errores.append("movilidad debe contener modos reconocidos.")
    if _numero(solicitud.get("presupuesto_por_persona")) is None:
        errores.append("presupuesto_por_persona debe ser un número no negativo en MXN.")
    tiempo = _numero(solicitud.get("tiempo_minutos"))
    if tiempo is None or tiempo <= 0:
        errores.append("tiempo_minutos debe ser un número positivo.")
    if _fecha(solicitud.get("fecha_hora_salida")) is None:
        errores.append("fecha_hora_salida debe incluir fecha, hora y zona UTC.")
    for clave in ("incluir_regreso", "requiere_accesibilidad"):
        if clave in solicitud and type(solicitud[clave]) is not bool:
            errores.append(f"{clave} debe ser booleano.")
    prohibidos = (set(hechos) - {"requiere_accesibilidad"}) | {
        "hechos", "datos_criticos_completos", "recomendable", "descartar",
        "viabilidad_base", "estado", "puntuacion_preferencias",
    }
    if prohibidos.intersection(solicitud):
        errores.append("La solicitud no puede declarar hechos ni resultados del motor.")
    return errores


def construir_hechos(solicitud: Mapping[str, Any], itinerario: Mapping[str, Any], *,
                      ahora: datetime | None = None, zona_validada: bool | None = None,
                      politica: PoliticaHechos | None = None) -> ResultadoHechos:
    """Normaliza un candidato y conserva advertencias que la API debe mostrar.

    ``zona_validada`` es la comprobación del servidor para la zona piloto; no
    debe copiarse del JSON del usuario. ``ahora`` permite pruebas reproducibles.
    El resultado se usa con evaluar(resultado["hechos"], cargar_base()).
    """
    if not isinstance(solicitud, Mapping) or not isinstance(itinerario, Mapping):
        raise ValueError("solicitud e itinerario deben ser objetos.")
    if zona_validada is not None and type(zona_validada) is not bool:
        raise ValueError("zona_validada debe ser True, False o None.")
    politica = politica or PoliticaHechos()
    reloj = datetime.now(timezone.utc) if ahora is None else _fecha(ahora)
    if reloj is None:
        raise ValueError("ahora debe ser una fecha con zona horaria.")
    hechos: dict[str, Hecho] = dict.fromkeys((
        "datos_usuario_validos", "modo_disponible", "ruta_calculada", "abierto",
        "dentro_presupuesto", "cabe_en_tiempo", "requiere_accesibilidad",
        "accesibilidad_verificada", "control_cierres_habilitado", "cierre_vigente",
        "datos_vigentes", "contexto_compatible", "intereses_compatibles",
        "poca_caminata", "pocos_transbordos",
    ))
    advertencias, faltantes = [], []
    errores = _validar_solicitud(solicitud, hechos)
    if zona_validada is False:
        errores.append("El origen está fuera de la zona piloto validada por backend.")
    elif zona_validada is None:
        faltantes.append("Backend debe confirmar la zona piloto antes de recomendar.")
    hechos["datos_usuario_validos"] = not errores
    hechos["control_cierres_habilitado"] = False
    accesibilidad = solicitud.get("requiere_accesibilidad", False)
    hechos["requiere_accesibilidad"] = accesibilidad if type(accesibilidad) is bool else None
    if accesibilidad is True:
        faltantes.append("Este MVP no dispone de evidencia de accesibilidad.")

    visitas = itinerario.get("visitas")
    tramos = itinerario.get("tramos")
    if not isinstance(visitas, list) or not all(isinstance(v, Mapping) for v in visitas):
        visitas = []
    if not isinstance(tramos, list) or not all(isinstance(t, Mapping) for t in tramos):
        tramos = []
    if not visitas:
        faltantes.append("Faltan visitas válidas en el candidato.")
    if not tramos:
        faltantes.append("Faltan tramos válidos; no se inventa el trayecto.")
    categorias = [_etiqueta(v.get("categoria")) for v in visitas]
    estancias = []
    vigencias = []
    aperturas = []
    costos: list[tuple[Decimal | None, Decimal | None]] = []
    for numero, (visita, categoria) in enumerate(zip(visitas, categorias), 1):
        estancia = _numero(visita.get("estancia_minutos"))
        if "estancia_minutos" not in visita and categoria in ESTANCIAS_MINUTOS:
            estancia = Decimal(ESTANCIAS_MINUTOS[categoria])
            advertencias.append(f"Visita {numero}: estancia estimada de {estancia} minutos por categoría.")
        if estancia is None or estancia <= 0:
            estancia = None
            faltantes.append(f"Visita {numero}: falta una estancia positiva.")
        estancias.append(estancia)
        vigencia = _vigente(visita.get("consultado_en"), reloj, politica.vigencia_minutos)
        vigencias.append(vigencia)
        if vigencia is not True:
            faltantes.append(f"Visita {numero}: consulta ausente, futura o vencida; no se usa su horario ni precio.")
        apertura = visita_en_horario(
            visita.get("horario"), visita.get("llegada_estimada"), estancia,
            politica.zona_horaria,
        ) if vigencia is True else None
        aperturas.append(apertura)
        if apertura is None:
            faltantes.append(f"Visita {numero}: no se puede comprobar el horario de toda la visita.")
        rango = _rango(visita.get("rango_precio")) if vigencia is True else (None, None)
        costos.append(rango)
        if rango[1] is None:
            faltantes.append(f"Visita {numero}: falta un máximo de precio en MXN; nivel_precio no equivale a pesos.")

    hechos["datos_vigentes"] = _todos(vigencias)
    hechos["abierto"] = _todos(aperturas)
    modos = [_etiqueta(t.get("modo")) for t in tramos]
    solicitados = set(_etiquetas(solicitud.get("movilidad")) or [])
    permitidos = solicitados | ({"caminando", "taxi_app"} if "combinado" in solicitados else set())
    if zona_validada is False or any(m in MODOS and m not in permitidos for m in modos):
        hechos["modo_disponible"] = False
    elif zona_validada is True and modos and all(m in {"caminando", "taxi_app"} for m in modos):
        hechos["modo_disponible"] = True
    if any(m not in {"caminando", "taxi_app"} for m in modos):
        faltantes.append("No hay líneas ni paradas de transporte público verificadas en este MVP.")
    if "taxi_app" in modos:
        advertencias.append("Taxi/App es un modo previsto; no confirma vehículo disponible ni tarifa de una plataforma.")
    for tramo, modo in zip(tramos, modos):
        costo = Decimal(0) if modo == "caminando" else (
            _numero(tramo.get("costo_por_persona")) if tramo.get("moneda") == "MXN" else None
        )
        costos.append((costo, costo))
        if costo is None:
            faltantes.append("Falta el costo por persona de un tramo; no se sustituye por cero.")

    minutos = [_numero(t.get("minutos")) for t in tramos]
    distancias = [_numero(t.get("km")) for t in tramos]
    regreso = itinerario.get("regreso_incluido")
    estructura = bool(visitas and tramos) and type(regreso) is bool
    estructura = estructura and len(tramos) == len(visitas) + int(regreso is True)
    if solicitud.get("incluir_regreso") is True and regreso is not True:
        estructura = False
        faltantes.append("Se solicitó regreso, pero el candidato no incluye su tramo.")
    if not estructura:
        faltantes.append("Se requiere un tramo por visita y otro de regreso cuando corresponda.")
    magnitudes = estructura and all(n is not None for n in minutos + distancias + estancias)
    salida = _fecha(solicitud.get("fecha_hora_salida"))
    llegadas = [_fecha(v.get("llegada_estimada")) for v in visitas]
    total, esperas = None, Decimal(0)
    cronologia = bool(magnitudes and salida is not None and all(l is not None for l in llegadas))
    if cronologia:
        anterior = salida
        try:
            for llegada, estancia, traslado in zip(llegadas, estancias, minutos):
                minima = anterior + timedelta(minutes=float(traslado))
                if llegada < minima:
                    cronologia = False
                    break
                esperas += Decimal(str((llegada - minima).total_seconds())) / 60
                anterior = llegada + timedelta(minutes=float(estancia))
            if regreso is True:
                anterior += timedelta(minutes=float(minutos[-1]))
            if cronologia:
                total = Decimal(str((anterior - salida).total_seconds())) / 60
        except (OverflowError, ValueError):
            cronologia = False
    if not cronologia:
        faltantes.append("Faltan llegadas coherentes con traslados y estancias; no se inventan horas.")
    estimados = [t.get("estimado") for t in tramos]
    if cronologia and all(type(e) is bool for e in estimados):
        if any(estimados):
            advertencias.append("Ruta, distancias y tiempos estimados: no verifican calles transitables ni tráfico real.")
        if not any(estimados) or politica.aceptar_rutas_estimadas:
            hechos["ruta_calculada"] = True
        else:
            faltantes.append("La política exige una ruta verificada y solo hay una estimación.")
    elif any(type(e) is not bool for e in estimados):
        faltantes.append("Cada tramo debe indicar estimado como booleano.")
    disponible = _numero(solicitud.get("tiempo_minutos"))
    if total is not None and disponible is not None:
        hechos["cabe_en_tiempo"] = total <= disponible

    presupuesto = _numero(solicitud.get("presupuesto_por_persona"))
    minimo = sum((bajo for bajo, _ in costos if bajo is not None), Decimal(0))
    maximo = sum((alto for _, alto in costos), Decimal(0)) if costos and all(
        alto is not None for _, alto in costos
    ) else None
    if estructura and presupuesto is not None:
        if minimo > presupuesto:
            hechos["dentro_presupuesto"] = False
        elif maximo is not None and maximo <= presupuesto:
            hechos["dentro_presupuesto"] = True
        elif maximo is not None:
            faltantes.append("El rango de costo cruza el presupuesto; no permite confirmar ni descartar por costo.")
    if any(bajo is not None or alto is not None for bajo, alto in costos[:len(visitas)]):
        advertencias.append("Los rangos de lugares son estimaciones por persona; no constituyen una cotización ni un cobro garantizado.")

    contexto = _etiqueta(solicitud.get("contexto"))
    if contexto in CONTEXTOS_CATEGORIAS and categorias and all(c in ESTANCIAS_MINUTOS for c in categorias):
        hechos["contexto_compatible"] = all(c in CONTEXTOS_CATEGORIAS[contexto] for c in categorias)
    intereses = _etiquetas(solicitud.get("intereses"))
    if intereses and categorias:
        if any(c in intereses for c in categorias):
            hechos["intereses_compatibles"] = True
        elif all(c in ESTANCIAS_MINUTOS for c in categorias):
            hechos["intereses_compatibles"] = False
    caminatas = [km for km, modo in zip(distancias, modos) if modo == "caminando"]
    modos_conocidos = bool(modos) and all(m in {"caminando", "taxi_app"} for m in modos)
    caminata_total = sum(caminatas, Decimal(0)) if modos_conocidos and all(k is not None for k in caminatas) else None
    if caminata_total is not None:
        hechos["poca_caminata"] = caminata_total <= Decimal(str(politica.limite_caminata_km))
    if modos_conocidos:
        hechos["pocos_transbordos"] = True
    if any(v is not None for v in aperturas):
        advertencias.append("Se utilizan horarios regulares; confirma posibles cierres o excepciones antes de salir.")
    for nombre, valor in hechos.items():
        if valor is None and nombre not in {"accesibilidad_verificada", "cierre_vigente"}:
            faltantes.append(f"Hecho sin información suficiente: {nombre}.")
    return {
        "hechos": hechos,
        "advertencias": list(dict.fromkeys(advertencias)),
        "datos_faltantes": list(dict.fromkeys(faltantes)),
        "errores_solicitud": errores,
        "resumen": {
            "duracion_total_minutos": float(total) if total is not None else None,
            "esperas_minutos": float(esperas) if cronologia else None,
            "caminata_km": float(caminata_total) if caminata_total is not None else None,
            "costo": None,
            "ruta_estimada": any(estimados) if estimados and all(type(e) is bool for e in estimados) else None,
            "minimo_acreditado_mxn": float(minimo) if costos else None,
            "maximo_considerado_mxn": float(maximo) if maximo is not None else None,
            "regreso_incluido": regreso if type(regreso) is bool else None,
            "evaluado_en": reloj.isoformat(),
        },
    }


def _main() -> None:
    import argparse
    import json
    from pathlib import Path
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ejemplo", action="store_true", help="Ejemplo sintético reproducible")
    parser.add_argument("--entrada", type=Path, help="JSON con solicitud e itinerario normalizados")
    parser.add_argument("--ahora", help="Fecha ISO con zona para reproducir una evaluación")
    parser.add_argument("--zona-validada", action="store_true", help="La zona ya fue verificada fuera del motor")
    parser.add_argument("--sin-rutas-estimadas", action="store_true")
    args = parser.parse_args()
    if args.ejemplo and args.entrada:
        parser.error("Usa --ejemplo o --entrada, no ambos.")
    if not args.ejemplo and args.entrada is None:
        parser.print_help()
        return
    raiz_backend = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(raiz_backend))
    from app.ia.motor import cargar_base, evaluar

    ruta = raiz_backend / "ejemplos" / "entrada_hechos.json" if args.ejemplo else args.entrada
    try:
        entrada = json.loads(ruta.read_text(encoding="utf-8"))
        reloj = args.ahora or (entrada["reloj_demostracion"] if args.ejemplo else None)
        if reloj is not None and _fecha(reloj) is None:
            raise ValueError("--ahora debe ser una fecha ISO con zona horaria.")
        resultado = construir_hechos(
            entrada["solicitud"], entrada["itinerario"],
            ahora=_fecha(reloj) if reloj else None,
            zona_validada=True if args.ejemplo or args.zona_validada else None,
            politica=PoliticaHechos(aceptar_rutas_estimadas=not args.sin_rutas_estimadas),
        )
        evaluacion = evaluar(resultado["hechos"], cargar_base())
        evaluacion["advertencias"] = list(dict.fromkeys(
            resultado["advertencias"] + evaluacion["advertencias"]
        ))
        salida = {
            "naturaleza": "Ejemplo sintético; no consulta Google ni la base de datos." if args.ejemplo else "Evaluación de un archivo local; la procedencia debe validarse en backend.",
            **resultado, "evaluacion": evaluacion,
        }
        print(json.dumps(salida, ensure_ascii=False, indent=2, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    _main()
