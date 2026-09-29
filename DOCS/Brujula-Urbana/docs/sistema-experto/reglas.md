# Borrador de 20 reglas proposicionales

**Versión:** 0.1.0. Las reglas de este documento tienen una representación ejecutable en [reglas.json](reglas.json). Los pesos son una propuesta del equipo de IA para revisión; no proceden de una prueba psicométrica ni de un modelo entrenado.

## 1. Notación

`Y` representa conjunción (`∧`); `NO` representa negación (`¬`); `ENTONCES` representa implicación (`→`). Cada antecedente debe estar sustentado por un valor conocido. En particular, `NO P` necesita `P=false`, nunca `P=null`.

Los nombres y sus fuentes están definidos en [variables.md](variables.md). Cada evaluación corresponde a un solo candidato; los hechos de dos rutas no se mezclan.

## 2. Base de conocimiento

| ID | Regla en lenguaje proposicional | Propósito |
| --- | --- | --- |
| R01 | SI NO `datos_usuario_validos` ENTONCES `requiere_correccion`. | Corregir la solicitud. |
| R02 | SI NO `modo_disponible` ENTONCES `descartar`. | Excluir un modo no habilitado. |
| R03 | SI NO `ruta_calculada` ENTONCES `descartar`. | Excluir inviabilidad confirmada de trayecto. |
| R04 | SI NO `abierto` ENTONCES `descartar`. | Respetar los horarios de todas las visitas. |
| R05 | SI NO `dentro_presupuesto` ENTONCES `descartar`. | Respetar el presupuesto. |
| R06 | SI NO `cabe_en_tiempo` ENTONCES `descartar`. | Respetar la duración disponible. |
| R07 | SI `cierre_vigente` ENTONCES `descartar`. | Excluir un cierre confirmado aplicable. |
| R08 | SI `requiere_accesibilidad` Y NO `accesibilidad_verificada` ENTONCES `descartar`. | Respetar accesibilidad solicitada. |
| R09 | SI NO `datos_criticos_completos` ENTONCES `pendiente_verificacion`. | Evitar recomendaciones con vacíos críticos. |
| R10 | SI NO `datos_vigentes` ENTONCES `pendiente_verificacion`. | Pedir actualización de evidencias. |
| R11 | SI NO `requiere_accesibilidad` ENTONCES `accesibilidad_resuelta`. | Resolver una condición que no fue solicitada. |
| R12 | SI `requiere_accesibilidad` Y `accesibilidad_verificada` ENTONCES `accesibilidad_resuelta`. | Resolver accesibilidad verificada. |
| R13 | SI NO `control_cierres_habilitado` ENTONCES `cierres_resueltos` Y `advertir_sin_cobertura_cierres`. | Permitir el MVP con su limitación visible. |
| R14 | SI `control_cierres_habilitado` Y NO `cierre_vigente` ENTONCES `cierres_resueltos`. | Aplicar la comprobación de cierres disponible. |
| R15 | SI `datos_usuario_validos` Y `modo_disponible` Y `ruta_calculada` Y `abierto` Y `dentro_presupuesto` Y `cabe_en_tiempo` ENTONCES `viabilidad_base`. | Reunir las restricciones básicas. |
| R16 | SI `viabilidad_base` Y `datos_criticos_completos` Y `datos_vigentes` Y `accesibilidad_resuelta` Y `cierres_resueltos` ENTONCES `recomendable`. | Habilitar la presentación del candidato. |
| R17 | SI `recomendable` Y `contexto_compatible` ENTONCES `priorizar_contexto`. | Preferencia de contexto. |
| R18 | SI `recomendable` Y `intereses_compatibles` ENTONCES `priorizar_intereses`. | Preferencia de intereses. |
| R19 | SI `recomendable` Y `poca_caminata` ENTONCES `priorizar_caminata`. | Preferencia de caminata. |
| R20 | SI `recomendable` Y `pocos_transbordos` ENTONCES `priorizar_transbordos`. | Preferencia de transbordos. |

Una regla con dos conclusiones, como R13, equivale a derivar ambas proposiciones del mismo antecedente. La advertencia es parte obligatoria de la salida.

## 3. Inferencia y resolución

Se emplea **encadenamiento hacia adelante**: partir de los hechos, activar las reglas cuyos antecedentes se conocen y añadir sus conclusiones hasta no obtener nuevos hechos. Se conserva el identificador, la ronda y la explicación de cada regla activada.

En la demo, una ronda consulta una copia de los hechos disponibles al inicio de esa ronda; las conclusiones nuevas se usan en la siguiente. Cada regla se registra una sola vez, aunque una conclusión ya exista. Así se conservan varias razones de descarte sin generar ciclos.

Las negaciones se aplican a hechos de entrada conocidos, no a conclusiones derivadas ausentes. Al cambiar el presupuesto, la hora o cualquier evidencia, se inicia una evaluación nueva; no se reutilizan conclusiones de la anterior.

El estado final sigue este orden:

1. `requiere_correccion`: solicitud inválida.
2. `descartado`: existe al menos una restricción incumplida.
3. `pendiente_verificacion`: falta información crítica o vigente.
4. `recomendable`: se activó R16.
5. Si ninguna condición resuelve el caso, `pendiente_verificacion` por precaución.

Se conserva toda la traza aunque haya más de un motivo. El orden de precedencia es una política explícita de presentación; no altera el significado de la implicación lógica. Las reglas están diseñadas para impedir una recomendación junto con un descarte a partir de una entrada coherente.

## 4. Orden de las opciones recomendables

Solo los candidatos con estado final `recomendable` reciben una puntuación de preferencias:

| Hecho | Puntos propuestos |
| --- | --- |
| `priorizar_contexto` | 2 |
| `priorizar_intereses` | 2 |
| `priorizar_caminata` | 1 |
| `priorizar_transbordos` | 1 |

El máximo es 6. Esta suma no es una probabilidad, una medida de seguridad ni una garantía de satisfacción. Un candidato descartado no compensa un exceso de presupuesto con intereses coincidentes.

Ordenar por puntuación descendente; en empate, por duración menor, costo considerado menor y finalmente identificador estable. Estos desempates se aplican en el planificador cuando disponga de esas magnitudes. La demo muestra la puntuación individual y no implementa el ordenamiento de rutas reales.

Presentar hasta tres opciones cuando existan, con costo, duración, alcance del regreso y razones. Si solo hay una o ninguna, mostrar ese resultado. Ofrecer al usuario ajustar presupuesto, tiempo o preferencias sin modificarlos automáticamente.

## 5. Control de cambios

Cambiar una condición, significado o peso requiere modificar `reglas.json`, este documento y los casos esperados afectados, incrementar la versión y ejecutar las comprobaciones. El backend revisa la propuesta antes de integrarla. Una explicación generada por un modelo de lenguaje, si se incorpora después, deberá respetar el estado y la traza ya calculados.
