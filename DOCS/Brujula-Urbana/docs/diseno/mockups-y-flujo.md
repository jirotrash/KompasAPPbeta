# Revisión funcional de mockups y flujo

**Versión documental:** 0.4.0. **Fecha:** 27 de septiembre de 2026, `America/Mexico_City`. Esta revisión conserva la lectura de Figma de 0.3.0 y actualiza su correspondencia con el diagrama de endpoints.

**Fuente:** [archivo de diseño compartido, página 0-1](https://www.figma.com/design/pqKwMubLEyDuIjO9HnEkZO/Com%C3%B3_MMN?node-id=0-1), clave `pqKwMubLEyDuIjO9HnEkZO`.

## 1. Alcance real de la inspección

Se recuperó la estructura de `Page 1` mediante la integración de Figma: identificadores, jerarquía, nombres de capas, textos, posiciones y dimensiones. La revisión funcional se concentra en seis marcos visibles principales de 402 × 874.

También aparecen dos variantes de acceso/registro (`2056:22` y `2056:80`) y cuatro marcos de la serie `2011` marcados como ocultos. No se asume que los ocultos sean versiones aprobadas ni que el mayor identificador signifique una versión más reciente.

La integración alcanzó su límite de consultas durante la solicitud de capturas. Cuatro solicitudes devolvieron enlaces de imagen, pero al descargarlos se recibió una página «Site Unavailable»; no se pudieron ver las capturas. El navegador, usado con autorización, mostró el mismo mensaje al abrir el diseño.

**La evidencia permite revisar contenidos y estructura; no permite certificar apariencia, contraste, legibilidad, animaciones, recortes o navegación del prototipo.** No se modificaron nodos ni se ejecutaron acciones de los botones. Los campos y textos siguientes proceden de metadatos del archivo, no de una reconstrucción inventada.

## 2. Inventario de seis marcos principales

| Marco y nodo | Contenido recuperado | Implicación funcional |
| --- | --- | --- |
| `iniciar-sesion` — `2035:9` | Correo, contraseña, recuperación, inicio de sesión, Google, Apple y enlace a registro. | Definir autenticación, recuperación y el alcance de acceso social. |
| `registrarse` — `2035:63` | Nombre completo, correo, contraseña, indicador de seguridad, aceptación de términos, creación de cuenta y acceso social. | Alinear campos con `Usuarios` y definir validación en servidor. |
| `inicio-descubrir` — `2009:7` | Marca Kompás, ubicación de ejemplo CDMX, buscador, «Ir a un lugar», «Planear una salida», categorías y lugares cercanos con calificación/distancia/tiempo. | Separar búsqueda de destino de planeación por preferencias; identificar datos de ejemplo. |
| `planificador-inteligente` — `2009:112` | Solo/Pareja/Amigos/Familia; presupuesto de ejemplo $200–$1,500 MXN; 2/4/6 horas o «Todo el día»; intereses; movilidad; «Crear mi plan». | Contrato de solicitud con contexto, presupuesto, tiempo, intereses y modos. |
| `planes-recomendados` — `2009:206` | Opciones equilibrada, rápida y económica; costo, duración, distancia, paradas y descripción. La equilibrada lleva «Mejor opción». | Evaluar viabilidad antes de ordenar y explicar recomendaciones. |
| `mapa-ruta-comunidad` — `2009:303` | Detalles del recorrido, caminata de ejemplo de 3.2 km, etiqueta de 45 min y tres lugares con horas estimadas de llegada. | Modelar paradas y tramos; aclarar qué mide cada duración. El nombre del marco no prueba que haya un módulo comunitario implementado. |

Los nombres y datos personales de ejemplo no se incorporan al diccionario como usuarios reales. Precios, calificaciones y tiempos del mockup tampoco acreditan consultas a proveedores.

## 3. Flujo propuesto a partir de las etiquetas

Esta secuencia es una interpretación funcional para acordar con el equipo; no se comprobaron enlaces interactivos del prototipo:

1. **Acceso:** iniciar sesión o registrarse. El diagrama posterior protege la creación de itinerarios; una modalidad invitada requeriría otro acuerdo. Tampoco se encontró una entrada de invitado entre los textos de los seis marcos revisados.
2. **Inicio:** elegir un destino concreto o configurar una salida.
3. **Solicitud:** confirmar origen, fecha/hora, contexto, intereses, presupuesto, duración, modo e inclusión de regreso.
4. **Evaluación en backend:** consultar fuentes, construir candidatos, normalizar hechos y aplicar las 20 reglas.
5. **Opciones:** mostrar únicamente como recomendables los candidatos que cumplen restricciones; explicar pendientes o ausencia de resultados.
6. **Detalle:** abrir visitas y tramos ordenados, tiempos considerados, costos disponibles y advertencias.
7. **Conservación:** precisar cuándo se guarda la opción elegida. El diagrama de endpoints indica que crear el itinerario ya guarda el plan, por lo que backend debe resolver su relación con la pantalla de selección.

La barra inferior incluye Inicio, Planificar, Mapa y Perfil. No se encontró un marco principal de Perfil ni estados de error en el inventario recuperado de `Page 1`; esto no descarta que existan en otra página o en versiones posteriores.

## 4. Hallazgos para ajustar el flujo

| ID | Evidencia del archivo | Ajuste propuesto |
| --- | --- | --- |
| UI-01 | El planificador muestra «4 horas»; la opción equilibrada tiene «4.5 hrs» y «Mejor opción». | Si son estados de la misma búsqueda, incumple `cabe_en_tiempo`. Ajustar el candidato o mostrarlo descartado; no flexibilizar el tiempo sin que el usuario lo cambie. |
| UI-02 | El presupuesto aparece como intervalo $200–$1,500 MXN. | Aclarar si es por persona o por grupo y cuál es el máximo obligatorio. Un límite inferior de preferencia no debe descartar automáticamente un plan más barato. |
| UI-03 | Existe la opción «Todo el día». | Convertirla en una hora límite o duración concreta; no usar un valor infinito ni una duración fija no explicada. |
| UI-04 | Entre los campos recuperados del planificador no aparecen origen, fecha/hora ni regreso. | Capturarlos o mostrar explícitamente de dónde se heredan; siguen siendo necesarios para horarios, rutas y duración total. |
| UI-05 | Se ofrecen contexto e intereses en grupos separados. | Modelarlos como conceptos diferentes. Acordar si los intereses permiten selección múltiple y reflejarlo en el contrato SQL. |
| UI-06 | Se ofrecen Taxi/App y Combinado. | Limitar cada modo a sus capacidades integradas. Combinado necesita tramos; Taxi/App no implica cotización real de una plataforma. |
| UI-07 | El detalle dice «45 min» y lista llegadas a las 11:00, 12:30 y 14:00. | Indicar si 45 min corresponde solo a traslado; mostrar por separado duración total, visitas, esperas y regreso. |
| UI-08 | Las tarjetas contienen descripciones generales de cada plan. | Añadir razones vinculadas a restricciones y reglas, además de las advertencias; la redacción promocional no explica la inferencia. |
| UI-09 | No aparecen textos de estados sin cobertura, costos desconocidos o datos vencidos en los seis marcos. | Diseñar estados de carga, validación, búsqueda sin opciones y pendiente de verificación. |
| UI-10 | El registro usa «Nombre completo»; el diagrama separa nombre y dos apellidos. | Acordar campos o ajustar el modelo; no partir nombres por espacios automáticamente. |
| UI-11 | Hay botones Google/Apple y recuperación de contraseña. | Confirmar su alcance con backend y documentar identidad externa y recuperación antes de presentarlos como funcionales. |
| UI-12 | La marca visible en las capas principales es Kompás/Kompás App; la documentación usa Brújula Urbana. | Confirmar nombre público y nombre académico. Hasta entonces se conserva el nombre del proyecto del repositorio. |
| UI-13 | La ubicación de ejemplo del inicio es CDMX. | No tomarla como selección aprobada de zona piloto ni como prueba de cobertura; parametrizar la zona real del usuario. |

El término «comunidad» aparece en el nombre de un marco y en un texto de invitación del registro. Eso no confirma reportes, verificación de incidentes ni disponibilidad del módulo. La comunidad sigue fuera del MVP por el acuerdo del equipo.

### Ejemplo concreto de UI-01

Si la opción de 4.5 horas pertenece a la solicitud de 4 horas:

```text
tiempo_disponible_segundos = 4 × 3600 = 14400
duracion_total_segundos = 4.5 × 3600 = 16200
16200 <= 14400 es falso
cabe_en_tiempo = false
R06 → descartar
```

La etiqueta «Mejor opción» debe asignarse después de comprobar restricciones, no antes. Si las pantallas muestran búsquedas distintas, basta identificarlas como escenarios separados para evitar una aparente contradicción.

Para UI-02, el contrato de IA actual usa presupuesto por persona. Si el equipo elige capturar un total de grupo, deberá acordar la conversión y el reparto de costos compartidos antes de alimentar `dentro_presupuesto`.

## 5. Correspondencia con MySQL y los endpoints recibidos

| Función | Contrato de datos necesario | Modelo o endpoint por acordar |
| --- | --- | --- |
| Registro/acceso | Nombre, correo e identidad según mecanismo aprobado. | POST `/api/auth/registro`, POST `/api/auth/login`, GET `/api/auth/yo`; cuerpos y mecanismo pendientes. |
| Búsqueda de lugares | Zona, radio y datos disponibles con fuente; búsqueda por texto pendiente de contrato. | GET `/api/lugares` con `lat`, `lng`, `radio_km`; GET `/api/lugares/{id}`. |
| Solicitud de salida | Contexto, intereses, presupuesto, tiempo, fecha/hora, origen, regreso y movilidad. | POST `/api/itinerarios` llama al motor y guarda en `planes`; precisar contenido y momento del guardado. |
| Comparación | Candidatos con estado, totales, versión de reglas y motivos. | Respuesta del motor; persistencia solo si se justifica. |
| Detalle de ruta | Visitas y tramos ordenados, geometrías, horarios e instrucciones. | GET `/api/rutas` y GET `/api/rutas/{id}` leen rutas; cálculo y detalles adicionales pendientes. |
| Planes e historial | Propietario, instante y referencia del resultado elegido. | GET `/api/planes`; POST y GET `/api/historial`. El POST se vincula a iniciar recorrido. |

El [catálogo completo](../api/catalogo-endpoints.md) conserva las 15 rutas de la nueva fuente y señala sus contratos pendientes. El diseño identifica MySQL, pero no se han creado endpoints ni tablas en esta entrega. La presencia de un campo en Figma no obliga a persistirlo si solo es necesario para evaluar una solicitud.

## 6. Siguiente revisión del diseño

Cuando se pueda obtener una vista o exportación legible, revisar jerarquía visual, contraste, controles, desplazamiento y transiciones. Para cerrar el flujo con el equipo, seleccionar la variante vigente de acceso/registro, confirmar marca y política de invitados, e incorporar estados pendientes y los datos faltantes del planificador.
