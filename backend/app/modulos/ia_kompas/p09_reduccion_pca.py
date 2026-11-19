"""Modulo de Reduccion de Dimensionalidad mediante PCA (Practica 09).

Este modulo implementa el Analisis de Componentes Principales (PCA) para reducir
el espacio multivariado de movilidad urbana (distancia, hora, duracion, presupuesto, etc.)
a 2 componentes principales ortogonales (PC1 y PC2).

Permite visualizar la distribucion espacial de los viajes, proyectar los clusters
descubiertos con K-Means y cuantificar el porcentaje de varianza explicada.
"""

from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from app.modulos.ia_kompas.p07_segmentacion_viajeros import COLUMNAS_CLUSTERING
from app.modulos.ia_kompas.pipeline_datos import RUTA_LIMPIO_DEFECTO, ejecutar_pipeline_completo


class ReductorDimensionalidadPCA:
    """Clase para proyectar datos multivariados de movilidad a planos bidimensionales."""

    def __init__(self, ruta_csv_limpio: Path | str = RUTA_LIMPIO_DEFECTO, semilla: int = 42):
        """Inicializa el reductor con la ruta de datos y semilla.
        
        Que hace:
            Establece la ruta a los datos limpios y fija la semilla para la reproducibilidad de PCA.
        Como lo hace:
            Guarda la ruta al archivo CSV limpio y crea los objetos StandardScaler y PCA con 2 componentes.
        Conexiones:
            Consume RUTA_LIMPIO_DEFECTO de pipeline_datos.py.
        """
        self.ruta_csv_limpio = Path(ruta_csv_limpio)
        self.semilla = semilla
        self.escalador = StandardScaler()
        self.pca = PCA(n_components=2, random_state=self.semilla)

    def ejecutar_pca_con_clusters(self, k: int = 3) -> dict[str, Any]:
        """Calcula los dos componentes principales y proyecta las observaciones y clusters.
        
        Que hace:
            Proyecta las dimensiones de COLUMNAS_CLUSTERING a dos ejes ortogonales (PC1 y PC2)
            y asocia a cada punto su etiqueta de cluster de K-Means.
        Como lo hace:
            1. Carga los datos limpios y extrae la matriz de caracteristicas cuantitativas.
            2. Aplica estandarizacion obligatoria con StandardScaler (media 0, varianza 1).
            3. Ajusta PCA(n_components=2) calculando:
               - Varianza explicada individual de PC1 y PC2.
               - Varianza explicada acumulada.
            4. Ajusta KMeans(n_clusters=k) sobre la matriz estandarizada para obtener las etiquetas.
            5. Transforma los centroides multidimensionales al espacio 2D de PCA.
            6. Estructura una lista de puntos con coordenadas (pc1, pc2), cluster y datos del viaje.
        Conexiones:
            Alimenta router.py bajo el endpoint GET /api/ia/proyeccion-pca.
        """
        if not self.ruta_csv_limpio.exists():
            ejecutar_pipeline_completo()

        df_limpio = pd.read_csv(self.ruta_csv_limpio)
        X_crudo = df_limpio[COLUMNAS_CLUSTERING].copy().values

        X_std = self.escalador.fit_transform(X_crudo)

        # Ajuste de PCA para 2 componentes
        coordenadas_2d = self.pca.fit_transform(X_std)
        varianzas_individuales = [round(float(v), 4) for v in self.pca.explained_variance_ratio_]
        varianza_acumulada = round(float(np.sum(varianzas_individuales)), 4)

        # Ajuste de KMeans para colorear los puntos segun su cluster
        km = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=self.semilla)
        etiquetas = km.fit_predict(X_std)

        # Proyeccion de los centroides al plano PCA 2D
        centroides_2d = self.pca.transform(km.cluster_centers_)

        puntos_proyectados = []
        for i in range(len(coordenadas_2d)):
            puntos_proyectados.append({
                "pc1": round(float(coordenadas_2d[i, 0]), 3),
                "pc2": round(float(coordenadas_2d[i, 1]), 3),
                "cluster": int(etiquetas[i]),
                "origen": str(df_limpio.iloc[i]["parada_origen"]),
                "destino": str(df_limpio.iloc[i]["parada_destino"]),
                "modo": str(df_limpio.iloc[i]["modo_transporte_optimo"]),
                "distancia_km": float(df_limpio.iloc[i]["distancia_km"]),
            })

        lista_centroides_2d = []
        for c_id in range(k):
            lista_centroides_2d.append({
                "cluster_id": c_id,
                "pc1": round(float(centroides_2d[c_id, 0]), 3),
                "pc2": round(float(centroides_2d[c_id, 1]), 3),
            })

        return {
            "total_observaciones": len(puntos_proyectados),
            "componentes_principales": 2,
            "varianza_explicada_pc1": varianzas_individuales[0],
            "varianza_explicada_pc2": varianzas_individuales[1],
            "varianza_explicada_acumulada": varianza_acumulada,
            "centroides_en_pca": lista_centroides_2d,
            "muestra_puntos_2d": puntos_proyectados[:20],
        }

