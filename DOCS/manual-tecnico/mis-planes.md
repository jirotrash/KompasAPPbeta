# Mis planes — primera entrega

Preparado sobre `main` de `jirotrash/KompasAPPbeta`, revisión
`197afb53e493d04d602d3fcb1686017b1b12f14d`, el 2 de noviembre de 2026.

## Problema que resuelve

Antes, el recorrido completo dependía del estado temporal de la pantalla. La base
guardaba preferencias y evaluación, pero no las referencias necesarias para volver
a consultar las paradas. Ahora se puede elegir una alternativa y recuperarla después
de cerrar la aplicación, además de cambiar su nombre, marcarla como realizada y
eliminarla de la lista.

Esta entrega corresponde al cliente Expo de `app/` y al backend FastAPI. La
exportación web de Expo permite probar ese mismo cliente desde un navegador.

## Flujo de uso

1. Iniciar sesión y crear una salida desde **Planificar**.
2. Pulsar **Guardar plan…** en la alternativa elegida.
3. En **Mis planes**, abrir la ficha y asignarle un nombre.
4. Pulsar **Consultar recorrido actualizado** para revisar las mismas paradas,
   en el mismo orden, desde el punto de partida actual y a la hora actual.
5. Marcar la salida como realizada o devolverla al estado pendiente.
6. Para quitarla de la lista, pulsar **Eliminar plan** y confirmar.

También se accede a Mis planes desde Perfil. Las tarjetas de planes del asistente
que contienen `id_plan` abren su ficha guardada, aunque la conversación se recargue.
Los resultados generados quedan como borradores hasta elegir una alternativa.

## Arquitectura y archivos

| Capa | Archivos | Responsabilidad |
| --- | --- | --- |
| Pantallas | `app/src/app/mis-planes/index.tsx`, `[id].tsx` | Listado paginado, edición, selección, recuperación y confirmación de borrado. |
| Integración móvil | `app/src/services/api.ts`, `app/src/types/dominio.ts` | Contrato tipado y solicitudes autenticadas. |
| Demostración | `app/src/services/mock/planes.ts`, `motor.ts` | Persistencia de ejemplos por cuenta en el dispositivo y reevaluación del recorrido. |
| API | `backend/app/modulos/itinerarios/router.py`, `esquemas.py` | Validación de entradas y respuestas públicas. |
| Servicio | `backend/app/modulos/itinerarios/servicio.py` | Selección, propiedad del plan y coordinación de la recuperación. |
| Recuperación | `backend/app/modulos/itinerarios/recuperacion.py` | Reconstrucción del recorrido con los hechos, reglas y planificador existentes. |
| Datos | `backend/app/modulos/itinerarios/repositorio.py` | Consultas por propietario, actualización y borrado lógico. |
| Servicio externo | `backend/app/externos/google_places.py` | Place Details de las paradas guardadas y errores recuperables. |
| Esquema MongoDB | `backend/scripts/preparar_bd.py` | Validación opcional de los nuevos campos. |

Se conserva la separación Router → Servicio → Repositorio → MongoDB.
No se modifican los archivos de `backend/app/ia/` ni las reglas R01–R20.
El módulo de recuperación reutiliza los formateadores actuales de `app.ia.servicio`;
si su contrato interno cambia, deben actualizarse conjuntamente la recuperación y
sus pruebas.

## Contrato de API para revisar con el equipo móvil

Todos los endpoints requieren `Authorization: Bearer <token>`.

| Método y ruta | Entrada | Resultado |
| --- | --- | --- |
| `POST /api/itinerarios` | Petición existente | La respuesta añade `id_plan`; conserva los campos anteriores. |
| `GET /api/planes` | `limite` de 1 a 100, por defecto 50; `antes_de` opcional | Fichas propias ordenadas por ID descendente. La app pide páginas de 20. |
| `GET /api/planes/{id}` | ID entero | Ficha propia, alternativas disponibles y estado. |
| `PATCH /api/planes/{id}` | `titulo`, `tipo_seleccionado` o `estado_usuario` | Ficha actualizada. |
| `POST /api/planes/{id}/recuperar` | `origen: {lat, lng}`, `hora_salida: "HH:MM"` | `{peticion, respuesta}` con el recorrido reevaluado. |
| `DELETE /api/planes/{id}` | ID entero | `204`, borrado lógico. |

La ficha añade `titulo`, `estado_usuario`, `tipo_seleccionado`, `tiene_detalle`,
`alternativas` y `actualizado_en`. Cada alternativa contiene `tipo` y
`numero_paradas`. Se conservan los campos originales de la ficha.

El listado incorpora un límite: los consumidores que antes asumían recibir todo el
historial deben recorrer páginas usando como `antes_de` el último ID recibido.
La pantalla nueva ya lo hace.

Ejemplo de selección y nombre:

```json
{"titulo": "Mi salida del sábado", "tipo_seleccionado": "equilibrado"}
```

El nombre admite de 1 a 80 caracteres después de normalizar espacios. Un PATCH
vacío, campos desconocidos, valores nulos o estados inventados producen `422`.
Solo puede elegirse una alternativa producida para ese mismo plan. No se aceptan
paradas arbitrarias enviadas por el cliente.

Estados: `borrador` al generar, `guardado` al elegir y `realizado` al marcar la salida.
Para marcarla como guardada o realizada debe existir una alternativa seleccionada.
Cambiar de alternativa devuelve el plan a guardado, salvo que la petición indique
explícitamente realizado.

## Modelo de datos y recuperación

Los campos nuevos en `planes` son opcionales para preservar los documentos antiguos:

```json
{
  "titulo": "Mi salida del sábado",
  "estado_usuario": "guardado",
  "tipo_seleccionado": "equilibrado",
  "opciones_guardadas": [
    {
      "tipo": "equilibrado",
      "paradas": [
        {"place_id": "referencia_del_lugar_1", "categoria": "comer"},
        {"place_id": "referencia_del_lugar_2", "categoria": "cafe"}
      ]
    }
  ]
}
```

Se mantienen las preferencias y el resumen de la evaluación original. Las nuevas
referencias guardan únicamente identificadores de Places y la categoría de Kompás,
en el orden calculado. No se persisten nombres, horarios, precios ni coordenadas
recibidos de Google, ni el origen GPS exacto del usuario, para esta recuperación.

Al abrir el recorrido se consultan sus referencias en Place Details. Con los datos
recién obtenidos se vuelven a calcular hechos, tiempos, presupuesto y reglas. No se
buscan sustitutos ni se altera el orden. Si las condiciones ya no permiten
recomendarlo, se presentan los motivos y el registro permanece guardado. Si Google
falla o indica que un lugar cerró, se muestra un error y se permite reintentar.
Recuperar no crea otro documento ni reemplaza la evaluación histórica.

Las fichas antiguas siguen visibles, renombrables y eliminables. Si no contienen
referencias de paradas, la app informa que solo existe un resumen y permite crear
otra salida. No se inventan recorridos históricos.

## Aislamiento y manejo de errores

- Todas las consultas y escrituras incluyen el ID del usuario autenticado y
  `deleted_at: null`. Un plan ajeno, ausente o eliminado devuelve el mismo `404`.
- `401`: falta una sesión válida. `409`: falta elegir una alternativa recuperable.
  `422`: entrada inválida o punto fuera de la zona piloto. `503`: servicio externo
  no disponible. Se conservan los manejadores existentes para errores de MongoDB.
- Borrar establece `deleted_at`; el documento permanece en la base, pero deja de
  estar disponible por la API y desde las tarjetas del asistente.
- Los botones bloquean acciones mientras se procesa una solicitud. El listado
  descarta respuestas obsoletas al perder foco y ofrece reintento.
- El estado temporal del viaje se reinicia al cambiar de cuenta. Las credenciales
  y la llave de Google siguen siendo configuración del servidor.

## Instalación y liberación

Usar las versiones fijadas por `app/package-lock.json` y la configuración existente
de `backend/.env`. No se añaden dependencias de ejecución; `mongomock` es una
dependencia exclusiva de las nuevas pruebas. WSL puede utilizarse como entorno de
desarrollo siguiendo la instalación ya existente.

Antes de integrar, el equipo móvil debe revisar el contrato anterior y el responsable
de datos debe revisar los campos opcionales de `planes`. Esta entrega no aplica
cambios al clúster compartido.

1. Integrar el cambio en una rama `feature/*` y abrir un PR a `main`.
2. Instalar dependencias del backend y validar en una base de desarrollo.
3. Con la conexión revisada por el responsable, actualizar validadores e índices:

   ```bash
   cd backend
   python -m pip install -r requirements.txt
   python -m scripts.preparar_bd --sin-datos
   ```

   `--sin-datos` evita cargar ejemplos y conserva los documentos. No utilizar
   `--recrear` en una base con información que se deba conservar.

4. Publicar primero el backend y comprobar una cuenta de prueba. Necesita la llave
   ya configurada de Google Places API (New) con Place Details disponible.
5. Compilar y distribuir la app con `EXPO_PUBLIC_USE_MOCK=false` y
   `EXPO_PUBLIC_API_URL` apuntando a esa API. Revisar `MONGO_DESTINO` y la base elegida
   en el servidor para evitar confundir datos locales con Atlas.
6. Completar una generación, selección, reapertura y borrado de prueba.

Para una demostración sin servicios externos, usar `EXPO_PUBLIC_USE_MOCK=true`.
Los ejemplos se guardan por cuenta en AsyncStorage del dispositivo/navegador y se
identifican como demostración en las pantallas. No se sincronizan con MongoDB.

## Verificación realizada

| Comprobación | Resultado |
| --- | --- |
| API, servicios, repositorios y motor con MongoDB en memoria y Google simulado | 24 pruebas nuevas aprobadas. |
| Pruebas existentes del motor `test_ia.py` | 2 pruebas aprobadas; 26 en la ejecución combinada. |
| TypeScript | `tsc --noEmit` aprobado. |
| Estilo y reglas de Expo | `expo lint` aprobado. |
| Exportación web de la app Expo | Compilación completada. |
| Navegador en modo demostración | Crear, elegir, renombrar, completar, cerrar/reabrir, recuperar, cancelar y confirmar borrado aprobados; sin errores JavaScript. |
| Presentación | Revisada en 390 × 844 y 1440 × 1000; sin desbordamiento horizontal en el listado móvil. |

Comandos desde `backend/`, con el entorno Python activo:

```bash
python -m pip install -r requirements-pruebas.txt
MONGO_URI=mongodb://127.0.0.1:28017 \
JWT_SECRET=clave-local-solo-pruebas-0123456789012345 \
python -m pytest tests/test_planes_guardados.py tests/test_ia.py -q
```

Estos dos archivos usan datos aislados y no requieren un servidor MongoDB. Los casos
cubren la propiedad del plan, campos inválidos, compatibilidad histórica, orden de
paradas, aumento de precios, fallos de Google y borrado lógico. `mongomock` no ejecuta
los validadores BSON; su aplicación debe probarse con MongoDB real antes de liberar.
Las demás pruebas existentes pueden requerir su base de pruebas, según `conftest.py`.

Desde `app/`:

```bash
npm ci
npx tsc --noEmit
npm run lint
npx expo export --platform web
```

## Límites de esta entrega

- La prueba de interfaz se realizó en la exportación web de Expo. Falta la validación
  en un dispositivo Android/iOS real.
- No se hicieron llamadas reales a Google ni se conectó el clúster de Atlas. No se
  ejecutaron cambios de esquema sobre una base compartida.
- El recorrido recuperado se evalúa para hoy y desde el origen actual, con las
  preferencias originales. No implementa agenda futura ni regreso al origen.
- Los importes y horarios se actualizan al consultar; no son una cotización histórica
  garantizada. Un lugar sin datos suficientes puede impedir recomendar el recorrido.
- No incluye compartir planes, sincronización offline ni restauración de borrados
  desde la interfaz. El borrado es lógico y no equivale a purgar datos personales.

Referencias de implementación: [Place Details](https://developers.google.com/maps/documentation/places/web-service/place-details),
[políticas de Places](https://developers.google.com/maps/documentation/places/web-service/policies)
y [rutas protegidas de Expo](https://docs.expo.dev/router/advanced/protected/).
