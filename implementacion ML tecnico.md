# Documento de Implementación Técnica de Machine Learning e IA (`ia_kompas`)

> **Destinatarios:** Equipo de Backend, Frontend Móvil y Auditoría Académica de Inteligencia Artificial.  
> **Arquitectura:** FastAPI (Capas: Router $\to$ Servicio $\to$ Repositorio), Scikit-Learn, Pandas, Numpy, Pydantic v2.  
> **Estándar:** Código y variables en español, preservación de zonas protegidas (`backend/app/ia/`) y no regresión de pruebas.

---

## 1. Arquitectura del Módulo y Trazabilidad Académica

El módulo `ia_kompas` adapta las prácticas de IA y Ciencia de Datos (`practicas_04_11_2026.rar`) al dominio de itinerarios y transporte de **Kompás**, desacoplando la dependencia dura hacia Ollama para el agente de asistencia:

```text
backend/
├── data/
│   ├── kompas_traslados_crudo.csv         # Dataset con ruido/nulos para auditar en etapa C
│   ├── kompas_traslados_limpio.csv        # Dataset preprocesado para entrenamiento (etapa D)
│   └── kompas_traslados_revision.csv      # Dataset de registros anómalos para auditoría
├── app/
│   └── modulos/
│       └── ia_kompas/
│           ├── __init__.py
│           ├── esquemas.py                # Modelos Pydantic v2 (I/O tipado estricto)
│           ├── busqueda_escalas.py        # Búsqueda en anchura (minimizar escalas BFS)
│           ├── reglas_transporte.py       # Heurística determinista baseline (reglas fijas)
│           ├── pipeline_datos.py          # Pipeline ETL/EDA Pandas de 5 etapas (A a E)
│           ├── modelo_predictivo.py       # DecisionTreeClassifier con partición 70/30
│           ├── servicio.py                # Servicio orquestador (ServicioIAKompas)
│           └── router.py                  # Endpoints REST bajo prefijo /api/ia/...
└── tests/
    └── test_ia_kompas.py                  # Suite de pruebas unitarias pytest
```

---

## 2. Especificación Técnica por Componente

### 2.1. `busqueda_escalas.py` (Búsqueda en Anchura para Escalas de Transporte)
* **Algoritmo:** Búsqueda en anchura (BFS) sobre grafo de adyacencia dirigido o no dirigido de nodos turísticos/estaciones de Toluca y Metepec.
* **Estructura de Datos:** `collections.deque` como cola FIFO de caminos acumulados y `set` para control de nodos visitados en tiempo $O(V + E)$.
* **Firma de la función:**
  ```python
  def buscar_ruta_bfs(grafo: dict[str, list[str]], origen: str, destino: str) -> dict: ...
  ```
* **Métricas computadas:**
  * `ruta_paradas`: Secuencia ordenada de paradas $[v_0, v_1, \dots, v_n]$.
  * `num_escalas`: Cantidad de paradas intermedias requeridas: $\max(0, \text{len}(\text{ruta\_paradas}) - 2)$.
  * `saltos_totales`: Aristas recorridas: $\max(0, \text{len}(\text{ruta\_paradas}) - 1)$.

### 2.2. `reglas_transporte.py` (Sistema Basado en Reglas / Baseline Determinista)
* **Objetivo:** Baseline comparativo contra el modelo supervisado y mecanismo de salvaguarda (*fallback* determinista) cuando la confianza del modelo sea insuficiente o falten características.
* **Lógica de negocio implementada:**
  1. $\text{distancia\_km} \le 1.5 \land \neg \text{clima\_lluvia} \implies \text{"caminando"}$.
  2. $\text{distancia\_km} \le 4.0 \land \neg \text{clima\_lluvia} \land \text{presupuesto\_mxn} < 40 \implies \text{"bicicleta" o "transporte\_publico"}$.
  3. $\text{clima\_lluvia} \lor (\text{es\_hora\_pico} \land \text{presupuesto\_mxn} \ge 100) \implies \text{"auto\_privado"}$.
  4. $\text{distancia\_km} > 1.5 \land \text{presupuesto\_mxn} < 80 \implies \text{"transporte\_publico"}$.
  5. Fallback por defecto $\implies \text{"auto\_privado"}$ si $\text{presupuesto\_mxn} \ge 80$, caso contrario $\text{"transporte\_publico"}$.

### 2.3. `pipeline_datos.py` (Pipeline de Datos con Pandas de 5 Etapas)
* **Etapa A (`etapa_a_analisis_inicial`):** Ingesta tabular con Pandas, inspección de dimensiones (`shape`), columnas y exportación inicial.
* **Etapa B (`etapa_b_exploracion_ia`):** EDA descriptivo: tipos de datos (`dtypes`), no nulos (`info`), resumen estadístico paramétrico (`describe`), medias y distribuciones por clase de transporte.
* **Etapa C (`etapa_c_auditoria_calidad`):** Detección de fallas de integridad tal como `p02problemascalidaddatos_c.py`:
  * Nulos por atributo (`isnull().sum()`).
  * Tuplas redundantes (`duplicated()`).
  * Rangos fuera de dominio ($\text{distancia\_km} \le 0$, $\text{rating\_destino} \notin [1.0, 5.0]$, $\text{presupuesto\_mxn} < 0$, $\text{duracion\_min} > 300$).
* **Etapa D (`etapa_d_limpieza_y_guardado`):** Estrategia de partición dual de `p02limpiezaguardadodatos_d.py`:
  1. `df_limpio = df.drop_duplicates().copy()`
  2. Construcción de máscara booleana estricta con `.between(min, max)`:
     ```python
     valido = (
         (df_limpio["distancia_km"] > 0)
         & df_limpio["duracion_min"].between(1, 300)
         & (df_limpio["rating_destino"].isna() | df_limpio["rating_destino"].between(1.0, 5.0))
         & (df_limpio["presupuesto_mxn"].isna() | (df_limpio["presupuesto_mxn"] >= 0))
     )
     ```
  3. Separación física:
     * `df_validos = df_limpio.loc[valido].copy()` $\to$ Imputación de `rating_destino` y `presupuesto_mxn` mediante la mediana $\to$ persistencia en `backend/data/kompas_traslados_limpio.csv`.
     * `df_revision = df_limpio.loc[~valido].copy()` $\to$ persistencia en `backend/data/kompas_traslados_revision.csv` para auditoría y trazabilidad.
* **Etapa E (`etapa_e_identificacion_variables`):** Partición matricial estricta:
  * Matriz de características $X \in \mathbb{R}^{N \times 6}$:
    `['distancia_km', 'hora_dia', 'es_hora_pico', 'presupuesto_mxn', 'clima_lluvia', 'rating_destino']`
  * Vector objetivo $y \in \{\text{'caminando'}, \text{'transporte_publico'}, \text{'auto_privado'}\}^N$.
  * Aserción de alineación: `assert len(X) == len(y)`.

### 2.4. `modelo_predictivo.py` (Modelado Predictivo y Evaluación Comparativa)
* **Partición de Datos:** Regla del **70% para entrenamiento y 30% para prueba**:
  ```python
  X_entrenamiento, X_prueba, y_entrenamiento, y_prueba = train_test_split(
      X, y, test_size=0.30, random_state=42, stratify=y
  )
  ```
* **Algoritmo Clasificador:** `DecisionTreeClassifier(max_depth=4, random_state=42)` de `scikit-learn`.
* **Evaluación Comparativa (Test Set ciego):**
  * $\text{Exactitud}_{\text{ML}} = \text{accuracy\_score}(y_{\text{prueba}}, \hat{y}_{\text{ML}})$.
  * $\text{Exactitud}_{\text{Regla Fija}} = \text{accuracy\_score}(y_{\text{prueba}}, \hat{y}_{\text{Regla}})$.
  * Generación de `classification_report` (Precision, Recall, F1-Score) y `confusion_matrix`.
* **Inferencia en Tiempo Real:** Exposición de `predecir_traslado(datos: dict)` retornando el modo clasificado, confianza probabilística (`predict_proba`), resultado del baseline y concordancia booleana.

---

## 3. Contrato de la API y Endpoints

### `GET /api/ia/pipeline-estado`
Regresa el estado actual del dataset, el reporte de calidad auditado (nulos, duplicados eliminados) y las métricas de exactitud de Machine Learning vs Reglas Fijas.

### `POST /api/ia/recomendar-traslado`
**Payload de entrada (`EsquemaConsultaTrasladoIA`):**
```json
{
  "distancia_km": 2.4,
  "presupuesto_mxn": 60.0,
  "hora_dia": 18,
  "clima_lluvia": false,
  "rating_destino": 4.5,
  "origen": "Cosmovitral",
  "destino": "Los Portales"
}
```

**Respuesta (`EsquemaRespuestaTrasladoIA`):**
```json
{
  "modo_recomendado": "transporte_publico",
  "confianza": 0.88,
  "origen_decision": "machine_learning",
  "tiempo_estimado_min": 12,
  "ruta_bfs": {
    "ruta_paradas": ["Cosmovitral", "Plaza Fray Andres", "Los Portales"],
    "num_escalas": 1,
    "saltos_totales": 2
  },
  "comparacion_baseline": {
    "prediccion_regla_fija": "transporte_publico",
    "coinciden": true
  },
  "explicacion": "El modelo de ML recomienda transporte_publico con 88% de confianza para un recorrido de 2.4 km en hora pico."
}
```

---

## 4. Desacoplamiento de Ollama en el Asistente

1. **Inyección en `ServicioAsistente`:**
   En `backend/app/modulos/asistente/servicio.py`, se agrega el `ServicioIAKompas`.
2. **Estrategia Fallback / Local First:**
   Si Ollama no está en ejecución localmente o arroja `ErrorOllama`, el asistente intercepta la excepción, consulta al motor `ia_kompas` y genera la respuesta conversacional estructurada acompañada de la tarjeta interactiva de ruta/plan en milisegundos sin arrojar HTTP 503.

---

## 5. Matriz de Trazabilidad: Prácticas Académicas vs Código Real de Producción

| Práctica Original (.rar) | Archivo Real de Producción | Entrada | Salida | Función de Negocio en Kompás |
| :--- | :--- | :--- | :--- | :--- |
| `p01BFS.py` | `busqueda_escalas.py` | Grafo de adyacencia, origen, destino | Ruta de paradas, escalas, saltos | Minimizar transbordos en itinerarios urbanos |
| `p01reglafija.PY` | `reglas_transporte.py` | Distancia, presupuesto, hora, lluvia | Modo recomendado, regla, explicación | Baseline determinista y fallback de seguridad |
| `p02analisisdedatos_a.py` | `pipeline_datos.py` (Etapa A) | `kompas_traslados_crudo.csv` | Resumen de dimensiones y columnas | Ingesta tabular de traslados en Toluca/Metepec |
| `p02explorardatosia_b.py` | `pipeline_datos.py` (Etapa B) | DataFrame crudo | Distribución por clase y promedios | Análisis exploratorio de movilidad urbana |
| `p02problemascalidaddatos_c.py` | `pipeline_datos.py` (Etapa C) | DataFrame crudo con anomalías | Conteo de nulos, duplicados y outliers | Auditoría de integridad de datos turísticos |
| `p02limpiezaguardadodatos_d.py` | `pipeline_datos.py` (Etapa D) | DataFrame auditado | `kompas_traslados_limpio.csv` y `revision` | Imputación por mediana y depuración dual |
| `p02identificacionvariables_e.py` | `pipeline_datos.py` (Etapa E) | DataFrame limpio | Matrices $X$ e $y$ validadas | Selección de características para el clasificador |
| `p03primermodelo.py` | `modelo_predictivo.py` | Matrices $X$ e $y$ (70% train / 30% test) | Modelo entrenado, exactitud y predicción | Inferencia ultrarrápida para el agente móvil |

---

## 6. Resultados de Validación y No Regresión (`pytest`)

Ejecución formal de la suite de pruebas unitarias sobre el entorno virtual:

1. **`backend/tests/test_ia_kompas.py` (12/12 PASSED - 0.49s):**
   * `test_bfs_encuentra_ruta_optima_con_minimas_escalas`: PASSED (0 escalas en arista directa).
   * `test_bfs_con_escalas_intermedias`: PASSED (recorrido multietapa Cosmovitral $\to$ Galerías Metepec).
   * `test_bfs_origen_igual_a_destino`: PASSED (0 saltos).
   * `test_bfs_nodo_inexistente`: PASSED (manejo de nodos ausentes).
   * `test_regla_fija_caminando_distancia_corta_sin_lluvia`: PASSED (activación R1).
   * `test_regla_fija_auto_privado_con_lluvia`: PASSED (activación R2 por condición climática).
   * `test_regla_fija_transporte_publico_distancia_larga_bajo_presupuesto`: PASSED (activación R4).
   * `test_pipeline_datos_genera_audita_y_limpia`: PASSED (detección de nulos/duplicados y depuración a 0 anomalías).
   * `test_modelo_predictivo_entrenamiento_70_30_y_metricas`: PASSED (partición exacta 70% train / 30% test estratificada, exactitud $\ge 0.70$).
   * `test_endpoint_pipeline_estado`: PASSED (FastAPI GET `/api/ia/pipeline-estado` $\to$ HTTP 200).
   * `test_endpoint_recomendar_traslado`: PASSED (FastAPI POST `/api/ia/recomendar-traslado` $\to$ HTTP 200).
   * `test_endpoint_ruta_bfs`: PASSED (FastAPI POST `/api/ia/ruta-bfs` $\to$ HTTP 200).

2. **Pruebas de No Regresión del Sistema:**
   * `backend/tests/test_transporte.py`: **6/6 PASSED** (100% verde).
   * `backend/tests/test_planes_guardados.py`: **24/24 PASSED** (100% verde).
   * **Total acumulado:** 42 pruebas en verde, 0 fallos, 0 regresiones.


