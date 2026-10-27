# Kompás — Plan v0.6: TypeScript + búsqueda heurística + algoritmo genético + asistente con Ollama

> **Para Claude Code en VS Code.** Va en la raíz del repo, junto a `PLAN_REFACTOR.md`. Prompt:
> *"Lee PLAN_V06.md (y AGENTS.md, ARQUITECTURA.md y MIGRACION_MONGODB.md como referencia) e impleméntalo todo, de principio a fin, sin detenerte entre pasos. Al final dame el resumen de la §8."*

## 1. Objetivo

Sobre la v0.5 (arquitectura modular + MongoDB + dashboard), agregar:

1. **Frontend web en TypeScript** (`.ts` / `.tsx`).
2. **Temas de Fundamentos de IA que faltan**: búsqueda heurística (**A\*** y **voraz/primero el mejor**) con heurística **Euclidiana** y **Manhattan**, **costo uniforme (UCS)**, comparación contra el DFS que ya existe, un **algoritmo genético** que optimiza el orden de las paradas de un plan y un **árbol binario de paradas** por cada ruta.
   **Importante:** estos algoritmos funcionan **por dentro** de las funciones normales de la app (¿Cómo llego?, Armar una salida, Asistente). **No se crea ningún apartado nuevo** de "Laboratorio" o "IA" en la app ni en la web de usuario, ni etiquetas como "calculado con A\*". Tampoco se dibuja ningún árbol: el **árbol binario de paradas** (§4.5) trabaja por dentro y su resultado se ve **en el mapa** (dónde subir, dónde bajar y el tramo en autobús), en la app móvil y en el dashboard.
3. **Asistente con LLM local (Ollama)** en la app móvil. Las conversaciones y las rutas/planes que el asistente consulte se guardan en MongoDB.
4. Gráficas nuevas en el dashboard y documentación para los manuales.

## 2. Reglas (las mismas de la v0.5, más estas)

1. Respetar `AGENTS.md` y la arquitectura en capas: router → servicio → repositorio. Nada de consultas a la base en routers.
2. **No modificar** `app/ia/motor.py`, `hechos.py`, `reglas.json`, `busqueda_dfs.py` ni `metricas_distancia.py`. Los algoritmos nuevos van en **archivos nuevos** dentro de `app/ia/` y pueden **importar** lo que ya existe (el grafo del DFS, las funciones de distancia).
3. El contrato actual de la API no cambia. Solo se agregan endpoints y campos **opcionales**.
4. **No inventar datos.** Si un nodo del grafo no tiene coordenadas, se obtienen de la colección `lugares` o de Google Places, guardando la fuente y la fecha. Si no se encuentran, se reporta y no se inventan. El asistente tampoco puede inventar horarios, tarifas ni rutas (§5.4).
5. La app móvil **nunca** llama a Ollama directo: todo pasa por la API.
6. Una sola rama: `feature/v0.6-ts-ia-ollama`. Commits pequeños en español e imperativo, **sin las líneas `Co-Authored-By: Claude` ni `Claude-Session:`**. PR a `main` al final.
7. Antes de cada commit: `pytest` verde; en `frontend/`: `npm run lint`, `npm run typecheck` y `npm run build` verdes; en `app/`: `npx tsc --noEmit` verde.

## 3. Frontend web a TypeScript

1. `npm i -D typescript @types/react @types/react-dom @types/leaflet` (y los `@types` que falten). `tsconfig.json` con `"strict": true`, `"jsx": "react-jsx"`, `"moduleResolution": "bundler"`, `"noEmit": true`. Script `"typecheck": "tsc --noEmit"` en `package.json`. Ajustar ESLint con `typescript-eslint`.
2. Renombrar con `git mv` todos los `.js` → `.ts` y `.jsx` → `.tsx` de `frontend/src/` (incluidos `vite.config` y `main`).
3. Crear `src/compartido/tipos/dominio.ts` copiando los tipos que aplican de `app/src/types/dominio.ts` (`Lugar`, `Ruta`, `Plan`, `Reporte`, `Usuario`…), más `src/modulos/dashboard/tipos.ts` con la forma de cada respuesta de `/api/dashboard/*`. Los JSDoc de los `api.ts` se convierten en tipos reales.
4. `solicitud<T>()` en `compartido/api/cliente.ts` pasa a ser genérica. `ErrorApi` queda tipada. Los datos del modo mock deben cumplir los mismos tipos.
5. Prohibido `any` explícito. Si algo de verdad no se puede tipar, usar `unknown` con validación.
6. Nada cambia visualmente ni de comportamiento.

## 4. IA: búsqueda heurística, UCS y algoritmo genético

### 4.1 `app/ia/busqueda_informada.py` (nuevo)

- **Reutiliza el grafo de `busqueda_dfs.py`** (importarlo, no copiarlo). Leer primero cómo está definido.
- **Costo de cada arista** (g): la distancia real entre los dos nodos en km, calculada con las coordenadas de cada nodo (`compartido.geo`, la misma función de distancia que ya usa el proyecto). Si el grafo ya trae costos, se usan esos.
- **Coordenadas de los nodos:** si el grafo no las tiene, crear `app/ia/datos/coordenadas_grafo.json` con `{nodo: {lat, lng, fuente, fecha_verificacion}}` obtenidas de la colección `lugares` o de Google Places (regla 4).
- Algoritmos, todos con la misma firma y la misma forma de respuesta que el DFS (camino, traza paso a paso, nodos explorados):
  - `costo_uniforme(origen, destino)`: UCS, f(n) = g(n).
  - `voraz(origen, destino, heuristica)`: primero el mejor, f(n) = h(n).
  - `a_estrella(origen, destino, heuristica)`: f(n) = g(n) + h(n).
- **Heurísticas:** `heuristica="euclidiana" | "manhattan"`. h(n) = distancia del nodo n al destino, usando las funciones de `metricas_distancia.py` sobre coordenadas convertidas a km (proyección local equirectangular centrada en Toluca; documentar la fórmula).
- La traza de cada paso incluye `nodo`, `g`, `h`, `f` y la `frontera` ordenada, para poder mostrarla como tabla.
- **Admisibilidad (para el manual):** la Euclidiana nunca sobreestima la distancia real, así que es admisible y A\* encuentra el camino óptimo. La Manhattan puede sobreestimar, así que no es admisible y A\* puede devolver un camino no óptimo. La respuesta incluye `es_admisible: bool` y el comparativo lo muestra con datos.

### 4.2 `app/ia/algoritmo_genetico.py` (nuevo)

Problema: **ordenar las paradas de un plan** para recorrer la menor distancia (tipo agente viajero, con origen fijo).

- **Cromosoma:** permutación de los índices de las paradas.
- **Aptitud:** `1 / (1 + distancia_total_km + penalización)`. La penalización aplica si una parada queda fuera de su horario según `hora_salida` y los tiempos estimados (usar `compartido.traslados`).
- **Operadores:** selección por torneo (k=3), cruza de orden (OX), mutación por intercambio, elitismo (2).
- **Parámetros** configurables, con estos valores por defecto: población 60, generaciones 150, prob. cruza 0.9, prob. mutación 0.2, semilla opcional para reproducir resultados.
- **Regresa:** mejor orden, distancia, aptitud, generación en que se encontró, `historial` (mejor y promedio de aptitud por generación) y parámetros usados.
- Con 8 paradas o menos, calcula también el óptimo por **fuerza bruta** para comparar (`brecha_vs_optimo_%`).

### 4.3 Uso dentro de la app (sin apartados nuevos)

Los algoritmos trabajan por dentro de las funciones que ya existen. El usuario solo ve mejores resultados; **no hay pantallas, pestañas, interruptores ni etiquetas de "IA", "Laboratorio" o "calculado con…"**.

| Función de la app | Algoritmo | Cómo |
|---|---|---|
| **Armar una salida** (itinerarios) | Algoritmo genético | **Siempre** se aplica, después de `recomendar()`: las paradas de cada plan se devuelven en el orden más corto. Con una sola parada no se ejecuta. No cambia nada de lo que decide el sistema experto. |
| **¿Cómo llego?** (rutas) | A\* con heurística Euclidiana + árbol binario | A\* encuentra combinaciones con transbordo cuando ninguna ruta de Kompás sola conecta origen y destino. El árbol binario de paradas (§4.5) encuentra dónde subir y dónde bajar. |
| **Asistente** | Todos | Usa los mismos servicios, así que sus respuestas ya salen con A\*, el árbol y el orden optimizado. |
| **Lugares cercanos** | Euclidiana / Manhattan | Ya se usaban en `compartido.geo`; solo se documenta dónde en el manual. |

**Contrato de la API** (solo campos nuevos opcionales):
- `POST /api/itinerarios` agrega en cada plan `orden_optimizado: {distancia_antes_km, distancia_despues_km, generaciones}`. Es para el dashboard y el manual; **la app y la web no lo muestran**.
- La opción con transbordo de "¿Cómo llego?" llega como una opción más (`tipo: "combinado"`), con sus tramos (camina → ruta X → transbordo → ruta Y → camina), dónde subir y bajar y el tiempo estimado. Se ve **igual que las demás opciones**, sin explicación del algoritmo. Si no hay combinación posible, no se agrega nada (no se inventa una ruta).

**A\* para transbordos** (`app/ia/transbordos.py`, nuevo):
- **Grafo:** se arma con los trazos de la colección `rutas`. Los nodos son los puntos de cada ruta, más el origen y el destino del usuario. Aristas:
  - a lo largo de una ruta: costo = distancia × factor de autobús;
  - a pie entre rutas distintas o desde el origen/destino, si están a ≤ 400 m: costo = distancia × factor de caminata + penalización por transbordo.
  - Los factores salen de `compartido.traslados`; no se inventan valores nuevos.
- **Búsqueda:** A\* con heurística Euclidiana (dividida entre la velocidad más rápida del grafo para que sea admisible).
- **Prueba:** `tests/test_transbordos.py` con dos rutas de prueba que se cruzan y un origen/destino que solo se conectan con transbordo.

**Registro para el dashboard:** cada ejecución del genético y de A\* se guarda en `bitacora_laboratorio` (`tipo: "genetico"` / `"transbordo"`, nodos explorados, km antes/después, ms), con el mismo manejo de error silencioso que el DFS.

**Endpoints de apoyo** (en `modulos/laboratorio/`, solo admin, sin pantalla de usuario; los usan el dashboard, las pruebas y el manual):

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/busqueda/comparar?origen=&destino=` | Corre DFS, UCS, voraz (2 heurísticas) y A\* (2 heurísticas) sobre el grafo del DFS. Tabla: costo, nodos explorados, longitud del camino, ¿óptimo?, ms |
| `POST` | `/api/genetico/ordenar-paradas` | Ejecuta el genético con parámetros a elegir y regresa lo de la §4.2 |

### 4.4 Sin pantallas nuevas de IA

- **No** se crea sección "Laboratorio IA" ni en la web de usuario ni en la app móvil.
- **No** se agregan interruptores de "optimizar" ni enlaces "¿Cómo se calculó?".
- **No** se dibuja ningún árbol. Lo que se nota es el resultado en el mapa (§4.5). Aparte está el **Asistente** (§5).

### 4.5 Árbol binario de paradas (por cada ruta)

**Backend: `app/ia/arbol_binario.py`** (nuevo, implementación propia, sin librerías):
- `NodoParada`: `clave` (km acumulado desde el inicio de la ruta), `parada` (id, nombre, lat, lng), `izquierdo`, `derecho`.
- `construir_balanceado(paradas_ordenadas)`: la mediana es la raíz y se repite recursivamente en cada mitad, así el árbol queda balanceado. Insertar en orden produciría una lista degenerada; eso se explica en el manual.
- Operaciones: `insertar`, `buscar(km)`, `mas_cercano(km) -> (nodo, camino_visitado)` (con predecesor y sucesor), `inorden`, `preorden`, `postorden`, `altura`, `total_nodos`, `a_dict()` para JSON (`{clave, parada, izquierdo, derecho}`).
- **Paradas de cada ruta:** usar las paradas que tenga la ruta en la base. Si la colección `rutas` no tiene paradas, usar los puntos de su trazo con el nombre `"Punto N"` (nunca inventar nombres de paradas) y avisarlo en el resumen final para que el equipo capture las paradas reales.

**Uso real (por dentro):** en "¿Cómo llego?", para cada opción en autobús o combinada:
1. se proyectan el origen y el destino sobre el trazo y se obtiene su km;
2. con `mas_cercano()` en el árbol de esa ruta se encuentran **dónde subir** y **dónde bajar**.

El árbol de cada ruta se construye una vez y se guarda en caché en memoria (se invalida si la ruta cambia).

**Endpoint de apoyo** (solo admin, sin pantalla; para pruebas y para sacar los datos del manual técnico):

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/rutas/{id_ruta}/arbol` | `{raiz, altura, total_nodos, inorden, preorden, postorden}` |

**Qué devuelve "¿Cómo llego?"** (campos opcionales nuevos en cada opción en autobús o combinada): `id_ruta`, `parada_subida` y `parada_bajada` (`{nombre, lat, lng, km}`), `tramo_en_ruta` (los puntos del trazo entre subida y bajada, sacados con el recorrido inorden del árbol) y las `paradas_intermedias`.

**App móvil (`app/`) — todo en el mapa, sin dibujar ningún árbol:**
- En el mapa del detalle de cada opción:
  - marcador de **dónde subir** y de **dónde bajar** (con su nombre);
  - el **tramo en autobús** resaltado solo entre subida y bajada (el resto del trazo de la ruta, tenue);
  - las paradas intermedias como puntos pequeños;
  - la caminata del origen a la subida y de la bajada al destino, punteada.
- Si la opción es combinada, lo mismo por cada ruta, con un marcador de transbordo.
- Debajo del mapa, el texto que ya existe ("Sube en … / Baja en …") toma esos datos.
- Funciones y tipos en `src/services/api.ts` y `src/types/dominio.ts`; el modo mock (`src/services/mock/`) regresa los mismos campos para una ruta de ejemplo marcada como demostración.
- Colores según `COLORIMETRIA.md`; debe funcionar en Expo Go.

**Web y dashboard — también en el mapa:**
- En "¿Cómo llego?" de la web, el mapa se comporta igual que en la app (subida, bajada, tramo resaltado, intermedias).
- En el **dashboard** (pestaña **Movilidad**), panel **"Rutas y paradas"**: mapa con selector de ruta que muestra su trazo y sus paradas numeradas en orden (recorrido inorden del árbol), y un **mapa de calor de las paradas más usadas para subir y bajar** (sale de la bitácora). No se dibuja el árbol.

## 5. Asistente con LLM (Ollama) en la app móvil

### 5.1 Arquitectura

```
App (Expo) ──POST /api/asistente/conversaciones/{id}/mensajes──► FastAPI
                                                                    │ módulo asistente
                                                                    ├─► MongoDB (conversaciones)
                                                                    ├─► herramientas: lugares, rutas, itinerarios (servicios existentes)
                                                                    └─► externos/ollama.py ──► Ollama (http://localhost:11434, en la PC)
```

- `app/externos/ollama.py`: cliente con `httpx` a `POST {OLLAMA_URL}/api/chat` (`stream: false`), timeout 60 s, `options: {temperature: 0.3, num_ctx: 4096}`. Usa el patrón Adaptador, igual que Google Places.
- `.env` (y `.env.example`): `OLLAMA_URL=http://localhost:11434`, `OLLAMA_MODELO=llama3.2:3b` (debe ser un modelo con soporte de *tools*; documentar en el README cómo cambiarlo y el `ollama pull` necesario).
- Módulo `app/modulos/asistente/` con router, servicio, repositorio y esquemas.

### 5.2 Herramientas que el LLM puede llamar (tool calling de Ollama)

| Herramienta | Llama a | Para qué |
|---|---|---|
| `buscar_lugares(texto, categoria?)` | servicio de lugares / Google Places | "¿Dónde hay un café cerca?" |
| `como_llegar(origen, destino, medios?)` | servicio de rutas | "¿Cómo llego al Cosmovitral desde la terminal?" |
| `armar_salida(contexto, presupuesto, tiempo, intereses, hora_salida)` | servicio de itinerarios (sistema experto) | "Plan con amigos, 300 pesos, 3 horas" |
| `mis_planes()` | repositorio de planes | "¿Qué planes he guardado?" |

- El servicio ejecuta la herramienta con los **servicios existentes** (no duplica lógica) y le devuelve al modelo el resultado en JSON.
- Si el modelo no soporta *tools* o falla al llamarlas, responde solo con texto y lo anota en el log.
- Máximo 3 llamadas a herramientas por mensaje.

### 5.3 Colección `conversaciones` (MongoDB)

```json
{
  "_id": "ObjectId",
  "id_usuario": 1,
  "titulo": "Cómo llegar al Cosmovitral",
  "modelo": "llama3.2:3b",
  "mensajes": [
    { "rol": "usuario", "contenido": "¿Cómo llego al Cosmovitral desde la terminal?", "creado_en": "..." },
    { "rol": "herramienta", "nombre": "como_llegar", "argumentos": {"origen": "...", "destino": "..."},
      "resultado_ref": { "tipo": "ruta", "id_ruta": 2 }, "creado_en": "..." },
    { "rol": "asistente", "contenido": "Puedes tomar…", "duracion_ms": 4200, "creado_en": "..." }
  ],
  "rutas_consultadas": [ { "id_ruta": 2, "origen": "...", "destino": "...", "transporte": "autobus", "consultado_en": "..." } ],
  "planes_creados": [ 31 ],
  "created_at": "...", "updated_at": "...", "deleted_at": null
}
```

- Índices: `{id_usuario: 1, updated_at: -1}`.
- Los mensajes se agregan con `$push`; las rutas consultadas con `$addToSet` (sin repetir).
- Cuando `armar_salida` crea un plan, también se guarda en `planes` como cualquier plan (con `origen_solicitud: "asistente"`), así aparece en *Mis planes* y en el dashboard.
- El título se genera de las primeras palabras del primer mensaje (sin llamar al LLM).
- Al modelo solo se le mandan los **últimos 12 mensajes** más el *system prompt*.
- Agregar la colección al validador `$jsonSchema`, a `preparar_bd.py` y al diccionario de datos del manual.

### 5.4 System prompt (en `modulos/asistente/prompt.py`)

Debe dejar claro que:
- Es el asistente de Kompás para **Toluca, Lerma y San Mateo Atenco**. Responde en español, breve.
- Solo usa datos que vengan de las herramientas. Si no hay información verificada de una ruta, horario o tarifa, lo dice en lugar de inventarla (misma regla que CONTEXTO.md §2).
- Fuera de movilidad y salidas en la zona, redirige amablemente.
- Nunca pide ni muestra contraseñas o datos de otros usuarios.

### 5.5 Endpoints (todos 🔒, cada usuario solo ve lo suyo)

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/asistente/estado` | `{disponible, modelo}`: hace ping a Ollama |
| `POST` | `/api/asistente/conversaciones` | Crea una conversación vacía |
| `GET` | `/api/asistente/conversaciones` | Lista: id, título, último mensaje, fecha |
| `GET` | `/api/asistente/conversaciones/{id}` | Conversación completa |
| `POST` | `/api/asistente/conversaciones/{id}/mensajes` | `{texto}` → guarda, llama al LLM con herramientas y regresa la respuesta y las tarjetas (rutas/planes) |
| `DELETE` | `/api/asistente/conversaciones/{id}` | Borrado lógico |

- Si Ollama no responde: **503** con el mensaje "El asistente no está disponible en este momento." El mensaje del usuario sí se guarda.
- `{id}` de otro usuario: 404 (no revelar que existe).
- Límite: 2000 caracteres por mensaje (422).

### 5.6 App móvil (`app/`)

- Pestaña nueva **Asistente** en la navegación (Expo Router):
  - `src/app/(tabs)/asistente/index.tsx`: lista de conversaciones con botón "Nueva conversación".
  - `src/app/(tabs)/asistente/[id].tsx`: el chat.
  - Si el layout de pestañas tiene otra estructura, seguir la que ya existe.
- **Chat:** burbujas usuario/asistente, indicador "Escribiendo…", y tarjetas para las rutas y planes que regresen (botón **Ver ruta** / **Ver plan**, que abren las pantallas que ya existen). También: borrar conversación y aviso si `/estado` dice que no está disponible.
- Funciones nuevas en `src/services/api.ts` y tipos nuevos en `src/types/dominio.ts` (`Conversacion`, `MensajeChat`, `TarjetaAsistente`).
- **Modo mock** (`EXPO_PUBLIC_USE_MOCK=true`): `src/services/mock/asistente.ts` con respuestas de ejemplo marcadas como demostración.
- Colores y contraste según `COLORIMETRIA.md` y `app/AGENTS.md`.

### 5.7 Red

- El backend corre en la PC y Ollama también, así que `OLLAMA_URL=http://localhost:11434` funciona.
- El celular sigue usando `EXPO_PUBLIC_API_URL=http://<IP de la PC>:8000`.
- Documentar en el README: Ollama abierto, `ollama pull <modelo>` y probar con `GET /api/asistente/estado`.

## 6. Dashboard (se amplía)

- **Pestaña "Laboratorio IA"** (ya existe; solo admin), gráficas nuevas:
  - nodos explorados por algoritmo (barras agrupadas DFS / UCS / voraz / A\*), con datos de `/api/busqueda/comparar`;
  - costo del camino vs. óptimo por heurística;
  - convergencia promedio del genético (línea);
  - km ahorrados por el genético en los planes reales (barras);
  - transbordos calculados con A\* y nodos explorados promedio.
- **Pestaña "Movilidad"**: panel "Rutas y paradas" en el mapa (§4.5).
- **Pestaña nueva "Asistente"** (solo datos agregados, **nunca el contenido de los mensajes**):
  - conversaciones y mensajes por día (línea);
  - herramientas más usadas (barras);
  - tiempo de respuesta del modelo (promedio y p90);
  - % de respuestas con error / no disponible;
  - planes creados desde el asistente vs. desde el planificador (dona).
- `scripts/sembrar_actividad_demo.py` también genera conversaciones demo (`demo: true`) y ejecuciones de búsqueda, transbordos y genético.

## 7. Pruebas y documentación

- **`tests/test_busqueda_informada.py`:**
  - A\* con Euclidiana da el mismo costo que UCS (óptimo);
  - el voraz explora menos nodos o igual que UCS en el caso de prueba;
  - origen = destino regresa un camino de un nodo.
- **`tests/test_arbol_binario.py`:** el árbol balanceado tiene altura ⌈log₂(n+1)⌉; inorden regresa las paradas en orden; `mas_cercano()` encuentra la parada correcta y su camino.
- **`tests/test_transbordos.py`:** ver §4.3.
- **`tests/test_genetico.py`:** con semilla fija es reproducible; con ≤ 8 paradas la brecha contra fuerza bruta es ≤ 5 %; el resultado siempre es una permutación válida.
- **`tests/test_asistente.py`:**
  - con Ollama **simulado** (mock de `externos/ollama.py`): se guardan los mensajes, se registran las rutas consultadas y la llamada a herramienta crea un plan;
  - 503 si Ollama no responde;
  - 404 con la conversación de otro usuario.
- **Manual técnico** (`DOCS/manual-tecnico/`):
  - `busqueda-y-heuristicas.md`: pseudocódigo de UCS, voraz y A\*, tabla comparativa real, admisibilidad y diagrama del grafo;
  - `algoritmo-genetico.md`: representación, aptitud, operadores, parámetros y gráfica de convergencia;
  - `arbol-binario.md`: estructura, construcción balanceada, búsqueda del más cercano, recorridos, cómo se usa para subir/bajar y un diagrama del árbol de una ruta real (en el manual sí va el diagrama, generado con `/api/rutas/{id}/arbol`);
  - `ia-en-la-app.md`: tabla de qué algoritmo trabaja dentro de cada función de la app (§4.3);
  - `asistente-llm.md`: arquitectura, diagrama de secuencia mensaje → herramienta → LLM → MongoDB, colección `conversaciones` y system prompt.
  - Actualizar `arquitectura.md` y `modelo-datos-mongodb.md`.
- **Manual de usuario:** capturas del asistente en la app, del mapa de una ruta con subida, bajada y tramo resaltado, y del panel "Rutas y paradas" del dashboard.

## 8. Checklist final y resumen

- [ ] `frontend/`: sin archivos `.js`/`.jsx` en `src/`; `typecheck`, `lint` y `build` verdes.
- [ ] Ni la app ni la web de usuario tienen sección "Laboratorio", interruptor de optimizar ni etiquetas de algoritmos.
- [ ] En "Armar una salida" los planes salen con el orden optimizado por el genético (se verifica con `orden_optimizado` en la respuesta).
- [ ] En "¿Cómo llego?" aparece la opción combinada con transbordo (A\*) cuando aplica, y dónde subir/bajar sale del árbol binario (por dentro).
- [ ] En la app, la web y el dashboard **no se dibuja ningún árbol**: el mapa muestra subida, bajada y el tramo resaltado de cada ruta.
- [ ] El dashboard muestra la comparación de algoritmos, la convergencia del genético y el panel "Rutas y paradas".
- [ ] Con Ollama abierto, el asistente de la app contesta "¿Cómo llego a …?" usando una ruta real y la conversación aparece al volver a abrir la app.
- [ ] `pytest` verde (las anteriores más las nuevas).
- [ ] `git diff main -- backend/app/ia/motor.py backend/app/ia/hechos.py backend/app/ia/busqueda_dfs.py backend/app/ia/metricas_distancia.py backend/app/ia/reglas.json` vacío.
- [ ] **Resumen final:** archivos creados y modificados, comandos para correr todo (backend, Ollama, web, app) y pendientes (por ejemplo, rutas sin paradas reales).
