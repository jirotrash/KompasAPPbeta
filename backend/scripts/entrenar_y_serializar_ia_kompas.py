"""Script de Entrenamiento y Serializacion Formal de Modelos de IA en Kompas (P10 a P13).

Este script replica el flujo de las Practicas 10, 11, 12 y 13:
1. P10: Lectura y validacion del dataset limpio de movilidad (kompas_traslados_limpio.csv).
2. P11: Entrenamiento del clasificador supervisado Random Forest y exportacion a .joblib.
3. P12: Ajuste de K-Means (4 clusters), calculo de centroides y exportacion con su StandardScaler a .joblib.
4. P13: Reduccion de dimensionalidad con PCA (2 componentes) y exportacion a .joblib.
5. Generacion de metadatos de versionado en formato JSON.
"""

from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from app.modulos.ia_kompas.p07_segmentacion_viajeros import COLUMNAS_CLUSTERING
from app.modulos.ia_kompas.pipeline_datos import RUTA_LIMPIO_DEFECTO

# Directorio donde se guardaran los modelos serializados
RUTA_DATA = Path(__file__).resolve().parents[1] / "data"
RUTA_MODELOS = RUTA_DATA / "modelos"
RUTA_MODELOS.mkdir(parents=True, exist_ok=True)

ARCHIVO_RF = RUTA_MODELOS / "modelo_random_forest_kompas.joblib"
ARCHIVO_KMEANS = RUTA_MODELOS / "modelo_kmeans_kompas.joblib"
ARCHIVO_PCA = RUTA_MODELOS / "modelo_pca_kompas.joblib"
ARCHIVO_METADATOS = RUTA_MODELOS / "metadatos_modelos.json"


def entrenar_y_serializar_todo(ruta_csv: Path = RUTA_LIMPIO_DEFECTO, semilla: int = 42) -> dict:
    print(f"Iniciando entrenamiento y serializacion desde: {ruta_csv}")
    df = pd.read_csv(ruta_csv)

    # 1. Modelo Supervisado (Random Forest) - Practica 11
    cols_features = ["distancia_km", "hora_dia", "presupuesto_mxn", "es_hora_pico", "clima_lluvia"]
    features_existentes = [c for c in cols_features if c in df.columns]
    target = "medio_transporte" if "medio_transporte" in df.columns else df.columns[-1]

    X_rf = df[features_existentes].values
    y_rf = df[target].values

    rf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=semilla)
    rf.fit(X_rf, y_rf)

    joblib.dump({
        "modelo": rf,
        "caracteristicas": features_existentes,
        "clases": list(rf.classes_),
        "algoritmo": "RandomForestClassifier",
    }, ARCHIVO_RF)
    print(f"Modelo Supervisado guardado en: {ARCHIVO_RF}")

    # 2. Modelo No Supervisado (K-Means) - Practica 12
    escalador_k = StandardScaler()
    X_k_esc = escalador_k.fit_transform(df[COLUMNAS_CLUSTERING].values)

    kmeans = KMeans(n_clusters=4, init="k-means++", n_init=10, random_state=semilla)
    kmeans.fit(X_k_esc)

    joblib.dump({
        "modelo": kmeans,
        "escalador": escalador_k,
        "columnas": COLUMNAS_CLUSTERING,
        "centroides": kmeans.cluster_centers_.tolist(),
        "inercia": float(kmeans.inertia_),
    }, ARCHIVO_KMEANS)
    print(f"Modelo K-Means guardado en: {ARCHIVO_KMEANS}")

    # 3. Reduccion de Dimensionalidad (PCA) - Practica 13
    escalador_pca = StandardScaler()
    X_pca_esc = escalador_pca.fit_transform(df[COLUMNAS_CLUSTERING].values)

    pca = PCA(n_components=2, random_state=semilla)
    pca.fit(X_pca_esc)

    joblib.dump({
        "modelo_pca": pca,
        "escalador": escalador_pca,
        "varianza_explicada_ratio": pca.explained_variance_ratio_.tolist(),
        "varianza_acumulada_pct": float(np.sum(pca.explained_variance_ratio_) * 100),
    }, ARCHIVO_PCA)
    print(f"Modelo PCA guardado en: {ARCHIVO_PCA}")

    # 4. Metadatos
    meta = {
        "version": "2.0.0",
        "fecha_creacion": pd.Timestamp.now().isoformat(),
        "total_registros_entrenamiento": len(df),
        "archivos": {
            "random_forest": ARCHIVO_RF.name,
            "kmeans": ARCHIVO_KMEANS.name,
            "pca": ARCHIVO_PCA.name,
        },
        "varianza_pca_pct": round(float(np.sum(pca.explained_variance_ratio_) * 100), 2),
    }

    with open(ARCHIVO_METADATOS, "w", encoding="utf-8") as fp:
        json.dump(meta, fp, indent=2)

    print(f"Metadatos guardados en: {ARCHIVO_METADATOS}")
    return meta


if __name__ == "__main__":
    entrenar_y_serializar_todo()
