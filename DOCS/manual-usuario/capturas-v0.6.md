# Manual de usuario — Capturas de la v0.6 (pendientes)

> Para Kevin (manual de usuario). Las capturas se toman con la app conectada a la API real
> (`EXPO_PUBLIC_USE_MOCK=false`) y Ollama abierto. Guárdalas en `DOCS/manual-usuario/img/` con el nombre indicado.

## 1. Asistente en la app

| Archivo | Pantalla | Cómo llegar |
|---|---|---|
| `asistente-lista.png` | Lista de conversaciones con el botón **Nueva conversación** | Pestaña **Asistente** |
| `asistente-chat-ruta.png` | Chat con la pregunta "¿Cómo llego a …?" y la tarjeta de ruta con **Ver ruta** | Nueva conversación → escribir la pregunta con un lugar de la zona |
| `asistente-escribiendo.png` | Indicador "Escribiendo…" mientras responde | Justo después de enviar un mensaje |
| `asistente-plan.png` | Tarjeta de plan con **Ver plan** | Pedir "Arma un plan con amigos, 300 pesos, 3 horas, comer y café" |
| `asistente-no-disponible.png` | Aviso "El asistente no está disponible en este momento." | Cerrar Ollama y enviar un mensaje |
| `asistente-reabrir.png` | La misma conversación al volver a abrir la app | Cerrar y abrir la app → Asistente → la conversación |

Texto sugerido: el asistente responde con datos de Kompás; si no tiene una ruta, un horario o una tarifa
verificados, lo dice. Los tiempos son estimaciones. Las conversaciones se pueden borrar con el ícono de basura.

## 2. Mapa de una ruta en autobús

| Archivo | Pantalla | Cómo llegar |
|---|---|---|
| `mapa-subida-bajada.png` | Mapa con el marcador **verde ↑** (dónde subir), **dorado ↓** (dónde bajar), el tramo en autobús resaltado, el resto de la ruta tenue, las paradas intermedias como puntos pequeños y la caminata punteada | Buscar un destino sobre una ruta registrada → tocar la opción en autobús |
| `mapa-transbordo.png` | Opción combinada con el marcador **rojo ⇄** de transbordo | Origen y destino que solo se conectan con dos rutas |
| `buscar-opcion-autobus.png` | Tarjeta "Sube en … / Baja en …" debajo de la opción | Pantalla ¿A dónde vas? |

Nota para el texto: si la ruta todavía no tiene paradas capturadas, las paradas aparecen como "Punto N".

## 3. Dashboard (web, administrador)

| Archivo | Pantalla | Cómo llegar |
|---|---|---|
| `dashboard-rutas-paradas.png` | Panel **Rutas y paradas**: trazo con paradas numeradas y círculos azules de las paradas más usadas | Pestaña **Movilidad** |
| `dashboard-laboratorio-busqueda.png` | Nodos explorados por algoritmo y costo vs. óptimo | Pestaña **Laboratorio IA** |
| `dashboard-genetico.png` | Convergencia del genético y km ahorrados | Pestaña **Laboratorio IA** |
| `dashboard-asistente.png` | Pestaña **Asistente** (solo datos agregados) | Pestaña **Asistente** |

Para tener datos en el dashboard sin uso real: `python -m scripts.sembrar_actividad_demo` (todo queda marcado
como demo y se puede ocultar con "Incluir datos demo").
