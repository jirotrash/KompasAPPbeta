# Plan de Implementación para Agentes de IA: Módulo `ia_kompas`

> **Instrucciones para el Agente de IA:** Ejecuta este plan de implementación de manera ordenada dentro de una nueva rama de Git (`feat/practicas-ia-modelo`). No rompas ninguna prueba existente en `backend/tests/test_planes_guardados.py` ni en `backend/tests/test_transporte.py`.

---

## Fase 1: Estructura de Archivos a Crear

Crea el nuevo módulo de Inteligencia Artificial y Ciencia de Datos dentro del backend siguiendo la convención en español del proyecto:

```text
backend/
├── data/
│   ├── kompas_traslados_crudo.csv         # Dataset con ruido/nulos para demostrar p02_c
│   └── kompas_traslados_limpio.csv        # Dataset procesado generado por p02_d
├── app/
│   └── modulos/
│       └── ia_kompas/
│           ├── __init__.py
│           ├── esquemas.py                # Modelos Pydantic de entrada/salida para IA
│           ├── p01_grafo_bfs.py           # Adaptación de p01BFS.py
│           ├── p01_regla_fija.py          # Adaptación de p01reglafija.PY
│           ├── p02_pipeline_datos.py      # Unificación modular de p02 (a, b, c, d, e)
│           ├── p03_modelo_predictivo.py   # Adaptación de p03primermodelo.py
│           ├── servicio.py                # Orquestador que conecta p01, p02 y p03
│           └── router.py                  # Endpoints FastAPI bajo /api/ia/...
└── tests/
    └── test_ia_kompas.py                  # Pruebas unitarias de las 3 prácticas adaptadas
```

---

## Fase 2: Especificación Técnica por Archivo

### 1. `backend/app/modulos/ia_kompas/p01_grafo_bfs.py`
* **Objetivo:** Adaptar `p01BFS.py` al grafo de conectividad de zonas y paradas turísticas de Kompas.
* **Requisitos de implementación:**
  * Definir un grafo base de zonas/lugares del dominio de Kompas (y permitir recibir un grafo dinámico construido desde las paradas de un itinerario).
  * Implementar `buscar_ruta_bfs(grafo: dict[str, list[str]], origen: str, destino: str) -> dict`:
    * Utilizar `collections.deque` para la cola FIFO y un conjunto `visitados`.
    * Retornar un diccionario con:
      * `origen`: str
      * `destino`: str
      * `ruta_paradas`: list[str]
      * `num_escalas`: int (`max(0, len(ruta_paradas) - 2)`)
      * `saltos_totales`: int (`max(0, len(ruta_paradas) - 1)`)
      * `algoritmo`: `"BFS (Búsqueda en Anchura)"`

### 2. `backend/app/modulos/ia_kompas/p01_regla_fija.py`
* **Objetivo:** Adaptar `p01reglafija.PY` como sistema experto determinista para recomendar transporte en un traslado de itinerario.
* **Requisitos de implementación:**
  * Implementar `evaluar_traslado_regla_fija(distancia_km: float, presupuesto_mxn: float, hora_dia: int, clima_lluvia: bool = False) -> dict`:
    * Definir reglas claras de negocio:
      1. Si `distancia_km <= 1.5` y `not clima_lluvia` $\rightarrow$ `"caminando"` (justificación: distancia corta y clima favorable).
      2. Si `distancia_km <= 4.0` y `not clima_lluvia` y `presupuesto_mxn < 40` $\rightarrow$ `"bicicleta"` o `"transporte_publico"`.
      3. Si `clima_lluvia` o `(hora_dia in [7, 8, 9, 18, 19, 20] and presupuesto_mxn >= 100)` $\rightarrow$ `"auto_privado"`.
      4. Si `distancia_km > 1.5` y `presupuesto_mxn < 80` $\rightarrow$ `"transporte_publico"`.
      5. Caso por defecto $\rightarrow$ `"auto_privado"` si `presupuesto_mxn >= 80` sino `"transporte_publico"`.
    * Retornar: `modo_recomendado`, `regla_activada`, `explicacion` y `metodo: "regla_fija"`.

### 3. `backend/app/modulos/ia_kompas/p02_pipeline_datos.py`
* **Objetivo:** Integrar de forma trazable las 5 etapas de `p02` (`a`, `b`, `c`, `d`, `e`).
* **Requisitos de implementación:**
  * Función `generar_dataset_crudo_kompas(ruta_csv)` (si no existe): Genera al menos 150 registros realistas de traslados en Kompas que incluyan deliberadamente ~10% de valores nulos en `rating_destino` y `presupuesto_mxn`, 5 filas duplicadas y 3 outliers (`distancia_km < 0` o `duracion_min > 500`) para que la auditoría de calidad tenga casos reales que limpiar.
  * Función `etapa_a_analisis_inicial(df) -> dict`: Resumen de dimensiones, tipos de datos y estadísticos básicos (`p02analisisdedatos_a.py`).
  * Función `etapa_b_exploracion_ia(df) -> dict`: Conteo por `modo_transporte_optimo`, promedios de distancia y tiempo por categoría (`p02explorardatosia_b.py`).
  * Función `etapa_c_auditoria_calidad(df) -> dict`: Reporte exacto de nulos por columna, filas duplicadas y registros fuera de rango (`distancia_km <= 0`, `rating_destino` fuera de $[1, 5]$) (`p02problemascalidaddatos_c.py`).
  * Función `etapa_d_limpieza_y_guardado(df, ruta_salida) -> pd.DataFrame`: Elimina duplicados, filtra distancias inválidas, imputa nulos con la mediana y guarda el CSV limpio (`p02limpiezaguardadodatos_d.py`).
  * Función `etapa_e_identificacion_variables(df_limpio) -> tuple[pd.DataFrame, pd.Series, dict]`: Separa y documenta las columnas `X` (`distancia_km`, `hora_dia`, `es_hora_pico`, `presupuesto_mxn`, `clima_lluvia`, `rating_destino`) y la columna objetivo `y` (`modo_transporte_optimo`) (`p02identificacionvariables_e.py`).

### 4. `backend/app/modulos/ia_kompas/p03_modelo_predictivo.py`
* **Objetivo:** Adaptar `p03primermodelo.py` entrenando un clasificador de `scikit-learn` (ej. `DecisionTreeClassifier` o `RandomForestClassifier`) sobre los datos limpios de la Práctica 2.
* **Requisitos de implementación:**
  * Dividir los datos con `train_test_split(X, y, test_size=0.2, random_state=42)`.
  * Entrenar el modelo y calcular:
    * `exactitud_modelo` (`accuracy_score` del modelo ML en test).
    * `exactitud_regla_fija` (`accuracy_score` aplicando `evaluar_traslado_regla_fija` a cada fila del mismo conjunto de test).
    * Importancia de las variables (`feature_importances_`).
  * Implementar `predecir_traslado(datos: dict) -> dict` que devuelva:
    * `prediccion_modelo`: modo de transporte predicho por el modelo ML.
    * `confianza`: probabilidad máxima (`predict_proba`).
    * `prediccion_regla_fija`: resultado de `p01_regla_fija` para los mismos datos.
    * `coinciden`: booleano indicando si el modelo ML y la regla fija están de acuerdo.

---

## Fase 3: Integración con los Módulos Existentes y Endpoints

1. **Crear endpoints en `backend/app/modulos/ia_kompas/router.py`:**
   * `GET /api/ia/pipeline-estado`: Ejecuta/consulta el reporte de las etapas `p02_a` a `p02_e` y métricas de `p03` vs `p01_regla_fija`.
   * `POST /api/ia/recomendar-traslado`: Recibe `{ distancia_km, presupuesto_mxn, hora_dia, clima_lluvia, rating_destino, origen_id, destino_id }` y responde con la ruta BFS (`p01BFS`), la decisión de la regla fija (`p01reglafija`) y la predicción del modelo (`p03primermodelo`).
2. **Conectar con `backend/app/modulos/rutas/servicio.py`:**
   * Enriquecer las alternativas de transporte con el campo opcional `recomendacion_ia` para que el frontend pueda destacar cuál alternativa sugiere el modelo entrenado.
3. **Actualizar `DOCS/manual-tecnico/`:**
   * Crear `DOCS/manual-tecnico/practicas-ia-modelo.md` documentando cómo se adaptó cada práctica al sistema Kompas.

---

## Fase 4: Verificación y Pruebas (`pytest`)

El agente debe crear y ejecutar `backend/tests/test_ia_kompas.py` validando:
1. Que `buscar_ruta_bfs` encuentre el camino con menos paradas entre dos lugares conectados.
2. Que `evaluar_traslado_regla_fija` devuelva `"caminando"` en distancias cortas sin lluvia y `"auto_privado"` en lluvia con presupuesto suficiente.
3. Que el pipeline `p02` reduzca a `0` los valores nulos y duplicados en el dataset limpio.
4. Que el modelo `p03` entrene correctamente, alcance una exactitud válida ($\ge 0.70$) y retorne predicciones estructuradas.