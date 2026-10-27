# Manual técnico — Qué algoritmo trabaja dentro de cada función de la app (Kompás v0.6)

Los temas de Fundamentos de IA trabajan **por dentro** de las funciones normales. En la app móvil y en la web de
usuario **no hay** sección de "Laboratorio" o "IA", interruptores de "optimizar" ni etiquetas como "calculado con A\*":
el usuario solo ve mejores resultados. Los comparativos y gráficas son solo para administradores, en el dashboard.

| Función de la app | Algoritmo | Archivo | Cómo trabaja |
|---|---|---|---|
| **Armar una salida** (itinerarios) | Sistema experto (R01–R20, encadenamiento hacia adelante) | `app/ia/motor.py`, `hechos.py` | Decide qué planes son recomendables y los explica (sin cambios en la v0.6) |
| **Armar una salida** | **Algoritmo genético** | `app/ia/algoritmo_genetico.py`, `orden_optimizado.py` | Siempre, después de `recomendar()`: las paradas de cada plan salen en el orden más corto. Con una parada no se ejecuta. No cambia lo que decide el sistema experto |
| **¿Cómo llego?** (rutas) | **Árbol binario de búsqueda** | `app/ia/arbol_binario.py`, `trazos.py` | Dónde subir y dónde bajar: `mas_cercano(km)` sobre el árbol de paradas de cada ruta; intermedias con el recorrido inorden |
| **¿Cómo llego?** | **A\*** con heurística **Euclidiana** | `app/ia/transbordos.py`, `busqueda_informada.py` | Si ninguna ruta sola conecta origen y destino, busca una combinación con transbordo (`tipo: "combinado"`). Si no hay combinación, no se agrega nada |
| **Asistente** | Todos los anteriores | `app/modulos/asistente/` | Usa los mismos servicios (rutas, itinerarios, lugares), así que sus respuestas ya salen con A\*, el árbol y el orden optimizado |
| **Lugares cercanos / distancias** | Euclidiana y Manhattan | `app/compartido/geo.py`, `app/ia/metricas_distancia.py` | La distancia por calles se estima con Manhattan; la línea recta con Euclidiana (sin cambios) |
| Dashboard (solo admin) | DFS, UCS, voraz y A\* | `GET /api/busqueda/comparar` | Tabla y gráficas comparativas sobre la red académica del DFS |

## A\* para transbordos

- **Nodos:** las paradas de cada ruta (reales o "Punto N" del trazo), más el origen y el destino del usuario.
- **Aristas:**
  - a lo largo de una ruta, en el sentido del trazo: costo = km × `FACTOR_AUTOBUS` (60 / 18 min por km);
  - a pie entre paradas de rutas distintas, o desde el origen / hacia el destino, si están a ≤ 400 m:
    costo = km por calles × `FACTOR_CAMINATA` (12 min por km) + penalización por transbordo (5).
  - Los factores salen de `compartido.traslados` (18 km/h es la misma velocidad de autobús que usa la app en
    `src/utils/geo.ts`). La penalización es un parámetro de la búsqueda para preferir menos transbordos; no es un
    tiempo de espera medido y **no se suma** al tiempo que ve el usuario.
- **Heurística:** Euclidiana en km × `FACTOR_AUTOBUS` (el modo más rápido del grafo). Ninguna arista cuesta menos
  que su línea recta a la velocidad del autobús, así que h es admisible y A\* da la combinación de menor costo.
- **Lo que no se inventa:** la espera (`tiempos.espera: null`) y la tarifa (`tarifa: null`), porque las rutas no
  tienen horarios ni tarifas verificados; la opción lo avisa.
- **Prueba:** `tests/test_transbordos.py` con dos rutas que se cruzan y un origen/destino que solo se conectan con
  transbordo; también revisa que se respete el sentido del trazo y que un camino solo a pie no cuente como transbordo.

## Registro para el dashboard (`bitacora_laboratorio`)

| `tipo` | Cuándo | Campos principales |
|---|---|---|
| `genetico` | Cada plan de "Armar una salida" y cada llamada al endpoint | `origen`, `tipo_plan`, `km_antes`, `km_despues`, `aplicado`, `historial_mejor`, `historial_promedio`, `ms` |
| `transbordo` | Cada búsqueda A\* de combinaciones | `encontrado`, `rutas_usadas`, `nodos_explorados`, `total_nodos`, `ms` |
| `abordaje` | Cada opción en autobús que se ofrece | `id_ruta`, `subida {nombre, lat, lng, km}`, `bajada {…}`, `tipo_opcion` |
| `busqueda` | Cada comparativo del dashboard | `origen`, `destino`, `costo_optimo_km`, `algoritmos[]` |

Igual que con el DFS, si la escritura falla la respuesta se devuelve igual (error silencioso con aviso en el log).
No se guarda la ubicación exacta del usuario: solo las paradas de la ruta.
