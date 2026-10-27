"""Arma las respuestas del dashboard: filtros de fecha, huecos con 0, redondeo y descripciones de reglas.

Toda estadística sale de los pipelines de `repositorio.py`; la web solo dibuja.
"""

from datetime import date, datetime, time, timedelta
from functools import lru_cache

from app.compartido.texto import INTERESES, MOVILIDADES, clave
from app.ia.busqueda_dfs import PARADAS_KOMPAS
from app.ia.busqueda_informada import NOMBRES as NOMBRES_BUSQUEDA
from app.ia.motor import cargar_base
from app.modulos.catalogos.servicio import ServicioCatalogos
from app.modulos.dashboard.repositorio import LIMITES_PRESUPUESTO, LIMITES_TIEMPO, RepositorioDashboard
from app.nucleo.bd import ZONA_HORARIA, ahora
from app.nucleo.errores import DatosInvalidos

DIAS_POR_DEFECTO = 30
CONTEXTOS = ("solo", "pareja", "amigos", "familia")
TIPOS_REPORTE = ("cierre_total", "accidente", "manifestacion", "afluencia")
ESTADOS_REPORTE = ("pendiente", "verificado", "descartado")
UNIDADES = {"dia": "day", "semana": "week", "mes": "month"}
ORDEN_ALGORITMOS = [("dfs", None), ("costo_uniforme", None), ("voraz", "euclidiana"), ("voraz", "manhattan"), ("a_estrella", "euclidiana"), ("a_estrella", "manhattan")]
TIPOS_PLAN = ("equilibrado", "rapido", "cercano")
HERRAMIENTAS = ("como_llegar", "buscar_lugares", "armar_salida", "mis_planes")


def _etiqueta_algoritmo(algoritmo: str, heuristica: str | None) -> str:
    base = {"dfs": "DFS", "costo_uniforme": "UCS", "voraz": "Voraz", "a_estrella": "A*"}.get(algoritmo, NOMBRES_BUSQUEDA.get(algoritmo, algoritmo))
    return f"{base} ({heuristica.capitalize()})" if heuristica else base


def percentil(valores: list[float], p: float) -> float | None:
    """Percentil con interpolación lineal (p entre 0 y 100)."""
    if not valores:
        return None
    orden = sorted(valores)
    k = (len(orden) - 1) * p / 100
    abajo, arriba = int(k), min(int(k) + 1, len(orden) - 1)
    return orden[abajo] + (orden[arriba] - orden[abajo]) * (k - abajo)


@lru_cache
def descripciones_reglas() -> dict[str, str]:
    """Explicación de cada regla R01–R20 (solo lectura de reglas.json; app/ia no se modifica)."""
    return {r["id"]: r["explicacion"] for r in cargar_base()["reglas"]}


def _r1(valor: float | None) -> float | None:
    return round(valor, 1) if valor is not None else None


def _etiquetas_buckets(limites: list[int], formato) -> list[tuple[object, str]]:
    """[(límite inferior que regresa $bucket, etiqueta legible), ...]"""
    return [(inferior, formato(inferior, superior)) for inferior, superior in zip(limites, limites[1:])]


def _inicio_periodo(dia: date, agrupar: str) -> date:
    if agrupar == "semana":
        return dia - timedelta(days=dia.weekday())
    if agrupar == "mes":
        return dia.replace(day=1)
    return dia


def _siguiente_periodo(dia: date, agrupar: str) -> date:
    if agrupar == "semana":
        return dia + timedelta(days=7)
    if agrupar == "mes":
        return (dia.replace(day=28) + timedelta(days=4)).replace(day=1)
    return dia + timedelta(days=1)


def _clave_fecha(valor: datetime) -> str:
    return valor.astimezone(ZONA_HORARIA).date().isoformat()


class Rango:
    """Periodo del dashboard en hora de Toluca. `hasta` incluye el día completo."""

    def __init__(self, desde: date | None, hasta: date | None, incluir_demo: bool):
        hoy = ahora().date()
        self.hasta = hasta or hoy
        self.desde = desde or self.hasta - timedelta(days=DIAS_POR_DEFECTO - 1)
        if self.desde > self.hasta:
            raise DatosInvalidos("La fecha inicial no puede ser posterior a la final.")
        if (self.hasta - self.desde).days > 3 * 366:
            raise DatosInvalidos("El periodo no puede ser mayor a 3 años.")
        self.incluir_demo = incluir_demo

    @property
    def inicio(self) -> datetime:
        return datetime.combine(self.desde, time.min, ZONA_HORARIA)

    @property
    def fin(self) -> datetime:
        return datetime.combine(self.hasta + timedelta(days=1), time.min, ZONA_HORARIA)

    def filtro(self, campo_fecha: str | None = "created_at", borrado_logico: bool = True) -> dict:
        filtro: dict = {}
        if borrado_logico:
            filtro["deleted_at"] = None
        if campo_fecha:
            filtro[campo_fecha] = {"$gte": self.inicio, "$lt": self.fin}
        if not self.incluir_demo:
            filtro["demo"] = {"$ne": True}
        return filtro

    def periodo(self) -> dict:
        return {"desde": self.desde, "hasta": self.hasta, "incluir_demo": self.incluir_demo}


class ServicioDashboard:
    def __init__(self, repo: RepositorioDashboard, catalogos: ServicioCatalogos):
        self.repo = repo
        self.catalogos = catalogos

    def _hay_demo(self, rango: Rango, *colecciones: str, campo_fecha: str = "created_at") -> bool:
        if not rango.incluir_demo:
            return False
        return any(self.repo.hay_demo(c, rango.filtro(campo_fecha, c != "bitacora_laboratorio")) for c in colecciones)

    def kpis(self, rango: Rango) -> dict:
        recomendacion = self.repo.planes_con_recomendacion(rango.filtro())
        evaluados = recomendacion["evaluados"]
        sin_fecha = rango.filtro(campo_fecha=None)
        hasta_fin = {**sin_fecha, "created_at": {"$lt": rango.fin}}
        vigentes = {**rango.filtro(campo_fecha=None), "vigente_hasta": {"$gt": ahora()}}
        return {
            "periodo": rango.periodo(),
            "usuarios_totales": self.repo.contar("usuarios", hasta_fin),
            "usuarios_nuevos": self.repo.contar("usuarios", rango.filtro()),
            "planes": self.repo.contar("planes", rango.filtro()),
            "planes_evaluados": evaluados,
            "porcentaje_con_recomendacion": _r1(100 * recomendacion["con_recomendacion"] / evaluados) if evaluados else 0.0,
            "recorridos": self.repo.contar("historial_rutas", rango.filtro()),
            "tiempo_promedio_recorrido_min": _r1(self.repo.tiempo_promedio(rango.filtro())),
            "reportes_vigentes": self.repo.contar("reportes", vigentes),
            "lugares": self.repo.contar("lugares", sin_fecha),
            "incluye_demo": self._hay_demo(rango, "usuarios", "planes", "historial_rutas", "reportes"),
        }

    def series(self, rango: Rango, agrupar: str) -> dict:
        unidad = UNIDADES[agrupar]
        filtro = rango.filtro()
        conteos = {c: self.repo.serie(c, filtro, unidad) for c in ("usuarios", "planes", "historial_rutas")}
        conteos = {c: {_clave_fecha(f): t for f, t in v.items()} for c, v in conteos.items()}
        por_interes: dict[str, dict[str, int]] = {}
        for fila in self.repo.serie_por_interes(filtro, unidad):
            por_interes.setdefault(_clave_fecha(fila["fecha"]), {})[fila["interes"]] = fila["total"]

        serie, intereses = [], []
        dia = _inicio_periodo(rango.desde, agrupar)
        while dia <= rango.hasta:
            fecha = dia.isoformat()
            serie.append(
                {
                    "fecha": fecha,
                    "usuarios": conteos["usuarios"].get(fecha, 0),
                    "planes": conteos["planes"].get(fecha, 0),
                    "recorridos": conteos["historial_rutas"].get(fecha, 0),
                }
            )
            intereses.append({"fecha": fecha, **{i: por_interes.get(fecha, {}).get(i, 0) for i in INTERESES}})
            dia = _siguiente_periodo(dia, agrupar)
        return {
            "periodo": rango.periodo(),
            "agrupar": agrupar,
            "serie": serie,
            "planes_por_interes": intereses,
            "incluye_demo": self._hay_demo(rango, "usuarios", "planes", "historial_rutas"),
        }

    def planes(self, rango: Rango) -> dict:
        datos = self.repo.planes(rango.filtro())
        por_interes = {g["_id"]: g["total"] for g in datos["por_interes"]}
        por_movilidad = {g["_id"]: g["total"] for g in datos["por_movilidad"]}
        por_contexto = {g["_id"]: g["total"] for g in datos["por_contexto"]}
        presupuesto = {g["_id"]: g["total"] for g in datos["presupuesto"]}
        tiempo = {g["_id"]: g["total"] for g in datos["tiempo_disponible"]}
        dia_hora = {(g["_id"]["dia"], g["_id"]["hora"]): g["total"] for g in datos["dia_hora"]}
        cruce = {(g["_id"]["contexto"], g["_id"]["interes"]): g["total"] for g in datos["interes_por_contexto"]}

        rangos_presupuesto = _etiquetas_buckets(LIMITES_PRESUPUESTO, lambda a, b: f"${a}–{b - 1}") + [("1200+", "$1200 o más")]
        rangos_tiempo = _etiquetas_buckets(LIMITES_TIEMPO, lambda a, b: f"{a / 60:g}–{b / 60:g} h") + [("8h+", "8 h o más")]
        return {
            "periodo": rango.periodo(),
            "total": sum(por_contexto.values()),
            "por_interes": sorted(
                ({"interes": i, "total": por_interes.get(i, 0)} for i in INTERESES), key=lambda x: -x["total"]
            ),
            "por_movilidad": [{"movilidad": m, "total": por_movilidad.get(m, 0)} for m in MOVILIDADES],
            "por_contexto": [{"contexto": c, "total": por_contexto.get(c, 0)} for c in CONTEXTOS],
            "presupuesto": [{"rango": etiqueta, "desde": inferior if inferior != "1200+" else 1200, "total": presupuesto.get(inferior, 0)} for inferior, etiqueta in rangos_presupuesto],
            "tiempo_disponible": [{"rango": etiqueta, "desde_min": inferior if inferior != "8h+" else 480, "total": tiempo.get(inferior, 0)} for inferior, etiqueta in rangos_tiempo],
            "dia_hora": [{"dia": d, "hora": h, "total": dia_hora.get((d, h), 0)} for d in range(1, 8) for h in range(24)],
            "interes_por_contexto": [{"interes": i, **{c: cruce.get((c, i), 0) for c in CONTEXTOS}} for i in INTERESES],
            "incluye_demo": self._hay_demo(rango, "planes"),
        }

    def sistema_experto(self, rango: Rango) -> dict:
        datos = self.repo.sistema_experto(rango.filtro())
        descripciones = descripciones_reglas()
        return {
            "periodo": rango.periodo(),
            "por_estado": sorted(
                ({"estado": g["_id"], "total": g["total"]} for g in datos["por_estado"] if g["_id"]), key=lambda x: -x["total"]
            ),
            "reglas_top": [
                {"id": g["_id"], "descripcion": descripciones.get(g["_id"]), "total": g["total"]} for g in datos["reglas_top"]
            ],
            "puntuacion_por_tipo": sorted(
                (
                    {"tipo": g["_id"], "promedio": _r1(g["promedio"]), "minimo": g["minimo"], "maximo": g["maximo"], "total": g["total"]}
                    for g in datos["puntuacion_por_tipo"]
                ),
                key=lambda x: x["tipo"],
            ),
            "sin_datos_suficientes": datos["sin_datos_suficientes"],
            "por_version": [{"version": g["_id"] or "sin versión", "total": g["total"]} for g in datos["por_version"]],
            "incluye_demo": self._hay_demo(rango, "planes"),
        }

    def movilidad(self, rango: Rango) -> dict:
        datos = self.repo.movilidad(rango.filtro())
        por_nombre = {g["_id"]: g for g in datos["por_transporte"] if g["_id"]}
        por_transporte = []
        for t in self.catalogos.transportes():
            g = por_nombre.pop(t["nombre"], None)
            por_transporte.append(
                {
                    "transporte": t["nombre"],
                    "clave": t["clave"],
                    "total": g["total"] if g else 0,
                    "promedio": _r1(g["promedio"]) if g else None,
                    "minimo": g["minimo"] if g else None,
                    "maximo": g["maximo"] if g else None,
                }
            )
        # Transportes que ya no están en el catálogo pero tienen recorridos
        for nombre, g in por_nombre.items():
            por_transporte.append(
                {"transporte": nombre, "clave": clave(nombre), "total": g["total"], "promedio": _r1(g["promedio"]), "minimo": g["minimo"], "maximo": g["maximo"]}
            )
        return {
            "periodo": rango.periodo(),
            "por_transporte": por_transporte,
            "rutas_top": [
                {"id_ruta": g["_id"], "ruta": f"Ruta {g['_id']}", "total": g["total"], "promedio": _r1(g["promedio"])}
                for g in datos["rutas_top"]
            ],
            "paradas_uso": [
                {**g["_id"], "subidas": g["subidas"], "bajadas": g["bajadas"], "total": g["subidas"] + g["bajadas"]}
                for g in self.repo.paradas_uso({**rango.filtro("creado_en", borrado_logico=False), "tipo": "abordaje"})
                if g["_id"].get("lat") is not None
            ],
            "incluye_demo": self._hay_demo(rango, "historial_rutas"),
        }

    def reportes(self, rango: Rango) -> dict:
        datos = self.repo.reportes(rango.filtro(), ahora())
        cruce = {(g["_id"]["tipo"], g["_id"]["estado"]): g["total"] for g in datos["por_tipo_estado"]}
        resumen = datos["vigentes_vs_vencidos"][0] if datos["vigentes_vs_vencidos"] else {"vigentes": 0, "total": 0}
        return {
            "periodo": rango.periodo(),
            "por_tipo_estado": [{"tipo": t, **{e: cruce.get((t, e), 0) for e in ESTADOS_REPORTE}} for t in TIPOS_REPORTE],
            "vigentes_vs_vencidos": {"vigentes": resumen["vigentes"], "vencidos": resumen["total"] - resumen["vigentes"]},
            "puntos": datos["puntos"],
            "incluye_demo": self._hay_demo(rango, "reportes"),
        }

    def lugares(self, rango: Rango) -> dict:
        # Los lugares son un catálogo: se cuentan todos los activos, sin filtro de fechas
        datos = self.repo.lugares(rango.filtro(campo_fecha=None))
        return {
            "periodo": rango.periodo(),
            "por_categoria": [{"categoria": g["_id"] or "Sin categoría", "total": g["total"]} for g in datos["por_categoria"]],
            "puntos": datos["puntos"],
            "incluye_demo": rango.incluir_demo and self.repo.hay_demo("lugares", rango.filtro(campo_fecha=None)),
        }

    def laboratorio(self, rango: Rango) -> dict:
        base = rango.filtro("creado_en", borrado_logico=False)
        datos = self.repo.laboratorio({**base, "tipo": "dfs"}, {**base, "tipo": "distancia"})

        def nombre(parada: str) -> str:
            return PARADAS_KOMPAS.get(parada, {}).get("nombre", parada)

        return {
            "periodo": rango.periodo(),
            "dfs_puntos": [
                {"limite_profundidad": g["_id"]["limite"], "nodos": g["_id"]["nodos"], "rutas": _r1(g["rutas"]), "consultas": g["total"]}
                for g in datos["dfs_puntos"]
            ],
            "dfs_pares_top": [
                {"par": f"{nombre(g['_id']['origen'])} → {nombre(g['_id']['destino'])}", "total": g["total"]}
                for g in datos["dfs_pares_top"]
            ],
            "distancias_puntos": [
                {"modo": d.get("modo"), "euclidiana": d["euclidiana"], "manhattan": d["manhattan"]} for d in datos["distancias_puntos"]
            ],
            **self._laboratorio_v06(base),
            "incluye_demo": self._hay_demo(rango, "bitacora_laboratorio", campo_fecha="creado_en"),
        }

    def _laboratorio_v06(self, base: dict) -> dict:
        """Comparativo de búsqueda, convergencia y ahorro del genético, y transbordos con A*."""
        grupos = {(g["_id"]["algoritmo"], g["_id"]["heuristica"]): g for g in self.repo.busqueda_algoritmos({**base, "tipo": "busqueda"})}
        claves = ORDEN_ALGORITMOS + [k for k in grupos if k not in ORDEN_ALGORITMOS]
        busqueda = []
        for algoritmo, heuristica in claves:
            g = grupos.get((algoritmo, heuristica))
            if g is None:
                continue
            busqueda.append(
                {
                    "algoritmo": algoritmo,
                    "heuristica": heuristica,
                    "etiqueta": _etiqueta_algoritmo(algoritmo, heuristica),
                    "consultas": g["consultas"],
                    "nodos_promedio": _r1(g["nodos"]),
                    "costo_promedio_km": round(g["costo"], 3) if g["costo"] is not None else None,
                    "costo_optimo_promedio_km": round(g["optimo"], 3) if g["optimo"] is not None else None,
                    "razon_vs_optimo": round(g["razon"], 4) if g["razon"] is not None else None,
                    "porcentaje_optimo": _r1(100 * g["optimos"] / g["consultas"]) if g["consultas"] else None,
                    "ms_promedio": round(g["ms"], 3) if g["ms"] is not None else None,
                }
            )
        genetico = {**base, "tipo": "genetico"}
        ahorro = {g["_id"]: g for g in self.repo.genetico_ahorro(genetico)}
        t = self.repo.transbordos({**base, "tipo": "transbordo"})
        return {
            "busqueda_algoritmos": busqueda,
            "genetico_convergencia": [
                {"generacion": g["_id"] + 1, "mejor": round(g["mejor"], 6), "promedio": round(g["promedio"], 6) if g["promedio"] is not None else None, "ejecuciones": g["ejecuciones"]}
                for g in self.repo.genetico_convergencia(genetico)
            ],
            "genetico_ahorro": [
                {
                    "tipo_plan": tipo,
                    "planes": ahorro[tipo]["planes"],
                    "reordenados": ahorro[tipo]["reordenados"],
                    "km_antes": round(ahorro[tipo]["km_antes"], 2),
                    "km_despues": round(ahorro[tipo]["km_despues"], 2),
                    "km_ahorrados": round(ahorro[tipo]["km_antes"] - ahorro[tipo]["km_despues"], 2),
                }
                for tipo in [*TIPOS_PLAN, *(k for k in ahorro if k not in TIPOS_PLAN)]
                if tipo in ahorro
            ],
            "transbordos": {
                "consultas": t["consultas"],
                "encontrados": t["encontrados"],
                "nodos_explorados_promedio": _r1(t["nodos"]),
                "nodos_grafo_promedio": _r1(t["total_nodos"]),
                "ms_promedio": round(t["ms"], 3) if t["ms"] is not None else None,
            },
        }

    def asistente(self, rango: Rango) -> dict:
        """Uso del asistente con datos agregados (nunca el contenido de los mensajes)."""
        datos = self.repo.asistente(rango.filtro(), rango.inicio, rango.fin)
        mensajes = {_clave_fecha(g["_id"]): g["total"] for g in datos["mensajes_por_dia"]}
        conversaciones = {_clave_fecha(f): t for f, t in datos["conversaciones_por_dia"].items()}
        por_dia, dia = [], rango.desde
        while dia <= rango.hasta:
            fecha = dia.isoformat()
            por_dia.append({"fecha": fecha, "conversaciones": conversaciones.get(fecha, 0), "mensajes": mensajes.get(fecha, 0)})
            dia += timedelta(days=1)
        usadas = {g["_id"]: g["total"] for g in datos["herramientas"] if g["_id"]}
        herramientas = [{"herramienta": h, "total": usadas.pop(h, 0)} for h in HERRAMIENTAS] + [
            {"herramienta": h, "total": t} for h, t in usadas.items()
        ]
        duraciones = [d["ms"] for d in datos["duraciones"]]
        roles = {g["_id"]: g["total"] for g in datos["por_rol"]}
        respuestas = roles.get("asistente", 0) + roles.get("error", 0)
        origenes = {g["_id"]: g["total"] for g in datos["planes_por_origen"]}
        return {
            "periodo": rango.periodo(),
            "por_dia": por_dia,
            "herramientas": sorted(herramientas, key=lambda h: -h["total"]),
            "tiempo_respuesta": {
                "respuestas": len(duraciones),
                "promedio_ms": _r1(sum(duraciones) / len(duraciones)) if duraciones else None,
                "p90_ms": _r1(percentil(duraciones, 90)),
            },
            "errores": {
                "respuestas": respuestas,
                "errores": roles.get("error", 0),
                "porcentaje_error": _r1(100 * roles.get("error", 0) / respuestas) if respuestas else 0.0,
            },
            "planes_por_origen": [{"origen": o, "total": origenes.get(o, 0)} for o in ("planificador", "asistente")],
            "incluye_demo": self._hay_demo(rango, "conversaciones", "planes"),
        }
