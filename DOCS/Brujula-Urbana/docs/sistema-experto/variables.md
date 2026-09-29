# Variables del sistema experto

**Estado:** propuesta 0.1.0 para revisión. **Unidad de evaluación:** un itinerario candidato completo para una solicitud y una hora de consulta determinadas.

## 1. Representación lógica

Cada variable es una proposición. `true` representa evidencia afirmativa y `false` evidencia negativa. `null` representa una proposición todavía sin valor conocido; es una convención del programa para información incompleta, no una afirmación de falsedad.

La regla `NO abierto → descartar` solo se activa con `abierto=false`. No se activa si `abierto=null`. No se aplica la suposición de que todo lo que no aparece en la base de hechos es falso.

El cliente envía preferencias y restricciones. **El backend obtiene o calcula los hechos**, incluyendo presupuesto, apertura y disponibilidad; no confía en un `dentro_presupuesto=true` enviado por el navegador.

## 2. Datos previos a la evaluación

| Dato | Tipo y unidad | Validación / uso |
| --- | --- | --- |
| `origen`, `destino` y paradas | Referencias de lugar o coordenadas | Ubicaciones válidas. Solicitar origen manual si no hay permiso de ubicación. |
| `salida_en`, `zona_horaria` | Fecha ISO 8601 con desplazamiento y zona IANA | Ejemplo de zona: `America/Mexico_City`; no mezclar horarios locales sin fecha. |
| `presupuesto_centavos`, `moneda` | Entero no negativo, moneda `MXN` en el piloto | Presupuesto por persona; rechazar cantidades negativas o monedas incompatibles. |
| `tiempo_disponible_segundos` | Entero mayor que cero | Ventana para todo el plan. |
| `incluir_regreso` | Booleano obligatorio | Define si se calcula también el regreso al origen. Debe verse en el resultado. |
| `modo_solicitado` | Enumeración aprobada por backend | Caminata, transporte público u otros modos realmente integrados. |
| `contexto`, `intereses` | Etiquetas elegidas por el usuario | No inferir gustos o relaciones personales sin su selección. |
| `requiere_accesibilidad` | Booleano declarado por el usuario | Si es verdadero, comprobar requisitos concretos en trayectos y lugares. |
| `caminata_preferida_max_segundos`, `transbordos_preferidos_max` | Enteros no negativos, opcionales | Preferencias para ordenar opciones; no certifican capacidad física ni seguridad. |
| Costos, duraciones y horarios del candidato | Valores con fuente, fecha y unidad | Los datos faltantes permanecen desconocidos. `priceLevel` de un lugar no es un precio exacto. |

Un costo estimado debe identificarse como tal. Cumplir una comparación matemática con una estimación no garantiza el cobro final. Si el usuario necesita un límite estricto, utilizar un máximo verificable; con un precio sin cota suficiente, el hecho queda desconocido.

## 3. Hechos de entrada del motor

| Proposición | Significado de `true` | Evidencia o cálculo | Si falta información |
| --- | --- | --- | --- |
| `datos_usuario_validos` | La solicitud pasó todas las validaciones. | Backend: origen, presupuesto, tiempo y opciones válidas. | Solicitar corrección si se sabe que la entrada es inválida. |
| `modo_disponible` | El modo está habilitado para la zona y solicitud. | Configuración y cobertura verificada del proveedor. | `null`; no asegurar que existe servicio. |
| `ruta_calculada` | Todos los tramos necesarios tienen una ruta utilizable. | Proveedor de rutas o catálogo propio verificado. | Error, timeout o falta de cobertura: `null`. `false` solo ante una respuesta concluyente de inviabilidad. |
| `abierto` | Todas las visitas caben completas en sus intervalos de apertura. | Hora de llegada y fin de visita frente a horarios aplicables a ese día. | `null`; no usar solo «abierto ahora». |
| `dentro_presupuesto` | El costo considerado del plan por persona no excede el presupuesto. | `costo_total_centavos <= presupuesto_centavos`. | `null` si falta un componente necesario. |
| `cabe_en_tiempo` | El itinerario termina dentro de la ventana disponible. | Duración de tramos, esperas, visitas, margen y regreso si se solicitó. | `null` si no se puede calcular el conjunto. |
| `requiere_accesibilidad` | El usuario pidió comprobar accesibilidad. | Preferencia explícita de la solicitud. | Desconocido; pedir el dato. No suponer `false`. |
| `accesibilidad_verificada` | Los requisitos pedidos están verificados en todos los lugares y tramos. | Evidencia específica; no basta una etiqueta general del establecimiento. | `null`; si se solicitó accesibilidad, no recomendar como verificado. |
| `control_cierres_habilitado` | Hay una fuente integrada y operativa para evaluar cierres. | Configuración del servidor. La demo y el MVP sin esa fuente usan `false`. | Es configuración obligatoria; rechazar una entrada ambigua. |
| `cierre_vigente` | Hay un cierre confirmado que afecta algún tramo o visita a la hora prevista. | Fuente admitida, localización, intervalo y fecha de consulta. | `null`. Si el control está deshabilitado, debe ser `null`. |
| `datos_vigentes` | Las evidencias críticas conocidas cumplen la política de vigencia. | Comparar consulta/expiración con la hora de evaluación. | `null` si no se puede establecer; `false` si hay datos vencidos. |
| `contexto_compatible` | Las etiquetas verificadas del plan coinciden con el contexto elegido. | Catálogo propio de etiquetas y preferencia explícita. | `null`; no suma preferencia. |
| `intereses_compatibles` | El plan incluye al menos un interés elegido. | Intersección de etiquetas del plan y del usuario. | `null`; no suma preferencia. |
| `poca_caminata` | La caminata total no excede la preferencia declarada. | Segundos de caminata comparados con el umbral elegido. | `null`; no suma preferencia. |
| `pocos_transbordos` | Los transbordos no exceden la preferencia declarada. | Conteo total frente al umbral elegido. | `null`; no suma preferencia. |

`datos_vigentes` mide frescura documental, no garantiza que la realidad no haya cambiado. La duración máxima aceptada por fuente debe acordarse con backend: este borrador no inventa una caducidad universal. Si un dato expira, su proposición se normaliza a `null` y se conserva una advertencia; un `false` antiguo no debe provocar un descarte presentado como actual.

## 4. Hecho calculado por el motor

`datos_criticos_completos` no se recibe del cliente. La demo lo calcula al comprobar que estos hechos tienen valor booleano:

- Siempre: `datos_usuario_validos`, `modo_disponible`, `ruta_calculada`, `abierto`, `dentro_presupuesto`, `cabe_en_tiempo`, `requiere_accesibilidad`, `control_cierres_habilitado` y `datos_vigentes`.
- Si se requiere accesibilidad: también `accesibilidad_verificada`.
- Si se habilita el control de cierres: también `cierre_vigente`.

Un hecho conocido como falso cuenta como completo, pero puede causar descarte. Completo no significa favorable. Antes de invocar el motor real, el adaptador debe comprobar también la existencia y suficiencia de la evidencia de todos los componentes; la demo solo recibe proposiciones ya preparadas.

## 5. Hechos derivados y estados

| Hecho derivado | Función |
| --- | --- |
| `requiere_correccion` | Detener y corregir una solicitud inválida. |
| `descartar` | Excluir el candidato por una restricción incumplida. |
| `pendiente_verificacion` | Registrar que faltan datos críticos o vigentes. |
| `accesibilidad_resuelta` | No fue requerida o está verificada. |
| `cierres_resueltos` | Se aplicó la política configurada de cierres. No significa «ruta segura». |
| `advertir_sin_cobertura_cierres` | Avisar que no se verifican cierres mediante una fuente integrada. |
| `viabilidad_base` | Se cumplen las restricciones básicas de solicitud, modo, ruta, apertura, presupuesto y tiempo. |
| `recomendable` | Se cumplen las condiciones del modelo para presentar el candidato. |
| `priorizar_contexto`, `priorizar_intereses` | Preferencias de contexto e intereses. |
| `priorizar_caminata`, `priorizar_transbordos` | Preferencias de esfuerzo de traslado. |

Los estados finales son `requiere_correccion`, `descartado`, `pendiente_verificacion` y `recomendable`. La interfaz debe mostrar la explicación y las limitaciones junto a una recomendación.

## 6. Cálculos y condiciones límite

`costo_total = transporte + entradas + consumo_presupuestado + otros_costos + margen_monetario`, con todos los componentes en centavos por persona y en la misma moneda. El consumo presupuestado es una cantidad declarada o una estimación identificada, no el precio verificado de un negocio. Un dato ausente no se convierte en cero.

`duracion_total = traslados + esperas_no_incluidas + visitas + margen_temporal`. Evitar sumar dos veces las esperas que ya incluye el proveedor. Si se pidió regreso, incluir ese tramo. La igualdad con el presupuesto o tiempo disponible se acepta (`<=`).

Para múltiples visitas, evaluar cada llegada en orden y conservar fechas completas, incluidos cruces de medianoche. Una visita que termine después del cierre hace `abierto=false`. Una ubicación omitida no se sustituye por coordenadas cero.

La información de popularidad, reseñas o un texto generado por IA no convierte una restricción incumplida en cumplida. Tampoco se deducen seguridad física, disponibilidad de taxis o precios actuales a partir de la puntuación.
