# Ejemplo de inferencia: una salida en Toluca

**Estado:** ejemplo reproducible en un lugar real, con datos operativos simulados. No documenta una salida realizada ni una consulta a una API de rutas. Para cumplir la parte de «caso real» de la tarea, falta sustituir los supuestos por evidencias actuales de una salida observada.

## 1. Contexto y procedencia

Una persona quiere visitar el Cosmovitral con amigos, le interesan el arte y la botánica, dispone de 100 MXN por persona y tiene dos horas. Desea regresar al punto de partida. La fecha del escenario es el miércoles 30 de septiembre de 2026, con salida a las 11:00 en `America/Mexico_City`.

El Cosmovitral es un lugar real de Toluca. La [ficha oficial del Sistema de Información Cultural](https://sic.cultura.gob.mx/ficha.php?table=museo&table_id=51), consultada el 27 de septiembre de 2026, publica horario de martes a sábado de 10:00 a 18:00 y entrada general de 25 MXN. **La propia ficha indica última modificación del 5 de septiembre de 2024.** Esos valores sirven como referencia histórica para el ejercicio; no certifican apertura o precio en la fecha del escenario.

| Elemento | Procedencia | Tratamiento en el ejercicio |
| --- | --- | --- |
| Lugar y referencia de horario/costo | Ficha oficial citada | Referencia documental con antigüedad identificada. |
| Presupuesto, intereses y tiempo disponible | Persona ficticia del ejercicio | Supuestos de entrada. |
| Origen «Centro de Toluca» | Descripción del escenario | No hay coordenadas ni trazado de ruta verificados. |
| Caminatas de 12 minutos por sentido | Supuesto didáctico | No son tiempos medidos ni de Google Maps. |
| Visita de 60 minutos y margen de 15 | Supuestos didácticos | Duraciones elegidas para explicar la comparación. |
| Apertura, vigencia y ruta utilizables | Hechos sintéticos del archivo de casos | Se suponen verdaderos únicamente para demostrar la inferencia. |

En producción, con solo la ficha antigua y sin verificar los trayectos, varios hechos serían `null` y el resultado sería `pendiente_verificacion`. La demo supone expresamente que esas comprobaciones ya se hicieron; no convierte la consulta del documento antiguo en verificación actual.

## 2. Construcción del candidato A

La variante A propone caminar, visitar el Cosmovitral durante una hora y regresar caminando. Para simplificar no se solicita comprobar accesibilidad. El control integrado de cierres está deshabilitado.

| Componente | Importe por persona / duración | Naturaleza |
| --- | --- | --- |
| Transporte a pie | 0 MXN; 12 minutos de ida y 12 de regreso | Supuesto de ruta peatonal utilizable. |
| Entrada | 25 MXN | Valor histórico usado como supuesto de la demo. |
| Margen monetario | 25 MXN | Reserva declarada para el ejercicio; no es un consumo obligatorio. |
| Visita | 60 minutos | Preferencia del usuario ficticio. |
| Margen temporal | 15 minutos | Margen propuesto, adicional a las caminatas y visita. |
| Total considerado | 50 MXN; 99 minutos | Resultado de las sumas del ejercicio. |

No se incluyó comida ni bebida: la reserva no demuestra que un establecimiento venda un producto a ese precio. Cualquier consumo adicional deberá incorporarse al plan y evaluarse de nuevo.

Comparaciones:

```text
costo_total_centavos = 0 + 2500 + 2500 = 5000
presupuesto_centavos = 10000
5000 <= 10000  → dentro_presupuesto = true

duracion_total_segundos = (12 + 60 + 12 + 15) × 60 = 5940
tiempo_disponible_segundos = 120 × 60 = 7200
5940 <= 7200  → cabe_en_tiempo = true

llegada prevista = 11:12
fin de visita = 12:12
fin del plan con regreso y margen = 12:39
```

La visita de 11:12 a 12:12 cabe dentro del horario supuesto de 10:00 a 18:00. La caminata total de 24 minutos cumple la preferencia ficticia de hasta 30 minutos; cero transbordos cumple la preferencia de hasta uno.

## 3. Base inicial de hechos

| Proposición | Valor |
| --- | --- |
| `datos_usuario_validos`, `modo_disponible`, `ruta_calculada` | `true` |
| `abierto`, `dentro_presupuesto`, `cabe_en_tiempo` | `true` |
| `requiere_accesibilidad` | `false` |
| `accesibilidad_verificada` | `null` — no se solicitó su comprobación. |
| `control_cierres_habilitado` | `false` |
| `cierre_vigente` | `null` — no hay una fuente integrada en el escenario. |
| `datos_vigentes` | `true` — supuesto sintético, no evaluación de la ficha histórica. |
| `contexto_compatible`, `intereses_compatibles` | `true` |
| `poca_caminata`, `pocos_transbordos` | `true` |

El motor obtiene `datos_criticos_completos=true`: todas las proposiciones requeridas por la política del escenario tienen valor booleano. Los dos valores `null` corresponden a comprobaciones no exigidas en esta solicitud.

## 4. Inferencia paso a paso

| Ronda | Regla | Antecedentes satisfechos | Conclusión |
| --- | --- | --- | --- |
| 1 | R11 | NO `requiere_accesibilidad` | `accesibilidad_resuelta`. |
| 1 | R13 | NO `control_cierres_habilitado` | `cierres_resueltos` y `advertir_sin_cobertura_cierres`. |
| 1 | R15 | Solicitud válida, modo, ruta, apertura, presupuesto y tiempo favorables. | `viabilidad_base`. |
| 2 | R16 | Viabilidad base, datos completos y vigentes, accesibilidad y política de cierres resueltas. | `recomendable`. |
| 3 | R17 | Recomendable y contexto compatible. | `priorizar_contexto`: 2 puntos. |
| 3 | R18 | Recomendable e intereses compatibles. | `priorizar_intereses`: 2 puntos. |
| 3 | R19 | Recomendable y caminata preferida. | `priorizar_caminata`: 1 punto. |
| 3 | R20 | Recomendable y transbordos preferidos. | `priorizar_transbordos`: 1 punto. |

No se activan las reglas de descarte. Al terminar la tercera ronda no aparecen conclusiones adicionales. Resultado: `recomendable`, con 6 puntos de preferencias y la advertencia de cierres obligatoria.

Texto de demostración para el usuario:

> Esta opción se ajusta al presupuesto y a las dos horas disponibles en los datos del ejercicio. Coincide con tus intereses y contempla el regreso. Total considerado: 50 MXN por persona y 99 minutos. Esta versión no verifica cierres mediante una fuente integrada. Los datos de esta demostración deben verificarse antes de realizar la salida.

## 5. Dos variantes que muestran los límites

| Candidato | Cambio respecto de A | Reglas activadas | Resultado |
| --- | --- | --- | --- |
| B: visita prolongada | Visita de 150 minutos: total de 189 frente a 120 disponibles; `cabe_en_tiempo=false`. | R06, R11 y R13. | `descartado`; sin puntuación de preferencias. |
| C: costo de traslado desconocido | Se conserva la demás evidencia sintética, pero se plantea un traslado cuyo costo falta; `dentro_presupuesto=null`. | R09, R11 y R13. | `pendiente_verificacion`; sin puntuación. |

En C no se afirma que el transporte sea gratuito ni que el presupuesto se cumpla. En B, la coincidencia con intereses no elimina el exceso de tiempo. Las variantes sirven para probar inferencia; no representan ofertas reales de operadores.

## 6. Reproducción

Desde la raíz del repositorio:

```bash
python3 herramientas/sistema_experto_demo.py
python3 herramientas/sistema_experto_demo.py --json
python3 herramientas/sistema_experto_demo.py --verificar
```

Los datos están en [casos.json](casos.json); las reglas, en [reglas.json](reglas.json). La salida debe indicar A recomendable con 6 puntos, B descartado y C pendiente. La validación incluye valores desconocidos, cierres, accesibilidad, datos vencidos y entradas inválidas.

## 7. Evidencia pendiente para convertirlo en caso observado

Registrar fecha y zona horaria de la salida, origen elegido, trayectos efectivos, duración observada, costo real o verificable, horarios confirmados y fuente de cada dato. Con autorización del participante, usar un origen público y anonimizar datos personales. Conservar solo evidencia cuyo uso y almacenamiento estén permitidos.

Volver a normalizar los hechos y ejecutar la misma base de reglas. Comparar las duraciones y costos considerados con los observados. Si el resultado cambia, documentar el cambio; el objetivo es demostrar el razonamiento y sus límites, no forzar una recomendación favorable.
