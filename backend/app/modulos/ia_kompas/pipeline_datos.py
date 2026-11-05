"""Pipeline de datos: ingesta, análisis exploratorio, auditoría de calidad y depuración.

Implementa la preparación secuencial de datos de traslados urbanos en el Valle de Toluca
siguiendo las 5 etapas metodológicas (A: análisis, B: EDA, C: calidad, D: limpieza dual, E: variables X e y).
(Trazabilidad académica: adaptado de las prácticas p02 a-e).
"""

from pathlib import Path
import numpy as np
import pandas as pd

DIRECTORIO_DATA = Path(__file__).resolve().parent.parent.parent.parent / "data"
RUTA_CRUDO_DEFECTO = DIRECTORIO_DATA / "kompas_traslados_crudo.csv"
RUTA_LIMPIO_DEFECTO = DIRECTORIO_DATA / "kompas_traslados_limpio.csv"
RUTA_REVISION_DEFECTO = DIRECTORIO_DATA / "kompas_traslados_revision.csv"

COLUMNAS_CARACTERISTICAS = [
    "distancia_km",
    "hora_dia",
    "es_hora_pico",
    "presupuesto_mxn",
    "clima_lluvia",
    "rating_destino",
]
COLUMNA_OBJETIVO = "modo_transporte_optimo"


def generar_dataset_crudo_kompas(ruta_csv: Path | str = RUTA_CRUDO_DEFECTO, semilla: int = 42) -> pd.DataFrame:
    """Genera un dataset sintético/histórico realista de traslados en el Valle de Toluca

    con ~160 registros que incluye deliberadamente nulos, duplicados y outliers
    para demostrar las capacidades de auditoría y limpieza de datos (etapas C y D).
    """
    ruta = Path(ruta_csv)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(semilla)
    n = 160

    lugares_origen = [
        "Cosmovitral", "Los Portales", "Terminal Toluca", "Alameda Central Toluca",
        "Estadio Nemesio Diez", "Centro Metepec", "Galerias Metepec", "Plazas Outlet Lerma"
    ]
    lugares_destino = [
        "Centro Metepec", "Galerias Metepec", "Cosmovitral", "Parque Bicentenario",
        "Los Portales", "San Mateo Atenco", "Lerma Centro", "Terminal Toluca"
    ]

    distancias = rng.gamma(shape=2.5, scale=1.8, size=n).round(2)
    distancias = np.clip(distancias, 0.4, 18.0)

    horas = rng.integers(6, 23, size=n)
    horas_pico_set = {7, 8, 9, 18, 19, 20}
    es_hora_pico = np.array([1 if h in horas_pico_set else 0 for h in horas])

    clima_lluvia = rng.choice([0, 1], size=n, p=[0.75, 0.25])
    presupuestos = rng.choice([15.0, 20.0, 35.0, 50.0, 80.0, 120.0, 160.0, 220.0], size=n)
    ratings = rng.uniform(3.8, 4.9, size=n).round(1)

    modos = []
    duraciones = []
    for d, h_pico, lluvia, pto in zip(distancias, es_hora_pico, clima_lluvia, presupuestos):
        if d <= 1.5 and lluvia == 0:
            modos.append("caminando")
            duraciones.append(int(round(d * 12.0)))
        elif lluvia == 1 or (h_pico == 1 and pto >= 100.0) or d > 8.0:
            modos.append("auto_privado")
            duraciones.append(int(round(10.0 + d * 2.5 + (10 if h_pico else 0))))
        else:
            modos.append("transporte_publico")
            duraciones.append(int(round(12.0 + d * 3.8 + (12 if h_pico else 0))))

    df = pd.DataFrame({
        "parada_origen": rng.choice(lugares_origen, size=n),
        "parada_destino": rng.choice(lugares_destino, size=n),
        "distancia_km": distancias,
        "hora_dia": horas,
        "es_hora_pico": es_hora_pico,
        "presupuesto_mxn": presupuestos,
        "clima_lluvia": clima_lluvia,
        "rating_destino": ratings,
        "duracion_min": duraciones,
        "modo_transporte_optimo": modos,
    })

    # Inyección intencional de problemas de calidad para auditar en etapa C:
    # 1. ~10% de valores nulos en rating_destino y presupuesto_mxn
    indices_nulos_rating = rng.choice(n, size=15, replace=False)
    df.loc[indices_nulos_rating, "rating_destino"] = np.nan

    indices_nulos_pto = rng.choice(n, size=12, replace=False)
    df.loc[indices_nulos_pto, "presupuesto_mxn"] = np.nan

    # 3 outliers (valores fuera de rango): distancia negativa, rating > 5.0 y duración aberrante
    df.loc[0, "distancia_km"] = -2.5
    df.loc[1, "rating_destino"] = 8.5
    df.loc[2, "duracion_min"] = 999

    # 5 filas duplicadas (copiadas de filas que no son outliers)
    duplicados = df.iloc[10:15].copy()
    df = pd.concat([df, duplicados], ignore_index=True)

    df.to_csv(ruta, index=False, encoding="utf-8")
    return df


# ----------------------------------------------------------------------
# Etapa A: Análisis Inicial
# ----------------------------------------------------------------------
def etapa_a_analisis_inicial(df: pd.DataFrame) -> dict:
    """Carga y genera resumen de dimensiones y estructura tabular."""
    return {
        "filas": int(df.shape[0]),
        "columnas": int(df.shape[1]),
        "lista_columnas": list(df.columns),
        "primeras_filas": df.head(3).to_dict(orient="records"),
    }


# ----------------------------------------------------------------------
# Etapa B: Exploración de Datos de IA (EDA)
# ----------------------------------------------------------------------
def etapa_b_exploracion_ia(df: pd.DataFrame) -> dict:
    """Calcula estadísticas descriptivas y distribuciones por modo de transporte."""
    conteo_modos = df[COLUMNA_OBJETIVO].value_counts().to_dict()
    resumen_numerico = df.describe().to_dict()
    promedios_por_modo = (
        df.groupby(COLUMNA_OBJETIVO)[["distancia_km", "duracion_min"]]
        .mean()
        .round(2)
        .to_dict(orient="index")
    )
    return {
        "distribucion_modos": conteo_modos,
        "promedios_por_modo": promedios_por_modo,
        "resumen_numerico": resumen_numerico,
    }


# ----------------------------------------------------------------------
# Etapa C: Auditoría de Calidad de Datos
# ----------------------------------------------------------------------
def etapa_c_auditoria_calidad(df: pd.DataFrame) -> dict:
    """Detecta valores nulos, tuplas duplicadas y valores fuera de rango físico/lógico."""
    nulos_por_columna = df.isnull().sum().to_dict()
    filas_con_nulos = int(df.isnull().any(axis=1).sum())
    filas_duplicadas = int(df.duplicated().sum())

    distancias_invalidas = int((df["distancia_km"] <= 0).sum())
    ratings_invalidos = int(((df["rating_destino"] < 1.0) | (df["rating_destino"] > 5.0)).sum())
    duraciones_invalidas = int(((df["duracion_min"] <= 0) | (df["duracion_min"] > 300)).sum())

    return {
        "nulos_por_columna": {k: int(v) for k, v in nulos_por_columna.items() if v > 0},
        "filas_con_al_menos_un_nulo": filas_con_nulos,
        "filas_completamente_duplicadas": filas_duplicadas,
        "outliers_detectados": {
            "distancia_menor_o_igual_a_cero": distancias_invalidas,
            "rating_fuera_de_rango_1_a_5": ratings_invalidos,
            "duracion_excesiva_mayor_300_min": duraciones_invalidas,
        },
    }


# ----------------------------------------------------------------------
# Etapa D: Limpieza y Guardado (Estrategia Dual Válidos / Revisión)
# ----------------------------------------------------------------------
def etapa_d_limpieza_y_guardado(
    df: pd.DataFrame,
    ruta_salida: Path | str = RUTA_LIMPIO_DEFECTO,
    ruta_revision: Path | str = RUTA_REVISION_DEFECTO,
) -> pd.DataFrame:
    """Aplica la estrategia de limpieza y separación formal:

    PASO 1. Eliminar filas completamente duplicadas (drop_duplicates).
    PASO 2. Identificar registros válidos mediante filtros booleanos y between().
    PASO 3. Separar los registros válidos (df_validos) de los registros que requieren
            revisión o auditoría (df_revision).
    PASO 4. Imputar valores faltantes en válidos y exportar ambos archivos CSV.
    """
    # PASO 1. Eliminar filas completamente duplicadas
    df_limpio = df.drop_duplicates().copy()

    # PASO 2. Identificar registros válidos (condiciones de dominio de Kompás)
    distancia_valida = df_limpio["distancia_km"] > 0
    duracion_valida = df_limpio["duracion_min"].between(1, 300)
    rating_en_rango = df_limpio["rating_destino"].isna() | df_limpio["rating_destino"].between(1.0, 5.0)
    presupuesto_en_rango = df_limpio["presupuesto_mxn"].isna() | (df_limpio["presupuesto_mxn"] >= 0)

    valido = (
        distancia_valida
        & duracion_valida
        & rating_en_rango
        & presupuesto_en_rango
    )

    # PASO 3. Separar los registros válidos de los que requieren revisión
    df_validos = df_limpio.loc[valido].copy()
    df_revision = df_limpio.loc[~valido].copy()

    # Imputación de nulos en registros válidos mediante la mediana
    mediana_rating = float(df_validos["rating_destino"].median())
    if np.isnan(mediana_rating):
        mediana_rating = 4.5
    df_validos["rating_destino"] = df_validos["rating_destino"].fillna(mediana_rating)

    mediana_pto = float(df_validos["presupuesto_mxn"].median())
    if np.isnan(mediana_pto):
        mediana_pto = 50.0
    df_validos["presupuesto_mxn"] = df_validos["presupuesto_mxn"].fillna(mediana_pto)

    # PASO 4. Exportar los resultados en archivos independientes
    p_salida = Path(ruta_salida)
    p_salida.parent.mkdir(parents=True, exist_ok=True)
    df_validos.to_csv(p_salida, index=False, encoding="utf-8")

    p_rev = Path(ruta_revision)
    p_rev.parent.mkdir(parents=True, exist_ok=True)
    df_revision.to_csv(p_rev, index=False, encoding="utf-8")

    return df_validos


# ----------------------------------------------------------------------
# Etapa E: Identificación de Variables X e y
# ----------------------------------------------------------------------
def etapa_e_identificacion_variables(
    df_limpio: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series, dict]:
    """Separa formalmente la matriz de características X y el vector objetivo y."""
    X = df_limpio[COLUMNAS_CARACTERISTICAS].copy()
    y = df_limpio[COLUMNA_OBJETIVO].copy()

    assert len(X) == len(y), "La longitud de X e y no coincide"

    metadatos = {
        "n_muestras": len(X),
        "variables_predictoras_X": COLUMNAS_CARACTERISTICAS,
        "variable_objetivo_y": COLUMNA_OBJETIVO,
        "clases_objetivo": sorted(list(y.unique())),
    }
    return X, y, metadatos


def ejecutar_pipeline_completo(
    ruta_crudo: Path | str = RUTA_CRUDO_DEFECTO,
    ruta_limpio: Path | str = RUTA_LIMPIO_DEFECTO,
    ruta_revision: Path | str = RUTA_REVISION_DEFECTO,
) -> dict:
    """Ejecuta secuencialmente las etapas A a E y retorna el informe integral de auditoría."""
    p_crudo = Path(ruta_crudo)
    if not p_crudo.exists():
        generar_dataset_crudo_kompas(p_crudo)

    df_crudo = pd.read_csv(p_crudo)
    res_a = etapa_a_analisis_inicial(df_crudo)
    res_b = etapa_b_exploracion_ia(df_crudo)
    res_c = etapa_c_auditoria_calidad(df_crudo)

    df_limpio = etapa_d_limpieza_y_guardado(df_crudo, ruta_salida=ruta_limpio, ruta_revision=ruta_revision)
    X, y, res_e = etapa_e_identificacion_variables(df_limpio)

    return {
        "etapa_a": res_a,
        "etapa_b": res_b,
        "etapa_c": res_c,
        "etapa_d": {
            "filas_limpias": len(df_limpio),
            "ruta_guardado_limpio": str(ruta_limpio),
            "ruta_guardado_revision": str(ruta_revision),
        },
        "etapa_e": res_e,
    }

