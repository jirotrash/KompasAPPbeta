# Kompás v0.6 — Resumen de cambios

> Rama `feature/v0.6-ts-ia-ollama` · 8 commits (de `6e56008` a `67a216e`) · 197 archivos, +8 980 / −1 169 líneas
> Plan de referencia: `PLAN_V06.md`. Detalle técnico de cada tema en `DOCS/manual-tecnico/`.

## 1. En una frase

La web pasó a **TypeScript**. Se agregaron los temas de Fundamentos de IA (**BFS, UCS, voraz, A\***, **algoritmo
genético** y **árbol binario**), que trabajan **por dentro** de las funciones que ya existían. La app tiene un
**asistente con Ollama** cuyas conversaciones se guardan en MongoDB. El dashboard ganó gráficas nuevas para ver todo
eso. El sistema experto de Einar no cambió.

## 2. Qué cambia para el usuario

No hay pantalla de "Laboratorio" ni etiquetas como "calculado con A\*": el usuario solo ve mejores resultados.

| Función | Qué hace ahora | Algoritmo por dentro |
|---|---|---|
| **Armar una salida** | Las paradas de cada plan salen en el orden más corto. Solo se cambia el orden si sale más corto **y** el sistema experto lo sigue marcando como recomendable | Algoritmo genético |
| **¿Cómo llego?** | Además de caminar, auto, etc., ofrece la opción **en autobús** sobre las rutas registradas, con dónde subir y dónde bajar, y las paradas intermedias | Árbol binario de paradas |
| **¿Cómo llego?** | Si ninguna ruta sola conecta origen y destino, propone una **combinación con transbordo** (`tipo: "combinado"`) | A\* con heurística Euclidiana |
| **Mapa** (app y web) | Marcador verde ↑ (subir), dorado ↓ (bajar), rojo ⇄ (transbordo), el tramo en autobús resaltado, el resto de la ruta tenue y la caminata punteada | — |
| **Asistente** (pestaña nueva en la app) | Chat que responde "¿cómo llego a…?", "¿dónde hay un café?", "ármame un plan…" y "¿qué planes tengo?" con datos reales de Kompás | LLM local (Ollama) + los mismos servicios de arriba |

Lo que **no** se inventa: la espera y la tarifa del autobús van en `null` porque no hay horarios ni tarifas verificados.
Los tiempos se marcan como estimaciones.

## 3. Algoritmos nuevos (`backend/app/ia/`, solo archivos nuevos)

| Archivo | Qué es | Puntos clave |
|---|---|---|
| `busqueda_bfs.py` | Búsqueda en amplitud | Usa el mismo grafo y la misma forma de respuesta que el DFS. Cola FIFO; un nodo descubierto no vuelve a entrar a la cola. Da el camino con **menos aristas** |
| `busqueda_informada.py` | UCS, voraz y A\* + comparativo | Cola de prioridad; solo cambia f(n). Heurísticas Euclidiana (admisible) y Manhattan (no admisible). `comparar_algoritmos()` corre las 7 variantes |
| `algoritmo_genetico.py` | Ordena paradas | Población 60, 150 generaciones, torneo k=3, cruza OX, mutación por intercambio, elitismo 2. Penaliza las visitas fuera de horario. Con ≤ 8 paradas se compara contra fuerza bruta: la peor brecha medida es 0.48 % |
| `orden_optimizado.py` | Conecta el genético con "Armar una salida" | Semilla fija (2026). Agrega `orden_optimizado` a cada plan con los km antes y después |
| `arbol_binario.py` | Árbol binario de búsqueda de paradas | Balanceado por la mediana, ordenado por km a lo largo de la ruta. `mas_cercano()` da dónde subir y bajar; el recorrido inorden da las intermedias |
| `trazos.py` | Paradas de cada ruta | Usa las paradas reales si existen; si no, los puntos del trazo ("Punto N"). Guarda los árboles en caché |
| `transbordos.py` | A\* para transbordos | Caminata ≤ 400 m entre rutas. Costo en minutos: 18 km/h en autobús y 12 min/km a pie, más 5 de penalización por transbordo (solo para la búsqueda; no se suma al tiempo que ve el usuario) |

**Sin tocar:** `motor.py`, `hechos.py`, `reglas.json`, `busqueda_dfs.py` y `metricas_distancia.py`
(`git diff main` vacío).

### Resultados reales del comparativo (red académica del DFS, 64 parejas con camino)

| Algoritmo | Nodos explorados | Aristas del camino | Veces óptimo (km) | Costo ÷ óptimo |
|---|---|---|---|---|
| DFS (primer camino) | 23.8 | 3.34 | 58 % | 1.683 |
| BFS | 5.5 | 2.25 | 94 % | 1.013 |
| UCS | 5.5 | 2.27 | 100 % | 1.000 |
| Voraz (Euclidiana) | 3.4 | 2.34 | 88 % | 1.026 |
| Voraz (Manhattan) | 3.4 | 2.34 | 88 % | 1.025 |
| A\* (Euclidiana) | 3.4 | 2.27 | **100 %** | **1.000** |
| A\* (Manhattan) | 3.4 | 2.25 | 95 % | 1.005 |

Ejemplo para la exposición, de la Terminal a Plaza Sendero:
- El óptimo mide 13.608 km.
- BFS y A\* con Manhattan dan 16.404 km. Es un camino con los mismos 3 tramos, pero más largo.

## 4. API (solo endpoints y campos nuevos; nada existente cambió)

| Método | Ruta | Qué hace |
|---|---|---|
| `GET` | `/api/rutas?origen=&destino=` | **Campos opcionales nuevos** en cada opción: `tipo`, `id_ruta`, `parada_subida`, `parada_bajada`, `tramo_en_ruta`, `paradas_intermedias`, `tramos`, `transbordos`. `modo` ahora puede ser `"autobus"` |
| `GET` | `/api/rutas/{id}/arbol` 🔒 admin | Árbol de paradas de una ruta (raíz, altura y los tres recorridos) |
| `POST` | `/api/itinerarios` | Cada plan trae `orden_optimizado` |
| `GET` | `/api/busqueda/comparar?origen=&destino=` 🔒 admin | DFS, BFS, UCS, voraz y A\* en una tabla |
| `POST` | `/api/genetico/ordenar-paradas` 🔒 admin | Corre el genético con los parámetros que se elijan |
| `GET` | `/api/asistente/estado` 🔒 | ¿Ollama responde? ¿Está el modelo? |
| `GET` / `POST` | `/api/asistente/conversaciones` 🔒 | Lista o crea conversaciones |
| `GET` / `DELETE` | `/api/asistente/conversaciones/{id}` 🔒 | Conversación completa / borrado lógico |
| `POST` | `/api/asistente/conversaciones/{id}/mensajes` 🔒 | Manda un mensaje y recibe la respuesta con tarjetas de ruta o plan |
| `GET` | `/api/dashboard/asistente` 🔒 admin | Uso del asistente (solo datos agregados, nunca el texto de los mensajes) |

La versión de la API ahora es **0.6.0**. La app **nunca** llama a Ollama directo: todo pasa por `/api/asistente`.

## 5. Asistente con Ollama

- **Modelo:** `llama3.2:3b` por defecto, configurable con `OLLAMA_MODELO`. Corre en la misma PC que la API (`OLLAMA_URL`).
- **Herramientas:** `buscar_lugares`, `como_llegar`, `armar_salida` y `mis_planes`. Usan los servicios que ya existían, sin duplicar lógica.
- **Límites:**
  - máximo 3 llamadas a herramientas por mensaje;
  - al modelo se le mandan los últimos 12 mensajes;
  - 2000 caracteres por mensaje.
- **Errores:**
  - Ollama apagado → `503` "El asistente no está disponible en este momento.";
  - conversación de otro usuario → `404`.
- **Lo probé contra el Ollama real de la PC:** contestó "¿Cómo llego…?" con una ruta de la base y redirigió una pregunta fuera de la zona.
- **Modelos chicos:** a veces escriben la llamada a la herramienta como texto JSON; el adaptador la reconoce.

## 6. Base de datos (avisar a Sebas)

| Cambio | Detalle |
|---|---|
| Colección nueva `conversaciones` | Validador `$jsonSchema` e índices `{id_usuario, updated_at}` y `{created_at}`, en `scripts/preparar_bd.py` |
| `planes.origen_solicitud` | Campo opcional nuevo: `"app"` o `"asistente"` |
| `rutas.nombre` y `rutas.paradas` | El código los **lee si existen** (son opcionales). Falta acordar si se agregan al validador y capturarlos |
| `bitacora_laboratorio` | Tipos nuevos de registro: `busqueda`, `genetico`, `transbordo` y `abordaje` |

Privacidad: no se guarda la ubicación del usuario ni datos de Google.

## 7. Web (`frontend/`)

- Migración completa a **TypeScript estricto**: no queda ningún `.js`/`.jsx` en `src/`. ESLint prohíbe `any`, y `npm run build` corre primero `tsc`.
- Tipos compartidos en `compartido/tipos/dominio.ts` y `modulos/dashboard/tipos.ts`.
- **Dashboard, gráficas nuevas:**
  - nodos explorados por algoritmo (DFS / BFS / UCS / voraz / A\*);
  - costo vs. óptimo;
  - convergencia del genético;
  - km ahorrados por el genético;
  - transbordos;
  - el panel "Rutas y paradas" (mapa con paradas numeradas y las más usadas);
  - una pestaña nueva "Asistente".
- Los colores salen de la paleta del dashboard y respetan `COLORIMETRIA.md`.
- Los datos de prueba (`mock.ts`) usan valores calculados con los algoritmos reales, no inventados.

## 8. App móvil (`app/`)

- **Pestaña nueva "Asistente":** lista de conversaciones, chat y tarjetas con **Ver ruta** y **Ver plan**. La app espera la respuesta hasta 120 s.
- **"¿A dónde vas?":** muestra "Sube en … / Baja en …" y los transbordos.
- **Mapa:** marcadores de subida, bajada, transbordo y paradas intermedias, y líneas tenues para el resto de la ruta.
- **Datos de prueba:** el mock del asistente y los traslados ya traen los campos nuevos.

## 9. Pruebas

- **Backend: 320 pruebas pasan.** Antes de la v0.6 había menos de 169. Pruebas nuevas:
  - `test_busqueda_informada.py`
  - `test_busqueda_bfs.py`
  - `test_genetico.py`
  - `test_arbol_binario.py`
  - `test_transbordos.py`
  - `test_asistente.py` (con Ollama simulado)
- **Web:** `lint`, `typecheck` y `build` sin errores.
- **App:** `tsc` y `expo lint` sin errores; la exportación web empaqueta.
- **Pruebas existentes que se ajustaron:**
  - `test_alternativas_de_la_pantalla_buscar`: usa un origen lejos de la ruta de prueba, porque ahora esa ruta sí da opción en autobús. El caso con autobús quedó en una prueba nueva.
  - `test_bitacora`, `test_dashboard` y `test_busqueda_informada`: el comparativo pasó de 6 a 7 filas por BFS.

## 10. Cómo correrlo

MongoDB es **local** (no Docker), en `mongodb://localhost:27017` (`MONGO_URI` en `backend/.env`). Tiene que estar
corriendo antes de levantar la API o las pruebas; las pruebas usan su propia base, `kompas_test`, y no tocan `kompas`.

```powershell
# Ollama (una vez). Si ya tienes llama3.2:latest es el mismo modelo: OLLAMA_MODELO=llama3.2:latest en backend/.env
ollama pull llama3.2:3b

# Backend
cd backend; .\venv\Scripts\activate
python -m scripts.preparar_bd          # crea la colección conversaciones y sus índices
python -m scripts.sembrar_actividad_demo   # opcional: datos demo para el dashboard (marcados como demo)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pytest -q                              # con el MongoDB local corriendo; usa la base kompas_test

# Web
cd frontend; npm install; npm run dev

# App
cd app; npx expo start                 # EXPO_PUBLIC_API_URL=http://<IP de la PC>:8000
```

## 11. Pendientes

| Quién | Qué |
|---|---|
| **Jesús** | Subir el último commit: `67a216e` está en local pero no en GitHub. Después, abrir el PR a `main`; también trae los commits de la v0.5, que aún no están en `main` |
| **Jesús** | Revisar que en `67a216e` no se fueron archivos que no van: `_to_delete/Plan v06.md` y `package-lock.json` de la raíz |
| **Einar** | Revisar los archivos nuevos de `app/ia/`. Su lógica (`motor.py`, `hechos.py`, `reglas.json`) no se tocó |
| **Sebas** | Capturar `nombre` y `paradas` reales en `rutas` y decidir si van al validador. Revisar `conversaciones` y `origen_solicitud` |
| **Sebas** | Cargar trazos de rutas en la base: sin rutas no aparece ninguna opción en autobús |
| **Kevin** | Tomar las capturas del manual de usuario; la lista está en `DOCS/manual-usuario/capturas-v0.6.md` |
| **Equipo** | Regenerar el diagrama de `arbol-binario.md` con una ruta real (hoy usa una ruta de prueba y lo dice) |
| **Equipo** | Activar `GOOGLE_MAPS_API_KEY` para que el asistente encuentre lugares por nombre ("el Cosmovitral") |
| **Equipo** | Revisar visualmente el dashboard y la app en un dispositivo (pasan lint y build, pero no se abrieron en pantalla) |

Notas:
- Siguen en "¿A dónde vas?" los enlaces a la demostración DFS y de distancias, que ya estaban y que pidió Héctor.
- La penalización por transbordo (5) es un parámetro nuevo de la búsqueda. Los 18 km/h del autobús son la misma velocidad que ya usaba la app.

## 12. Documentación nueva o actualizada

- `DOCS/manual-tecnico/`, nuevos:
  - `busqueda-y-heuristicas.md` (DFS, BFS, UCS, voraz, A\*, admisibilidad y tablas reales)
  - `algoritmo-genetico.md`
  - `arbol-binario.md`
  - `ia-en-la-app.md` (qué algoritmo trabaja en cada función)
  - `asistente-llm.md`
- `DOCS/manual-tecnico/`, actualizados: `arquitectura.md`, `modelo-datos-mongodb.md` y `dashboard.md`.
- `DOCS/manual-usuario/capturas-v0.6.md`: la lista de capturas pendientes.
- `README.md`, `backend/README.md` (sección de Ollama y endpoints v0.6) y `CONTEXTO.md`.
