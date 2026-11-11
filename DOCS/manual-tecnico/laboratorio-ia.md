# Manual Técnico: Laboratorio de Inteligencia Artificial de Kompás (`laboratorio-ia`)

Documentación integral de extremo a extremo (Backend FastAPI + Frontend React Native / Expo Router + Pruebas Automatizadas) para la adaptación de las prácticas de **Fundamentos de Inteligencia Artificial** (`p01BFS`, `p01reglafija`, `p02` a–e y `p03primermodelo`) al dominio de planificación turística y movilidad urbana de **KompasAPPbeta**.

---

## 1. Arquitectura de Extremo a Extremo

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ FRONTEND MÓVIL / WEB (Expo Router + Tamagui · COLORIMETRIA.md)               │
│  ├── app/src/app/(tabs)/perfil.tsx  ──► Botón "Laboratorio IA / Métricas"    │
│  ├── app/src/app/laboratorio-ia.tsx ──► Tarjetas, Particiones, Curva Depth,  │
│  │                                      Matriz de Confusión y Simulador      │
│  ├── app/src/services/api.ts        ──► obtenerMetricasIA()                  │
│  │                                      simularPrediccionIA(payload)         │
│  └── app/src/services/mock/laboratorioIa.ts ──► Fallback determinista offline│
└───────────────────────────────────────┬──────────────────────────────────────┘
                                        │ HTTP JSON (GET /api/ia/metricas, POST /api/ia/simular)
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ BACKEND FASTAPI (backend/app/modulos/ia_kompas/)                             │
│  ├── router.py               ──► GET /api/ia/metricas, POST /api/ia/simular  │
│  │                               GET /api/ia/evaluacion-modelo               │
│  ├── servicio.py             ──► ServicioIAKompas                            │
│  ├── datos_y_limpieza.py     ──► Práctica 02: 500 planes, imputación y rango │
│  ├── bfs_y_reglas.py         ──► Práctica 01: Grafo BFS + predecir_con_reglas│
│  └── modelo_entrenamiento.py ──► Práctica 03: Particiones + Curva max_depth  │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Fórmulas y Métricas de Evaluación

Sobre el conjunto de prueba ciego ($N_{\text{test}}$) se calculan las métricas de clasificación supervisada del `DecisionTreeClassifier` frente al sistema heurístico de Reglas Fijas:

1. **Exactitud (*Accuracy*):**
   $$\text{Exactitud} = \frac{VP + VN}{VP + VN + FP + FN}$$
2. **Precisión (*Precision*):**
   $$\text{Precisión} = \frac{VP}{VP + FP}$$
3. **Sensibilidad (*Recall*):**
   $$\text{Recall} = \frac{VP}{VP + FN}$$
4. **Puntaje $F_1$ (*F1-Score*):**
   $$F_1 = 2 \cdot \frac{\text{Precisión} \cdot \text{Recall}}{\text{Precisión} + \text{Recall}}$$
5. **Brecha de Generalización (Control de Sobreajuste):**
   $$\Delta_{\text{ajuste}} = \text{Exactitud}_{\text{Train}} - \text{Exactitud}_{\text{Val/Test}}$$

---

## 3. Resultados del Pipeline de Limpieza (Práctica 02 — `datos_y_limpieza.py`)

El generador reproducible (`seed=42`) crea 500 planes base con `distancia_km` $\in [0.5, 25.0]$, `presupuesto_mxn` $\in [20, 500]$, `rating_lugar` $\in [3.0, 5.0]$, `num_paradas` $\in [1, 8]$, `trafico_nivel` $\in [1, 10]$ y objetivo binario `plan_viable` $\in \{0, 1\}$, inyectando ~5% de ruido controlado:

| Indicador de Calidad | Valor Antes | Acción Aplicada (Etapa D) | Valor Después |
| --- | --- | --- | --- |
| **Registros totales** | `519` | Filtrado de duplicados y *outliers* | **`500`** |
| **Valores nulos (`NaN`)** | `26` (`15` en `rating_lugar`, `11` en `presupuesto_mxn`) | Imputación por mediana (`4.0★` y `$256.13 MXN`) | **`0`** |
| **Filas duplicadas** | `15` | Eliminación exacta con `drop_duplicates()` | **`0`** |
| **Outliers fuera de rango** | `4` (distancia $<0$, presupuesto $<0$, rating $>5$, tráfico $>10$) | Validación booleana de rangos `.between()` | **`0`** |

---

## 4. Tabla Comparativa de Particiones (`modelo_entrenamiento.py`)

Evaluación del `DecisionTreeClassifier` con profundidad óptima (`max_depth=5`) comparando el baseline de clase (**70% Train / 30% Test**) frente a cuatro esquemas alternativos:

| Código | Proporción | Muestras (Train / Val / Test) | Exactitud Train | Exactitud Val / CV | Exactitud Prueba | F1-Score Prueba | Exactitud Reglas Fijas | Estado |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `60_40` | 60% Train / 40% Test | 300 / 0 / 200 | 94.67% | 85.67% | 83.00% | 83.01% | 78.00% | Evaluada |
| `70_30` | **70% Train / 30% Test** | 350 / 0 / 150 | 94.00% | 81.14% | 82.67% | 82.67% | 78.67% | **Baseline de clase** |
| `75_25` | 75% Train / 25% Test | 375 / 0 / 125 | 94.13% | 85.60% | 83.20% | 83.22% | 75.20% | Supera al 70/30 |
| `80_20` | 80% Train / 20% Test | 400 / 0 / 100 | 92.50% | 85.00% | 84.00% | 84.01% | 83.00% | Supera al 70/30 |
| `60_20_20` | **60% Train / 20% Val / 20% Test** | **300 / 100 / 100** | **95.33%** | **85.00%** | **86.00%** | **86.00%** | **83.00%** | **Partición Óptima (+3.33% vs 70/30)** |

---

## 5. Monitor de Underfitting vs. Overfitting (`curva_complejidad`)

Evaluación de profundidades `max_depth` en `[1, 2, 3, 4, 5, 8, 12, 15]`:

| `max_depth` | Número de Hojas | Exactitud Train | Exactitud Validación | 5-Fold CV | Brecha (Train - Val) | Estado Diagnosticado |
| --- | --- | --- | --- | --- | --- | --- |
| **`1`** | 2 | 79.00% | 84.00% | 79.25% | -5.00% | **`Underfitting (Subajuste)`** |
| **`2`** | 4 | 83.00% | 84.00% | 82.75% | -1.00% | **`Underfitting (Subajuste)`** |
| **`3`** | 7 | 86.00% | 83.00% | 82.75% | +3.00% | **`Buen ajuste`** |
| **`4`** | 13 | 91.67% | 85.00% | 83.00% | +6.67% | **`Buen ajuste`** |
| **`5` (Óptimo)** | **22** | **95.33%** | **85.00%** | **85.00%** | **+10.33%** | **`Buen ajuste` (Seleccionado)** |
| **`8`** | 38 | 99.33% | 78.00% | 83.00% | +21.33% | **`Overfitting (Sobreajuste)`** |
| **`12`** | 40 | 100.00% | 79.00% | 82.50% | +21.00% | **`Overfitting (Sobreajuste)`** |
| **`15`** | 40 | 100.00% | 79.00% | 82.50% | +21.00% | **`Overfitting (Sobreajuste)`** |

### Matriz de Confusión (Partición Óptima, 100 muestras de prueba)
- **Verdaderos Negativos (`no_viable` acertado):** `46`
- **Falsos Positivos (Error Tipo I):** `7`
- **Falsos Negativos (Error Tipo II):** `7`
- **Verdaderos Positivos (`viable` acertado):** `40`
- **Exactitud total ML:** `86.00%` vs. **Exactitud Reglas Fijas:** `83.00%` (+3.00% en partición 60/20/20 y hasta +8.00% en partición 75/25).

---

## 6. Captura Lógica de la Pantalla `app/src/app/laboratorio-ia.tsx`

```text
+-------------------------------------------------------------------------+
| < Perfil                     Laboratorio IA                             |
+-------------------------------------------------------------------------+
| [ÁRBOL DE DECISIÓN (P03)]          | [PARTICIÓN ÓPTIMA SELECCIONADA]    |
| 86.0% Exactitud ML                 | 60% Train / 20% Validation / 20%   |
| Supera a Reglas Fijas (83.0%)      | max_depth = 5 · +3.3% vs 70/30     |
| F1: 86.0% · Prec: 86.0%            | 500 recorridos · 5-Folds CV        |
+-------------------------------------------------------------------------+
| Optimización de Particiones (Más allá del 70/30)                        |
|  - 60% Train / 40% Test                           Test: 83.0% [======= ]|
|  - 70% Train / 30% Test [BASELINE CLASE]          Test: 82.7% [======= ]|
|  - 75% Train / 25% Test                           Test: 83.2% [======= ]|
|  - 80% Train / 20% Test                           Test: 84.0% [========]|
|  - 60% Train / 20% Validation / 20% Test [ÓPTIMA] Test: 86.0% [========]|
+-------------------------------------------------------------------------+
| Control de Underfitting vs. Overfitting (max_depth)                     |
|  - max_depth = 1 (2 hojas)   --> [Underfitting (Subajuste)]  CV: 79.3%  |
|  - max_depth = 4 (13 hojas)  --> [Buen ajuste]               CV: 83.0%  |
|  - max_depth = 5 (22 hojas)  --> [SELECCIONADO · Buen ajuste]CV: 85.0%  |
|  - max_depth = 12 (40 hojas) --> [Overfitting (Sobreajuste)] Train:100% |
+-------------------------------------------------------------------------+
| Matriz de Confusión (Prueba)       | Limpieza de Datos (Práctica 02)    |
|  [VN: 46]          [FP: 7]         |  Crudos: 519  -> Nulos imp.: 26    |
|  [FN: 7]           [VP: 40]        |  Duplicados: 15 -> Limpios: 500    |
+-------------------------------------------------------------------------+
| Simulador Interactivo en Vivo (P01 + P03)                               |
|  [Paseo corto Centro] [Tour Metepec (4 paradas)] [Presupuesto ajustado] |
|  Distancia: 7.5 km (-) (+)   Presupuesto: $260 MXN (-) (+)              |
|  Paradas: 4 (-) (+)          Tráfico: Nivel 6/10 (-) (+)                |
|  [Evaluar con Reglas Fijas, Árbol ML y BFS]                             |
|  -> ÁRBOL ML: Plan Viable · auto_privado (Confianza 92%)                |
|  -> REGLA FIJA: Plan Viable · transporte_publico [R4_PRESUPUESTO_HOLGADO]|
|  -> RUTA BFS: Terminal Toluca → Centro Metepec → Galerias Metepec       |
+-------------------------------------------------------------------------+
```
