# Contexto de Integración: Prácticas de IA y Ciencia de Datos en KompasAPPbeta

> **Propósito de este documento:** Este archivo provee el contexto técnico, de dominio y arquitectónico necesario para que cualquier Agente de IA (Claude, Cursor, Copilot, etc.) comprenda las prácticas académicas (`practicas_04_11_2026.rar`) y las adapte e integre de forma nativa en el proyecto **KompasAPPbeta**.

---

## 1. Objetivo General de la Integración

Adaptar los ejercicios base de búsqueda en grafos, sistemas basados en reglas, limpieza/análisis de datos y entrenamiento de un primer modelo de Machine Learning para que funcionen como un **motor inteligente real** dentro del backend de **KompasAPPbeta** (FastAPI + Python), conectándose con los módulos recién integrados de **Mis Planes** (`backend/app/modulos/itinerarios/`) y **Transporte** (`backend/app/modulos/rutas/`).

**Regla crítica académica y de arquitectura:**
No se deben subir los scripts `.py` originales aislados ni con datos genéricos de juguete. Cada práctica debe transformarse en un submódulo funcional aplicado a **lugares turísticos, paradas de itinerarios, cálculo de rutas, costos y recomendación de modos de transporte**.

---

## 2. Inventario de las Prácticas Originales (`practicas_04_11_2026.rar`)

El paquete original consta de **7 scripts en Python** divididos en 3 fases:

### Fase 1: Búsqueda y Heurísticas (`p01`)
1. **`p01BFS.py` (Búsqueda en Anchura - Breadth-First Search):**
   * **Funcionamiento original:** Implementa el algoritmo BFS utilizando una cola (`collections.deque`) para explorar un grafo no ponderado nivel por nivel y encontrar la ruta con el menor número de saltos/aristas entre un nodo inicial y un nodo objetivo.
   * **Adaptación requerida en KompasAPPbeta:**
     * Integrar en el motor de rutas (`backend/app/modulos/rutas/` o `backend/app/modulos/ia_kompas/`).
     * Los nodos del grafo deben representar **lugares turísticos / estaciones / zonas del itinerario** y las aristas las **conexiones directas de traslado**.
     * **Caso de uso en Kompas:** Encontrar la ruta con el **menor número de transbordos o escalas intermedias** entre dos actividades de un plan, sirviendo además como comparativa algorítmica frente a la búsqueda DFS previamente documentada en el repositorio.

2. **`p01reglafija.PY` (Sistema Basado en Reglas Fijas / Baseline Heurístico):**
   * **Funcionamiento original:** Evalúa entradas mediante bloques condicionales deterministas (`if / elif / else`) para clasificar o emitir una recomendación sin aprendizaje estadístico.
   * **Adaptación requerida en KompasAPPbeta:**
     * Construir el **Recomendador Heurístico Base (Baseline)** para el módulo de **Transporte** y **Mis Planes**.
     * Evaluar variables del dominio de Kompas: `distancia_km`, `presupuesto_disponible`, `clima_lluvia`, `hora_pico` y `tiempo_disponible_min`.
     * **Salida:** Recomendar el modo de traslado (`caminando`, `transporte_publico`, `auto_privado`, `bicicleta`) y clasificar la viabilidad del traslado (`optimo`, `ajustado`, `no_recomendado`).
     * **Rol en el sistema:** Actuar como *fallback* determinista cuando el modelo predictivo no tenga confianza suficiente y como *baseline* de comparación frente al modelo de la Práctica 3.

---

### Fase 2: Pipeline de Datos y Calidad (`p02`)
Los 5 scripts de la serie `p02` conforman un pipeline secuencial de ingeniería de datos con `pandas` y `numpy`:

3. **`p02analisisdedatos_a.py` (Carga y Resumen Estadístico):**
   * **Original:** Carga de dataset y generación de estadísticas descriptivas básicas (`head`, `info`, `describe`).
   * **Adaptación Kompas:** Carga de registros históricos/sintéticos de **traslados e itinerarios de usuarios en Kompas** (conectado con datos de `google_places.py` y planes guardados).

4. **`p02explorardatosia_b.py` (Exploración de Distribuciones y Correlaciones):**
   * **Original:** Análisis exploratorio de datos (EDA), revisión de distribuciones por categoría y relación entre variables.
   * **Adaptación Kompas:** Analizar la relación entre `distancia_km`, `hora_dia`, `rating_lugar`, `nivel_precio_lugar`, `presupuesto_usuario` y el `tiempo_traslado_min` o `modo_transporte`.

5. **`p02problemascalidaddatos_c.py` (Auditoría de Calidad de Datos):**
   * **Original:** Detección programática de valores nulos (`NaN`), registros duplicados, valores fuera de rango (*outliers*) e inconsistencias de formato.
   * **Adaptación Kompas:** Detectar problemas reales al consumir lugares y rutas:
     * Lugares de Google Places sin `rating` o sin `price_level` (`NaN`).
     * Distancias negativas o iguales a `0` entre paradas distintas.
     * Tiempos de traslado extremos o coordenadas fuera del polígono de la ciudad.
     * Paradas duplicadas en un mismo itinerario.

6. **`p02limpiezaguardadodatos_d.py` (Imputación, Limpieza y Persistencia):**
   * **Original:** Eliminación de duplicados, imputación de valores faltantes (media/mediana/moda), filtrado de anomalías y exportación a CSV limpio.
   * **Adaptación Kompas:**
     * Imputar `rating` faltante con la mediana de la categoría del lugar.
     * Imputar `nivel_precio` faltante con la moda según el tipo de actividad.
     * Recortar o filtrar distancias/tiempos inválidos.
     * Guardar el dataset procesado en `backend/data/kompas_traslados_limpio.csv`.

7. **`p02identificacionvariables_e.py` (Selección de Features $X$ y Target $y$):**
   * **Original:** Separación formal de variables independientes (predictoras $X$) y variable dependiente (objetivo $y$), codificación de variables categóricas.
   * **Adaptación Kompas:**
     * **Variables Predictoras ($X$):**
       * `distancia_km` (float)
       * `hora_dia` (int, 0-23)
       * `es_hora_pico` (int/bool, 0 o 1)
       * `presupuesto_mxn` (float)
       * `clima_lluvia` (int/bool, 0 o 1)
       * `num_paradas_itinerario` (int)
       * `rating_promedio_destino` (float, 1.0 - 5.0)
     * **Variable Objetivo ($y$):**
       * **Modo Clasificación:** `modo_transporte_optimo` (`caminando`, `transporte_publico`, `auto_privado`).
       * **Modo Regresión (opcional/secundario):** `duracion_estimada_min` (float).

---

### Fase 3: Modelado Predictivo (`p03`)
8. **`p03primermodelo.py` (Entrenamiento, Evaluación e Inferencia del Primer Modelo):**
   * **Funcionamiento original:** Toma las matrices $X$ y $y$, divide el conjunto en entrenamiento y prueba (`train_test_split`), entrena un modelo supervisado con `scikit-learn`, calcula métricas de desempeño (`accuracy_score` / `mean_squared_error` / matriz de confusión) y realiza predicciones sobre nuevos casos.
   * **Adaptación requerida en KompasAPPbeta:**
     * Entrenar el modelo sobre `kompas_traslados_limpio.csv`.
     * Comparar explícitamente el rendimiento del **Modelo ML (`p03`)** contra la **Regla Fija (`p01reglafija`)** sobre el mismo conjunto de prueba.
     * Exponer una función de inferencia `predecir_transporte_kompas(datos_entrada)` que pueda ser invocada desde el servicio de `rutas` e `itinerarios` en FastAPI.

---

## 3. Relación con la Arquitectura Actual del Repositorio

El agente de IA debe respetar la estructura existente en `KompasAPPbeta`:

* **`backend/app/modulos/rutas/`**:
  * Ya cuenta con `esquemas.py` y `servicio.py` (integrados en la rama de Transporte).
  * Aquí se debe conectar el buscador BFS (`p01BFS`) y la comparación entre `regla_fija` (`p01reglafija`) y `modelo_ia` (`p03primermodelo`).
* **`backend/app/modulos/itinerarios/`**:
  * Ya cuenta con `esquemas.py`, `router.py`, `servicio.py`, `repositorio.py` y `recuperacion.py` (integrados en la rama de Mis Planes).
  * Al generar o recuperar un plan guardado, se puede enriquecer cada traslado entre paradas con la recomendación del modelo y el número mínimo de escalas BFS.
* **`app/src/` (Frontend React Native / Expo)**:
  * En `TarjetaTransporte.tsx`, `LineaRecorrido.tsx` o `TarjetaAsistente.tsx` se puede mostrar una insignia indicando si la recomendación provino del **Modelo IA de Kompas** o de la **Regla Rápida**, junto con el cálculo de escalas.