"""Modulo de Analisis Avanzado de Clusters, Deteccion de Anomalias y Persistencia (Practica 08).

Este modulo implementa la auditoria avanzada de calidad de los clusters de viajeros:
1. Comparacion de estrategias de inicializacion (k-means++ vs random).
2. Comparacion del impacto de los escaladores (StandardScaler vs MinMaxScaler).
3. Evaluacion de estabilidad del agrupamiento mediante el Adjusted Rand Index (ARI).
4. Deteccion matematica de viajes anomalos / atipicos basada en distancia euclidiana
   al centroide del cluster (percentil 95).
5. Persistencia automatica de los perfiles resultantes en la base de datos MongoDB de Kompas.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.preprocessing import MinMaxScaler, StandardScaler

from app.modulos.ia_kompas.p07_segmentacion_viajeros import COLUMNAS_CLUSTERING, SegmentadorViajerosKompas
from app.modulos.ia_kompas.pipeline_datos import RUTA_LIMPIO_DEFECTO
from app.nucleo.bd import get_bd


class AuditorClustersKompas:
    """Clase para la evaluacion rigurosa, deteccion de anomalias y persistencia de clusters."""

    def __init__(self, ruta_csv_limpio: Path | str = RUTA_LIMPIO_DEFECTO, semilla: int = 42):
        """Inicializa el auditor con la ruta de datos y la semilla base.
        
        Que hace:
            Configura la ruta de datos y la semilla para los experimentos comparativos.
        Como lo hace:
            Instancia el segmentador base y guarda la ruta hacia el archivo CSV de traslados limpios.
        Conexiones:
            Utiliza SegmentadorViajerosKompas de p07_segmentacion_viajeros.py.
        """
        self.ruta_csv_limpio = Path(ruta_csv_limpio)
        self.semilla = semilla
        self.segmentador = SegmentadorViajerosKompas(ruta_csv_limpio=self.ruta_csv_limpio, semilla=self.semilla)

    def comparar_inicializaciones(self, X_escalado: np.ndarray, k: int = 3) -> dict[str, Any]:
        """Compara la convergencia de K-Means utilizando k-means++ versus random.
        
        Que hace:
            Demuestra empiricamente por que la inicializacion informada k-means++ supera
            a la seleccion puramente aleatoria en terminos de inercia e iteraciones requeridas.
        Como lo hace:
            1. Ajusta un modelo con init='k-means++' y mide inercia y numero de iteraciones (n_iter_).
            2. Ajusta un modelo con init='random' bajo la misma semilla y datos.
            3. Compara inercia y Coeficiente de Silueta entre ambas aproximaciones.
        Conexiones:
            Recibe la matriz X estandarizada por StandardScaler.
        """
        km_plus = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=self.semilla)
        etiquetas_plus = km_plus.fit_predict(X_escalado)

        km_random = KMeans(n_clusters=k, init="random", n_init=10, random_state=self.semilla)
        etiquetas_random = km_random.fit_predict(X_escalado)

        return {
            "k_evaluado": k,
            "kmeans_plus_plus": {
                "inercia": round(float(km_plus.inertia_), 2),
                "iteraciones_convergencia": int(km_plus.n_iter_),
                "coeficiente_silueta": round(float(silhouette_score(X_escalado, etiquetas_plus)), 4),
            },
            "kmeans_random": {
                "inercia": round(float(km_random.inertia_), 2),
                "iteraciones_convergencia": int(km_random.n_iter_),
                "coeficiente_silueta": round(float(silhouette_score(X_escalado, etiquetas_random)), 4),
            },
            "conclusion": (
                "k-means++ proporciona una convergencia mas estable al dispersar los centroides iniciales."
                if km_plus.inertia_ <= km_random.inertia_
                else "Ambas inicializaciones alcanzaron valores comparables de inercia."
            ),
        }

    def comparar_escaladores(self, X_crudo: np.ndarray, k: int = 3) -> dict[str, Any]:
        """Compara el efecto de StandardScaler frente a MinMaxScaler en la segmentacion.
        
        Que hace:
            Evalua si la distribucion normalizada (Z-score) o el rango acotado [0, 1] genera
            clusters mas compactos y mejor diferenciados para el problema de movilidad urbana.
        Como lo hace:
            Aplica respectivamente StandardScaler y MinMaxScaler, entrena K-Means sobre cada matriz
            y calcula el Coeficiente de Silueta resultante.
        Conexiones:
            Recibe la matriz cruda de caracteristicas de movilidad de COLUMNAS_CLUSTERING.
        """
        std_scaler = StandardScaler()
        X_std = std_scaler.fit_transform(X_crudo)

        minmax_scaler = MinMaxScaler()
        X_minmax = minmax_scaler.fit_transform(X_crudo)

        km_std = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=self.semilla)
        etiquetas_std = km_std.fit_predict(X_std)

        km_minmax = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=self.semilla)
        etiquetas_minmax = km_minmax.fit_predict(X_minmax)

        sil_std = float(silhouette_score(X_std, etiquetas_std))
        sil_minmax = float(silhouette_score(X_minmax, etiquetas_minmax))

        return {
            "standard_scaler": {
                "coeficiente_silueta": round(sil_std, 4),
                "inercia": round(float(km_std.inertia_), 2),
                "descripcion": "Centra en media 0 y escala a varianza 1 (adecuado con presencia de colas moderadas).",
            },
            "minmax_scaler": {
                "coeficiente_silueta": round(sil_minmax, 4),
                "inercia": round(float(km_minmax.inertia_), 2),
                "descripcion": "Acota los valores estrictamente al intervalo cerrado [0, 1].",
            },
            "escalador_recomendado": "StandardScaler" if sil_std >= sil_minmax else "MinMaxScaler",
        }

    def evaluar_estabilidad_ari(self, X_escalado: np.ndarray, k: int = 3) -> dict[str, Any]:
        """Mide la estabilidad de las agrupaciones frente a diferentes semillas con ARI.
        
        Que hace:
            Calcula el Indice de Rand Ajustado (Adjusted Rand Index) comparando los clusters
            obtenidos con la semilla base contra los clusters generados con otras semillas aleatorias.
        Como lo hace:
            1. Un ARI cercano a 1.0 indica que los clusters son casi identicos independientemente de la semilla.
            2. Un ARI cercano a 0 indica que la asignacion es equivalente al azar.
            3. Ejecuta K-Means con semillas [42, 100, 2026, 777] y calcula el ARI cruzado.
        Conexiones:
            Recibe la matriz X estandarizada y entrega el indice de robustez para el reporte.
        """
        semillas = [42, 100, 2026, 777]
        particiones = []

        for s in semillas:
            km = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=s)
            etiquetas = km.fit_predict(X_escalado)
            particiones.append(etiquetas)

        # Comparar la semilla base (indice 0: 42) contra las demas
        comparaciones = []
        base = particiones[0]
        for idx in range(1, len(semillas)):
            ari = float(adjusted_rand_score(base, particiones[idx]))
            comparaciones.append({
                "semilla_base": semillas[0],
                "semilla_comparada": semillas[idx],
                "adjusted_rand_index": round(ari, 4),
            })

        promedio_ari = float(np.mean([c["adjusted_rand_index"] for c in comparaciones]))

        return {
            "k_utilizado": k,
            "comparaciones_semillas": comparaciones,
            "promedio_ari": round(promedio_ari, 4),
            "diagnostico_estabilidad": (
                "Alta estabilidad: Los perfiles descubiertos son robustos y reproducibles."
                if promedio_ari > 0.75
                else "Estabilidad moderada: Algunos viajes perifericos cambian de grupo segun la semilla."
            ),
        }

    def detectar_viajes_anomalos(
        self, df: pd.DataFrame, X_escalado: np.ndarray, modelo_kmeans: KMeans, percentil: float = 95.0
    ) -> tuple[pd.DataFrame, list[dict[str, Any]], float]:
        """Identifica viajes que se encuentran a una distancia inusualmente lejana de su centroide.
        
        Que hace:
            Aplica deteccion de anomalias no supervisada basada en distancia euclidiana al centroide.
        Como lo hace:
            1. Para cada punto de X_escalado, calcula la distancia euclidiana hacia el centroide de su cluster.
            2. Calcula el umbral estadistico en el percentil indicado (por defecto 95%).
            3. Todo viaje cuya distancia al centroide supere el percentil 95 se marca como anomalo / caso atipico.
        Conexiones:
            Permite a los administradores de Kompas auditar viajes fraudulentos, errores de GPS
            o traslados con tarifas incoherentes.
        """
        etiquetas = modelo_kmeans.labels_
        centroides = modelo_kmeans.cluster_centers_

        distancias = np.zeros(len(X_escalado))
        for i in range(len(X_escalado)):
            c_idx = etiquetas[i]
            distancias[i] = euclidean_distances([X_escalado[i]], [centroides[c_idx]])[0][0]

        umbral = float(np.percentile(distancias, percentil))
        mascara_anomala = distancias > umbral

        df_anomalos = df.loc[mascara_anomala].copy()
        df_anomalos["cluster_asignado"] = etiquetas[mascara_anomala]
        df_anomalos["distancia_centroide"] = distancias[mascara_anomala].round(3)

        lista_anomalias = []
        for _, fila in df_anomalos.iterrows():
            lista_anomalias.append({
                "origen": str(fila["parada_origen"]),
                "destino": str(fila["parada_destino"]),
                "distancia_km": float(fila["distancia_km"]),
                "hora_dia": int(fila["hora_dia"]),
                "duracion_min": int(fila["duracion_min"]),
                "presupuesto_mxn": float(fila["presupuesto_mxn"]),
                "cluster_asignado": int(fila["cluster_asignado"]),
                "distancia_centroide": float(fila["distancia_centroide"]),
                "motivo_anomalia": "Distancia euclidiana al centroide supera el umbral del percentil 95.",
            })

        return df_anomalos, lista_anomalias, umbral

    def persistir_perfiles_en_mongodb(self, perfiles: list[dict[str, Any]], k: int) -> dict[str, Any]:
        """Almacena los perfiles descubiertos en la coleccion perfiles_viajeros de MongoDB.
        
        Que hace:
            Guarda de forma persistente los segmentos calculados para consulta rapida desde la app y panel.
        Como lo hace:
            1. Invoca get_bd() desde app.nucleo.bd para obtener la conexion activa a MongoDB.
            2. Construye un documento que incluye marca temporal UTC, metadata de K y los perfiles.
            3. Inserta el documento en la coleccion 'perfiles_viajeros' reemplazando o agregando el registro actual.
        Conexiones:
            Se conecta con app.nucleo.bd.get_bd() (la conexion central a MongoDB de Kompas).
        """
        try:
            bd = get_bd()
            doc_perfiles = {
                "tipo": "segmentacion_k_means",
                "k_clusters": k,
                "fecha_actualizacion": datetime.now(timezone.utc).isoformat(),
                "total_perfiles": len(perfiles),
                "perfiles": perfiles,
            }

            resultado = bd.perfiles_viajeros.insert_one(doc_perfiles)
            return {
                "guardado_exitoso": True,
                "coleccion": "perfiles_viajeros",
                "id_documento_mongo": str(resultado.inserted_id),
                "mensaje": "Los perfiles de movilidad fueron almacenados correctamente en MongoDB.",
            }
        except Exception as error_bd:
            return {
                "guardado_exitoso": False,
                "coleccion": "perfiles_viajeros",
                "id_documento_mongo": None,
                "mensaje": f"No se pudo guardar en MongoDB: {error_bd}",
            }

    def ejecutar_auditoria_completa(self) -> dict[str, Any]:
        """Ejecuta la auditoria integral: inicializaciones, escaladores, ARI, atipicos y guardado.
        
        Que hace:
            Orquesta todas las comprobaciones avanzadas de la Practica 08.
        Como lo hace:
            1. Carga los datos limpios y extrae la matriz numerica.
            2. Escala con StandardScaler y MinMaxScaler para contrastar.
            3. Compara k-means++ frente a random.
            4. Mide el Adjusted Rand Index en 4 corridas.
            5. Detecta viajes atipicos en el percentil 95.
            6. Obtiene los perfiles interpretados y los persiste en MongoDB.
        Conexiones:
            Alimenta router.py en los endpoints GET /api/ia/auditoria-clusters y
            POST /api/ia/persistir-segmentos.
        """
        df_limpio = pd.read_csv(self.ruta_csv_limpio)
        X_crudo = df_limpio[COLUMNAS_CLUSTERING].copy().values

        std_scaler = StandardScaler()
        X_std = std_scaler.fit_transform(X_crudo)

        k_optimo = 3
        comp_init = self.comparar_inicializaciones(X_std, k=k_optimo)
        comp_scaler = self.comparar_escaladores(X_crudo, k=k_optimo)
        estabilidad = self.evaluar_estabilidad_ari(X_std, k=k_optimo)

        # Entrenar modelo final
        km_final = KMeans(n_clusters=k_optimo, init="k-means++", n_init=15, random_state=self.semilla)
        km_final.fit(X_std)

        # Deteccion de casos anomalos
        _, lista_anomalias, umbral_dist = self.detectar_viajes_anomalos(
            df_limpio, X_std, km_final, percentil=95.0
        )

        # Obtener perfiles desestandarizados
        centroides_orig = std_scaler.inverse_transform(km_final.cluster_centers_)
        perfiles = self.segmentador.interpretar_perfiles(df_limpio, km_final.labels_, centroides_orig)

        # Persistencia en base de datos
        res_mongo = self.persistir_perfiles_en_mongodb(perfiles, k=k_optimo)

        return {
            "total_registros_auditados": len(df_limpio),
            "k_clusters": k_optimo,
            "comparacion_inicializaciones": comp_init,
            "comparacion_escaladores": comp_scaler,
            "estabilidad_ajuste_ari": estabilidad,
            "auditoria_anomalias": {
                "umbral_distancia_p95": round(umbral_dist, 3),
                "total_viajes_anomalos_detectados": len(lista_anomalias),
                "ejemplos_anomalias": lista_anomalias[:5],
            },
            "persistencia_mongodb": res_mongo,
        }

