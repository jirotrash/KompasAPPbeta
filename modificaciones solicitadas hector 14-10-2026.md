# Modificaciones solicitadas — Héctor — 14-10-2026

## Objetivo

Integra la demostración del algoritmo de búsqueda en profundidad (DFS) en el backend local de Kompás. Mantén esta demostración separada de las rutas operativas mientras no existan líneas y paradas verificadas en la base de datos.

## Archivos nuevos e integrados

- `backend/app/ia/busqueda_dfs.py`: Define el grafo académico, ejecuta DFS, evita ciclos, limita la profundidad, registra la exploración y devuelve todos los caminos encontrados mediante backtracking.
- `backend/app/routers/dfs.py`: Publica los endpoints `GET /api/dfs/paradas` y `GET /api/dfs/buscar`.
- `backend/app/esquemas/dfs.py`: Valida y documenta la respuesta de la demostración.
- `backend/tests/test_busqueda_dfs.py`: Comprueba control de ciclos, todas las soluciones, límite de profundidad y señalización de datos no verificados.
- `app/src/app/dfs.tsx`: Añade la pantalla móvil del laboratorio DFS. Permite elegir origen, destino y profundidad, y presenta exploración, caminos, tramos, transbordos y tiempos estimados.

## Archivos existentes modificados e integración específica

- `backend/app/main.py`: Registra el router DFS para que FastAPI habilite los endpoints bajo `/api/dfs`.
- `app/src/app/_layout.tsx`: Registra la pantalla `dfs` en el navegador protegido por sesión y le asigna el título **Demostración DFS**.
- `app/src/app/buscar.tsx`: Incorpora el acceso **Ver demostración DFS** desde la pantalla de búsqueda habitual, sin modificar el comportamiento de `/api/rutas`.
- `app/src/services/api.ts`: Centraliza las solicitudes `listarParadasDfs()` y `buscarRutasDfs()` al backend. Estas solicitudes no usan el modo mock porque el grafo DFS vive en la API local.
- `app/src/types/dominio.ts`: Declara los tipos TypeScript de parada, tramo, ruta y respuesta DFS para validar el intercambio de datos entre pantalla y backend.

## Uso

1. Inicia el backend desde `backend/` con `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`.
2. Consulta `GET /api/dfs/paradas` para obtener los identificadores disponibles.
3. Ejecuta `GET /api/dfs/buscar?origen=TerminalToluca&destino=PlazaSendero&limite_profundidad=5`.
4. Interpreta `orden_exploracion` como el orden DFS y `rutas` como todos los caminos simples encontrados dentro del límite de aristas.

## Visualización en la aplicación móvil

1. Configura `EXPO_PUBLIC_USE_MOCK=false` y `EXPO_PUBLIC_API_URL` con la dirección accesible del backend; en un teléfono usa la IP local de la computadora, no `localhost`.
2. Inicia el backend y la aplicación Expo.
3. Abre la pantalla **¿A dónde vas?** y presiona **Ver demostración DFS**.
4. Selecciona una parada de origen, una parada de destino y el límite de profundidad.
5. Presiona **Explorar rutas DFS** para enviar la petición al endpoint `/api/dfs/buscar`.
6. Revisa el orden de exploración, el total de caminos, cada secuencia de paradas, los tramos, los transbordos, el tiempo estimado y la gráfica de indagación.

La pantalla no muestra costo porque el backend no dispone de tarifas verificadas. También presenta de forma visible el aviso de que la red es académica y no representa recomendaciones de transporte real. La búsqueda normal permanece en `/api/rutas`; el laboratorio DFS no modifica sus resultados.

## Corrección de selección y gráfica de indagación

- Se eliminó el origen automático por ubicación actual. La parada más cercana podía ser Plaza Sendero, un nodo sin conexiones salientes, y ocasionaba resultados sin caminos aunque la búsqueda funcionara correctamente.
- Se restauraron los selectores manuales de parada de origen y destino. La pantalla propone Terminal de Autobuses de Toluca como origen y Plaza Sendero Lerma como destino, pero el usuario puede cambiar ambos antes de ejecutar DFS.
- Se agregó una traza real en el backend. Cada evento registra el número de paso, nodo, profundidad, camino actual y una de estas decisiones: visita, avance, ciclo evitado, objetivo alcanzado, límite de profundidad o retroceso.
- Se agregó la **Gráfica de indagación** en la app móvil. Muestra la secuencia vertical de decisiones, la sangría por profundidad y el camino parcial de cada evento; así permite explicar visualmente cómo DFS explora ramas y realiza backtracking.

Archivos modificados para esta corrección:

- `backend/app/ia/busqueda_dfs.py`: Genera y devuelve la traza de ejecución DFS.
- `backend/app/esquemas/dfs.py`: Declara el modelo `PasoDFS` y agrega `traza` a la respuesta.
- `backend/tests/test_busqueda_dfs.py`: Verifica ciclos evitados, objetivos y límite de profundidad en la traza.
- `app/src/types/dominio.ts`: Declara el tipo TypeScript `PasoDFS`.
- `app/src/app/dfs.tsx`: Restaura origen manual y dibuja la gráfica de indagación.

## Alcance obligatorio

- Presenta la red como una demostración académica; no la presentes como información de transporte real.
- Conserva `/api/rutas` sin cambios: ese endpoint debe seguir indicando que no hay información suficiente de transporte público hasta cargar datos verificados.
- Sustituye `PARADAS_KOMPAS` y `GRAFO_TRANSPORTE` por datos aprobados por el equipo antes de usar DFS para recomendaciones de viaje.
- Conserva la señalización `datos_verificados: false` y el aviso de la respuesta hasta validar la fuente de cada parada, conexión y tiempo.

## Criterios cubiertos

- Registra el orden de exploración.
- Evita ciclos al no visitar nodos que ya pertenezcan al camino actual.
- Encuentra todos los caminos simples mediante backtracking.
- Aplica un límite máximo de profundidad expresado en aristas.
