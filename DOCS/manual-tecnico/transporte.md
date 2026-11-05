# Transporte — comparación y detalle de recorridos

Entrega del 3 de noviembre de 2026 para el cliente Expo de `app/` y el backend
FastAPI. Continúa las mejoras de Mis planes sobre la revisión
`197afb53e493d04d602d3fcb1686017b1b12f14d` de `jirotrash/KompasAPPbeta`.

## Qué cambia para el usuario

En **Buscar**, el usuario puede elegir un destino, cambiar el origen entre su
ubicación y los puntos de referencia disponibles, y comparar alternativas:

- Filtros: todos, autobús, taxi/aplicación o a pie.
- Orden: tiempo calculado, menos caminata o menos transbordos.
- Tarjetas con subida, bajada, transbordos, caminata, espera y tarifa disponible.
- Pasos desplegables para cada autobús y caminata de conexión.
- Acceso al recorrido en el mapa y, cuando hay paradas capturadas en una respuesta
  real, un enlace a Google Maps para caminar al abordaje.
- Actualización de alternativas, indicadores de carga y reintentos ante errores.

La ubicación de referencia se identifica como tal: no se presenta como GPS. Al
cambiar el origen o el destino se dejan de mostrar los resultados anteriores. Una
respuesta tardía no reemplaza la búsqueda más reciente. El mapa utiliza los puntos
y la hora de la consulta que produjo la alternativa seleccionada.

## Corrección de tiempos y calidad de datos

Antes, el listado convertía una espera desconocida en cero y el mapa omitía incluso
la espera conocida. Ahora ambos conservan la distinción entre cero y falta de datos.

| Situación | Presentación |
| --- | --- |
| Caminata 3, trayecto 20 y espera 8 minutos | 31 minutos estimados; la espera se cuenta una sola vez en el mapa. |
| Caminata 3, trayecto 20 y espera desconocida | `23 min + espera`; no se afirma un total ni una hora de llegada posterior al autobús. |
| Todos los tiempos desconocidos | `Sin tiempo disponible`, no cero minutos. |
| Recorrido a pie | Solo requiere el tiempo de caminata; no necesita espera ni trayecto en vehículo. |
| Varios autobuses y una espera agregada conocida | El total la incluye una vez; no se inventa su reparto entre paradas. |
| Origen exactamente en la parada | Caminata de cero minutos; no se añade un minuto artificial. |

El orden **Tiempo calculado** compara la suma de los componentes disponibles. Una
estimación parcial no demuestra que una opción sea la más rápida: la interfaz lo
advierte. Valores totalmente desconocidos se colocan al final. No se modifica la
lista original al ordenar o filtrar.

`paradas_reales: true` significa **paradas capturadas en el catálogo**, no horarios,
tarifas o seguridad física verificados. Cuando es falso, los puntos proceden del
trazo de la ruta; se advierte que hay que confirmar el lugar de abordaje. El enlace
peatonal se ofrece solo para paradas capturadas y fuera del modo de demostración.

Las tarifas y esperas desconocidas aparecen como **Por confirmar** y **Sin dato**.
Taxi y aplicación son alternativas estimadas; ningún botón reserva ni contrata un
viaje. Los tiempos de ejemplo siguen identificados como demostración.

## Arquitectura y archivos

| Archivo | Responsabilidad |
| --- | --- |
| `app/src/app/buscar.tsx` | Origen, filtros, orden, actualización y estados de la búsqueda. |
| `app/src/hooks/useAlternativas.ts` | Vincula cada respuesta con sus puntos y su intento; descarta respuestas obsoletas. |
| `app/src/components/TarjetaTransporte.tsx` | Tarjeta, pasos del viaje, avisos y enlace al abordaje. |
| `app/src/utils/transporte.ts` | Tiempos completos/parciales, filtros, orden y URL peatonal. |
| `app/src/utils/recorrido.ts` | Construcción del mapa con espera separada, sin duplicarla ni inventar llegadas. |
| `app/src/app/(tabs)/mapa.tsx`, `app/src/components/LineaRecorrido.tsx` | Tiempo parcial o estimado y detalle de paradas. |
| `app/src/services/mapas.ts` | Validación y tiempo límite de la respuesta de OSRM. |
| `app/src/components/mapa/html.ts` | Carga de Leaflet con aviso de error y reintento. |
| `app/src/services/mock/traslados.ts` | Ejemplos con caminatas y tiempos coherentes entre tarjeta y mapa. |
| `app/src/types/dominio.ts` | Contrato tipado del cliente. |
| `backend/app/modulos/rutas/esquemas.py`, `servicio.py` | Procedencia de paradas, suma de caminatas y corrección de puntos intermedios. |

Se mantiene Router → Servicio → Repositorio → MongoDB. No se cambia el algoritmo
de búsqueda, los sentidos de circulación, el radio de acceso de 400 m ni las
velocidades estimadas existentes. `backend/app/ia/` permanece intacto.

## API y datos: revisión del equipo móvil

Se conserva `GET /api/rutas?origen=lat,lng&destino=lat,lng&hora=HH:MM`, con sus
validaciones actuales. La consulta sin parámetros sigue devolviendo el catálogo.
Los campos nuevos son opcionales y aditivos:

| Campo | Tipo | Significado |
| --- | --- | --- |
| `alternativas[].paradas_reales` | booleano o null | Si los puntos de abordaje/bajada son paradas capturadas. |
| `alternativas[].caminata_km` | número no negativo o null | Suma de los tramos a pie de la alternativa. |
| `alternativas[].tramos[].paradas_reales` | booleano o null | Procedencia de las paradas de cada tramo de autobús. |

Estos campos se calculan a partir del catálogo existente. Esta mejora de transporte
no añade colecciones ni requiere una migración de MongoDB. El guardado de búsquedas
existente no cambia. Si también se integra Mis planes, revisar sus cambios de
validadores por separado en `mis-planes.md`.

No se añaden endpoints ni dependencias. El equipo móvil debe revisar este contrato
antes de integrar. No se ha enviado un aviso externo ni abierto un PR desde esta
entrega porque la conexión disponible solo permite leer el repositorio.

## Errores y servicios externos

- La búsqueda muestra el error de API y permite reintentar sin conservar tarjetas
  que correspondan a otra consulta.
- OSRM tiene un límite de ocho segundos y valida geometría, coordenadas, distancia
  y duración. Una respuesta inválida o un fallo conserva el mecanismo existente de
  estimación; no se representa como un trayecto confirmado por calles.
- Si no carga la biblioteca de Leaflet, se muestra un aviso y **Reintentar mapa**.
  Los pasos del viaje continúan disponibles. Esto no añade mapas sin conexión ni
  garantiza la disponibilidad de los mosaicos de Esri.
- Google Maps se abre solo al pulsar el enlace, con el origen y la parada elegida.
  Se maneja el error al abrirlo. No se envían credenciales de Kompás en la URL.

## Instalación y comprobación

Se utiliza el entorno del proyecto: Expo SDK 57 y las versiones fijadas por
`app/package-lock.json`; backend con sus archivos de requisitos. WSL puede seguir
siendo el entorno de desarrollo. No hace falta añadir paquetes de ejecución.

Desde `app/`:

```bash
npm ci
node --test tests/transporte.test.cjs
npx tsc --noEmit
npm run lint
EXPO_PUBLIC_USE_MOCK=true npx expo start --web --clear
```

El modo demostración permite revisar la interfaz sin conectarse a MongoDB. Para
validar el contrato real, usar el backend actualizado y `EXPO_PUBLIC_USE_MOCK=false`.
Al cambiar variables `EXPO_PUBLIC_*`, reiniciar Expo con `--clear`: durante esta
revisión se detectó que una exportación reutilizaba el modo anterior desde caché.
En un teléfono, la URL debe ser accesible desde ese dispositivo; `127.0.0.1` apunta
al propio teléfono, no al ordenador.

Desde `backend/`, con un entorno Python activo:

```bash
python -m pip install -r requirements-pruebas.txt
MONGO_URI=mongodb://127.0.0.1:28017 \
JWT_SECRET=clave-local-solo-pruebas-0123456789012345 \
python -m pytest tests/test_transporte.py tests/test_transbordos.py tests/test_planes_guardados.py tests/test_ia.py -q
```

La clave del comando es solo para pruebas locales, no para producción. Estos casos
usan repositorios sobre MongoDB en memoria y servicios externos simulados; no
necesitan ni modifican el clúster del profesor.

## Evidencia de verificación

| Comprobación | Resultado |
| --- | --- |
| Backend: transporte nuevo, transbordos existentes, Mis planes e IA existente | 36 pruebas aprobadas. |
| Cliente: tiempos, cero/desconocido, orden, transbordos, llegadas, enlace y OSRM | 13 pruebas aprobadas con el ejecutor de Node. |
| TypeScript y Expo lint | Aprobados. |
| Exportación web de Expo con el modo API real seleccionado | Compilación completada. |
| Navegador: filtros, cambio de origen, detalle de transbordo y búsqueda sin autobuses | Aprobados con respuestas generadas por el servicio Python e interceptadas en la prueba. |
| Navegador: error 503, reintento y respuesta tardía de otro origen | Aprobados; los resultados anteriores no reaparecen. |
| Navegador: mapa con espera desconocida y fallo/reintento de Leaflet | Sin errores JavaScript; tiempo parcial y aviso visibles. |
| Presentación | Tarjetas revisadas en 390 × 844 y 1440 × 1000; sin desbordamiento horizontal en la búsqueda móvil. |

La prueba de navegador utiliza autenticación y respuestas de API controladas. No
es una comprobación de Atlas, GPS, horarios reales, tráfico ni servicios de terceros
en producción. El timeout de OSRM se comprueba con reloj simulado. El backend
mantiene un aviso de deprecación existente de Starlette/httpx; las pruebas pasan.

## Liberación, mantenimiento y límites

1. Aplicar el parche correspondiente en una rama `feature/*` y revisar el diff.
2. Ejecutar las pruebas y revisar el contrato con el equipo móvil.
3. Publicar primero el backend y comprobar rutas capturadas de desarrollo.
4. Compilar la app con la URL correcta y el modo de ejemplo desactivado.
5. Probar abordaje, transbordos, filtros y reintentos en Android/iOS antes de liberar.

El catálogo debe mantenerse con nombres, sentidos, trazos y paradas correctos. No
hay llegada de autobuses en vivo, tarifas verificadas, reservas ni garantía de
disponibilidad. El parámetro `hora` del endpoint continúa sin intervenir en la
búsqueda; no representa un horario de operación ni una consulta de viajes futuros.
Faltan pruebas en un dispositivo físico y con los proveedores reales. Los servicios
públicos de geocodificación/trazado actuales son de prototipo; el proveedor de
producción sigue pendiente en el proyecto.

Referencias utilizadas: [Expo SDK 57](https://docs.expo.dev/versions/v57.0.0/),
[Expo Linking](https://docs.expo.dev/versions/v57.0.0/sdk/linking/) y
[Google Maps URLs](https://developers.google.com/maps/documentation/urls/get-started).
