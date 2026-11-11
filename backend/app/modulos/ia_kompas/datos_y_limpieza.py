"""Generación y limpieza de datos de planes y traslados turísticos de Kompás (Práctica 02).

Genera un conjunto reproducible (`seed=42`) de 500 registros limpios del dominio de Kompás:
- `distancia_km` [0.5 - 25.0]
- `presupuesto_mxn` [20.0 - 500.0]
- `rating_lugar` [3.0 - 5.0]
- `num_paradas` [1 - 8]
- `trafico_nivel` [1 - 10]
- `plan_viable` [0 o 1] (variable objetivo binaria de viabilidad del plan/traslado)
- `modo_optimo` ('caminando', 'transporte_publico', 'auto_privado')

Introduce ~5% de valores nulos y duplicados controlados y ejecuta el pipeline de limpieza
(eliminación de duplicados, validación de rangos e imputación por mediana), devolviendo
las estadísticas comparativas del antes y después (`resumen_limpieza`).
"""

from pathlib import Path
import numpy as np
import pandas as pd

from app.modulos.ia_kompas.pipeline_datos import DIRECTORIO_DATA

RUTA_PLANES_CRUDO = DIRECTORIO_DATA / "kompas_planes_500_crudo.csv"
RUTA_PLANES_LIMPIO = DIRECTORIO_DATA / "kompas_planes_500_limpio.csv"

CARACTERISTICAS_PLAN_KOMPAS: list[str] = [
    "distancia_km",
    "presupuesto_mxn",
    "rating_lugar",
    "num_paradas",
    "trafico_nivel",
]
OBJETIVO_VIABILIDAD = "plan_viable"

ZONAS_TURISTICAS_KOMPAS: list[str] = [
    "Terminal Toluca",
    "Cosmovitral",
    "Los Portales",
    "Alameda Central Toluca",
    "Estadio Nemesio Diez",
    "Parque Metropolitano Bicentenario",
    "Centro Metepec",
    "Galerias Metepec",
    "Parque Ambiental Bicentenario",
    "San Mateo Atenco",
    "Lerma Centro",
    "Plazas Outlet Lerma",
]


def _evaluar_viabilidad_real_kompas(
    distancia_km: float,
    presupuesto_mxn: float,
    rating_lugar: float,
    num_paradas: int,
    trafico_nivel: int,
    rng: np.random.Generator,
) -> tuple[int, str]:
    """Determina la viabilidad real (`plan_viable` 0 o 1) y el modo de transporte sugerido.

    Considera la interacción no lineal entre presupuesto por parada, distancia acumulada,
    congestión vial en Toluca/Metepec y calidad del atractivo turístico.
    """
    costo_base_paradas = num_paradas * 38.0
    sobrecosto_trafico = (trafico_nivel >= 7) * 45.0
    costo_distancia = distancia_km * (5.5 if trafico_nivel >= 6 else 3.2)
    presupuesto_requerido = costo_base_paradas + sobrecosto_trafico + costo_distancia

    holgura_presupuesto = presupuesto_mxn - presupuesto_requerido

    # Viabilidad multicriterio del plan en el dominio de Kompás
    if (
        holgura_presupuesto >= -15.0
        and rating_lugar >= 3.5
        and not (distancia_km > 18.0 and trafico_nivel >= 8 and num_paradas >= 6)
        and not (presupuesto_mxn < 95.0 and num_paradas >= 4)
    ):
        viable = 1
    elif holgura_presupuesto >= 40.0 and rating_lugar >= 3.2 and trafico_nivel <= 8:
        viable = 1
    else:
        viable = 0

    # Variación controlada en casos límite (~6%) para modelar la incertidumbre real y hacer
    # evidente el sobreajuste (overfitting) cuando max_depth >= 12 memoriza ruido
    en_borde = abs(holgura_presupuesto) <= 32.0 or (3.35 <= rating_lugar <= 3.65)
    if en_borde and rng.random() < 0.16:
        viable = 1 - viable

    # Modo de transporte asociado
    if distancia_km <= 3.2 and num_paradas <= 3 and trafico_nivel <= 7:
        modo = "caminando"
    elif presupuesto_mxn >= 220.0 and (trafico_nivel >= 6 or distancia_km > 10.0 or num_paradas >= 5):
        modo = "auto_privado"
    else:
        modo = "transporte_publico"

    return int(viable), modo


def generar_y_limpiar_datos_kompas(
    n_registros: int = 500,
    semilla: int = 42,
    ruta_crudo: Path | str = RUTA_PLANES_CRUDO,
    ruta_limpio: Path | str = RUTA_PLANES_LIMPIO,
) -> tuple[pd.DataFrame, dict]:
    """Genera el dataset reproducible de 500 registros de Kompás, inyecta ~5% de nulos y duplicados,
    y aplica el pipeline de limpieza (Práctica 02).

    Returns:
        `(df_limpio, resumen_limpieza)` con conteos detallados antes y después.
    """
    rng = np.random.default_rng(semilla)

    distancia_km = np.round(rng.uniform(0.5, 25.0, size=n_registros), 2)
    presupuesto_mxn = np.round(rng.uniform(20.0, 500.0, size=n_registros), 2)
    rating_lugar = np.round(rng.uniform(3.0, 5.0, size=n_registros), 1)
    num_paradas = rng.integers(1, 9, size=n_registros)
    trafico_nivel = rng.integers(1, 11, size=n_registros)

    origenes = rng.choice(ZONAS_TURISTICAS_KOMPAS, size=n_registros)
    destinos = rng.choice(ZONAS_TURISTICAS_KOMPAS, size=n_registros)

    viables = []
    modos = []
    for d, p, r, np_it, t in zip(distancia_km, presupuesto_mxn, rating_lugar, num_paradas, trafico_nivel):
        v, m = _evaluar_viabilidad_real_kompas(float(d), float(p), float(r), int(np_it), int(t), rng)
        viables.append(v)
        modos.append(m)

    df_base = pd.DataFrame({
        "parada_origen": origenes,
        "parada_destino": destinos,
        "distancia_km": distancia_km,
        "presupuesto_mxn": presupuesto_mxn,
        "rating_lugar": rating_lugar,
        "num_paradas": num_paradas,
        "trafico_nivel": trafico_nivel,
        "modo_optimo": modos,
        "plan_viable": viables,
    })

    # Inyección controlada del 5% de valores nulos (25 celdas en rating_lugar y presupuesto_mxn)
    n_nulos_rating = int(round(n_registros * 0.03))  # 15 nulos
    n_nulos_presupuesto = int(round(n_registros * 0.02))  # 10 nulos
    idx_nulos_r = rng.choice(n_registros, size=n_nulos_rating, replace=False)
    idx_nulos_p = rng.choice(n_registros, size=n_nulos_presupuesto, replace=False)

    df_con_ruido = df_base.copy()
    df_con_ruido.loc[idx_nulos_r, "rating_lugar"] = np.nan
    df_con_ruido.loc[idx_nulos_p, "presupuesto_mxn"] = np.nan

    # Inyección controlada de 15 filas duplicadas (~3%) y 4 outliers fuera de rango
    duplicados = df_con_ruido.iloc[10:25].copy()
    outliers = df_con_ruido.iloc[:4].copy().reset_index(drop=True)
    outliers.loc[0, "distancia_km"] = -4.2
    outliers.loc[1, "presupuesto_mxn"] = -80.0
    outliers.loc[2, "rating_lugar"] = 7.8
    outliers.loc[3, "trafico_nivel"] = 25

    df_crudo = pd.concat([df_con_ruido, duplicados, outliers], ignore_index=True)

    p_crudo = Path(ruta_crudo)
    p_crudo.parent.mkdir(parents=True, exist_ok=True)
    df_crudo.to_csv(p_crudo, index=False, encoding="utf-8")

    # ------------------------------------------------------------------
    # Pipeline de Limpieza (Práctica 02: Etapas A, B, C, D y E)
    # ------------------------------------------------------------------
    registros_iniciales = int(len(df_crudo))
    nulos_antes = {col: int(val) for col, val in df_crudo.isnull().sum().to_dict().items() if val > 0}
    total_nulos_antes = int(sum(nulos_antes.values()))
    duplicados_detectados = int(df_crudo.duplicated().sum())

    # 1. Eliminación de duplicados
    df_sin_dup = df_crudo.drop_duplicates().copy()

    # 2. Validación de rangos físicos y de dominio
    mask_valido = (
        df_sin_dup["distancia_km"].between(0.5, 25.0)
        & (df_sin_dup["presupuesto_mxn"].isna() | df_sin_dup["presupuesto_mxn"].between(20.0, 500.0))
        & (df_sin_dup["rating_lugar"].isna() | df_sin_dup["rating_lugar"].between(3.0, 5.0))
        & df_sin_dup["num_paradas"].between(1, 8)
        & df_sin_dup["trafico_nivel"].between(1, 10)
    )
    outliers_eliminados = int((~mask_valido).sum())
    df_limpio = df_sin_dup.loc[mask_valido].copy().reset_index(drop=True)

    # 3. Imputación por mediana
    mediana_rating = float(df_limpio["rating_lugar"].median())
    mediana_presupuesto = float(df_limpio["presupuesto_mxn"].median())
    df_limpio["rating_lugar"] = df_limpio["rating_lugar"].fillna(round(mediana_rating, 1))
    df_limpio["presupuesto_mxn"] = df_limpio["presupuesto_mxn"].fillna(round(mediana_presupuesto, 2))

    p_limpio = Path(ruta_limpio)
    p_limpio.parent.mkdir(parents=True, exist_ok=True)
    df_limpio.to_csv(p_limpio, index=False, encoding="utf-8")

    resumen_limpieza = {
        "registros_iniciales": registros_iniciales,
        "nulos_imputados": total_nulos_antes,
        "detalle_nulos_imputados": nulos_antes,
        "duplicados_eliminados": duplicados_detectados,
        "outliers_eliminados": outliers_eliminados,
        "registros_limpios": int(len(df_limpio)),
        "mediana_rating_imputada": round(mediana_rating, 2),
        "mediana_presupuesto_imputada": round(mediana_presupuesto, 2),
        "nulos_restantes": int(df_limpio.isnull().sum().sum()),
        "distribucion_plan_viable": {
            "viable_1": int((df_limpio["plan_viable"] == 1).sum()),
            "no_viable_0": int((df_limpio["plan_viable"] == 0).sum()),
        },
    }
    return df_limpio, resumen_limpieza
