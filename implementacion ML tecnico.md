# Documento de Implementación Técnica de Machine Learning e IA (`ia_kompas`)

> **Destinatarios:** Equipo de Backend, Frontend Móvil y Auditoría Académica de Inteligencia Artificial.  
> **Arquitectura:** FastAPI (Capas: Router $\to$ Servicio $\to$ Repositorio), Scikit-Learn, Pandas, Numpy, Pydantic v2.  
> **Estándar:** Código y variables en español, preservación de zonas protegidas (`backend/app/ia/`) y no regresión de pruebas.

---

## 1. Arquitectura del Módulo y Trazabilidad Académica

El módulo `ia_kompas` adapta las prácticas de IA y Ciencia de Datos (`practicas_04_11_2026.rar`) al dominio de itinerarios y transporte de **Kompás**. **Sustituye al asistente con Ollama**: el módulo `backend/app/modulos/asistente/` y `backend/app/externos/ollama.py` se retiraron por decisión del equipo (ver §4).

Tiene dos modelos:

| Modelo | Pregunta | Datos de entrenamiento | Algoritmo |
| :--- | :--- | :--- | :--- |
| Transporte (`modelo_predictivo.py`) | ¿Qué medio conviene? | `backend/data/kompas_traslados_*.csv` (**sintético**, generado con semilla 42 con nulos, duplicados y outliers a propósito) | `DecisionTreeClassifier` 70/30 vs regla fija |
| Hábitos (`habitos.py`) | ¿A dónde suele ir el usuario a esta hora? | Colección **`historial_rutas`** de MongoDB (recorridos reales del usuario) | Frecuencia por franja (Laplace) → `KNeighborsClassifier` vs "ruta más frecuente" |

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
│           ├── habitos.py                 # Destinos probables: frecuencia por franja / KNN (lógica pura)
│           ├── repositorio.py             # RepositorioHabitos: lectura de historial_rutas
│           ├── servicio.py                # ServicioIAKompas + ServicioHabitos
│           └── router.py                  # Endpoints REST bajo prefijo /api/ia/...
├── scripts/
│   └── sembrar_habitos_demo.py            # 5 rutas + 3 usuarios + 12 semanas de recorridos demo (demo: true)
└── tests/
    ├── test_ia_kompas.py                  # BFS, regla fija, pipeline, modelo de transporte, endpoints
    └── test_habitos.py                    # Hábitos: lógica pura + endpoints con kompas_test
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
* **Hora pico y lluvia:** son variables del árbol (`es_hora_pico`, `clima_lluvia`) y la duración ya suma +8/+10 min en hora pico. El servicio **no** vuelve a sumar minutos ni reescribe el modo cuando llueve (eso hacía inconsistente `tiempo_estimado_min` con el modo).
* **Consejo de clima:** `servicio.consejo_clima(clima_lluvia, temperatura)` agrega `consejo_clima` a la respuesta (paraguas con lluvia, bloqueador > 26 °C, suéter < 15 °C). Sin `temperatura` no se aconseja por calor o frío.

### 2.5. `habitos.py` + `repositorio.py` (Destinos probables con `historial_rutas`)

**Fuente de datos (sin cambiar el esquema de MongoDB):** el documento que ya escribe `modulos/historial`:

```json
{ "_id": 57, "id_usuario": 3, "id_ruta": 2, "transporte": {"id": 2, "nombre": "Transporte público"},
  "tiempo_estimado": 18, "created_at": "2026-11-03T07:12:00-06:00", "deleted_at": null }
```

**Preparación de datos (`RepositorioHabitos.viajes_del_usuario`):**
1. Filtro `{"id_usuario": id, "deleted_at": None, "created_at": {"$ne": None}}` (borrado lógico y registros sin fecha fuera).
2. Proyección a `id_ruta`, `transporte`, `created_at`; orden `_id` descendente; `limit(LIMITE_VIAJES=300)` (recencia y costo acotado de la validación).
3. `created_at.astimezone(America/Mexico_City)`: toda hora/día se interpreta en hora de Toluca.
4. Salida de dominio `{id_ruta, transporte, momento}` (sin `ObjectId` ni documento crudo).
5. El nombre y la última parada se resuelven con `ServicioRutas.detalle()` (regla de módulos: no se importa el repositorio de otro módulo). Ruta borrada → `"Ruta N (ya no disponible)"`.

**Identificación de variables (como p02 etapa E):**
* $X$ = `caracteristicas(hora_decimal, dia_semana)` = $[\sin\frac{2\pi h}{24}, \cos\frac{2\pi h}{24}, \sin\frac{2\pi d}{7}, \cos\frac{2\pi d}{7}, \text{laborable}]$. La codificación circular hace que 23:30 y 00:30, o domingo y lunes, queden cerca.
* $y$ = `id_ruta`.

**Selección automática del método según $n$ (viajes del usuario):**

| $n$ | `estado` / `metodo` | Cálculo |
| :--- | :--- | :--- |
| $n < 5$ (`MIN_VIAJES`) | `datos_insuficientes` / `null` | No se predice (regla 1 de CONTEXTO.md: no inventar). |
| $5 \le n < 20$ (`UMBRAL_KNN`) | `ok` / `frecuencia_franja` | $P(r \mid f, t) = \dfrac{c_{f,t}(r) + \alpha\,P(r)}{N_{f,t} + \alpha}$, con $f$ = franja (madrugada 0–5, mañana 6–11, tarde 12–18, noche 19–23), $t$ = laborable/fin de semana, $\alpha = 1$ y $P(r)$ la frecuencia global. |
| $n \ge 20$ | `ok` / `knn` | `KNeighborsClassifier(n_neighbors=min(7, n), weights="distance")` → `predict_proba`. |

**Evaluación (como p03 contra la regla fija):** con KNN se calcula leave-one-out (`cross_val_score(..., cv=LeaveOneOut())`) y la exactitud del baseline "ruta más frecuente del resto". Se reportan `exactitud_validacion` y `exactitud_baseline`. Con la rutina de `test_habitos.py` (4 semanas) el KNN supera al baseline; con el sembrador demo (12 semanas, con 10 % de ruido): **0.96 vs 0.39** (ver §7).

**Autonomía:** el modelo se reentrena en cada consulta con los últimos 300 viajes (no hay artefacto persistido que se quede viejo). La hora y el día los manda el dispositivo; si no llegan, se usa la hora de Toluca del servidor.

**Salida por destino:** `id_ruta`, `nombre`, `ultima_parada`, `probabilidad`, `viajes` y `hora_habitual` (la mediana de la hora de salida, HH:MM). Máximo 3 destinos.

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
  "explicacion": "El modelo de ML recomienda transporte_publico con 88% de confianza para un recorrido de 2.4 km en hora pico.",
  "consejo_clima": null
}
```

Campo de entrada opcional **nuevo**: `temperatura` (°C, de −20 a 50). Campo de salida **nuevo**: `consejo_clima` (`string | null`). Solo se agregaron campos: los clientes actuales no se rompen.

### `GET /api/ia/destinos-probables?hora=7&dia=1` 🔒 (nuevo)
Requiere `Authorization: Bearer <token>`; el usuario sale del JWT (nunca del query). `hora` va de 0 a 23 y `dia` de 0 a 6 (0 = lunes, como `datetime.weekday()`); los dos son opcionales.

```json
{
  "estado": "ok",
  "metodo": "knn",
  "hora_consulta": 7,
  "dia_consulta": "martes",
  "franja": "manana",
  "viajes_analizados": 60,
  "minimo_viajes": 5,
  "destinos": [
    {"id_ruta": 4, "nombre": "Ruta UTVT", "ultima_parada": "UTVT", "probabilidad": 0.87, "viajes": 27, "hora_habitual": "07:04"}
  ],
  "exactitud_validacion": 1.0,
  "exactitud_baseline": 0.45,
  "explicacion": "Un modelo KNN entrenado con tus 60 recorridos compara la hora y el día de hoy con tus viajes anteriores. ...",
  "aviso": "Estimación a partir de tus recorridos guardados en Kompás; no es un dato verificado."
}
```
Con menos de 5 recorridos: `estado: "datos_insuficientes"`, `metodo: null` y `destinos: []`. Sin token: **401**.

### `GET /api/ia/mis-habitos` 🔒 (nuevo)
Solo cuenta lo que hay en el historial (no estima tráfico):
```json
{
  "total_viajes": 60,
  "rutas_frecuentes": [{"id_ruta": 4, "nombre": "Ruta UTVT", "ultima_parada": "UTVT", "viajes": 27}],
  "transportes": {"Transporte público": 50, "Taxi/App": 10},
  "por_franja": {"manana": 27, "tarde": 23, "noche": 10},
  "por_dia": {"lunes": 10, "martes": 11}
}
```

### Integración en la app móvil

**Ciclo completo:** el usuario elige una opción en autobús → `POST /api/historial` → `historial_rutas` → el modelo se reentrena en la siguiente consulta → Asistente e Inicio.

* **`app/src/services/api.ts`:**
  * `destinosProbables(momento, hora?)` manda la hora y el día del dispositivo (`diaApi()`: 0 = lunes); `hora` sirve para consultar otra franja.
  * `misHabitos()` consulta `GET /api/ia/mis-habitos`.
  * `guardarRecorrido({id_ruta, transporte, tiempo_estimado})` resuelve `id_transporte` con `listarTransportes()` (`GET /api/transportes`, una vez por sesión) y llama a `POST /api/historial`.
  * En modo mock las tres regresan `null`, porque no hay historial real. `consultarClima()` lee wttr.in y regresa `null` si no responde (no se inventa el clima).
  * Se eliminaron `estadoAsistente`, `listarConversaciones`, `crearConversacion`, `obtenerConversacion`, `enviarMensaje` y `borrarConversacion`, y `TIEMPO_LIMITE_ASISTENTE_MS`.
* **`app/src/app/(tabs)/asistente/index.tsx` (pestaña Asistente, ícono `reloj`):**
  * `ChipGroup` para elegir la hora: Ahora / 7:00 / 15:00 / 20:00.
  * `TarjetaPrediccion`.
  * Tarjeta "Cómo lo calculé" con `metodo`, `exactitud_validacion` y `exactitud_baseline`.
  * Tarjeta "Tus hábitos" con barras de `rutas_frecuentes` y `por_franja`, y el texto de `transportes`. Las barras usan solo los tokens `$suave` y `$primario`.
  * Recarga con `useFocusEffect` al volver a la pestaña.
  * `_layout.tsx` solo declara `index`.
* **`app/src/app/buscar.tsx` (`verEnMapa`):** si la alternativa tiene `id_ruta` (o, en las combinadas, el `id_ruta` del último tramo `autobus`) y no es de ejemplo, guarda el recorrido con `transporte: "Transporte público"` y `tiempo_estimado` = caminata + espera + trayecto. Es *fire-and-forget*: si falla, la navegación sigue.
* **`app/src/components/TarjetaPrediccion.tsx`:** la tarjeta "A esta hora sueles ir a…" con probabilidad, hora habitual, viajes, otros destinos, el aviso de estimación y el botón **¿Cómo llego?** (`/buscar?q=`). Usa solo tokens del tema, según COLORIMETRIA.md.
* **`app/src/app/(tabs)/index.tsx` (Inicio):** la misma tarjeta, con sesión iniciada, y la píldora de temperatura con el consejo (mismo criterio que `consejo_clima()`).
* **Eliminados:** `asistente/[id].tsx` (chat), `components/TarjetaAsistente.tsx`, `services/mock/asistente.ts` y los tipos `EstadoAsistente`, `TarjetaAsistente`, `MensajeChat`, `Conversacion`, `ResumenConversacion`, `RespuestaMensaje` y `PuntoNombrado` de `types/dominio.ts`.

---

## 4. Retiro del asistente con Ollama

**Decisión del equipo:** la pestaña **Asistente** se conserva, pero ya no es un chat con un LLM: es el machine learning de `ia_kompas`, que **aprende del historial del usuario**. Se retiraron:
* Backend: `backend/app/modulos/asistente/` (router, servicio, herramientas, prompt, repositorio y esquemas), `backend/app/externos/ollama.py` y el registro de `asistente.router` en `main.py`. Queda una copia de referencia, `ollama.txt`, que no se importa.
* Pruebas: `backend/tests/test_asistente.py`.
* App: el chat y sus piezas (ver "Integración en la app móvil" en §3).

**Lo que no cambia:** el sistema experto de Einar (`backend/app/ia/`, R01–R20) sigue evaluando los planes. `ia_kompas` no lo reemplaza; trabaja a su lado.

**Pendientes del retiro:**
* `CONTEXTO.md` (§1 y §4) todavía menciona Ollama como parte del stack.
* El dashboard y `sembrar_actividad_demo.py` todavía leen o generan la colección `conversaciones`. Esos datos históricos se conservan.
* Hay que borrar `backend/sembrar_datos_ml.py` (script de Gemini con un esquema que no es el real) y `backend/app/externos/ollama.txt`.
* En `kompas` local quedan 4 documentos del script de Gemini (`usuario_id: "kevin_eduardo"`, sin `id_usuario`). El modelo los ignora, pero el dashboard los cuenta. Se borran con `db.historial_rutas.deleteMany({usuario_id: "kevin_eduardo"})`.

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
| `p03primermodelo.py` | `modelo_predictivo.py` | Matrices $X$ e $y$ (70% train / 30% test) | Modelo entrenado, exactitud y predicción | Inferencia ultrarrápida del medio de transporte |
| `p02` (c, d, e) + `p03` sobre datos reales | `repositorio.py` + `habitos.py` | `historial_rutas` del usuario | Destinos probables, exactitud LOO vs baseline | Predicción autónoma del destino según hora y día |

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

2. **`backend/tests/test_habitos.py` (7/7 PASSED):**
   * `test_franjas_y_caracteristicas_circulares`: franjas y cercanía de 23:30 con 00:30.
   * `test_sin_suficientes_viajes_no_inventa_destino`: menos de 5 viajes regresa `datos_insuficientes`.
   * `test_frecuencia_por_franja_con_pocos_datos`: con 11 viajes predice la escuela en la mañana y el centro en la tarde.
   * `test_knn_aprende_la_rutina_y_supera_al_baseline`: con 44 viajes el KNN acierta mañana, tarde y sábado, y supera al baseline.
   * `test_resumen_de_habitos_solo_cuenta`: conteos por ruta, transporte y día.
   * `test_destinos_probables_requiere_sesion`: sin token regresa 401.
   * `test_destinos_probables_desde_historial_real`: integración contra `kompas_test`, con rutas y recorridos reales en MongoDB y ruta + última parada resueltas. Limpia lo que crea.

3. **Pruebas de No Regresión del Sistema (corrida del 5 de noviembre de 2026):**
   * `backend/tests/test_transporte.py` y `backend/tests/test_planes_guardados.py`: en verde.
   * `app/tests/transporte.test.cjs`: **13/13** en verde. `tsc --noEmit` y `expo lint` sin errores.
   * Suite completa del backend (ya sin `test_asistente.py`, ver §4): **214 passed, 2 failed**. Los 2 fallos son de `test_itinerarios.py` y ya existían antes de estos cambios: `itinerarios` guarda `categoria: "Comer"` y el validador de `planes` exige el enum en minúsculas (`"comer"`).

---

## 7. Datos de entrenamiento y verificación con la base `kompas`

### 7.1. `scripts/sembrar_habitos_demo.py`

```powershell
python -m scripts.sembrar_habitos_demo                # 12 semanas (por defecto)
python -m scripts.sembrar_habitos_demo --semanas 20
python -m scripts.sembrar_habitos_demo --borrar       # borra recorridos, usuarios y rutas de este script
```

* **Marca:** todo lleva `demo: true` y `origen_demo: "habitos"`. `--borrar` solo toca lo que tiene las dos marcas, así que no afecta a `sembrar_actividad_demo`. Volver a correrlo primero borra sus recorridos anteriores (es reproducible, con semilla 31).
* **Rutas:** si hay menos de 5 rutas activas, crea las rutas "Demo · …" con trazo densificado (`densificar()`, cada ~150 m), parada inicial y final y validación de zona piloto. **Son trazos de referencia, no líneas reales**; el prefijo "Demo ·" lo deja claro en la UI.
* **Usuarios:** usa demo@kompas.mx y crea `habitos.oficina@kompas.mx` y `habitos.nocturno@kompas.mx` con contraseña aleatoria que nadie conoce.
* **Rutinas** (`PERFILES`): tuplas `(ruta, días, hora_min, hora_max, transporte, probabilidad)`. La hora se sortea uniforme en el rango.
* **Ruido:** con `PROBABILIDAD_RUIDO = 0.10` por día, hay un viaje a una ruta y una hora (6–22) al azar.
* **`tiempo_estimado`:** distancia por calles × min/km del transporte × U(0.85, 1.25).
* Al final corre `ajustar_contadores()`.

**Resultado en `kompas` local (corrida del 5 de noviembre de 2026):**

| Usuario | Recorridos | Rutina |
| :--- | ---: | :--- |
| demo@kompas.mx | 148 | R0 entre semana 6:30–7:30 · R1 entre semana 14:30–16:00 · R2 vie/sáb 18:30–21:00 (Taxi/App) · R3 dom 10:00–12:30 · R4 lun/mié 19:30–20:30 (Caminando) |
| habitos.oficina@kompas.mx | 116 | R4 entre semana 8–9 · R2 entre semana 18:00–19:30 · R3 sáb 11–13 (Taxi/App) |
| habitos.nocturno@kompas.mx | 44 | R2 mar/jue 21:00–22:30 (Taxi/App) · R1 sáb 9–11 · R0 vie 16:00–17:30 |

### 7.2. Verificación de punta a punta

**a) HTTP como la app** (`TestClient` contra `kompas`: `POST /api/auth/login` → `GET /api/ia/destinos-probables`):

| Consulta (demo@kompas.mx) | Destino principal | Probabilidad | Método | `hora_habitual` |
| :--- | :--- | ---: | :--- | :--- |
| martes 7:00 (`hora=7&dia=1`) | UTVT | 1.00 | knn | 07:00 |
| jueves 15:00 | Centro de Lerma | 1.00 | knn | 15:04 |
| viernes 20:00 | Metepec | 0.61 | knn | 19:28 |
| domingo 11:00 | San Mateo Atenco | 1.00 | knn | 11:27 |

* Leave-one-out sobre 148 viajes: **KNN 0.96 contra el baseline 0.39**.
* `mis-habitos`: `por_franja` = mañana 64, tarde 53, noche 31; `transportes` = Transporte público 115, Taxi/App 18, Caminando 15.
* Sin token: **401**.

**b) Personalización:** con la misma consulta (lunes 8:00), al estudiante le predice R0 (UTVT) y al oficinista R4 (Toluca oriente). Cada usuario se entrena solo con su `id_usuario`.

**c) Holdout temporal (la evidencia más fuerte):** se ordenan los viajes por `created_at`, se entrena con el 75 % más antiguo y se predice el 25 % más reciente con `predecir_destinos(entreno, hora, día, minuto)`. El baseline es la ruta más frecuente del entrenamiento.

| Usuario | Entrenamiento / prueba | Exactitud del modelo | Exactitud del baseline |
| :--- | :---: | ---: | ---: |
| estudiante | 111 / 37 | **0.95** | 0.38 |
| oficina | 87 / 29 | **0.93** | 0.41 |
| nocturno | 33 / 11 | **0.91** | 0.64 |

### 7.3. Limitaciones conocidas
* **No hay clase "no viaja".** A una hora sin historial (por ejemplo, el nocturno un lunes a las 8:00), el KNN regresa el vecino más cercano. Mejora pendiente: un umbral de distancia o de probabilidad mínima para responder "a esta hora no sueles salir".
* **Solo se registran las opciones en autobús**: caminata y taxi no tienen `id_ruta`. La etiqueta $y$ es la ruta, no un lugar.
* Los datos de §7.1 son **sintéticos**. Las cifras de §7.2 muestran que el método aprende rutinas; la exactitud con usuarios reales se medirá cuando `historial_rutas` acumule recorridos guardados desde la app.


