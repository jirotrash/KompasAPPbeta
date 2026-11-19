"""Modulo de Segmentacion de Perfiles de Movilidad mediante K-Means (Practica 07).

Este modulo implementa el agrupamiento no supervisado (clustering) utilizando
el algoritmo K-Means para descubrir patrones y perfiles de movilidad de los
viajeros de Kompas sin depender de etiquetas predefinidas.

Incluye escalamiento de variables con StandardScaler, seleccion automatica del
numero de clusters mediante el Coeficiente de Silueta e Inercia (Metodo del Codo),
e interpretacion funcional de los centroides calculados en el Valle de Toluca.
"""

from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from app.modulos.ia_kompas.pipeline_datos import RUTA_LIMPIO_DEFECTO, ejecutar_pipeline_completo

COLUMNAS_CLUSTERING = [
    "distancia_km",
    "hora_dia",
    "duracion_min",
    "presupuesto_mxn",
    "es_hora_pico",
]


class SegmentadorViajerosKompas:
    """Clase para la agrupacion no supervisada de usuarios y traslados de Kompas."""

    def __init__(self, ruta_csv_limpio: Path | str = RUTA_LIMPIO_DEFECTO, semilla: int = 42):
        """Inicializa el segmentador con la ruta de datos y semilla.
        
        Que hace:
            Configura el origen de los datos de traslados y fija la semilla aleatoria para K-Means.
        Como lo hace:
            Establece la ruta al archivo CSV limpio y crea el objeto escalador StandardScaler.
        Conexiones:
            Consume RUTA_LIMPIO_DEFECTO generado por pipeline_datos.py.
        """
        self.ruta_csv_limpio = Path(ruta_csv_limpio)
        self.semilla = semilla
        self.escalador = StandardScaler()

    def preparar_matriz_clustering(self, df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
        """Extrae y estandariza las variables cuantitativas de movilidad.
        
        Que hace:
            Transforma las columnas de distancia, hora, duracion y presupuesto a una escala
            con media 0 y varianza unitaria para evitar que variables con magnitudes grandes
            dominen el calculo de distancias euclidianas.
        Como lo hace:
            1. Selecciona el subconjunto de columnas definidas en COLUMNAS_CLUSTERING.
            2. Aplica fit_transform con StandardScaler sobre las columnas numericas.
        Conexiones:
            Recibe el DataFrame cargado desde kompas_traslados_limpio.csv.
        """
        X_crudo = df[COLUMNAS_CLUSTERING].copy().values
        X_escalado = self.escalador.fit_transform(X_crudo)
        return X_escalado, COLUMNAS_CLUSTERING

    def evaluar_rango_k(self, X_escalado: np.ndarray, k_min: int = 2, k_max: int = 6) -> dict[str, Any]:
        """Evalua diferentes valores de K mediante Inercia y Coeficiente de Silueta.
        
        Que hace:
            Permite fundamentar cuantitativamente el numero optimo de perfiles de viajeros.
        Como lo hace:
            1. Itera K desde k_min hasta k_max.
            2. Ajusta KMeans(n_clusters=k, init='k-means++', random_state=self.semilla).
            3. Registra la inercia (suma de distancias cuadradas al centroide mas cercano).
            4. Calcula el Coeficiente de Silueta (silhouette_score) que mide que tan similar
               es un punto a su propio cluster comparado con los otros clusters (-1 a 1).
            5. Identifica el K que maximiza el Coeficiente de Silueta.
        Conexiones:
            Alimenta la decision del numero de clusters que se utiliza en el entrenamiento final.
        """
        evaluaciones = []
        mejor_k = k_min
        mejor_silueta = -2.0

        for k in range(k_min, k_max + 1):
            km = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=self.semilla)
            etiquetas = km.fit_predict(X_escalado)

            inercia = float(km.inertia_)
            silueta = float(silhouette_score(X_escalado, etiquetas))

            evaluaciones.append({
                "k": k,
                "inercia": round(inercia, 2),
                "coeficiente_silueta": round(silueta, 4),
            })

            if silueta > mejor_silueta:
                mejor_silueta = silueta
                mejor_k = k

        return {
            "rango_evaluado": f"K de {k_min} a {k_max}",
            "resultados_por_k": evaluaciones,
            "k_recomendado": mejor_k,
            "mejor_silueta": round(mejor_silueta, 4),
        }

    def interpretar_perfiles(
        self, df: pd.DataFrame, etiquetas: np.ndarray, centroides_reales: np.ndarray
    ) -> list[dict[str, Any]]:
        """Asigna una etiqueta funcional y describe cada cluster en el dominio de Kompas.
        
        Que hace:
            Traduce los centroides matematicos a descripciones utiles para el negocio de transporte.
        Como lo hace:
            Analiza los promedios reales de distancia, hora, presupuesto y preferencia modal:
            - Viajes con bajo presupuesto y distancia media matutina: Estudiante / Transporte Economico.
            - Viajes con alto presupuesto, mayor duracion y en hora pico: Profesionista / Auto Privado.
            - Viajes con distancias cortas o fuera de hora pico: Viajero Local / Recreativo.
        Conexiones:
            Recibe los centroides en escala original y las etiquetas asignadas a cada fila del DataFrame.
        """
        df_temp = df.copy()
        df_temp["cluster"] = etiquetas

        perfiles = []
        for c_id in sorted(df_temp["cluster"].unique()):
            sub = df_temp[df_temp["cluster"] == c_id]
            dist_prom = float(sub["distancia_km"].mean())
            hora_prom = float(sub["hora_dia"].mean())
            pres_prom = float(sub["presupuesto_mxn"].mean())
            dur_prom = float(sub["duracion_min"].mean())
            pico_pct = float(sub["es_hora_pico"].mean() * 100.0)

            # Modo de transporte mas frecuente en este cluster
            modo_frec = str(sub["modo_transporte_optimo"].mode().iloc[0])

            # Reglas semanticas de caracterizacion de perfil
            if pres_prom <= 45.0 and dist_prom < 6.0:
                nombre = "Viajero Cotidiano / Transporte Economico"
                descripcion = "Usuarios que realizan traslados habituales hacia escuelas o centros de trabajo con presupuesto ajustado."
            elif pres_prom >= 100.0 or pico_pct >= 50.0:
                nombre = "Profesionista / Horario Pico de Alta Demanda"
                descripcion = "Usuarios con traslados mas largos o en horario de trafico con mayor disposicion al uso de auto privado o taxi."
            else:
                nombre = "Viajero Regional / Horario Flexible"
                descripcion = "Traslados intermedios en horarios valle entre diferentes municipios del Valle de Toluca."

            perfiles.append({
                "cluster_id": int(c_id),
                "nombre_perfil": nombre,
                "descripcion": descripcion,
                "total_viajeros": int(len(sub)),
                "porcentaje_total": round(float(len(sub) / len(df_temp) * 100.0), 2),
                "centroide_promedios": {
                    "distancia_km_media": round(dist_prom, 2),
                    "hora_dia_media": round(hora_prom, 1),
                    "presupuesto_mxn_medio": round(pres_prom, 2),
                    "duracion_min_media": round(dur_prom, 1),
                    "porcentaje_hora_pico": round(pico_pct, 1),
                    "modo_predilecto": modo_frec,
                },
            })

        return perfiles

    def ejecutar_segmentacion_completa(self, k: int | None = None) -> dict[str, Any]:
        """Ejecuta el ciclo de clustering completo: carga, evaluacion de K, ajuste y perfiles.
        
        Que hace:
            Orquesta todo el proceso de aprendizaje no supervisado y genera el reporte consolidado.
        Como lo hace:
            1. Carga los datos limpios.
            2. Escala las variables cuantitativas de movilidad.
            3. Evalua K de 2 a 5 para determinar el K optimo (o usa el k recibido).
            4. Entrena el modelo definitivo con KMeans(n_clusters=k_elegido).
            5. Desestandariza los centroides mediante escalador.inverse_transform.
            6. Construye la interpretacion semantica de cada perfil descubierto.
        Conexiones:
            Alimenta el servicio de IA y el endpoint GET /api/ia/segmentacion-viajeros de router.py.
        """
        if not self.ruta_csv_limpio.exists():
            ejecutar_pipeline_completo()

        df_limpio = pd.read_csv(self.ruta_csv_limpio)
        X_escalado, columnas = self.preparar_matriz_clustering(df_limpio)

        eval_k = self.evaluar_rango_k(X_escalado, k_min=2, k_max=5)
        k_final = k if k is not None else eval_k["k_recomendado"]

        modelo_kmeans = KMeans(
            n_clusters=k_final,
            init="k-means++",
            n_init=15,
            random_state=self.semilla,
        )
        etiquetas = modelo_kmeans.fit_predict(X_escalado)

        # Desestandarizar centroides para devolverlos en unidades reales (km, pesos, etc.)
        centroides_originales = self.escalador.inverse_transform(modelo_kmeans.cluster_centers_)

        perfiles = self.interpretar_perfiles(df_limpio, etiquetas, centroides_originales)
        silueta_final = float(silhouette_score(X_escalado, etiquetas))

        return {
            "total_registros_analizados": len(df_limpio),
            "variables_utilizadas": columnas,
            "analisis_metodo_codo_y_silueta": eval_k,
            "k_utilizado": k_final,
            "inercia_final": round(float(modelo_kmeans.inertia_), 2),
            "coeficiente_silueta_final": round(silueta_final, 4),
            "perfiles_descubiertos": perfiles,
        }

