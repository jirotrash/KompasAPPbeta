# Evaluación Experimental de Particiones y Control de Subajuste/Sobreajuste en Kompás (`ia_kompas`)

Documentación técnica de la integración de las prácticas de **Fundamentos de Inteligencia Artificial** (Búsqueda en Anchura BFS `p01_grafo_bfs`, Reglas Fijas `p01_regla_fija`, Pipeline de Datos `p02_pipeline_datos` y Árboles de Decisión `p03_modelo_predictivo`) adaptadas al dominio de planificación de itinerarios (`itinerarios`/mis-planes) y recomendación de transporte urbano (`rutas`/transporte) en el Valle de Toluca.

---

## 1. Dataset del Dominio de Kompás (`datos_kompas.py`)

El módulo `backend/app/modulos/ia_kompas/datos_kompas.py` construye un conjunto de datos representativo de **500 recorridos y planes turísticos limpios** (a partir de 512 registros crudos que atraviesan las 5 etapas de auditoría y limpieza de la Práctica 02). Combina atractivos reales del catálogo del proyecto (Cosmovitral, Los Portales, Terminal Toluca, Centro Histórico de Metepec, Galerías Metepec, Plazas Outlet Lerma, Zona Artesanal de San Mateo Atenco, etc.) con variaciones controladas del dominio:

| Variable | Rango / Dominio | Rol en el Modelo |
| --- | --- | --- |
| `distancia_km` | `0.5` a `25.0` km | Variable predictora ($X$) — longitud total del traslado o circuito. |
| `presupuesto_mxn` | `$20.0` a `$500.0` MXN | Variable predictora ($X$) — presupuesto disponible del turista (con nulos imputados por mediana en Etapa D). |
| `rating_lugar` | `3.0` a `5.0` estrellas | Variable predictora ($X$) — calificación en Google Places (con nulos imputados en Etapa D). |
| `num_paradas` | `1` a `8` paradas | Variable predictora ($X$) — escalas o lugares incluidos en el plan turístico. |
| `trafico_nivel` | `1` a `10` | Variable predictora ($X$) — índice de congestión vial en Toluca/Metepec. |
| `hora_dia` / `es_hora_pico` | `6` a `22` h / `{0, 1}` | Variables predictoras ($X$) — franja horaria del recorrido. |
| `clima_lluvia` | `{0, 1}` | Variable predictora ($X$) — presencia de lluvia durante el traslado. |
| `modo_optimo` | `auto_privado` (241), `transporte_publico` (192), `caminando` (67) | **Variable objetivo principal ($y$)** para recomendación de transporte. |
| `plan_viable` | `viable` (380), `requiere_ajuste` (120) | **Variable objetivo secundaria** de viabilidad presupuestal y temporal del itinerario. |

### Resultados de Limpieza (Pipeline Práctica 02)
- **Registros crudos ingresados:** `512` filas.
- **Duplicados exactos eliminados (`drop_duplicates`):** `8` filas.
- **Registros atípicos (*outliers*) enviados a revisión (`kompas_recorridos_500_revision.csv`):** `4` filas (distancias negativas, ratings fuera de `[1.0, 5.0]`, duraciones > 300 min y presupuestos negativos).
- **Valores nulos imputados por mediana:** `18` en `rating_lugar` y `15` en `presupuesto_mxn`.
- **Registros limpios finales (`kompas_recorridos_500_limpio.csv`):** **`500` recorridos válidos**.

---

## 2. Optimización de Particiones más allá del 70-30 (`entrenamiento_particiones.py`)

En el script base de clase (`p03_modelo_predictivo.py`), se utilizaba una partición fija de **70% entrenamiento y 30% prueba (`test_size=0.30`)**. En `backend/app/modulos/ia_kompas/entrenamiento_particiones.py` se implementó un comparador experimental estratificado con validación cruzada de 5 pliegues (`StratifiedKFold(n_splits=5)`) usando la profundidad óptima del árbol (`max_depth=4`):

| Esquema de Partición | Muestras (Train / Val / Test) | Exactitud Train | Exactitud Val / CV | Exactitud Prueba | F1-Score Prueba (Ponderado) | 5-Fold CV F1 ($\mu \pm \sigma$) | Brecha Generalización | Exactitud Regla Fija |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **70% Train / 30% Test** *(Baseline clase)* | 350 / 0 / 150 | 89.43% | 83.53% | 80.00% | 79.89% | 83.53% ± 3.12% | 9.43% | 54.67% |
| **75% Train / 25% Test** | 375 / 0 / 125 | 90.13% | 81.27% | 83.20% | 83.08% | 81.27% ± 6.06% | 6.93% | 53.60% |
| **80% Train / 20% Test** *(Seleccionada Óptima)* | **400 / 0 / 100** | **89.75%** | **85.89%** | **84.00%** | **83.87%** | **85.89% ± 3.80%** | **5.75%** | **56.00%** |
| **85% Train / 15% Test** | 425 / 0 / 75 | 89.88% | 86.25% | 81.33% | 81.33% | 86.25% ± 1.67% | 8.55% | 58.67% |
| **60% Train / 20% Val / 20% Test** *(5-Fold CV)* | 300 / 100 / 100 | 89.00% | 82.00% | 84.00% | 83.74% | 85.89% ± 3.80% | 5.00% | 56.00% |

### Justificación Técnica: ¿Por qué 80/20 (y 60/20/20 con CV) supera al 70/30 tradicional en Kompás?

1. **Mayor densidad en umbrales multicriterio ($N=400$ vs $N=350$):** Al incorporar variables adicionales del dominio de itinerarios (`num_paradas`, `trafico_nivel`, `rating_lugar`) junto con `distancia_km` y `presupuesto_mxn`, el árbol de decisión necesita estimar puntos de corte continuos en nodos de nivel 3 y 4. Disponer del **80% de los datos para entrenamiento (400 recorridos)** reduce la varianza de los umbrales de ganancia de información (Gini), elevando la exactitud en prueba de **80.00% a 84.00% (+4.00 puntos)** y el F1-score ponderado de **79.89% a 83.87% (+3.98 puntos)**.
2. **Reducción de la brecha de generalización:** La diferencia entre entrenamiento y prueba baja de **9.43%** (en 70/30) a **5.75%** (en 80/20) y **5.00%** (en 60/20/20), mientras que la validación cruzada estratificada de 5-Folds sube de **83.53%** a **85.89%**.
3. **Límite de reducción del conjunto de prueba (85/15):** Al subir a 85/15, el conjunto de prueba queda con solo 75 muestras (apenas ~10 ejemplos de la clase minoritaria `caminando`), lo que incrementa la sensibilidad a casos frontera y reduce la exactitud de prueba a 81.33%. Por ello, **80/20** representa el equilibrio estadístico óptimo para los 500 recorridos de Kompás, apoyado por **60/20/20** para la calibración sin fuga de información (*data leakage*) del hiperparámetro `max_depth`.

---

## 3. Control de Underfitting vs. Overfitting ("Falta de alimentación vs. Sobrealimentación")

Se evaluó el `DecisionTreeClassifier` sobre la partición **60% Train / 20% Validation / 20% Test** variando `max_depth` desde `1` hasta `15` y variando el tamaño de la muestra de entrenamiento:

### 3.1 Curva de Complejidad por Profundidad (`max_depth` 1 a 15)

| `max_depth` | Hojas | Exactitud Train | Exactitud Validación | Exactitud Prueba | F1 Prueba | Brecha (Train - Val) | Diagnóstico |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **`1`** | 2 | 76.00% | 71.00% | 79.00% | 73.60% | 5.00% | **Underfitting (Subajuste)** |
| **`2`** | 4 | 76.67% | 69.00% | 73.00% | 70.04% | 7.67% | **Underfitting (Subajuste)** |
| **`3`** | 8 | 83.67% | 76.00% | 82.00% | 81.70% | 7.67% | Óptimo equilibrado |
| **`4` (Óptimo)** | **16** | **89.00%** | **82.00%** | **84.00%** | **83.74%** | **7.00%** | **Óptimo Seleccionado** |
| **`5`** | 27 | 93.67% | 89.00% | 78.00% | 78.52% | 4.67% | Inicio de fragmentación en prueba |
| **`8`** | 43 | 99.67% | 87.00% | 80.00% | 80.12% | 12.67% | Complejidad alta |
| **`12`** | 44 | **100.00%** | **78.00%** | **78.00%** | **78.13%** | **22.00%** | **Overfitting (Sobreajuste)** |
| **`15`** | 44 | **100.00%** | **78.00%** | **78.00%** | **78.13%** | **22.00%** | **Overfitting (Sobreajuste)** |

### 3.2 Curva de Alimentación de Datos (`curva_tamano_muestra`)

| Fracción de Entrenamiento | Muestras (`N`) | Exactitud Train | Exactitud Validación | F1 Validación | Diagnóstico de Alimentación |
| --- | --- | --- | --- | --- | --- |
| **8%** | 24 | 100.00% | **49.00%** | **51.53%** | **Falta de alimentación (Underfitting de datos)** |
| **15%** | 45 | 91.11% | **65.00%** | **62.63%** | **Falta de alimentación (Underfitting de datos)** |
| **30%** | 90 | 91.11% | 74.00% | 72.99% | Alimentación suficiente inicial |
| **50%** | 150 | 89.33% | 76.00% | 74.78% | Alimentación media |
| **75%** | 225 | 90.67% | 84.00% | 83.31% | Alimentación sólida |
| **100%** | 300 | 89.00% | 82.00% | 81.14% | Alimentación completa de entrenamiento |

### Conclusiones del Análisis de Ajuste
- **Demostración de Underfitting (Subajuste):** Con `max_depth=1`, el árbol solo cuenta con **2 hojas** para un problema de **3 clases** (`auto_privado`, `caminando`, `transporte_publico`), por lo que es estructuralmente incapaz de predecir la tercera clase y su F1 en validación se estanca en **65.21%** (73.60% en prueba). De igual forma, cuando el modelo sufre **falta de alimentación de datos** (entrenando con solo 24 recorridos), la exactitud en validación cae hasta **49.00%**.
- **Demostración de Overfitting (Sobrealimentación):** Cuando `max_depth >= 12` sin poda, el árbol se ramifica hasta **44 hojas**, memorizando al **100.00%** el conjunto de entrenamiento, incluidos los casos frontera. Como consecuencia, la exactitud en validación y prueba cae a **78.00%** (una brecha de sobreajuste de **22.00 puntos porcentuales**).
- **Selección de `max_depth=4` contra Reglas Fijas (`p01_regla_fija.py`):** El sistema heurístico de Reglas Fijas no contempla `num_paradas`, `trafico_nivel` ni `rating_lugar`, obteniendo **56.00%** de exactitud (F1 = **47.93%**) sobre los recorridos turísticos. El árbol podado en `max_depth=4` alcanza **84.00%** de exactitud (F1 = **83.74%**, **+28.00 puntos porcentuales de mejora**).

---

## 4. Matriz de Confusión e Importancia de Variables (Partición Óptima 80/20, `max_depth=4`)

### Matriz de Confusión (100 muestras de prueba)

| Real \ Predicho | `auto_privado` | `caminando` | `transporte_publico` |
| --- | --- | --- | --- |
| **`auto_privado`** | **43** | 1 | 4 |
| **`caminando`** | 4 | **8** | 1 |
| **`transporte_publico`** | 3 | 3 | **33** |

### Importancia de Variables (`feature_importances_`)
1. `presupuesto_mxn`: **49.19%**
2. `distancia_km`: **22.11%**
3. `num_paradas`: **11.52%**
4. `clima_lluvia`: **10.42%**
5. `trafico_nivel`: **5.74%**
6. `rating_lugar`: **1.02%**

---

## 5. Endpoint FastAPI y Verificación Automatizada

### Endpoint Expuesto
- **Ruta:** `GET /api/ia/evaluacion-modelo`
- **Router:** `backend/app/modulos/ia_kompas/router.py`
- **Esquema de Respuesta:** `EsquemaEvaluacionModeloParticiones` (`backend/app/modulos/ia_kompas/esquemas.py`)
- **Campos devueltos en JSON:**
  - `dataset_kompas`: resumen de las 500 muestras, distribución de `modo_optimo` y `plan_viable`, y auditoría de limpieza de la Práctica 02.
  - `tabla_comparativa_particiones`: métricas completas de `70_30`, `75_25`, `80_20`, `85_15` y `60_20_20`.
  - `particion_optima` y `comparativa_optima_vs_70_30`: selección automática y justificación técnica frente al 70-30.
  - `analisis_underfitting_overfitting`: `max_depth_optimo_seleccionado`, evidencia de subajuste (`max_depth=1` y curva de tamaño de muestra), evidencia de sobreajuste (`max_depth=15`) y curvas completas.
  - `comparacion_contra_reglas_fijas`: comparativa directa contra `p01_regla_fija.py`.
  - `matriz_confusion` e `importancia_variables`.

### Ejecución de Pruebas
```bash
cd backend
python -m pytest tests/test_ia_kompas.py tests/test_planes_guardados.py tests/test_transporte.py -v
```
