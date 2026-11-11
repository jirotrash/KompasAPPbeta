"""Generación y preparación del conjunto de datos de 500 recorridos y planes turísticos de Kompás.

Combina lugares reales del catálogo del Valle de Toluca (Toluca, Metepec, Lerma, San Mateo Atenco)
y metadatos tipo Google Places con variaciones controladas de tráfico, número de paradas,
presupuesto y distancia para evaluar pipelines de limpieza (Práctica 02) y particiones de
entrenamiento de árboles de decisión (Práctica 03).
"""

from pathlib import Path
import numpy as np
import pandas as pd

from app.modulos.ia_kompas.pipeline_datos import (
    DIRECTORIO_DATA,
    etapa_a_analisis_inicial,
    etapa_b_exploracion_ia,
    etapa_c_auditoria_calidad,
    etapa_d_limpieza_y_guardado,
)

RUTA_RECORRIDOS_CRUDO = DIRECTORIO_DATA / "kompas_recorridos_500_crudo.csv"
RUTA_RECORRIDOS_LIMPIO = DIRECTORIO_DATA / "kompas_recorridos_500_limpio.csv"
RUTA_RECORRIDOS_REVISION = DIRECTORIO_DATA / "kompas_recorridos_500_revision.csv"

# Catálogo de lugares reales del dominio de Kompás con su rating base de referencia (Google Places)
CATALOGO_LUGARES_KOMPAS: list[dict] = [
    {"nombre": "Cosmovitral Jardín Botánico", "zona": "Toluca Centro", "rating_base": 4.7},
    {"nombre": "Los Portales de Toluca", "zona": "Toluca Centro", "rating_base": 4.6},
    {"nombre": "Terminal de Autobuses Toluca", "zona": "Toluca", "rating_base": 3.9},
    {"nombre": "Alameda Central Toluca", "zona": "Toluca Centro", "rating_base": 4.4},
    {"nombre": "Estadio Nemesio Diez", "zona": "Toluca", "rating_base": 4.8},
    {"nombre": "Parque Metropolitano Bicentenario", "zona": "Toluca", "rating_base": 4.6},
    {"nombre": "Centro Histórico de Metepec", "zona": "Metepec", "rating_base": 4.7},
    {"nombre": "Iglesia del Calvario de Metepec", "zona": "Metepec", "rating_base": 4.8},
    {"nombre": "Galerías Metepec", "zona": "Metepec", "rating_base": 4.5},
    {"nombre": "Parque Ambiental Bicentenario", "zona": "Metepec", "rating_base": 4.7},
    {"nombre": "Zona Artesanal de San Mateo Atenco", "zona": "San Mateo Atenco", "rating_base": 4.3},
    {"nombre": "Centro de Lerma", "zona": "Lerma", "rating_base": 4.2},
    {"nombre": "Plazas Outlet Lerma", "zona": "Lerma", "rating_base": 4.4},
    {"nombre": "Museo Torres Bicentenario", "zona": "Toluca", "rating_base": 4.3},
    {"nombre": "Parque Estatal Sierra Morelos", "zona": "Toluca", "rating_base": 4.6},
    {"nombre": "Mercado 16 de Septiembre", "zona": "Toluca Centro", "rating_base": 4.1},
]

COLUMNAS_CARACTERISTICAS_RECORRIDOS: list[str] = [
    "distancia_km",
    "presupuesto_mxn",
    "rating_lugar",
    "num_paradas",
    "trafico_nivel",
    "hora_dia",
    "es_hora_pico",
    "clima_lluvia",
]

COLUMNA_OBJETIVO_MODO = "modo_optimo"
COLUMNA_OBJETIVO_VIABILIDAD = "plan_viable"


def _determinar_modo_y_viabilidad(
    distancia_km: float,
    presupuesto_mxn: float,
    rating_lugar: float,
    num_paradas: int,
    trafico_nivel: int,
    clima_lluvia: int,
    rng: np.random.Generator,
) -> tuple[str, str, int]:
    """Evalúa las reglas latentes del dominio turístico de Kompás con variación controlada.

    Integra las variables de itinerario (`num_paradas`, `rating_lugar`) y de movilidad urbana
    (`distancia_km`, `presupuesto_mxn`, `trafico_nivel`, `clima_lluvia`) para asignar:
    - `modo_optimo`: 'caminando', 'transporte_publico' o 'auto_privado'
    - `plan_viable`: 'viable' o 'requiere_ajuste'
    - `duracion_min`: tiempo total estimado del recorrido en minutos
    """
    # 1. Determinación del modo óptimo de transporte considerando paradas, tráfico y rating
    if distancia_km <= 3.6 and num_paradas <= 4 and clima_lluvia == 0:
        modo = "caminando"
    elif presupuesto_mxn >= 220.0 and (clima_lluvia == 1 or trafico_nivel >= 6 or num_paradas >= 5):
        modo = "auto_privado"
    elif distancia_km > 12.0 and presupuesto_mxn >= 150.0 and rating_lugar >= 4.2:
        modo = "auto_privado"
    else:
        modo = "transporte_publico"

    # Variación estocástica controlada (~6.5%) en casos frontera para reflejar decisiones humanas reales
    # y permitir observar el sobreajuste (overfitting) en árboles de profundidad excesiva (max_depth >= 12)
    en_frontera = (
        (3.1 <= distancia_km <= 4.0)
        or (195.0 <= presupuesto_mxn <= 245.0)
        or (4 <= num_paradas <= 5 and 5 <= trafico_nivel <= 7)
    )
    if en_frontera and rng.random() < 0.22:
        alternativas = ["caminando", "transporte_publico", "auto_privado"]
        alternativas.remove(modo)
        modo = str(rng.choice(alternativas))

    # 2. Estimación de duración en minutos según modo, tráfico y paradas
    if modo == "caminando":
        duracion_min = int(round(distancia_km * 12.0 + num_paradas * 8.0))
    elif modo == "auto_privado":
        duracion_min = int(round(8.0 + distancia_km * 2.4 + trafico_nivel * 2.2 + num_paradas * 6.0))
    else:
        duracion_min = int(round(12.0 + distancia_km * 3.5 + trafico_nivel * 2.8 + num_paradas * 7.5))
    duracion_min = int(np.clip(duracion_min, 5, 290))

    # 3. Evaluación de viabilidad del itinerario turístico (plan_viable)
    costo_minimo_estimado = num_paradas * 25.0 + (
        0.0 if modo == "caminando" else (18.0 * num_paradas if modo == "transporte_publico" else 85.0 + distancia_km * 6.0)
    )
    if presupuesto_mxn >= costo_minimo_estimado * 0.75 and duracion_min <= 210 and rating_lugar >= 3.3:
        plan_viable = "viable"
    else:
        plan_viable = "requiere_ajuste"

    return modo, plan_viable, duracion_min


def generar_dataset_recorridos_kompas(
    ruta_csv: Path | str = RUTA_RECORRIDOS_CRUDO,
    n_recorridos_limpios: int = 500,
    semilla: int = 42,
) -> pd.DataFrame:
    """Genera el dataset representativo de 500 recorridos/planes turísticos de Kompás.

    Incluye lugares reales del catálogo de Kompás y variables de dominio:
    - `distancia_km` (entre 0.5 y 25.0 km)
    - `presupuesto_mxn` (entre 20 y 500 MXN)
    - `rating_lugar` (entre 3.0 y 5.0, con valores nulos intencionales para limpieza)
    - `num_paradas` (entre 1 y 8 paradas)
    - `trafico_nivel` (entre 1 y 10)
    - `modo_optimo` y `plan_viable` (variables objetivo)

    Además inyecta nulos controlados, duplicados y outliers para ser auditados y depurados
    por el pipeline de la Práctica 02, garantizando `n_recorridos_limpios` (500) registros válidos.
    """
    ruta = Path(ruta_csv)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(semilla)
    n = n_recorridos_limpios

    nombres_lugares = [lugar["nombre"] for lugar in CATALOGO_LUGARES_KOMPAS]
    ratings_base_map = {lugar["nombre"]: lugar["rating_base"] for lugar in CATALOGO_LUGARES_KOMPAS}

    origenes = rng.choice(nombres_lugares, size=n)
    destinos = rng.choice(nombres_lugares, size=n)

    # Distribución de distancias entre 0.5 y 25.0 km (con presencia de tramos cortos, medios y largos)
    distancias_cortas = rng.uniform(0.5, 2.8, size=int(n * 0.26))
    distancias_medias = rng.uniform(2.8, 10.5, size=int(n * 0.46))
    distancias_largas = rng.uniform(10.5, 25.0, size=n - len(distancias_cortas) - len(distancias_medias))
    distancias = np.concatenate([distancias_cortas, distancias_medias, distancias_largas])
    rng.shuffle(distancias)
    distancias = np.round(np.clip(distancias, 0.5, 25.0), 2)

    # Presupuesto entre 20 y 500 MXN
    presupuestos = np.round(rng.uniform(20.0, 500.0, size=n), 2)

    # Número de paradas del plan turístico (1 a 8 paradas)
    num_paradas = rng.integers(1, 9, size=n)

    # Hora del día y nivel de tráfico (1 a 10)
    horas = rng.integers(6, 23, size=n)
    horas_pico_set = {7, 8, 9, 18, 19, 20}
    es_hora_pico = np.array([1 if int(h) in horas_pico_set else 0 for h in horas])

    trafico_nivel = np.array([
        int(np.clip(rng.integers(6, 11) if pico else rng.integers(1, 8), 1, 10))
        for pico in es_hora_pico
    ])

    clima_lluvia = rng.choice([0, 1], size=n, p=[0.74, 0.26])

    # Rating del lugar entre 3.0 y 5.0 basado en el destino + variación local
    ratings = np.array([
        round(float(np.clip(ratings_base_map[dest] + rng.normal(0.0, 0.35), 3.0, 5.0)), 1)
        for dest in destinos
    ])

    modos = []
    viabilidades = []
    duraciones = []

    for dist, pto, rat, paradas, traf, lluvia in zip(
        distancias, presupuestos, ratings, num_paradas, trafico_nivel, clima_lluvia
    ):
        modo, viable, duracion = _determinar_modo_y_viabilidad(
            distancia_km=float(dist),
            presupuesto_mxn=float(pto),
            rating_lugar=float(rat),
            num_paradas=int(paradas),
            trafico_nivel=int(traf),
            clima_lluvia=int(lluvia),
            rng=rng,
        )
        modos.append(modo)
        viabilidades.append(viable)
        duraciones.append(duracion)

    df = pd.DataFrame({
        "parada_origen": origenes,
        "parada_destino": destinos,
        "distancia_km": distancias,
        "presupuesto_mxn": presupuestos,
        "rating_lugar": ratings,
        "rating_destino": ratings,
        "num_paradas": num_paradas,
        "trafico_nivel": trafico_nivel,
        "hora_dia": horas,
        "es_hora_pico": es_hora_pico,
        "clima_lluvia": clima_lluvia,
        "duracion_min": duraciones,
        "modo_optimo": modos,
        "modo_transporte_optimo": modos,
        "plan_viable": viabilidades,
    })

    # Inyección controlada de valores nulos en registros válidos (se imputarán en Etapa D)
    idx_nulos_rating = rng.choice(n, size=18, replace=False)
    df.loc[idx_nulos_rating, "rating_lugar"] = np.nan
    df.loc[idx_nulos_rating, "rating_destino"] = np.nan

    idx_nulos_pto = rng.choice(n, size=14, replace=False)
    df.loc[idx_nulos_pto, "presupuesto_mxn"] = np.nan

    # Adición de 4 registros atípicos (outliers) que serán separados a revisión en Etapa D
    outliers = df.iloc[:4].copy().reset_index(drop=True)
    outliers.loc[0, "distancia_km"] = -3.5
    outliers.loc[1, "rating_lugar"] = 9.2
    outliers.loc[1, "rating_destino"] = 9.2
    outliers.loc[2, "duracion_min"] = 850
    outliers.loc[3, "presupuesto_mxn"] = -45.0

    # Adición de 8 filas duplicadas exactas que serán eliminadas por drop_duplicates() en Etapa D
    duplicados = df.iloc[25:33].copy()

    df_crudo = pd.concat([df, outliers, duplicados], ignore_index=True)
    df_crudo.to_csv(ruta, index=False, encoding="utf-8")
    return df_crudo


def limpiar_dataset_recorridos_kompas(
    df_crudo: pd.DataFrame | None = None,
    ruta_crudo: Path | str = RUTA_RECORRIDOS_CRUDO,
    ruta_limpio: Path | str = RUTA_RECORRIDOS_LIMPIO,
    ruta_revision: Path | str = RUTA_RECORRIDOS_REVISION,
) -> tuple[pd.DataFrame, dict]:
    """Ejecuta el pipeline de limpieza de la Práctica 02 sobre el dataset de 500 recorridos de Kompás.

    Retorna la tupla `(df_limpio, reporte_calidad)`.
    """
    if df_crudo is None:
        p_crudo = Path(ruta_crudo)
        if not p_crudo.exists():
            df_crudo = generar_dataset_recorridos_kompas(ruta_csv=p_crudo)
        else:
            df_crudo = pd.read_csv(p_crudo)

    res_a = etapa_a_analisis_inicial(df_crudo)
    res_b = etapa_b_exploracion_ia(df_crudo)
    res_c = etapa_c_auditoria_calidad(df_crudo)

    # Limpieza dual (Etapa D) e imputación de rating_lugar y presupuesto_mxn
    df_limpio = etapa_d_limpieza_y_guardado(
        df_crudo,
        ruta_salida=ruta_limpio,
        ruta_revision=ruta_revision,
    )
    df_limpio["rating_lugar"] = df_limpio["rating_destino"]
    df_limpio["modo_optimo"] = df_limpio["modo_transporte_optimo"]
    df_limpio.to_csv(Path(ruta_limpio), index=False, encoding="utf-8")

    reporte = {
        "etapa_a": res_a,
        "etapa_b": res_b,
        "etapa_c": res_c,
        "etapa_d": {
            "filas_crudas": int(len(df_crudo)),
            "filas_limpias": int(len(df_limpio)),
            "duplicados_eliminados": int(res_c["filas_completamente_duplicadas"]),
            "nulos_imputados": res_c["nulos_por_columna"],
            "ruta_limpio": str(ruta_limpio),
            "ruta_revision": str(ruta_revision),
        },
    }
    return df_limpio, reporte


def obtener_variables_recorridos_kompas(
    df_limpio: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.Series, dict]:
    """Extrae la matriz predictora X y el vector objetivo y (`modo_optimo`) de los 500 recorridos."""
    if df_limpio is None:
        df_limpio, _ = limpiar_dataset_recorridos_kompas()

    X = df_limpio[COLUMNAS_CARACTERISTICAS_RECORRIDOS].copy()
    y = df_limpio[COLUMNA_OBJETIVO_MODO].copy()

    metadatos = {
        "total_muestras": int(len(X)),
        "columnas_predictoras": list(COLUMNAS_CARACTERISTICAS_RECORRIDOS),
        "variable_objetivo": COLUMNA_OBJETIVO_MODO,
        "clases": sorted(list(y.unique())),
        "distribucion_clases": {str(k): int(v) for k, v in y.value_counts().to_dict().items()},
        "distribucion_viabilidad": {
            str(k): int(v) for k, v in df_limpio[COLUMNA_OBJETIVO_VIABILIDAD].value_counts().to_dict().items()
        },
    }
    return X, y, metadatos
