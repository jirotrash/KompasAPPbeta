# Documentacion Tecnica y Guia de Defensa: Practicas de IA en KompasAPPbeta

Este documento detalla la adaptacion, arquitectura e implementacion de las Practicas de Inteligencia Artificial de la Universidad (de la Practica 04 a la Practica 09) integradas en el proyecto real **KompasAPPbeta**.

---

## 1. Librerias Utilizadas y Como Instalarlas

El motor de Machine Learning e Inteligencia Artificial de KompasAPPbeta utiliza el ecosistema cientifico estandar de Python.

### Lista de Librerias
1. **`scikit-learn` (v1.9.1 o superior):**
   - Provee los algoritmos supervisados (`DecisionTreeClassifier`, `RandomForestClassifier`, `KNeighborsClassifier`), tecnicas no supervisadas (`KMeans`, `PCA`), preprocesamiento (`StandardScaler`, `MinMaxScaler`), particionado (`train_test_split`, `StratifiedKFold`), optimizacion (`GridSearchCV`, `cross_val_score`) y metricas (`accuracy_score`, `silhouette_score`, `adjusted_rand_score`, `confusion_matrix`, `classification_report`).
2. **`pandas` (v3.1.1 o superior):**
   - Manejo de estructuras tabulares (`DataFrame`, `Series`), lectura y exportacion de datasets CSV, mascaras booleanas e imputacion.
3. **`numpy` (v2.4.6 o superior):**
   - Operaciones vectoriales, calculo matricial, distancias euclidianas y percentiles estadisticos.
4. **`pymongo` (v4.19.0 o superior):**
   - Driver oficial de conexion y persistencia a la base de datos MongoDB (local o Atlas).
5. **`fastapi` y `pydantic`:**
   - Exposicion de endpoints REST y tipado estricto de esquemas.

### Instrucciones de Instalacion Paso a Paso

Si se requiere instalar o reconstruir el entorno virtual en Windows PowerShell:

```powershell
# 1. Posicionarse en la carpeta del backend
cd C:\Users\kevin\Downloads\KompasAPPbeta\backend

# 2. Crear el entorno virtual (si no existe)
python -m venv venv

# 3. Activar el entorno virtual
.\venv\Scripts\Activate.ps1

# 4. Actualizar pip
python -m pip install --upgrade pip

# 5. Instalar las dependencias cientificas y del backend
pip install scikit-learn pandas numpy pymongo fastapi uvicorn pydantic pytest
```

Para verificar la correcta instalacion:
```powershell
python -c "import sklearn, pandas, numpy, pymongo, fastapi; print('Todas las librerias estan correctamente instaladas')"
```

---

## 2. Inventario de Archivos Creados y Modificados

Todos los modulos fueron desarrollados bajo la regla estricta de no contener emojis y documentar en cada bloque:
1. **Que hace esa seccion.**
2. **Como lo hace.**
3. **En donde estan sus conexiones.**

| Practica | Archivo Implementado | Ruta del Archivo | Endpoint Expuesto |
| :--- | :--- | :--- | :--- |
| **P04** | `p04_ajuste_modelo.py` | `backend/app/modulos/ia_kompas/p04_ajuste_modelo.py` | `GET /api/ia/diagnostico-ajuste` |
| **P05** | `p05_comparacion_modelos.py` | `backend/app/modulos/ia_kompas/p05_comparacion_modelos.py` | `GET /api/ia/comparar-algoritmos` |
| **P06** | `p06_optimizacion_hiperparametros.py` | `backend/app/modulos/ia_kompas/p06_optimizacion_hiperparametros.py` | `GET /api/ia/optimizar-hiperparametros` |
| **P07** | `p07_segmentacion_viajeros.py` | `backend/app/modulos/ia_kompas/p07_segmentacion_viajeros.py` | `GET /api/ia/segmentacion-viajeros` |
| **P08** | `p08_clusters_avanzado.py` | `backend/app/modulos/ia_kompas/p08_clusters_avanzado.py` | `GET /api/ia/auditoria-clusters` |
| **P09** | `p09_reduccion_pca.py` | `backend/app/modulos/ia_kompas/p09_reduccion_pca.py` | `GET /api/ia/proyeccion-pca` |
| **Orquestador** | `servicio.py` | `backend/app/modulos/ia_kompas/servicio.py` | Centraliza metodos para el router |
| **API REST** | `router.py` | `backend/app/modulos/ia_kompas/router.py` | Define las rutas de acceso en FastAPI |
| **Pruebas** | `test_ia_avanzada.py` | `backend/tests/test_ia_avanzada.py` | 7 pruebas unitarias con Pytest |

---

## 3. Desglose Tecnico por Practica

---

### Practica 04: Particion 60/20/20 y Diagnostico de Ajuste (Overfitting vs Underfitting)

#### Que hace:
Aisla formalmente los datos de traslados en tres subconjuntos y evalua la capacidad de generalizacion del modelo en tres regimenes de complejidad:
- Subajuste (Underfitting): Modelo excesivamente simple que no aprende los patrones de los traslados.
- Ajuste adecuado: Modelo equilibrado con buena generalizacion en datos no vistos.
- Sobreajuste (Overfitting): Arbol sin limite de profundidad que memoriza el ruido y falla en nuevos casos.

#### Como lo hace:
1. Aplica un proceso de particion estratificada en dos pasos con `train_test_split`:
   - Primer paso: Extrae el 20% como conjunto de prueba ciego final (`test_size=0.20`, `stratify=y`).
   - Segundo paso: Sobre el 80% restante, extrae el 25% para validacion (`test_size=0.25`, `stratify=y_temporal`), reservando el 60% para entrenamiento.
2. Entrena arboles `DecisionTreeClassifier` con:
   - `max_depth = 1` (Subajuste).
   - `max_depth = 4` (Ajuste adecuado).
   - `max_depth = None` (Sobreajuste).
3. Calcula `accuracy_score` en los tres conjuntos. Si el entrenamiento tiene alta exactitud pero la validacion cae con una brecha superior al 8%, se diagnostica sobreajuste. Si la exactitud en entrenamiento y validacion es baja (< 70%), se diagnostica subajuste.
4. Selecciona el mejor modelo guiandose unicamente por el conjunto de validacion y genera el reporte de clasificacion final (`classification_report` y `confusion_matrix`) sobre el conjunto de prueba ciego.

#### Conexiones:
- **Entrada:** Consume `etapa_e_identificacion_variables` desde `pipeline_datos.py` leyendo `kompas_traslados_limpio.csv`.
- **Salida:** Alimenta `ServicioIAKompas.diagnostico_ajuste_p04()` en `servicio.py`.
- **Endpoint:** Expuesto en `GET /api/ia/diagnostico-ajuste`.

---

### Practica 05: Comparacion de Algoritmos de Machine Learning

#### Que hace:
Enfrenta a tres clasificadores supervisados distintos (Arbol de Decision, Bosque Aleatorio y K-Nearest Neighbors) bajo las mismas condiciones para elegir el mejor algoritmo de prediccion de transporte en Kompas.

#### Como lo hace:
1. Utiliza las particiones 60/20/20 generadas por la Practica 04.
2. Entrena:
   - `DecisionTreeClassifier(max_depth=4)`.
   - `RandomForestClassifier(n_estimators=50, max_depth=5)`.
   - `KNeighborsClassifier(n_neighbors=5, weights='distance')`.
3. Mide con `time.perf_counter()` la latencia de entrenamiento y de inferencia en milisegundos.
4. Calcula Precision ponderada, Recall ponderado, F1-Score y Exactitud en validacion y prueba ciega.
5. Ordena los modelos descendentemente segun su exactitud en validacion.

#### Conexiones:
- **Entrada:** Recibe los datos y particiones de `p04_ajuste_modelo.py` y `pipeline_datos.py`.
- **Salida:** Alimenta `ServicioIAKompas.comparar_algoritmos_p05()` en `servicio.py`.
- **Endpoint:** Expuesto en `GET /api/ia/comparar-algoritmos`.

---

### Practica 06: Optimizacion de Hiperparametros y Validacion Cruzada

#### Que hace:
Reemplaza la seleccion manual de hiperparametros por una busqueda sistematica exhaustiva mediante `GridSearchCV` combinada con validacion cruzada estratificada de 5 pliegues (`StratifiedKFold`).

#### Como lo hace:
1. Define un generador de pliegues `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`.
2. Para el arbol de decision, explora la rejilla:
   - `max_depth`: [2, 3, 4, 5, 6, 8, None]
   - `min_samples_split`: [2, 5, 10, 20]
   - `criterion`: ['gini', 'entropy']
3. Para el bosque aleatorio, explora:
   - `n_estimators`: [25, 50, 100]
   - `max_depth`: [3, 4, 5, 7]
   - `min_samples_split`: [2, 5, 10]
4. Evalua cada combinacion en los 5 pliegues y extrae los mejores hiperparametros (`best_params_`), la exactitud media y la desviacion estandar entre pliegues.

#### Conexiones:
- **Entrada:** Recibe las caracteristicas $X$ y la etiqueta $y$ desde `pipeline_datos.py`.
- **Salida:** Alimenta `ServicioIAKompas.optimizar_hiperparametros_p06()` en `servicio.py`.
- **Endpoint:** Expuesto en `GET /api/ia/optimizar-hiperparametros`.

---

### Practica 07: Segmentacion No Supervisada con K-Means (Clustering)

#### Que hace:
Descubre grupos naturales de comportamiento y patrones de movilidad urbana de los usuarios de Kompas sin depender de etiquetas supervisadas.

#### Como lo hace:
1. Extrae las variables cuantitativas de movilidad: `distancia_km`, `hora_dia`, `duracion_min`, `presupuesto_mxn` y `es_hora_pico`.
2. Aplica estandarizacion con `StandardScaler` (media 0 y varianza unitaria).
3. Evalua un rango de $K \in [2, 5]$ calculando:
   - Inercia (Metodo del Codo: suma de distancias cuadradas al centroide).
   - Coeficiente de Silueta (`silhouette_score`: compacidad interna vs separacion entre clusters).
4. Selecciona el $K$ optimo que maximiza la silueta y entrena el modelo `KMeans(init='k-means++')`.
5. Desestandariza los centroides mediante `inverse_transform` y genera los perfiles semanticos:
   - "Viajero Cotidiano / Transporte Economico": distancias medias matutinas, presupuesto bajo.
   - "Profesionista / Horario Pico de Alta Demanda": distancias mayores, horario de congestion, auto o taxi.
   - "Viajero Regional / Horario Flexible": traslados en horarios valle entre municipios.

#### Conexiones:
- **Entrada:** Lee `kompas_traslados_limpio.csv` generado por `pipeline_datos.py`.
- **Salida:** Alimenta `ServicioIAKompas.segmentar_viajeros_p07()` en `servicio.py`.
- **Endpoint:** Expuesto en `GET /api/ia/segmentacion-viajeros`.

---

### Practica 08: Auditoria Avanzada de Clusters, Estabilidad ARI, Anomalias y Persistencia

#### Que hace:
Audita la robustez cientifica de los clusters de movilidad, detecta viajes atipicos o sospechosos (anomalias) y persiste los perfiles en la base de datos MongoDB de Kompas.

#### Como lo hace:
1. **Comparacion de inicializaciones:** Ajusta K-Means con `init='k-means++'` y con `init='random'`, comparando la inercia resultante y el numero de iteraciones para converger.
2. **Comparacion de escaladores:** Contrasta `StandardScaler` frente a `MinMaxScaler` evaluando el Coeficiente de Silueta.
3. **Estabilidad con ARI (Adjusted Rand Index):** Ejecuta K-Means con semillas [42, 100, 2026, 777] y calcula el ARI cruzado. Un valor superior a 0.75 confirma que los segmentos son estables y no producto del azar.
4. **Deteccion de viajes anomalos:** Calcula la distancia euclidiana de cada observacion al centroide de su cluster asignado mediante `euclidean_distances`. Aquellos viajes cuya distancia supera el **percentil 95** se clasifican como anomalias (casos atipicos para revision).
5. **Persistencia en MongoDB:** Utiliza la funcion `get_bd()` de `backend/app/nucleo/bd.py` para almacenar el documento estructurado en la coleccion `perfiles_viajeros`.

#### Conexiones:
- **Entrada:** Consume `p07_segmentacion_viajeros.py` y `pipeline_datos.py`.
- **Base de datos:** Se conecta directamente con MongoDB (`bd.perfiles_viajeros.insert_one(...)`).
- **Endpoint:** Expuesto en `GET /api/ia/auditoria-clusters`.

---

### Practica 09: Reduccion de Dimensionalidad mediante PCA

#### Que hace:
Transforma el espacio multidimensional de movilidad (5 variables) a un plano bidimensional de 2 componentes principales ($PC_1$ y $PC_2$), preservando la maxima varianza posible para visualizacion de los clusters de viajeros.

#### Como lo hace:
1. Estandariza la matriz de caracteristicas con `StandardScaler`.
2. Aplica `PCA(n_components=2)`.
3. Calcula el porcentaje de varianza explicada por cada componente (`explained_variance_ratio_`) y la varianza acumulada (> 50%).
4. Proyecta las observaciones y los centroides multidimensionales al plano cartesiano $(PC_1, PC_2)$, permitiendo graficar los clusters sin perdida de correlacion.

#### Conexiones:
- **Entrada:** Consume las columnas de clustering de `p07_segmentacion_viajeros.py`.
- **Salida:** Alimenta `ServicioIAKompas.proyeccion_pca_p09()` en `servicio.py`.
- **Endpoint:** Expuesto en `GET /api/ia/proyeccion-pca`.

---

## 4. Guia de Preguntas y Respuestas para Evaluacion / Examen

Si el evaluador o docente te pregunta sobre cualquier parte del codigo, aqui tienes las respuestas tecnicas exactas:

### P1: "¿Por que divides los datos en 60%, 20% y 20% en lugar del tipico 70% y 30%?"
- **Respuesta:** "Porque en un flujo riguroso de Machine Learning necesitamos tres conjuntos con roles diferentes:
  1. El **60% (Entrenamiento)** se usa para que los algoritmos aprendan los pesos y reglas.
  2. El **20% (Validacion)** se utiliza exclusivamente para ajustar hiperparametros y seleccionar que modelo o profundidad es mejor, sin contaminar la prueba.
  3. El **20% (Prueba)** se mantiene completamente ciego y solo se evalua al final para obtener una estimacion honesta y no sesgada de como se comportara el modelo con datos reales en produccion."

### P2: "¿Como detectas si hay sobreajuste (overfitting) o subajuste (underfitting)?"
- **Respuesta:** "Monitoreando la brecha de exactitud entre el conjunto de entrenamiento y el conjunto de validacion:
  - Hay **subajuste** cuando el modelo es demasiado rigido (`max_depth=1`) y obtiene una exactitud pobre tanto en entrenamiento como en validacion (< 70%).
  - Hay **sobreajuste** cuando el modelo es demasiado complejo (`max_depth=None`) y alcanza 100% en entrenamiento, pero la exactitud en validacion cae mas de un 8% o 10%, indicando que memorizo el ruido en vez de aprender patrones generales."

### P3: "¿Por que comparaste tres algoritmos distintos en la Practica 05?"
- **Respuesta:** "Porque ningun algoritmo es universalmente superior para todos los problemas (teorema del *No Free Lunch*). Comparamos un modelo explicable (Arbol de Decision), un ensamble robusto (Random Forest) y un metodo basado en instancias (KNN) midiendo no solo su exactitud y F1-score, sino tambien la latencia en milisegundos, que es critica para la experiencia de usuario en una aplicacion movil como Kompas."

### P4: "¿Que ventaja tiene GridSearchCV con 5 pliegues frente a probar hiperparametros a mano?"
- **Respuesta:** "Evita el sesgo y la suerte de una particion fija. Con 5 pliegues estratificados (`StratifiedKFold`), cada combinacion de hiperparametros se entrena y valida 5 veces sobre diferentes particiones. Se reporta el promedio y la desviacion estandar, garantizando que el modelo elegido es estadisticamente estable."

### P5: "¿Como determinaron el numero de grupos K en K-Means?"
- **Respuesta:** "No elegimos K al azar. Evaluamos K de 2 a 5 combinando dos metricas:
  1. El **Metodo del Codo (Inercia)**, que mide la suma de distancias cuadradas internas.
  2. El **Coeficiente de Silueta**, que mide simultaneamente que tan cerca esta cada punto de su cluster y que tan lejos esta del cluster vecino mas proximo. Elegimos el K que maximiza el coeficiente de silueta."

### P6: "¿Para que sirve el Adjusted Rand Index (ARI) en la Practica 08?"
- **Respuesta:** "Mide la estabilidad de las agrupaciones. Si ejecutamos K-Means con diferentes semillas aleatorias y el ARI es cercano a 1.0, significa que los grupos descubiertos son consistentes y reflejan estructuras reales en los datos de movilidad, no agrupaciones fortuitas causadas por el azar de la inicializacion."

### P7: "¿Como funciona el detector de anomalias en los viajes?"
- **Respuesta:** "Calculamos la distancia euclidiana de cada viaje estandarizado hacia el centroide de su cluster asignado. Luego determinamos el percentil 95 de esa distribucion de distancias. Todo viaje cuya distancia supere ese percentil se cataloga como atipico, permitiendo a Kompas auditar traslados sospechosos, errores en coordenadas de paradas o cobros inconsistentes."

### P8: "¿Como se conecta la Practica 08 con MongoDB?"
- **Respuesta:** "Mediante la funcion `get_bd()` de `app.nucleo.bd`, que obtiene el pool de conexiones del cliente PyMongo de Kompas. Los perfiles interpretados y sus metricas se guardan como un documento JSON estructurado en la coleccion `perfiles_viajeros`, permitiendo que la app movil o el panel administrativo los consuman de forma persistente."

---

## 5. Como Ejecutar las Pruebas

Para correr las 7 pruebas unitarias de las practicas avanzadas:
```powershell
cd C:\Users\kevin\Downloads\KompasAPPbeta\backend
.\venv\Scripts\pytest tests/test_ia_avanzada.py -v
```

Resultado esperado:
```text
tests/test_ia_avanzada.py::test_p04_particion_y_diagnostico_ajuste PASSED
tests/test_ia_avanzada.py::test_p05_comparacion_algoritmos PASSED
tests/test_ia_avanzada.py::test_p06_optimizacion_hiperparametros PASSED
tests/test_ia_avanzada.py::test_p07_segmentacion_viajeros PASSED
tests/test_ia_avanzada.py::test_p08_auditoria_clusters_y_anomalias PASSED
tests/test_ia_avanzada.py::test_p09_reduccion_pca PASSED
tests/test_ia_avanzada.py::test_servicio_ia_endpoints_avanzados PASSED

======================== 7 passed in ~22s ========================
```

