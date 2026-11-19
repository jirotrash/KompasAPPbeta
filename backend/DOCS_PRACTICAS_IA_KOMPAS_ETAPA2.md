# Documentacion Tecnica y Guia de Integracion: Practicas de IA Avanzada (P10 a P27) en KompasAPPbeta

> **Fecha de Implementacion y Registro:** 18 de noviembre de 2026  
> **Proyecto:** KompasAPPbeta - Sistema Inteligente de Movilidad y Transporte Metropolitano  
> **Modulo:** Machine Learning, Deep Learning y Big Data en Produccion  

---

## 1. Resumen Ejecutivo del Sistema Multi-Modelo

El backend de Kompas evoluciona de modelos tabulares aislados hacia una arquitectura holistica de Inteligencia Artificial en produccion dividida en 4 pilares:

```text
                                       +-------------------------------------------------------------+
                                       |             ARQUITECTURA DE IA KOMPASAPPBETA                |
                                       +-------------------------------------------------------------+
                                                                      |
                   +----------------------------------+---------------+----------------------------------+
                   |                                  |                                  |
                   v                                  v                                  v
+--------------------------------------+ +--------------------------------+ +----------------------------------+
|      MOTOR DE RECOMENDACIONES        | |   DEEP LEARNING CONVOLUCIONAL  | |      BIG DATA & DATA LAKE        |
|          MULTIMODELO (P14)           | |         1D PYTORCH (P24, P27)  | |         APACHE SPARK (P20-P22)   |
+--------------------------------------+ +--------------------------------+ +----------------------------------+
| 1. Random Forest (P11): Modo optimo  | | 1. CNN 1D Clasificacion (P24): | | 1. Generador Sintetico (P20):    |
| 2. K-Means (P12): 4 Perfiles viajer. | |    Deteccion de Congestion     | |    50,000 micro-eventos          |
| 3. PCA 2D (P13): Proyeccion plana    | | 2. CNN 1D Regresion (P27):     | | 2. Agregaciones PySpark (P21):   |
| 4. Reglas Directivas de Movilidad    | |    ETA continuo en minutos     | |    Analisis de cuellos de botella|
| 5. Persistencia Atlas (P15, P16, P19)| | 3. Benchmark ML vs DL (P25)    | | 3. Conector Spark-Atlas (P22)    |
+--------------------------------------+ +--------------------------------+ +----------------------------------+
                   |                                  |                                  |
                   +----------------------------------+---------------+----------------------------------+
                                                                      |
                                                                      v
                                       +-------------------------------------------------------------+
                                       |              ARQUITECTURA DUAL DE DASHBOARDS                |
                                       |  1. Produccion: React + TypeScript + Vite (frontend/)       |
                                       |  2. Evaluacion Academica: Streamlit + Plotly (backend/)     |
                                       +-------------------------------------------------------------+
```

---

## 2. Inventario de Archivos Creados e Implementados

| Practica | Archivo Implementado | Ubicacion en KompasAPPbeta | Endpoint / Interfaz |
| :--- | :--- | :--- | :--- |
| **P14** | `p14_motor_recomendaciones.py` | `backend/app/modulos/ia_kompas/p14_motor_recomendaciones.py` | `POST /api/ia/motor-recomendacion-integral` |
| **P15 - P16 - P19** | `p16_consultas_analiticas.py` | `backend/app/modulos/ia_kompas/p16_consultas_analiticas.py` | `GET /api/ia/analitica/reporte-clusters`<br>`GET /api/ia/analitica/horas-pico` |
| **P17 - P18 - P19** | `app_dashboard_movilidad.py` | `backend/dashboard_admin/app_dashboard_movilidad.py` | Consola Streamlit (Puerto 8501) |
| **Frontend React** | `api.ts` | `frontend/src/modulos/dashboard/api.ts` | Cliente API REST en TypeScript |
| **P20** | `p20_generador_traslados_masivos.py` | `backend/bigdata_spark/p20_generador_traslados_masivos.py` | CLI Generador Batch (50,000 registros) |
| **P21** | `p21_procesamiento_spark.py` | `backend/bigdata_spark/p21_procesamiento_spark.py` | PySpark DataFrame API + Parquet |
| **P22** | `p22_carga_spark_atlas.py` | `backend/bigdata_spark/p22_carga_spark_atlas.py` | Conector Spark -> MongoDB Atlas (Upsert) |
| **P23 - P24** | `p24_red_cnn1d_clasificacion.py` | `backend/app/modulos/ia_kompas/p24_red_cnn1d_clasificacion.py` | `POST /api/ia/deep-learning/clasificar-congestion` |
| **P25** | `p25_comparacion_modelos_dl.py` | `backend/app/modulos/ia_kompas/p25_comparacion_modelos_dl.py` | `GET /api/ia/deep-learning/comparar-modelos` |
| **P26 - P27** | `p27_red_cnn1d_eta_regresion.py` | `backend/app/modulos/ia_kompas/p27_red_cnn1d_eta_regresion.py` | `POST /api/ia/deep-learning/predecir-eta` |
| **Serializacion** | `entrenar_y_serializar_ia_kompas.py` | `backend/scripts/entrenar_y_serializar_ia_kompas.py` | Generador de artefactos `.joblib` |
| **Pruebas** | `test_ia_etapa2.py` | `backend/tests/test_ia_etapa2.py` | PyTest Suite (Pruebas unitarias completas) |

---

## 3. ¿Que Genera el Generador de Datos Masivos (`p20`)?

El script `p20_generador_traslados_masivos.py` genera un conjunto de **50,000 registros sinteticos de telemetria de traslados urbanos** que simulan el trafico real del area metropolitana:

### Estructura de Columnas Generadas:
1. **`id_viaje` (string):** Clave unica de identificacion del recorrido (`VI-TR-000001` a `VI-TR-050000`).
2. **`id_usuario` (string):** Identificador anonimizado del viajero (`USR-1000` a `USR-9999`) para agrupar trayectos recurrentes y permitir `GroupShuffleSplit`.
3. **`hora_dia` / `hora_entera` (float/int):** Horario del viaje generado con **distribucion bimodal real**:
   - 40% de viajes concentrados en la **hora pico matutina** (7:00 a 9:30 hrs).
   - 40% de viajes concentrados en la **hora pico vespertina** (18:00 a 20:30 hrs).
   - 20% en horas valle diurnas.
4. **`distancia_km` (float):** Distancia recorrida modelada con una **distribucion Gamma** ($\text{shape}=2.5, \text{scale}=4.0$), abarcando desde traslados de ultima milla (0.8 km) hasta viajes interurbanos metropolitanos (hasta 45 km).
5. **`medio_transporte` (string):** Distribucion basada en las proporciones de aforo modal metropolitano:
   - Metro: 35%
   - Metrobus: 25%
   - Autobus concesionado: 20%
   - Bicicleta compartida (EcoBici): 8%
   - Auto por aplicacion (Uber/Didi): 7%
   - Caminata: 5%
6. **`costo_mxn` (float):** Tarifa real en pesos mexicanos (Metro \$5, Metrobus \$6, Autobus \$12, Bici \$0, Auto App \$45 base + \$1.50/km).
7. **`duracion_min` (float):** Tiempo de traslado calculado a partir de la velocidad media del modo, penalizado con un factor de congestion de $+35\%$ en horas pico y ruido gaussiano.
8. **`retraso_demora` (int: 0 o 1):** Etiqueta calculada matematicamente: `1` si el viaje excedio en mas del 25% el tiempo normal; `0` si fue fluido.

### Proposito Real del Generador en Kompas:
Permite a Kompas disponer de un **Data Lake sintetico masivo** para entrenar redes convolucionales profundas (CNN 1D), validar consultas analiticas en MongoDB Atlas y poner a prueba los pipelines distribuidos de **Apache Spark** antes de contar con telemetria de millones de usuarios en vivo.

---

## 4. Funcion Real de Todo lo Implementado en KompasAPPbeta

El sistema cubre las cuatro etapas de la experiencia de movilidad:

```text
               CICLO DE VIDA REAL DE UN VIAJE EN KOMPASAPPBETA
               
  [ FASE 1: ANTES DE SALIR ]  ──►  [ FASE 2: EN EL TRAYECTO ]  ──►  [ FASE 3: EN LA NUBE Y BACKOFFICE ]
               │                                  │                                     │
               ▼                                  ▼                                     ▼
     Motor Recomendador (P14)           Deep Learning CNN (P24/P27)           Big Data y Analitica (P16/P21)
  * Sabe quien eres (Cluster).       * Monitorea las paradas vivas.        * Persiste en 3 colecciones Atlas.
  * Predice el modo optimo (RF).     * Alerta cuellos de botella (P24).    * Agrega millones de datos en Spark.
  * Emite directivas de ruta.        * Recalcula tu ETA continuo (P27).    * Dashboard administrativo en vivo.
```

### Fase 1: Planificacion Inteligente Antes de Salir (P14)
* **Que hace:** El usuario abre Kompas y consulta como llegar a su destino.
* **Funcion real:** El motor orquesta tres modelos:
  1. Identifica el **Perfil del Viajero** con K-Means: *Economico, Expres, Larga Distancia o Multimodal*.
  2. Predice el **Modo de Transporte Optimo** con Random Forest.
  3. Mapea sus coordenadas en **PCA 2D**.
  4. Genera directivas reales: si es hora pico y llueve, le advierte que el autobus colapsara y le sugiere tomar el Metrobus en carril confinado o Metro, adelantando su salida 15 minutos.

### Fase 2: Monitoreo en Tiempo Real Durante el Viaje (P24 y P27)
* **Que hace:** Mientras el usuario va en trayecto, la aplicacion recibe la velocidad de los tramos y paradas consecutivas.
* **Funcion real:**
  - **Deteccion de Congestion (CNN 1D - P24):** Si la velocidad cae de 45 km/h a 12 km/h y la ocupacion llega al 95%, la red clasifica la secuencia como **"Cuello de Botella Critico"** y sugiere transbordar de inmediato.
  - **Estimacion de ETA Continuo (CNN 1D - P27):** Calcula el tiempo exacto en minutos restantes con margen de error inferior a $\pm 1.8$ minutos utilizando perdida Huber (`SmoothL1Loss`).

### Fase 3: Persistencia y Auditoria en la Nube (P15, P16 y P19)
* **Que hace:** Almacena cada evento en MongoDB Atlas.
* **Funcion real:** Vincula tres colecciones NoSQL:
  1. `viajeros`: Registro del perfil y habitos.
  2. `traslados_registrados`: Distancias, costos y horas del recorrido.
  3. `evaluaciones_ia_kompas`: Historial de predicciones, cluster asignado y recomendaciones.
  Permite al sistema saber que usuarios ahorraron tiempo gracias a los consejos de la IA.

### Fase 4: Analisis Distribuido y Control Gerencial (P20 a P22, Dashboards)
* **Que hace:** Procesa grandes volumenes de datos con Apache Spark y muestra metricas ejecutivas.
* **Funcion real:**
  - **Apache Spark:** Corre por lotes nocturnos para recalcular que avenidas presentan las mayores tasas de demora sin saturar la base de datos transaccional de la app.
  - **Dashboard:** Operadores y autoridades de transporte visualizan mapas 2D de clusters, curvas de demanda y pueden probar simulaciones de viajes en caliente.

---

## 5. Arquitectura Dual de Dashboards: React vs Streamlit

Para satisfacer tanto la aplicacion web real como la evaluacion de la universidad, se disenaron dos componentes:

1. **Dashboard de Produccion en React (`frontend/src/modulos/dashboard`):**
   - Construido con **React 18 + Vite + TypeScript + Tailwind CSS**.
   - Consume directamente la API REST del backend (`/api/ia`) mediante las funciones tipadas en [api.ts](file:///C:/Users/kevin/Downloads/KompasAPPbeta/frontend/src/modulos/dashboard/api.ts).
   - Muestra las graficas de Machine Learning y Deep Learning integradas dentro del diseno oficial de Kompas.

2. **Dashboard de Evaluacion Academica en Streamlit (`backend/dashboard_admin/app_dashboard_movilidad.py`):**
   - Construido en **Python con Streamlit y Plotly Express**.
   - Reproduce fielmente las practicas **P17, P18 y P19** de la universidad.
   - Permite una ejecucion inmediata con un solo comando para defensas en clase:
     ```powershell
     cd C:\Users\kevin\Downloads\KompasAPPbeta\backend
     .\venv\Scripts\streamlit run dashboard_admin/app_dashboard_movilidad.py
     ```

---

## 6. Guia de Preguntas y Respuestas para Evaluacion / Examen

### P1: "¿Por que el codigo no se copio tal cual de SmartAcademy?"
- **Respuesta:** "Porque SmartAcademy era un ejercicio escolar con datos academicos (alumnos, materias y calificaciones de parciales). Para KompasAPPbeta, adaptamos toda la base matematica y las redes convolucionales al dominio real de la movilidad urbana: variables de distancia, duracion, horas pico, presupuesto y secuencias de velocidad de tramos viales, resolviendo problemas de congestion y tiempo de arribo (ETA)."

### P2: "¿Que funcion cumple el modelo PCA dentro del recomendador?"
- **Respuesta:** "PCA reduce las dimensiones multivariadas (distancia, hora, duracion, presupuesto y hora pico) a 2 componentes ortogonales principales ($PC_1$ y $PC_2$) conservando mas del 50% de la varianza. Esto permite proyectar cartesianamente al usuario frente a los centroides de los 4 clusters de viajeros, explicando visualmente por que la app le asigno dicho perfil."

### P3: "¿Por que utilizar una CNN 1D en lugar de una red recurrente (LSTM o GRU) para analizar el trafico?"
- **Respuesta:** "Porque para secuencias cortas de tramos (ultimas 4 o 5 paradas), la **CNN 1D con PyTorch** tiene una latencia de inferencia significativamente menor que una LSTM, no sufre de problemas de desvanecimiento de gradiente y aplica filtros convolucionales paralelos que extraen de forma inmediata patrones de desaceleracion vehicular."

---

## 7. Ejecucion de Pruebas Unitarias

```powershell
cd C:\Users\kevin\Downloads\KompasAPPbeta\backend
.\venv\Scripts\pytest tests/test_ia_etapa2.py -v
```
