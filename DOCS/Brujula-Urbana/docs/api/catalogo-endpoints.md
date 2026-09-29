# Catálogo de endpoints del equipo

**Versión documental:** 0.4.0. **Fuente recibida:** 27 de septiembre de 2026, `America/Mexico_City`.

Se transcriben los métodos, rutas, candados y relaciones visibles en el [diagrama original](../referencias/diagrama-endpoints-2026-09-27.png). El encabezado identifica **FastAPI** y **MySQL**. Es una especificación de diseño: no se recibió un contrato OpenAPI, cuerpos JSON, respuestas ni código que acredite endpoints ejecutables.

![Diagrama de pantallas, endpoints, MySQL y motor de IA aportado por el equipo](../referencias/diagrama-endpoints-2026-09-27.png)

## 1. Transcripción de las 15 operaciones

En «Candado», **Sí** significa que el dibujo marca acceso protegido; el mecanismo está por definir. **No visible** solo describe la imagen: no certifica que el endpoint sea público. Los propósitos son interpretaciones del nombre y de las flechas.

| ID | Módulo | Método | Ruta observada | Candado | Propósito interpretado y relación visible |
| --- | --- | --- | --- | --- | --- |
| EP-01 | Cuenta | POST | `/api/auth/registro` | No visible | Registrar una cuenta; bloque relacionado con `usuarios` y `residencia`. |
| EP-02 | Cuenta | POST | `/api/auth/login` | No visible | Iniciar sesión; formato de credenciales y resultado pendiente. |
| EP-03 | Cuenta | GET | `/api/auth/yo` | Sí | Consultar la cuenta autenticada. |
| EP-04 | Cuenta | GET | `/api/residencia` | Sí | Consultar la residencia asociada a la identidad. |
| EP-05 | Cuenta | PUT | `/api/residencia` | Sí | Escribir o actualizar residencia; precisar creación, reemplazo y campos opcionales. |
| EP-06 | Catálogos | GET | `/api/categorias` | No visible | Cargar categorías desde `categorias`. |
| EP-07 | Catálogos | GET | `/api/transportes` | No visible | Cargar opciones desde `transportes`. |
| EP-08 | Lugares | GET | `/api/lugares` | No visible | Buscar lugares cercanos en `lugares_de_interes`; se indican `lat`, `lng` y `radio_km`. |
| EP-09 | Lugares | GET | `/api/lugares/{id}` | No visible | Consultar un lugar; tipo y validación de `id` pendientes. |
| EP-10 | Itinerarios / IA | POST | `/api/itinerarios` | Sí | Leer candidatos, llamar a `recomendar()`, guardar el plan y responder. |
| EP-11 | Itinerarios / IA | GET | `/api/planes` | Sí | Consultar planes guardados en `planes`; filtros y formato pendientes. |
| EP-12 | Rutas | GET | `/api/rutas` | No visible | Leer rutas para el mapa desde `rutas`. |
| EP-13 | Rutas | GET | `/api/rutas/{id}` | No visible | Leer una ruta; la base se rotula con geometría `LINESTRING`. |
| EP-14 | Historial | POST | `/api/historial` | Sí | Registrar el evento «iniciar recorrido» en `historial_rutas`. |
| EP-15 | Historial | GET | `/api/historial` | Sí | Consultar historial; filtros y orden pendientes. |

**Recuento:** seis módulos, 15 operaciones y siete marcas de acceso protegido. No se usa el prefijo `/api/v1`: las rutas propuestas en versiones anteriores quedan sustituidas por esta transcripción.

El dibujo abrevia EP-08 como `GET /api/lugares?lat&lng&radio_km`. La ruta es `/api/lugares`; los tres nombres corresponden a parámetros de consulta, que requieren valores. No se ha probado una petición ni se conoce la URL base del servidor. La obligatoriedad, rangos y radio máximo necesitan un esquema de validación.

## 2. Correspondencia entre pantallas y servicios

| Pantalla o acción del diagrama | Operaciones | Datos o componente relacionado |
| --- | --- | --- |
| Login, registro y perfil | EP-01 a EP-05 | `usuarios`, `residencia`. |
| Planificar: cargar opciones | EP-06 y EP-07 | `categorias`, `transportes`. |
| Inicio: cerca de ti | EP-08 y EP-09 | `lugares_de_interes`. |
| Planificar → Tus planes: crear mi plan | EP-10 y EP-11 | Candidatos, `app/ia/motor.py`, `planes`. |
| Mapa: dibujar ruta | EP-12 y EP-13 | `rutas`, `LINESTRING`. |
| Mapa: iniciar recorrido | EP-14 y EP-15 | `historial_rutas`. |

Las ocho entidades del modelo provisional aparecen en los bloques del diagrama de endpoints. El primero usa nombres como `Usuarios`; el segundo los escribe en minúsculas. Esto se registra como correspondencia conceptual, no como cambio automático de nombres físicos en MySQL.

## 3. Flujo observado de creación

El bloque EP-10 enumera tres pasos: leer lugares candidatos, llamar a la IA de Einar y guardar el plan para responder. La flecha al motor se llama `recomendar()` y apunta a `app/ia/motor.py`. El dibujo no especifica sus parámetros ni el formato de retorno.

La integración propuesta se explica en [conexión del motor con backend](integracion-sistema-experto.md). La función ejecutable de esta entrega sigue siendo `evaluar(entrada, base)` en la demo; no se creó `app/ia/motor.py` ni un servidor FastAPI.

## 4. Acuerdos pendientes para convertir el dibujo en un contrato

| ID | Punto concreto | Acuerdo necesario |
| --- | --- | --- |
| API-01 | Hay siete candados, pero no un esquema de autenticación. | Definir sesión o token, vencimiento y cómo obtiene backend la identidad. No asumir JWT. Proteger residencia, planes e historial por propietario. |
| API-02 | EP-10 dice «guarda el plan» y los mockups presentan varias opciones. | Acordar si guarda todas las candidatas, un borrador o la elección del usuario. La consulta `GET /api/planes` no describe cómo seleccionar una opción. Evitar guardar como confirmado un candidato pendiente o descartado. |
| API-03 | El modelo de lugares tiene nombre, coordenadas y referencias. | Determinar de dónde salen horarios, costos, duración de visitas, evidencia de accesibilidad y vigencia. La existencia de una fila no completa esos hechos de IA. |
| API-04 | Las rutas se leen de una tabla con `LINESTRING`. | Definir cálculo o importación de rutas, instrucciones, modo, duración y relación con las paradas. No afirmar que los GET calculan transporte o tarifas en tiempo real. |
| API-05 | Los cuerpos y respuestas no aparecen en el diagrama. | Publicar esquemas de entrada/salida, errores, identificadores y ejemplos; después contrastar el manual con OpenAPI. |
| API-06 | EP-14 se activa al iniciar recorrido. | Precisar campos y momento del historial. No tratarlo como viaje completado; definir cómo evitar duplicados por reintento. |
| API-07 | Figma muestra Google, Apple y recuperación de contraseña. | Definir esas operaciones o posponer esos controles. Las tres rutas `/api/auth/…` observadas no documentan acceso social ni recuperación. |
| API-08 | El endpoint de itinerarios tiene candado. | El flujo vigente de diseño requiere identidad para crear un plan. Una modalidad invitada sería un cambio por acordar, no una capacidad documentada del diagrama. |
| API-09 | Las listas no muestran paginación, filtros ni límites. | Acordar alcance por usuario, orden y límites de categorías, lugares, rutas, planes e historial según su uso. |
| API-10 | El buscador de Inicio admite texto; EP-08 solo muestra coordenadas y radio. | Definir búsqueda por nombre y resolución de un destino escrito. No inventar un parámetro o endpoint de geocodificación como si ya estuviera aprobado. |

Los ajustes son propuestas de revisión; no cambian los 15 endpoints de la fuente ni constituyen tareas de implementación ya aprobadas.

## 5. Datos mínimos del contrato por documentar

Para cada operación, backend debe entregar: propósito, esquema de autenticación cuando corresponda, parámetros, cuerpo y validaciones, códigos y esquemas de respuesta, errores, efecto sobre la base, propiedad de los registros y ejemplos anonimizados. En EP-10 también se requieren la firma de `recomendar()`, la política de guardado y la respuesta sin opciones viables.

FastAPI permite describir operaciones y esquemas mediante OpenAPI y ofrecer documentación interactiva. Esto facilitará el contraste cuando exista el servidor; el dibujo por sí solo no genera una API ejecutable. Referencia: [características oficiales de FastAPI](https://fastapi.tiangolo.com/features/).
