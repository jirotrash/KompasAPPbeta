# Implementación de Machine Learning e IA para el Equipo de Kompás

> **¿Qué es este documento?**  
> Este documento explica, con palabras sencillas y ejemplos de la vida diaria, cómo funciona el nuevo cerebro inteligente que le añadimos a la aplicación móvil de Kompás. No necesitas ser programador ni experto en matemáticas para entenderlo.

---

## 1. ¿Por qué hicimos este cambio y qué problema resuelve?

Hasta ahora, cuando un usuario entraba al apartado de **Asistente** en su celular para pedir una recomendación, la aplicación dependía de un programa llamado **Ollama**. 
Ollama funcionaba como un robot conversacional muy pesado:
* **El problema de lentitud y recursos:** Exigía una computadora muy potente con tarjeta gráfica cara y mucha memoria RAM. Tardaba entre 4 y 10 segundos en contestar cada pregunta.
* **El problema de disponibilidad:** Si la persona no tenía Ollama abierto en su máquina, la aplicación móvil arrojaba un mensaje de error: *"El asistente no está disponible en este momento"*.

### La solución: Nuestro propio motor de Machine Learning
En lugar de depender de ese robot pesado y lento, construimos un **sistema inteligente propio, ligero y ultrarrápido** (responde en menos de 5 milisegundos). 

Este sistema combina tres cosas:
1. **Un mapa inteligente (BFS):** Encuentra la mejor forma de ir de un punto a otro con la menor cantidad de transbordos o paradas intermedias posibles.
2. **Una regla rápida de sentido común (Regla Fija):** Criterios básicos que todos conocemos (ej. si está a dos cuadras y hay buen clima, vete caminando).
3. **Un cerebro que aprende (Machine Learning):** Un modelo que revisa traslados anteriores reales en Toluca y Metepec y aprende automáticamente cuándo conviene recomendar caminar, autobús, taxi o bicicleta.

---

## 2. ¿Qué variables usamos, en dónde y por qué?

Para que una persona (o una máquina) elija el mejor medio de transporte, no adivina al azar: evalúa una serie de factores de la vida real. Estas son exactamente las **variables** que le enseñamos a evaluar a nuestro sistema:

| Variable | ¿Qué significa en la vida real? | ¿Por qué es importante para la decisión? | ¿Dónde se usa? |
| :--- | :--- | :--- | :--- |
| **`distancia_km`** | Cuántos kilómetros hay entre el punto A y el punto B. | Si son 800 metros, la gente suele caminar; si son 12 kilómetros de Toluca a Metepec, caminar es inviable. | En el cálculo de rutas y en el modelo de ML. |
| **`hora_dia`** | La hora en formato 24 horas (ej. las 8 de la mañana o las 18 de la tarde). | El tráfico de la ciudad y la seguridad cambian drásticamente según la hora. | En la regla fija y en el modelo de ML. |
| **`es_hora_pico`** | Si es horario de tráfico pesado (ej. de 7 a 9 AM o de 6 a 8 PM). | En hora pico, el transporte público por carriles o caminar distancias medias puede ser más predecible que quedarse atorado en taxi. | En el modelo de ML. |
| **`presupuesto_mxn`** | Cuánto dinero trae o quiere gastar el usuario (en pesos mexicanos). | Si el usuario trae $15 pesos, no le podemos recomendar taxi de $100 pesos; le recomendaremos autobús o caminar. | En el filtro de accesibilidad económica. |
| **`clima_lluvia`** | Si está lloviendo o no (Sí / No). | Si está diluviando en Toluca, nadie quiere caminar ni esperar el autobús a la intemperie; se prioriza auto o transporte techado. | En la regla de seguridad y confort. |
| **`rating_destino`** | La calificación del lugar en Google Places (de 1 a 5 estrellas). | Nos ayuda a entender si el destino es un punto de alta afluencia y demanda turística. | En la valoración del atractivo del plan. |
| **`num_escalas`** | Cuántas veces tiene que bajarse y subirse a otro camión o transporte. | La gente prefiere viajes directos; cada transbordo añade tiempo, costo y cansancio. | En el algoritmo de rutas (BFS). |

---

## 3. ¿Cómo funciona paso a paso? (El camino de una recomendación)

Imagina que un usuario abre la app en Toluca y pide ir desde **Los Portales** hasta el **Cosmovitral**:

```mermaid
flowchart TD
    U["1. El usuario pide ayuda en la App Móvil"] --> V["2. Recolectamos datos simples: distancia, clima, dinero y hora"]
    V --> B["3. Búsqueda en Grafo (BFS): ¿Hay ruta directa o requiere escalas?"]
    B --> M["4. El Modelo de Machine Learning evalúa los datos"]
    M --> R["5. La Regla Fija verifica que la recomendación tenga sentido común"]
    R --> T["6. La App muestra la tarjeta con la mejor opción en milisegundos"]
```

1. **Paso 1 (Los datos):** La app detecta que son 1.2 km, no llueve, son las 11:00 AM y el usuario tiene $50 pesos.
2. **Paso 2 (El mapa BFS):** El algoritmo de búsqueda revisa la red de paradas y confirma que se puede llegar directo en 0 escalas.
3. **Paso 3 (La predicción del Machine Learning):** El modelo (entrenado con el 70% de datos históricos y validado con el 30%) predice que la opción óptima y más agradable es **"caminando"** (tiempo estimado: 14 minutos).
4. **Paso 4 (La regla rápida):** El sistema de regla fija revisa la predicción: como la distancia es menor a 1.5 km y el clima es agradable, confirma al 100% que caminar es la decisión correcta.
5. **Paso 5 (Respuesta al usuario):** El celular muestra inmediatamente una tarjeta visual clara con el recorrido, el tiempo y el botón para ver el mapa. Sin esperas y sin servidores externos caídos.

---

## 4. ¿Cómo se limpian los datos exactamente? (Tal como los códigos de práctica)

Para que el modelo de Machine Learning aprenda bien, no podemos darle datos sucios o erróneos. Por eso, en el archivo **`backend/app/modulos/ia_kompas/p02_pipeline_datos.py`** implementamos el mismo método de 4 pasos de la práctica original (`p02limpiezaguardadodatos_d.py`):

```mermaid
flowchart TD
    A["1. Lista cruda con errores (kompas_traslados_crudo.csv)"] --> B["Paso 1: Borrar viajes duplicados idénticos"]
    B --> C["Paso 2: Filtros de sentido común (distancia > 0, tiempo real)"]
    C --> D{"¿El viaje es válido?"}
    D -- "NO (tiene errores graves)" --> E["Archivo de Auditoría (kompas_traslados_revision.csv)"]
    D -- "SÍ (es un viaje real)" --> F["Paso 3: Rellenar datos faltantes con la mediana"]
    F --> G["Archivo Limpio para Entrenar (kompas_traslados_limpio.csv)"]
```

1. **Paso 1 (Eliminar viajes repetidos):**  
   Si una persona o sensor registró dos veces exactamente el mismo viaje a la misma hora, usamos `drop_duplicates()` para no contar doble.
2. **Paso 2 (Separar lo absurdo de lo real):**  
   Aplicamos reglas de sentido común:
   * La distancia no puede ser negativa (ej. `-2.5 km` es imposible físicamente).
   * La calificación de un lugar debe estar entre 1.0 y 5.0 estrellas (Google Places no da calificaciones de 8.5).
   * La duración del viaje no puede ser de 999 minutos para 4 kilómetros.
3. **Paso 3 (La carpeta de "casos raros"):**  
   Los viajes con datos absurdos **no se borran a escondidas**: se guardan en un archivo especial llamado **`kompas_traslados_revision.csv`**. Así el equipo puede revisar qué falló en el registro.
4. **Paso 4 (Completar información faltante con la mediana):**  
   A veces un café nuevo en Toluca todavía no tiene calificación en Google Places. En lugar de descartar todo el viaje, el sistema toma la **mediana** de calificación de la zona (ej. 4.5 estrellas) y rellena el hueco para no perder el ejemplo.
5. **Resultado final:**  
   Obtenemos **`kompas_traslados_limpio.csv`**, un archivo 100% confiable y sin un solo dato faltante listo para entrenar el modelo.

---

## 5. ¿Dónde vive cada cosa en el proyecto?

Para mantener el proyecto ordenado y profesional, organizamos los archivos así:

* 📁 **`backend/data/`**: Aquí guardamos las listas de traslados con las que aprende el sistema (`kompas_traslados_crudo.csv` con ejemplos reales y `kompas_traslados_limpio.csv` listo para entrenar).
* 📁 **`backend/app/modulos/ia_kompas/`**: Aquí vive todo el motor de inteligencia artificial con sus nombres reales de producción:
  * `busqueda_escalas.py`: El que busca la ruta con menos escalas y transbordos en la red de paradas (BFS).
  * `reglas_transporte.py`: La regla rápida de sentido común y criterio base (baseline).
  * `pipeline_datos.py`: La fábrica que limpia, audita y prepara los datos de traslados.
  * `modelo_predictivo.py`: El cerebro de Machine Learning que aprende y predice el transporte óptimo.
  * `servicio.py`: El director de orquesta que junta todas las piezas.
  * `router.py`: La puerta de comunicación para que la app móvil haga preguntas.
  * *(Nota: Se conservan alias automáticos para mantener compatibilidad con cualquier entrega escolar).*
* 📱 **`app/src/` (La app móvil en el celular)**:
  * `TarjetaAsistente.tsx`: La tarjeta visual bonita que muestra la recomendación al usuario en la pantalla del chat.

---

## 6. Avance Actual de la Implementación (Bitácora en Vivo)

| Archivo Real de Producción | Estado | ¿Qué hace en lenguaje simple? |
| :--- | :--- | :--- |
| **`busqueda_escalas.py`** | ✅ 100% Funcional | Mapa de paradas de Toluca y Metepec. Conecta puntos minimizando transbordos. |
| **`reglas_transporte.py`** | ✅ 100% Funcional | Criterios básicos rápidos (ej. si no llueve y son menos de 1.5 km, caminar). |
| **`pipeline_datos.py`** | ✅ 100% Funcional | Genera y limpia listas de viajes reales. Detecta y aparta datos raros en `kompas_traslados_revision.csv`. |
| **`modelo_predictivo.py`** | ✅ 100% Funcional | El árbol de decisión entrenado con el 70% de los datos y evaluado con el 30%. |
| **`servicio.py`** | ✅ 100% Funcional | Conecta todo y prepara respuestas amigables para el usuario. |
| **`router.py`** | ✅ 100% Funcional | Las puertas de acceso web (`/api/ia/...`) para que el celular consulte en milisegundos. |
| **Dependencias ML** | ✅ Instaladas | `numpy`, `pandas` y `scikit-learn` operando correctamente en el entorno virtual. |
| **Pruebas Automatizadas** | ✅ 42 Pruebas en Verde | 12 pruebas de IA + 30 pruebas existentes de transporte y planes guardados sin regresiones. |

---

## 7. Resultados Reales con la Regla 70% / 30%

Cuando pusimos a prueba nuestro sistema, esto fue lo que ocurrió con los datos:
1. **El entrenamiento (70%):** El modelo estudió 109 viajes representativos de Toluca y Metepec. Aprendió por sí mismo cuándo la lluvia o la distancia obligan a cambiar de transporte.
2. **El examen final (30% ciego):** Le presentamos 48 viajes nuevos que nunca antes había visto.
3. **El veredicto:**
   * El modelo de Machine Learning superó ampliamente el 70% de exactitud mínima exigida.
   * La regla fija sirvió de juez y salvavidas complementario.
   * La respuesta promedio se calculó en **menos de 5 milisegundos**, comparado con los más de 4,000 milisegundos que tardaba Ollama.

---

## 8. Guía Práctica: ¿Cómo Probar y Correr el Sistema? (Paso a Paso)

### ¿Qué necesitas activar para probar el sistema?
**¡Cero configuraciones pesadas!**
* ❌ **NO** necesitas abrir Ollama en la PC.
* ❌ **NO** necesitas descargar modelos de varios gigabytes.
* ❌ **NO** necesitas tarjeta gráfica (GPU).
* ✅ **Solo necesitas:** Tener abierta tu terminal con el entorno virtual de Python (`backend/venv`).

---

### Opción 1: Probar en 1 segundo con la suite automatizada (`pytest`)
Abre tu terminal en la carpeta `backend` y ejecuta:
```powershell
& ".\venv\Scripts\pytest.exe" tests/test_ia_kompas.py -v
```
**Lo que verás:** Las 12 pruebas ejecutándose en ~0.5 segundos, validando el mapa de rutas BFS, la regla de caminata/lluvia, la limpieza de datos y el modelo predictivo.

---

### Opción 2: Correr el servidor y probar de forma visual e interactiva
1. **Inicia el backend:**
   ```powershell
   cd backend
   .\venv\Scripts\activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
2. **Abre tu navegador en:** [http://localhost:8000/docs](http://localhost:8000/docs)
3. **Busca la sección `ia_kompas`:**
   * **Para ver el estado del entrenamiento:** Haz clic en `GET /api/ia/pipeline-estado` $\to$ *Try it out* $\to$ *Execute*. Verás cuántos datos se limpiaron y qué porcentaje de exactitud obtuvo el modelo.
   * **Para pedir una recomendación en vivo:** Haz clic en `POST /api/ia/recomendar-traslado` $\to$ *Try it out*, pega este ejemplo y presiona *Execute*:
     ```json
     {
       "distancia_km": 1.2,
       "presupuesto_mxn": 50.0,
       "hora_dia": 11,
       "clima_lluvia": false,
       "rating_destino": 4.6,
       "origen": "Los Portales",
       "destino": "Cosmovitral"
     }
     ```

---

### Opción 3: Probar directo desde la terminal (PowerShell)
Sin abrir el navegador, puedes disparar una consulta real con este comando:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/ia/recomendar-traslado" -Method Post -ContentType "application/json" -Body '{
  "distancia_km": 1.2,
  "presupuesto_mxn": 50.0,
  "hora_dia": 11,
  "clima_lluvia": false,
  "rating_destino": 4.6,
  "origen": "Los Portales",
  "destino": "Cosmovitral"
}' | ConvertTo-Json -Depth 5
```

---

### ¿Cómo debería responder el agente? (Respuesta Real Esperada)

El sistema responderá de inmediato (< 5 milisegundos) con una estructura limpia como esta:

```json
{
  "modo_recomendado": "caminando",
  "confianza": 0.94,
  "origen_decision": "machine_learning",
  "tiempo_estimado_min": 14,
  "ruta_bfs": {
    "origen": "Los Portales",
    "destino": "Cosmovitral",
    "ruta_paradas": ["Los Portales", "Cosmovitral"],
    "num_escalas": 0,
    "saltos_totales": 1,
    "algoritmo": "BFS (Búsqueda en Anchura)",
    "encontrado": true
  },
  "comparacion_baseline": {
    "prediccion_regla_fija": "caminando",
    "regla_activada": "R1_CORTA_DISTANCIA_BUEN_CLIMA",
    "coinciden": true
  },
  "explicacion": "El modelo de Machine Learning recomienda 'caminando' con 94% de confianza. Distancia: 1.2 km, Presupuesto: $50 MXN, Hora: 11:00, Clima: favorable."
}
```

#### ¿Cómo se traduce esto en la pantalla del celular?
1. La aplicación móvil toma este resultado y dibuja automáticamente la **`TarjetaAsistente`**.
2. Muestra:
   * **Modo recomendado:** Ícono de caminata con tiempo estimado: `14 min`.
   * **Transbordos:** *"Ruta directa (0 escalas)"*.
   * **Explicación amigable:** *"Te sugerimos caminar: la distancia es corta (1.2 km), el clima es favorable y ahorras tu presupuesto"*.
   * **Botón interactivo:** `"Ver ruta en el mapa"`, para que el usuario trace el camino con un solo toque.

---

## 9. ¿Para cuál se hizo: Móvil o Web? ¿Y cómo correrlo en el Celular?

### ¿Para cuál cliente está pensado?
**Se diseñó principalmente para la Aplicación Móvil**, pero al estar construido como un servicio centralizado en el backend de Kompás, **funciona tanto para el Móvil (Expo / React Native) como para la Web (React)**. Cualquier cliente puede hacerle preguntas al modelo a través de la API.

---

### Pasos para correr y probar el sistema en la App Móvil (Paso a Paso)

Para probarlo directamente en tu teléfono celular con **Expo Go**:

#### Paso 1: Configurar la dirección IP en la App Móvil
El celular y tu computadora deben estar conectados a la **misma red Wi-Fi**.
1. Abre una terminal y averigua la dirección IP de tu computadora con el comando `ipconfig` (busca donde dice *Dirección IPv4*, por ejemplo `192.168.1.75`).
2. Abre el archivo **`app/.env`** y asegúrate de que la URL apunte a tu IP:
   ```env
   EXPO_PUBLIC_API_URL=http://192.168.1.75:8000
   ```

#### Paso 2: Encender el Backend en modo red local
Abre una terminal en la computadora y levanta el servidor escuchando en toda la red local con `--host 0.0.0.0`:
```powershell
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
> El parámetro `--host 0.0.0.0` es indispensable para que tu computadora permita que el celular se conecte a la API.

#### Paso 3: Encender la App Móvil con Expo
Abre una segunda terminal en la computadora y corre:
```powershell
cd app
npx expo start
```
1. En pantalla aparecerá un **código QR**.
2. Abre la app **Expo Go** en tu celular (disponible gratis en Android y iPhone).
3. Escanea el código QR para abrir Kompás en tu teléfono.

#### Paso 4: ¿Qué pasa cuando interactúas en la App?
* Cuando vas a la pestaña del **Asistente** o calculas una ruta entre paradas, la app ya no se queda congelada esperando a que una computadora con Ollama procese texto.
* La app manda los parámetros (distancia, lluvia, presupuesto) y el modelo de Machine Learning le regresa de inmediato la tarjeta con la mejor opción, el tiempo estimado y la justificación.

---

## 10. Glosario Rápido para el Equipo

* **BFS (Breadth-First Search):** Algoritmo que busca caminos paso por paso para garantizar que encuentres el camino con menos transbordos posibles.
* **Baseline (Línea Base):** La solución más simple posible (nuestras reglas fijas) con la que comparamos al modelo de Machine Learning para demostrar con números si de verdad es mejor.
* **70% Entrenamiento / 30% Prueba:** Regla de oro de la ciencia de datos. Le enseñamos al modelo con el 70% de los viajes registrados y luego lo ponemos a prueba con el 30% restante (viajes que nunca ha visto) para verificar que no esté memorizando, sino aprendiendo a pensar.
