"""Pipelines de agregación del dashboard. Aquí vive todo el $match/$group/$facet/$bucket/$dateTrunc.

Cada método recibe el filtro ya armado y regresa listas de dict sin ObjectId. Rellenar huecos con 0,
redondear y poner descripciones es trabajo del servicio.
"""

from datetime import datetime

from pymongo.database import Database

TZ = "America/Mexico_City"
LIMITE_PUNTOS = 500

LIMITES_PRESUPUESTO = [0, 100, 200, 300, 500, 800, 1200]
LIMITES_TIEMPO = [0, 60, 120, 180, 240, 360, 480]


def _conteo(grupos: list[dict]) -> dict:
    return {g["_id"]: g["total"] for g in grupos if g["_id"] is not None}


class RepositorioDashboard:
    def __init__(self, bd: Database):
        self.bd = bd

    # ─────────────────────────────── Conteos simples ───────────────────────────────

    def contar(self, coleccion: str, filtro: dict) -> int:
        return self.bd[coleccion].count_documents(filtro)

    def hay_demo(self, coleccion: str, filtro: dict) -> bool:
        return self.bd[coleccion].count_documents({**filtro, "demo": True}, limit=1) > 0

    def tiempo_promedio(self, filtro: dict) -> float | None:
        resultado = list(
            self.bd.historial_rutas.aggregate(
                [{"$match": filtro}, {"$group": {"_id": None, "promedio": {"$avg": "$tiempo_estimado"}}}]
            )
        )
        return resultado[0]["promedio"] if resultado else None

    def planes_con_recomendacion(self, filtro: dict) -> dict:
        """Planes evaluados y cuántos tuvieron al menos un candidato `recomendable`."""
        resultado = list(
            self.bd.planes.aggregate(
                [
                    {"$match": {**filtro, "evaluacion": {"$exists": True}}},
                    {
                        "$group": {
                            "_id": None,
                            "evaluados": {"$sum": 1},
                            "con_recomendacion": {
                                "$sum": {"$cond": [{"$in": ["recomendable", {"$ifNull": ["$evaluacion.candidatos.estado", []]}]}, 1, 0]}
                            },
                        }
                    },
                ]
            )
        )
        return resultado[0] if resultado else {"evaluados": 0, "con_recomendacion": 0}

    # ─────────────────────────────────── Series ────────────────────────────────────

    def serie(self, coleccion: str, filtro: dict, unidad: str) -> dict:
        """{inicio_del_periodo: total} agrupando `created_at` por día, semana (lunes) o mes en hora de Toluca."""
        trunc = {"date": "$created_at", "unit": unidad, "timezone": TZ}
        if unidad == "week":
            trunc["startOfWeek"] = "monday"
        pipeline = [
            {"$match": filtro},
            {"$group": {"_id": {"$dateTrunc": trunc}, "total": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ]
        return _conteo(self.bd[coleccion].aggregate(pipeline))

    def serie_por_interes(self, filtro: dict, unidad: str) -> list[dict]:
        trunc = {"date": "$created_at", "unit": unidad, "timezone": TZ}
        if unidad == "week":
            trunc["startOfWeek"] = "monday"
        pipeline = [
            {"$match": filtro},
            {"$unwind": "$intereses"},
            {"$group": {"_id": {"fecha": {"$dateTrunc": trunc}, "interes": "$intereses"}, "total": {"$sum": 1}}},
            {"$sort": {"_id.fecha": 1}},
        ]
        return [{"fecha": g["_id"]["fecha"], "interes": g["_id"]["interes"], "total": g["total"]} for g in self.bd.planes.aggregate(pipeline)]

    # ──────────────────────────────────── Planes ───────────────────────────────────

    def planes(self, filtro: dict) -> dict:
        """Una sola consulta con $facet para todas las gráficas de la pestaña Planes."""
        pipeline = [
            {"$match": filtro},
            {
                "$facet": {
                    "por_interes": [
                        {"$unwind": "$intereses"},
                        {"$group": {"_id": "$intereses", "total": {"$sum": 1}}},
                        {"$sort": {"total": -1}},
                    ],
                    "por_movilidad": [{"$unwind": "$movilidad"}, {"$group": {"_id": "$movilidad", "total": {"$sum": 1}}}],
                    "por_contexto": [{"$group": {"_id": "$contexto", "total": {"$sum": 1}}}],
                    "presupuesto": [
                        {"$match": {"presupuesto.max": {"$type": "number"}}},
                        {
                            "$bucket": {
                                "groupBy": "$presupuesto.max",
                                "boundaries": LIMITES_PRESUPUESTO,
                                "default": "1200+",
                                "output": {"total": {"$sum": 1}},
                            }
                        },
                    ],
                    "tiempo_disponible": [
                        {
                            "$bucket": {
                                "groupBy": "$tiempo_disponible",
                                "boundaries": LIMITES_TIEMPO,
                                "default": "8h+",
                                "output": {"total": {"$sum": 1}},
                            }
                        }
                    ],
                    "dia_hora": [
                        {"$match": {"fecha_plan": {"$type": "date"}}},
                        {
                            "$group": {
                                "_id": {
                                    "dia": {"$isoDayOfWeek": {"date": "$fecha_plan", "timezone": TZ}},
                                    "hora": {"$hour": {"date": "$fecha_plan", "timezone": TZ}},
                                },
                                "total": {"$sum": 1},
                            }
                        },
                    ],
                    "interes_por_contexto": [
                        {"$unwind": "$intereses"},
                        {"$group": {"_id": {"contexto": "$contexto", "interes": "$intereses"}, "total": {"$sum": 1}}},
                    ],
                }
            },
        ]
        return next(self.bd.planes.aggregate(pipeline))

    # ─────────────────────────────── Sistema experto ───────────────────────────────

    def sistema_experto(self, filtro: dict) -> dict:
        filtro = {**filtro, "evaluacion": {"$exists": True}}
        pipeline = [
            {"$match": filtro},
            {"$unwind": "$evaluacion.candidatos"},
            {
                "$facet": {
                    "por_estado": [{"$group": {"_id": "$evaluacion.candidatos.estado", "total": {"$sum": 1}}}],
                    "reglas_top": [
                        {"$unwind": "$evaluacion.candidatos.reglas"},
                        {"$group": {"_id": "$evaluacion.candidatos.reglas", "total": {"$sum": 1}}},
                        {"$sort": {"total": -1, "_id": 1}},
                        {"$limit": 20},
                    ],
                    "puntuacion_por_tipo": [
                        {"$match": {"evaluacion.candidatos.puntuacion": {"$ne": None}}},
                        {
                            "$group": {
                                "_id": "$evaluacion.candidatos.tipo",
                                "promedio": {"$avg": "$evaluacion.candidatos.puntuacion"},
                                "minimo": {"$min": "$evaluacion.candidatos.puntuacion"},
                                "maximo": {"$max": "$evaluacion.candidatos.puntuacion"},
                                "total": {"$sum": 1},
                            }
                        },
                    ],
                }
            },
        ]
        resultado = next(self.bd.planes.aggregate(pipeline))
        # Estas dos cuentan planes, no candidatos: van fuera del $unwind
        resultado["sin_datos_suficientes"] = self.bd.planes.count_documents({**filtro, "evaluacion.datos_suficientes": False})
        resultado["por_version"] = list(
            self.bd.planes.aggregate(
                [{"$match": filtro}, {"$group": {"_id": "$evaluacion.version_reglas", "total": {"$sum": 1}}}, {"$sort": {"_id": 1}}]
            )
        )
        return resultado

    # ─────────────────────────────────── Movilidad ─────────────────────────────────

    def movilidad(self, filtro: dict) -> dict:
        pipeline = [
            {"$match": filtro},
            {
                "$facet": {
                    "por_transporte": [
                        {
                            "$group": {
                                "_id": "$transporte.nombre",
                                "total": {"$sum": 1},
                                "promedio": {"$avg": "$tiempo_estimado"},
                                "minimo": {"$min": "$tiempo_estimado"},
                                "maximo": {"$max": "$tiempo_estimado"},
                            }
                        },
                        {"$sort": {"total": -1}},
                    ],
                    "rutas_top": [
                        {"$group": {"_id": "$id_ruta", "total": {"$sum": 1}, "promedio": {"$avg": "$tiempo_estimado"}}},
                        {"$sort": {"total": -1, "_id": 1}},
                        {"$limit": 10},
                    ],
                }
            },
        ]
        return next(self.bd.historial_rutas.aggregate(pipeline))

    # ──────────────────────────────────── Reportes ─────────────────────────────────

    def reportes(self, filtro: dict, momento: datetime) -> dict:
        vigente = {"$gt": ["$vigente_hasta", momento]}
        pipeline = [
            {"$match": filtro},
            {
                "$facet": {
                    "por_tipo_estado": [{"$group": {"_id": {"tipo": "$tipo", "estado": "$estado"}, "total": {"$sum": 1}}}],
                    "vigentes_vs_vencidos": [
                        {"$group": {"_id": None, "vigentes": {"$sum": {"$cond": [vigente, 1, 0]}}, "total": {"$sum": 1}}}
                    ],
                    "puntos": [
                        {"$sort": {"observado_en": -1}},
                        {"$limit": LIMITE_PUNTOS},
                        {
                            "$project": {
                                "_id": 0,
                                "lng": {"$arrayElemAt": ["$ubicacion.coordinates", 0]},
                                "lat": {"$arrayElemAt": ["$ubicacion.coordinates", 1]},
                                "tipo": 1,
                                "estado": 1,
                                "vigente": vigente,
                            }
                        },
                    ],
                }
            },
        ]
        return next(self.bd.reportes.aggregate(pipeline))

    # ──────────────────────────────────── Lugares ──────────────────────────────────

    def lugares(self, filtro: dict) -> dict:
        pipeline = [
            {"$match": filtro},
            {
                "$facet": {
                    "por_categoria": [{"$group": {"_id": "$categoria.nombre", "total": {"$sum": 1}}}, {"$sort": {"total": -1}}],
                    "puntos": [
                        {"$sort": {"_id": 1}},
                        {"$limit": LIMITE_PUNTOS},
                        {
                            "$project": {
                                "_id": 0,
                                "id": "$_id",
                                "nombre": 1,
                                "lng": {"$arrayElemAt": ["$ubicacion.coordinates", 0]},
                                "lat": {"$arrayElemAt": ["$ubicacion.coordinates", 1]},
                                "categoria": "$categoria.nombre",
                            }
                        },
                    ],
                }
            },
        ]
        return next(self.bd.lugares.aggregate(pipeline))

    # ─────────────────────────────────── Laboratorio ───────────────────────────────

    def laboratorio(self, filtro_dfs: dict, filtro_distancias: dict) -> dict:
        dfs = [
            {"$match": filtro_dfs},
            {
                "$facet": {
                    # Burbujas: consultas con el mismo límite y nodos explorados se juntan (total = cuántas)
                    "dfs_puntos": [
                        {
                            "$group": {
                                "_id": {"limite": "$limite_profundidad", "nodos": "$total_nodos_explorados"},
                                "rutas": {"$avg": "$total_rutas"},
                                "total": {"$sum": 1},
                            }
                        },
                        {"$sort": {"_id.limite": 1, "_id.nodos": 1}},
                        {"$limit": LIMITE_PUNTOS},
                    ],
                    "dfs_pares_top": [
                        {"$group": {"_id": {"origen": "$origen", "destino": "$destino"}, "total": {"$sum": 1}}},
                        {"$sort": {"total": -1, "_id.origen": 1}},
                        {"$limit": 10},
                    ],
                }
            },
        ]
        resultado = next(self.bd.bitacora_laboratorio.aggregate(dfs))
        resultado["distancias_puntos"] = list(
            self.bd.bitacora_laboratorio.find(
                filtro_distancias, {"_id": 0, "modo": 1, "euclidiana": 1, "manhattan": 1}
            ).sort("creado_en", -1).limit(LIMITE_PUNTOS)
        )
        return resultado
