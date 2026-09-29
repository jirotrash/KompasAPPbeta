# Revisión del modelo de datos provisional

**Revisión documental:** 0.4.0. **Recepción y actualización:** 27 de septiembre de 2026, `America/Mexico_City`. **Decisión vigente:** base relacional SQL hasta nuevo aviso, concretada como MySQL en el diagrama de endpoints; MongoDB queda fuera del alcance actual.

Se revisa el [diagrama compartido por el equipo](../referencias/diagrama-bd-provisional-2026-09-27.png). El usuario indicó que tendrá cambios durante el desarrollo. Esta revisión no modifica el diseño original ni crea esquemas de base de datos; registra decisiones que el equipo puede aprobar en su siguiente versión.

La [transcripción de ocho entidades, 39 campos y nueve marcas FK](../manual-tecnico/diccionario-datos.md) conserva lo observado. Los nombres nuevos de este documento son propuestas.

## 1. Qué cubre el borrador

El modelo separa usuarios, direcciones, lugares, categorías, transportes, geometrías de rutas, historial y planes. Esa organización permite iniciar el diccionario y discutir qué datos captura cada flujo. Todavía no demuestra cómo se compone un itinerario ni cómo se obtienen las evidencias que usan las reglas.

## 2. Decisiones antes de implementar

| ID | Observación concreta | Propuesta para revisar | Responsable de decisión |
| --- | --- | --- | --- |
| BD-01 | SQL está confirmado; el diagrama de endpoints identifica MySQL. | Fijar versión, controlador y migraciones con backend. | Sebas y backend. |
| BD-02 | La latitud se lee como `DECIMAL(102,8)`. | Confirmar el rótulo y corregir la precisión para MySQL. Propuesta: `DECIMAL(10,8)` para latitud y validación de −90 a 90. | Autor del modelo y backend. |
| BD-03 | `contraseña: VARCHAR(100)` no especifica si se almacena un hash. | Si hay autenticación propia, documentar `hash_contrasena` con capacidad para el formato generado; `VARCHAR(255)` es una propuesta a validar. Si se delega identidad, almacenar su identificador en lugar de una contraseña local. | Backend. |
| BD-04 | `Planes` incluye acompañantes, tiempo, categoría y transporte. | Definir si representa la solicitud, la opción calculada o un plan guardado; separar esos conceptos si tienen ciclos de vida diferentes. | Backend y equipo de IA. |
| BD-05 | No hay relación visible entre planes y sus lugares/rutas ordenados. | Diseñar paradas y tramos asociados a un itinerario, con orden y tiempos. | Sebas y backend. |
| BD-06 | `tiempo_disponible` y `tiempo_estimado` no tienen unidad. | Usar una unidad explícita en contratos; propuesta: segundos. Distinguir traslado, espera y visita. | Backend y equipo de IA. |
| BD-07 | El historial no tiene fecha del evento. | Definir el evento que registra y añadir su instante cuando se implemente, sin confundir consulta con viaje realizado. | Backend. |
| BD-08 | Cada plan e historial tienen una FK a un transporte. | Precisar si es preferencia. Para viajes multimodales, modelar el modo por tramo y permitir transbordos. | Backend. |
| BD-09 | `Lugares_de_interes.id_usuario` es ambiguo. | Si significa creador, nombrarlo y documentarlo así. Si significa favorito, considerar una asociación usuario–lugar para evitar duplicar un catálogo compartido. | Sebas y producto. |
| BD-10 | La FK `Planes.id_usuario` no tiene un conector claramente visible; otros extremos del dibujo requieren confirmación. | Revisar cardinalidades, nulabilidad, unicidad y borrados con el modelo editable; no derivarlos solo de la captura. | Autor del modelo. |
| BD-11 | `id_cat` y `id_categoria` nombran una referencia equivalente; hay identificadores con ñ. | Acordar una convención, por ejemplo `id_categoria`, `numero_acompanantes` y nombres en `snake_case`; preservar el mapeo al original en la documentación. | Backend. |
| BD-12 | Aparecen domicilio completo y fecha de nacimiento sin un caso de uso documentado. | Definir cuándo son necesarios y si serán opcionales. La consulta de una ruta debe poder usar un origen manual o actual. | Producto y backend. |

La elección del hash es una decisión de implementación: OWASP recomienda algoritmos de almacenamiento de contraseñas como Argon2id y desaconseja texto plano. El tipo `VARCHAR` de la imagen no prueba que ya se esté guardando texto plano; falta especificarlo. Fuente: [Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html).

La corrección de precisión depende del gestor: MySQL limita la precisión de `DECIMAL` a 65. Fuente: [documentación de MySQL](https://dev.mysql.com/doc/refman/8.4/en/precision-math-decimal-characteristics.html).

## 3. Correspondencia con el sistema experto

Los hechos pueden calcularse en memoria con datos del usuario, configuración y proveedores. **No hace falta guardar cada hecho como una columna.** Sí hace falta definir cómo se obtiene, qué significa y cuándo es desconocido.

| Hecho o necesidad de IA | Apoyo visible en el diagrama | Información o contrato pendiente | Efecto de su ausencia |
| --- | --- | --- | --- |
| `dentro_presupuesto` | No se observa un presupuesto en `Planes`. | Presupuesto por persona, moneda y costos considerados con fuente. | `null`; R09 mantiene pendiente la verificación. |
| `cabe_en_tiempo` | Tiempo disponible y estimado, ambos sin unidad. | Duración de todos los tramos, esperas, visitas y regreso; evitar doble conteo. | No se puede afirmar viabilidad con una duración parcial. |
| `abierto` | Lugares con nombre y coordenadas. | Hora/fecha de salida, zona horaria, horarios aplicables y duración de cada visita. | Sin evidencia suficiente, `null`. |
| `ruta_calculada` | `Rutas.ruta` es una geometría. | Respuesta utilizable para origen, destino, hora y modo, con instrucciones. | Una línea sola no acredita una ruta utilizable. |
| `modo_disponible` | Catálogo `Transportes`. | Cobertura comprobada del modo en la zona y solicitud. | Existir en el catálogo no equivale a servicio disponible. |
| Preferencias de contexto e intereses | `Categorias` y `Planes.id_categoria`. | Separar tipo de lugar, contexto de salida e intereses elegidos; acordar etiquetas. | No sumar coincidencias no verificadas. |
| `poca_caminata`, `pocos_transbordos` | No se observan esas magnitudes. | Segundos de caminata y conteo de transbordos por itinerario, frente a preferencias. | No sumar esos puntos de preferencia. |
| Accesibilidad solicitada y verificada | No se observa un dato específico. | Preferencia explícita y evidencia para lugares y trayectos. | Si se solicita y falta evidencia, pendiente. |
| `datos_vigentes` | No se observan fechas de fuente o consulta. | Política de vigencia y procedencia de evidencias. | Reconsultar o marcar datos desconocidos. |
| Cierres | Comunidad fuera del alcance inicial. | Configuración del servidor; fuente futura cuando se integre. | Aplicar R13 y mostrar que no se verifican cierres. |
| Explicación de la decisión | No aparece una evaluación vinculada al plan. | Versión de reglas, estado, reglas activadas y advertencias. | Se puede devolver en la respuesta; decidir después si se conserva y por cuánto tiempo. |

El número de acompañantes sirve para dimensionar una salida, pero no define por sí solo presupuesto por persona, edades, consumo de alcohol o accesibilidad. Esas preferencias deben capturarse explícitamente cuando sean relevantes.

## 4. Propuesta mínima de estructura funcional

Antes de concretar las tablas SQL, distinguir estas unidades:

| Unidad propuesta | Contenido mínimo para el flujo | Relación lógica |
| --- | --- | --- |
| Solicitud | Origen/destino o contexto, presupuesto por persona, moneda, hora, tiempo disponible, regreso y preferencias. | Puede originar varias opciones de itinerario. |
| Itinerario candidato | Referencia a solicitud, totales considerados, estado, versión de reglas y advertencias. | Contiene una secuencia de visitas y tramos. |
| Parada de visita | Referencia de lugar, orden, llegada y duración de la visita. | Pertenece a un itinerario; no se confunde con parada de autobús. |
| Tramo | Origen, destino, orden, modo, duración, caminata, transbordos y costo si está disponible. | Conecta los puntos del itinerario; puede incluir pasos detallados del proveedor. |
| Evidencia | Fuente, consulta, vigencia, unidad y naturaleza estimada/verificada. | Sustenta hechos usados en la evaluación; persistencia sujeta a permiso y necesidad. |

Si `Planes` se aprueba como solicitud, las opciones resultantes pueden modelarse aparte. Si se aprueba como itinerario, habrá que definir dónde vive la solicitud original. En el modelo SQL vigente se propone una relación de paradas por itinerario y otra de tramos, con orden y referencias explícitas. Los nombres de tablas y sus restricciones se aprobarán antes de escribir migraciones.

El contrato de IA actual compara costos y presupuesto por persona. Si la interfaz captura un total de grupo, el equipo debe definir cómo se convierte y cómo se reparten costos compartidos antes de evaluar. El tiempo debe cubrir el plan completo e indicar si incluye regreso. Un cambio de restricciones inicia otra evaluación de las reglas existentes.

## 5. Orden de actualización del modelo

1. Fijar la versión de MySQL y el significado de `Planes`, `Transportes`, `Categorias` e `id_usuario` de lugares.
2. Corregir rótulos y completar relaciones, unidades y nulabilidad.
3. Definir el contrato de solicitud y la estructura de itinerarios con paradas/tramos.
4. Asignar fuentes a los hechos de IA y acordar su vigencia.
5. Publicar una versión del modelo editable y sus migraciones SQL.
6. Actualizar diccionario y contratos; revisar en una rama antes de integrar a `main`.

El módulo de comunidad y la comparación de tarifas de plataformas mantienen el alcance pospuesto de la propuesta. No se crean tablas para ellos como condición para terminar esta revisión.

## 6. Hallazgos al contrastar con los mockups

La [revisión funcional de seis marcos de Figma](../diseno/mockups-y-flujo.md) confirma controles de presupuesto, contexto, tiempo, intereses y movilidad. Su presencia en la interfaz refuerza la necesidad de definir dónde viven esos datos en la solicitud SQL o en el contrato transitorio de evaluación.

- El registro pide un nombre completo, mientras `Usuarios` separa nombre y dos apellidos. Debe acordarse un contrato compatible; no dividir nombres automáticamente por espacios.
- El presupuesto aparece como intervalo en MXN; definir si es por persona y cómo se obtiene el límite máximo usado por `dentro_presupuesto`.
- Los contextos de salida y los intereses aparecen como grupos distintos. No tratarlos como un único `id_categoria` sin precisar su significado y multiplicidad.
- La opción «Combinado» necesita tramos con modos distintos; una FK de preferencia no describe todo el itinerario.
- Google y Apple aparecen como opciones de acceso. Si se implementan, su identidad externa requiere un contrato adicional; los botones por sí solos no prueban una integración ni autorizan almacenar contraseñas de esos proveedores.

Estos ajustes se incorporarán al siguiente modelo aprobado. La captura original y sus 39 campos se mantienen sin alteración para conservar trazabilidad.

## 7. Correspondencia con el diagrama de endpoints

El [catálogo transcrito](../api/catalogo-endpoints.md) vincula las ocho entidades con seis módulos FastAPI. `POST /api/itinerarios` lee candidatos y guarda en `planes`; todavía debe acordarse si conserva solicitudes, alternativas o una elección. `POST /api/historial` corresponde a «iniciar recorrido», lo que refuerza la necesidad de definir evento e instante sin confundirlo con un viaje completado.

Los GET de rutas leen `LINESTRING`, pero no se documenta su carga o cálculo. Los datos de lugares siguen sin acreditar horarios, costos o vigencia. Esos contratos deben completarse para calcular los hechos de IA, aunque las tablas y los endpoints existan.
