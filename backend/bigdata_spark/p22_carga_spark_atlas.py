"""Modulo de Persistencia Masiva con Spark y MongoDB Atlas (Practica 22).

Este modulo toma los resultados agregados del procesamiento batch de Apache Spark
y los persiste de forma distribuida en colecciones analiticas de MongoDB Atlas:
- Coleccion destino: `metricas_bigdata_kompas`.
- Permite que el backend FastAPI y los dashboards de administracion consulten
  indicadores precalculados de alto rendimiento sin recalcular sobre millones de filas.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from pymongo.database import Database
from pymongo import ReplaceOne, ASCENDING

from app.nucleo.bd import get_bd
from bigdata_spark.p21_procesamiento_spark import ProcesadorSparkKompas

COLECCION_BIGDATA = "metricas_bigdata_kompas"


class PersistenciaSparkAtlasKompas:
    """Conector para sincronizar los lotes de Spark con MongoDB Atlas."""

    def __init__(self, bd: Database | None = None):
        """Inicializa el conector con MongoDB Atlas."""
        self.bd = bd if bd is not None else get_bd()
        self.coleccion = self.bd[COLECCION_BIGDATA]

    def sincronizar_lote_en_atlas(self, ruta_csv: Path | str | None = None) -> dict[str, Any]:
        """Ejecuta el procesamiento y vuelca los documentos en Atlas (Practica 22).
        
        Que hace:
            Ejecuta ProcesadorSparkKompas y guarda el resultado consolidado en MongoDB Atlas.
        Como lo hace:
            Inserta un lote con id de ejecucion, timestamp y métricas por transporte.
        """
        proc = ProcesadorSparkKompas(ruta_csv=ruta_csv) if ruta_csv else ProcesadorSparkKompas()
        metricas = proc.ejecutar_pipeline_batch()

        documento = {
            "fecha_sincronizacion": datetime.now(timezone.utc),
            "motor": metricas.get("motor_procesamiento"),
            "registros_analizados": metricas.get("total_registros_procesados"),
            "metricas_por_transporte": metricas.get("agregacion_por_transporte"),
            "diagnostico": metricas.get("diagnostico_big_data"),
            "estado": "ACTUALIZADO",
            "clave_lote": "LOTE_ULTIMO_PROCESADO",
        }

        # Creacion de indices de optimizacion (Practica 22)
        try:
            self.coleccion.create_index([("fecha_sincronizacion", ASCENDING)])
            self.coleccion.create_index([("clave_lote", ASCENDING)])
        except Exception:
            pass

        # Operacion idempotente con ReplaceOne / upsert
        res = self.coleccion.replace_one(
            {"clave_lote": "LOTE_ULTIMO_PROCESADO"},
            documento,
            upsert=True,
        )

        id_doc = str(res.upserted_id or "ACTUALIZADO_EXISTENTE")
        return {
            "id_insercion_atlas": id_doc,
            "mensaje": "Lote analitico de Big Data sincronizado exitosamente en MongoDB Atlas.",
            "fecha_utc": documento["fecha_sincronizacion"].isoformat(),
        }


if __name__ == "__main__":
    conector = PersistenciaSparkAtlasKompas()
    res = conector.sincronizar_lote_en_atlas()
    print("Sincronizacion completada:", res)
