# Laboratorio de IA y Optimización de Particiones en Kompás (`laboratorio-ia-particiones`)

Documentación técnica integral de los cambios implementados en la rama `feat/ia-optimizacion-particiones` para integrar las prácticas académicas de **Fundamentos de Inteligencia Artificial** (Búsqueda en Anchura BFS, Reglas Fijas, Pipeline de Limpieza de Datos y Árboles de Decisión) en el backend FastAPI (`backend/app/modulos/ia_kompas/`) y en la aplicación móvil/web Expo Router (`app/src/`).

---

## 1. Adaptación de las Prácticas de Clase al Dominio de Kompás

Cada ejercicio académico se integró nativamente con las entidades de **Mis Planes** (`itinerarios`) y **Transporte** (`rutas`) del Valle de Toluca (Toluca, Metepec, Lerma y San Mateo Atenco):

| Práctica Académica | Módulos en `backend/app/modulos/ia_kompas/` | Aplicación Real en Kompás |
| --- | --- | --- |
| **Práctica 01 — Búsqueda BFS** (`p01BFS.py`) | `p01_grafo_bfs.py`, `busqueda_escalas.py`, `bfs_y_reglas.py` | Búsqueda en anchura con cola FIFO (`collections.deque`) sobre el grafo de 12 zonas turísticas (`GRAFO_BASE_KOMPAS`) para minimizar escalas y transbordos entre paradas de un itinerario. |
| **Práctica 01 — Reglas Fijas** (`p01reglafija.py`) | `p01_regla_fija.py`, `reglas_transporte.py`, `bfs_y_reglas.py` (`predecir_con_reglas`) | Sistema experto heurístico determinista (*baseline*) para clasificar viabilidad del plan (`plan_viable` $\in \{0, 1\}$) y recomendar transporte (`caminando`, `transporte_publico`, `auto_privado`). |
| **Práctica 02 — Pipeline de Datos** (`p02` a–e) | `p02_pipeline_datos.py`, `datos_kompas.py`, `datos_y_limpieza.py` | Generación reproducible (`seed=42`) de **500 recorridos y planes turísticos** con `distancia_km` $[0.5, 25.0]$, `presupuesto_mxn` $[20, 500]$, `rating_lugar` $[3.0, 5.0]$, `num_paradas` $[1, 8]$ y `trafico_nivel` $[1, 10]$. Inyecta ~5% de nulos y duplicados y ejecuta auditoría, eliminación de duplicados/outliers e imputación por mediana. |
| **Práctica 03 — Primer Modelo ML** (`p03primermodelo.py`) | `p03_modelo_predictivo.py`, `entrenamiento_particiones.py`, `modelo_entrenamiento.py` | Entrenamiento de `DecisionTreeClassifier`, optimización experimental de particiones superando el 70/30 fijo de clase, control de *Underfitting* vs. *Overfitting* por `max_depth` y simulador interactivo frente a Reglas Fijas. |

---

## 2. Comparativa de Particiones: Superando el 70/30 Tradicional

El script original de clase utilizaba una partición fija de **70% entrenamiento y 30% prueba (`test_size=0.30`)**. En Kompás se implementó un comparador experimental estratificado con validación cruzada de 5 pliegues (`StratifiedKFold(n_splits=5)`) tanto para la recomendación multiclase (`modo_optimo` en `entrenamiento_particiones.py`) como para la viabilidad del plan (`plan_viable` en `modelo_entrenamiento.py`):

### 2.1 Resultados en Clasificación de Viabilidad del Plan (`GET /api/ia/metricas`, `max_depth=5`)

| Código | Esquema de Partición | Muestras (Train / Val / Test) | Exactitud Train | Exactitud Val / CV | Exactitud Prueba | F1-Score Prueba | Exactitud Reglas Fijas | Selección |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `60_40` | 60% Train / 40% Test | 300 / 0 / 200 | 94.67% | 85.67% | 83.00% | 83.01% | 78.00% | Evaluada |
| `70_30` | **70% Train / 30% Test** | 350 / 0 / 150 | 94.00% | 81.14% | 82.67% | 82.67% | 78.67% | **Baseline de clase** |
| `75_25` | 75% Train / 25% Test | 375 / 0 / 125 | 94.13% | 85.60% | 83.20% | 83.22% | 75.20% | Supera al 70/30 |
| `80_20` | **80% Train / 20% Test** | 400 / 0 / 100 | 92.50% | 85.00% | **84.00%** | **84.01%** | 83.00% | **Óptima sin bloque Val (+1.33% vs 70/30)** |
| `60_20_20` | **60% Train / 20% Val / 20% Test** | **300 / 100 / 100** | **95.33%** | **85.00%** | **86.00%** | **86.00%** | **83.00%** | **Partición Óptima Global (+3.33% vs 70/30)** |

### 2.2 Resultados en Recomendación Multiclase de Transporte (`GET /api/ia/evaluacion-modelo`, `max_depth=4`)

| Código | Esquema de Partición | Muestras (Train / Val / Test) | Exactitud Train | 5-Fold CV F1 | Exactitud Prueba | F1-Score Prueba | Brecha Generalización | Selección |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `70_30` | **70% Train / 30% Test** | 350 / 0 / 150 | 89.43% | 83.53% | 80.00% | 79.89% | 9.43% | **Baseline de clase** |
| `75_25` | 75% Train / 25% Test | 375 / 0 / 125 | 90.13% | 81.27% | 83.20% | 83.08% | 6.93% | Supera al 70/30 |
| `80_20` | **80% Train / 20% Test** | **400 / 0 / 100** | **89.75%** | **85.89%** | **84.00%** | **83.87%** | **5.75%** | **Partición Óptima (+4.00% vs 70/30)** |
| `85_15` | 85% Train / 15% Test | 425 / 0 / 75 | 89.88% | 86.25% | 81.33% | 81.33% | 8.55% | Evaluada |
| `60_20_20` | **60% Train / 20% Val / 20% Test** | 300 / 100 / 100 | 89.00% | 85.89% | 84.00% | 83.74% | 5.00% | **Óptima con Validación** |

**Justificación técnica:** En un dataset de dominio turístico de tamaño medio ($N=500$), reservar un 30% para prueba (150 registros) como en el baseline 70/30 resta datos valiosos para calibrar los umbrales de corte entre `presupuesto_mxn`, `distancia_km`, `num_paradas` y `trafico_nivel`. Las configuraciones **80/20** y **60/20/20 (con 5-Fold CV)** estabilizan las particiones del árbol, reducen la brecha de generalización y elevan la exactitud en prueba entre **+3.33 y +4.00 puntos porcentuales** sobre el 70/30 tradicional.

---

## 3. Análisis de Underfitting vs. Overfitting ("Falta de alimentación vs. Sobrealimentación")

Se evaluó el `DecisionTreeClassifier` variando `max_depth` en `[1, 2, 3, 4, 5, 8, 12, 15]` y variando el tamaño de la muestra de entrenamiento:

| `max_depth` | Hojas | Exactitud Train | Exactitud Validación | 5-Fold CV | Brecha (Train - Val) | Estado Diagnosticado |
| --- | --- | --- | --- | --- | --- | --- |
| **`1`** | 2 | 79.00% | 84.00% | 79.25% | -5.00% | **`Underfitting (Subajuste)`** |
| **`2`** | 4 | 83.00% | 84.00% | 82.75% | -1.00% | **`Underfitting (Subajuste)`** |
| **`3`** | 7 | 86.00% | 83.00% | 82.75% | +3.00% | **`Buen ajuste`** |
| **`4`** | 13 | 91.67% | 85.00% | 83.00% | +6.67% | **`Buen ajuste`** |
| **`5` (Óptimo)** | **22** | **95.33%** | **85.00%** | **85.00%** | **+10.33%** | **`Buen ajuste` (Seleccionado)** |
| **`8`** | 38 | 99.33% | 78.00% | 83.00% | +21.33% | **`Overfitting (Sobreajuste)`** |
| **`12`** | 40 | 100.00% | 79.00% | 82.50% | +21.00% | **`Overfitting (Sobreajuste)`** |
| **`15`** | 40 | 100.00% | 79.00% | 82.50% | +21.00% | **`Overfitting (Sobreajuste)`** |

- **Evidencia de Underfitting (Subajuste):** Con `max_depth=1` o `2`, el árbol carece de capacidad para combinar las 5 variables del recorrido (`cv_score = 79.25%`). Asimismo, al alimentar el modelo con solo el 8% de los datos (24 muestras), la exactitud de validación cae a **49.00%** por falta de alimentación de datos.
- **Evidencia de Overfitting (Sobreajuste):** Con `max_depth >= 12` sin poda, el árbol memoriza el 100.00% del conjunto de entrenamiento (40–44 hojas), provocando que la validación caiga a **78.00%–79.00%** (una brecha de sobreajuste $>21\%$).

---

## 4. Nuevas Rutas en Backend y Frontend

### Backend (`backend/app/modulos/ia_kompas/router.py`)
- `GET /api/ia/metricas`: Devuelve `resumen_limpieza`, `comparativa_particiones`, `curva_complejidad` (`max_depth` con diagnóstico de *Underfitting* / *Buen ajuste* / *Overfitting*) y `comparativa_sistemas` (Exactitud ML vs. Reglas Fijas + Matriz de Confusión).
- `POST /api/ia/simular`: Recibe `{ distancia_km, presupuesto_mxn, rating_lugar, num_paradas, trafico_nivel, origen, destino }` y retorna en tiempo real la decisión de Reglas Fijas, la predicción del Árbol de Decisión óptimo y la ruta con menos escalas vía BFS.
- `GET /api/ia/evaluacion-modelo`: Reporte experimental completo de particiones (`70/30`, `75/25`, `80/20`, `85/15`, `60/20/20`), curvas de `max_depth` (`1..15`) y curva de tamaño de muestra.

### Frontend (`app/src/`)
- `app/src/app/laboratorio-ia.tsx`: Nueva pantalla interactiva accesible desde **Perfil → "Laboratorio IA / Métricas del Modelo"** (`app/src/app/(tabs)/perfil.tsx`), registrada en `app/src/app/_layout.tsx` y respaldada por `obtenerMetricasIA()` y `simularPrediccionIA()` en `app/src/services/api.ts` (con fallback offline en `app/src/services/mock/laboratorioIa.ts`).
