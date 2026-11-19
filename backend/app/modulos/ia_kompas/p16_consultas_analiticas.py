"""Modulo de Persistencia y Consultas Analiticas Avanzadas en MongoDB Atlas (Practicas 15 y 16).

Este modulo implementa la capa de persistencia analitica y consultas avanzadas
utilizando el Aggregation Framework de MongoDB sobre las evaluaciones inteligentes de movilidad:
1. Persistencia de evaluaciones integrales con metadatos de modelos (Practica 15).
2. Consultas analiticas avanzadas con $match, $group, $sort, $project y $facet (Practica 16).
3. Generacion de reportes de clusters, horas pico y deteccion de viajes con riesgo de demora.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import pandas as pd
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.nucleo.bd import get_bd

NOMBRE_COLECCION_EVALUACIONES = "evaluaciones_ia_kompas"


class AnaliticaAtlasKompas:
    """Clase para la persistencia y ejecucion de consultas analiticas inteligentes en MongoDB Atlas."""

    def __init__(self, bd: Database | None = None):
        """Inicializa el modulo de analitica con conexion a la base de datos MongoDB.
        
        Que hace:
            Configura el cliente y la coleccion de evaluaciones analiticas de Kompas.
        Como lo hace:
            Utiliza la instancia de base de datos provista o invoca get_bd() del nucleo.
        Conexiones:
            Se comunica con el pool de conexiones de app.nucleo.bd.
        """
        self.bd = bd if bd is not None else get_bd()
        self.coleccion = self.bd[NOMBRE_COLECCION_EVALUACIONES]

    def guardar_evaluacion(self, datos_evaluacion: dict[str, Any]) -> dict[str, Any]:
        """Persiste una evaluacion integral generada por el motor de recomendaciones (Practica 15).
        
        Que hace:
            Almacena el resultado del analisis multi-modelo con marca de tiempo UTC y metadatos.
        Como lo hace:
            Inserta un documento estructurado en la coleccion evaluaciones_ia_kompas.
        Conexiones:
            Es invocado despues de ejecutar MotorRecomendacionesKompas.evaluar_traslado_integral.
        """
        documento = {
            "fecha_evaluacion": datetime.now(timezone.utc),
            "datos_entrada": datos_evaluacion.get("datos_entrada", {}),
            "prediccion_supervisada": datos_evaluacion.get("prediccion_supervisada", {}),
            "segmentacion_no_supervisada": datos_evaluacion.get("segmentacion_no_supervisada", {}),
            "reduccion_dimensionalidad_pca": datos_evaluacion.get("reduccion_dimensionalidad_pca", {}),
            "recomendaciones_operativas": datos_evaluacion.get("recomendaciones_operativas", []),
            "estado": "PROCESADO",
        }
        res = self.coleccion.insert_one(documento)
        return {
            "id_evaluacion": str(res.inserted_id),
            "mensaje": "Evaluacion persistida exitosamente en MongoDB Atlas.",
            "fecha_utc": documento["fecha_evaluacion"].isoformat(),
        }

    def registro_integral_tres_colecciones(
        self, datos_usuario: dict[str, Any], datos_traslado: dict[str, Any], resultado_ia: dict[str, Any]
    ) -> dict[str, Any]:
        """Implementa el registro integral multi-coleccion (Practica 19).
        
        Que hace:
            Vincula tres entidades en MongoDB Atlas:
            1. Coleccion 'viajeros': perfil del usuario y preferencias.
            2. Coleccion 'traslados_registrados': datos brutos del viaje.
            3. Coleccion 'evaluaciones_ia_kompas': inferencia predictiva, cluster y PCA.
        Como lo hace:
            Ejecuta inserciones cruzadas vinculadas por id_usuario e id_traslado con UUID.
        """
        import uuid
        id_usuario = str(datos_usuario.get("id_usuario", uuid.uuid4().hex[:8]))
        id_traslado = str(uuid.uuid4())
        ahora_utc = datetime.now(timezone.utc)

        # 1. Coleccion viajeros (upsert)
        col_viajeros = self.bd["viajeros"]
        col_viajeros.update_one(
            {"id_usuario": id_usuario},
            {
                "$set": {
                    "nombre": datos_usuario.get("nombre", "Viajero Kompas"),
                    "dispositivo": datos_usuario.get("dispositivo", "Android"),
                    "ultima_actividad": ahora_utc,
                }
            },
            upsert=True,
        )

        # 2. Coleccion traslados_registrados
        col_traslados = self.bd["traslados_registrados"]
        doc_traslado = {
            "id_traslado": id_traslado,
            "id_usuario": id_usuario,
            "fecha_registro": ahora_utc,
            **datos_traslado,
        }
        col_traslados.insert_one(doc_traslado)

        # 3. Coleccion evaluaciones_ia_kompas
        doc_ia = {
            "id_traslado": id_traslado,
            "id_usuario": id_usuario,
            "fecha_evaluacion": ahora_utc,
            "datos_entrada": datos_traslado,
            "prediccion_supervisada": resultado_ia.get("prediccion_supervisada", {}),
            "segmentacion_no_supervisada": resultado_ia.get("segmentacion_no_supervisada", {}),
            "reduccion_dimensionalidad_pca": resultado_ia.get("reduccion_dimensionalidad_pca", {}),
            "recomendaciones_operativas": resultado_ia.get("recomendaciones_operativas", []),
            "estado": "PROCESADO",
        }
        res_ia = self.coleccion.insert_one(doc_ia)

        return {
            "id_usuario": id_usuario,
            "id_traslado": id_traslado,
            "id_evaluacion_ia": str(res_ia.inserted_id),
            "mensaje": "Registro academico e integral completado en las 3 colecciones NoSQL.",
        }

    def estadisticas_por_cluster(self) -> list[dict[str, Any]]:
        """Agrupa las evaluaciones historicas por perfil de viajero (Practica 16: Operacion $group).
        
        Que hace:
            Calcula el total de viajes evaluados, la confianza promedio y los valores medios de distancia
            y costo por cada uno de los 4 perfiles descubiertos por K-Means.
        Como lo hace:
            Ejecuta un pipeline de agregacion con $group y $project ordenado por id de cluster.
        Conexiones:
            Alimenta vistas ejecutivas y el endpoint GET /api/ia/analitica/reporte-clusters.
        """
        pipeline = [
            {
                "$group": {
                    "_id": "$segmentacion_no_supervisada.cluster_asignado",
                    "nombre_perfil": {"$first": "$segmentacion_no_supervisada.nombre_perfil"},
                    "total_viajes": {"$sum": 1},
                    "confianza_promedio": {"$avg": "$prediccion_supervisada.confianza"},
                    "distancia_media_km": {"$avg": "$datos_entrada.distancia_km"},
                    "presupuesto_medio_mxn": {"$avg": "$datos_entrada.presupuesto_mxn"},
                }
            },
            {
                "$project": {
                    "cluster_id": "$_id",
                    "nombre_perfil": 1,
                    "total_viajes": 1,
                    "confianza_promedio": {"$round": ["$confianza_promedio", 4]},
                    "distancia_media_km": {"$round": ["$distancia_media_km", 2]},
                    "presupuesto_medio_mxn": {"$round": ["$presupuesto_medio_mxn", 2]},
                    "_id": 0,
                }
            },
            {"$sort": {"cluster_id": 1}},
        ]
        return list(self.coleccion.aggregate(pipeline))

    def resumen_horas_pico_congestion(self) -> list[dict[str, Any]]:
        """Analiza la distribucion horaria de las solicitudes (Practica 16: Operacion $match + $group).
        
        Que hace:
            Identifica las horas del dia con mayor concentracion de solicitudes y su modo de transporte predilecto.
        Como lo hace:
            Agrupa por hora_dia, cuenta la cantidad de registros y calcula el modo mas frecuente.
        Conexiones:
            Alimenta el endpoint GET /api/ia/analitica/horas-pico.
        """
        pipeline = [
            {
                "$group": {
                    "_id": "$datos_entrada.hora_dia",
                    "solicitudes": {"$sum": 1},
                    "es_hora_pico": {"$first": "$datos_entrada.es_hora_pico"},
                    "duracion_promedio_min": {"$avg": "$datos_entrada.duracion_min"},
                }
            },
            {
                "$project": {
                    "hora": "$_id",
                    "solicitudes": 1,
                    "es_hora_pico": 1,
                    "duracion_promedio_min": {"$round": ["$duracion_promedio_min", 2]},
                    "_id": 0,
                }
            },
            {"$sort": {"hora": 1}},
        ]
        return list(self.coleccion.aggregate(pipeline))

    def viajes_riesgo_o_atipicos(self, umbral_confianza_min: float = 0.50) -> list[dict[str, Any]]:
        """Filtra traslados con baja certidumbre de clasificacion o condiciones complejas.
        
        Que hace:
            Detecta traslados donde el modelo tuvo incertidumbre o con condiciones climaticas adversas.
        Como lo hace:
            Aplica un $match con operadores logicos $or y $lte.
        """
        pipeline = [
            {
                "$match": {
                    "$or": [
                        {"prediccion_supervisada.confianza": {"$lt": umbral_confianza_min}},
                        {"datos_entrada.clima_lluvia": 1},
                    ]
                }
            },
            {
                "$project": {
                    "fecha": "$fecha_evaluacion",
                    "distancia_km": "$datos_entrada.distancia_km",
                    "hora_dia": "$datos_entrada.hora_dia",
                    "transporte_optimo": "$prediccion_supervisada.transporte_optimo",
                    "confianza": "$prediccion_supervisada.confianza",
                    "perfil": "$segmentacion_no_supervisada.nombre_perfil",
                    "_id": 0,
                }
            },
            {"$sort": {"confianza": 1}},
            {"$limit": 20},
        ]
        return list(self.coleccion.aggregate(pipeline))

    def exportar_reporte_dataframe(self) -> pd.DataFrame:
        """Exporta los registros historicos a un DataFrame estructurado de Pandas.
        
        Que hace:
            Permite procesar o descargar los resultados de la base de datos hacia hojas de calculo CSV.
        Como lo hace:
            Realiza un find() y aplana los subdocumentos en columnas individuales.
        """
        documentos = list(self.coleccion.find({}, {"_id": 0}))
        if not documentos:
            return pd.DataFrame()

        filas = []
        for doc in documentos:
            fila = {
                "fecha": doc.get("fecha_evaluacion"),
                "distancia_km": doc.get("datos_entrada", {}).get("distancia_km"),
                "hora_dia": doc.get("datos_entrada", {}).get("hora_dia"),
                "presupuesto_mxn": doc.get("datos_entrada", {}).get("presupuesto_mxn"),
                "transporte_predicho": doc.get("prediccion_supervisada", {}).get("transporte_optimo"),
                "confianza": doc.get("prediccion_supervisada", {}).get("confianza"),
                "cluster_id": doc.get("segmentacion_no_supervisada", {}).get("cluster_asignado"),
                "perfil_nombre": doc.get("segmentacion_no_supervisada", {}).get("nombre_perfil"),
                "pc1": doc.get("reduccion_dimensionalidad_pca", {}).get("coordenada_pc1"),
                "pc2": doc.get("reduccion_dimensionalidad_pca", {}).get("coordenada_pc2"),
            }
            filas.append(fila)

        return pd.DataFrame(filas)
