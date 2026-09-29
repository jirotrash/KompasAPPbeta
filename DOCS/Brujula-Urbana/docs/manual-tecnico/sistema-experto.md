# Manual técnico: sistema experto

## 1. Propósito

El sistema experto de Brújula Urbana evalúa itinerarios según restricciones y preferencias explícitas del usuario. Su función es explicar por qué una opción puede recomendarse, descartarse o mantenerse pendiente de verificación. Las alternativas se valoran individualmente antes de presentarlas como una gama de opciones.

Este componente materializa el uso de lógica proposicional en Fundamentos de IA. La base de conocimiento contiene reglas declaradas por el equipo y revisables por el profesor. No requiere entrenar un modelo ni depende de un chatbot para decidir si un plan cumple el presupuesto.

## 2. Componentes

| Componente | Responsabilidad | Estado en esta entrega |
| --- | --- | --- |
| Captura de solicitud | Recibir origen, destino o contexto, presupuesto, tiempo, regreso y preferencias. | Contrato propuesto; interfaz pendiente. |
| Planificador | Formar itinerarios y pedir rutas entre paradas. | Pendiente del backend. |
| Adaptadores y normalización | Obtener evidencia, comprobar vigencia y calcular proposiciones. | Especificados; integración pendiente. |
| Base de hechos | Hechos de una solicitud y un candidato, sin mezclarlos con otros. | Representada por los casos sintéticos. |
| Base de conocimiento | Las 20 reglas identificadas R01–R20. | Archivo JSON versionado. |
| Motor de inferencia | Aplicar reglas por encadenamiento hacia adelante hasta un punto fijo. | Demostración local implementada. |
| Explicación | Mostrar reglas activadas, razones y advertencias. | Traza y mensajes disponibles en la demo. |
| Selección de resultados | Ordenar candidatos recomendables y presentar hasta tres. | Política documentada; planificador pendiente. |

## 3. Especificación normativa del borrador

Los documentos siguientes forman esta sección del manual y evitan duplicar definiciones:

- [Diccionario de variables](../sistema-experto/variables.md): significados, unidades, fuentes, desconocidos y condiciones límite.
- [Base de reglas](../sistema-experto/reglas.md): antecedentes, conclusiones, prioridades y pesos.
- [Ejemplo resuelto](../sistema-experto/ejemplo-inferencia.md): hechos iniciales, cálculos y tres rondas de inferencia.
- [Contrato lógico de datos](diccionario-datos.md): formato de entrada y resultado; estado del modelo físico.

El archivo `reglas.json` constituye la representación ejecutable de esta versión. Cualquier discrepancia con las tablas debe corregirse antes de aprobar la entrega.

## 4. Secuencia del componente

1. Validar la solicitud y fijar su hora de evaluación.
2. Generar candidatos con paradas y tramos concretos.
3. Recopilar evidencia y normalizar hechos: desconocido o vencido no equivale a falso.
4. Comprobar datos críticos según accesibilidad y la configuración de cierres.
5. Evaluar cada candidato con la misma versión de reglas.
6. Guardar en memoria la traza de inferencia y resolver su estado.
7. Ordenar solo opciones recomendables; presentar también motivos útiles para corregir una búsqueda sin resultados.
8. Volver a evaluar desde cero cuando cambien datos o preferencias.

## 5. Garantías que puede comprobar la demo

La inferencia es determinista para los mismos hechos y la misma base de reglas. Cada regla se activa como máximo una vez; las conclusiones solo se añaden durante una evaluación. Con 20 reglas, el proceso es finito.

No usa `eval`, instrucciones generadas por un modelo ni consultas a una base de datos. Solo compara valores booleanos conocidos con antecedentes declarados. Rechaza cadenas, números y hechos derivados que se intenten inyectar como entrada.

La completitud del contexto real depende del normalizador: el motor de demostración no puede saber si un booleano está respaldado por un horario confiable. Tampoco certifica seguridad física, exactitud de trayectos ni tarifas.

## 6. Alcance del cuatrimestre

El núcleo inicial comprende recomendaciones por restricciones y preferencias, con explicaciones. La comunidad y la verificación de reportes quedan para otra fase. Cuando no exista una fuente de cierres integrada, se usa la política explícita de R13 con su advertencia; no se genera `cierre_vigente=false` por falta de reportes.

Un posible servicio de lenguaje natural puede ayudar a redactar explicaciones, siempre a partir del resultado calculado. Su texto no debe crear destinos, modificar restricciones ni atribuir datos actuales a servicios que no se consultaron.

## 7. Integración con backend

El motor debe ejecutarse en el servidor, separado de los adaptadores de transporte y lugares. El diagrama del equipo ya indica FastAPI y sitúa la IA en `app/ia/motor.py`: `POST /api/itinerarios` obtiene candidatos y llama a `recomendar()`. Esa función aún no está implementada en esta rama. La demo disponible usa `evaluar(entrada, base)` para un candidato ya normalizado; las diferencias y responsabilidades se explican en la [guía de integración](../api/integracion-sistema-experto.md).

El servicio de integración deberá construir itinerarios completos, normalizar evidencias, evaluar y ordenar opciones, y coordinar con backend qué se guarda en MySQL. Las 20 reglas y sus casos conservan el mismo significado. El dibujo no determina la firma de `recomendar()` ni sustituye las pruebas de integración con datos reales.

La aplicación deberá registrar `version_reglas` y un identificador de evaluación. La persistencia de resultados o evidencias requiere un diseño aprobado y las restricciones de las fuentes. No se deben guardar credenciales, ubicación exacta ni respuestas de proveedores indiscriminadamente en logs.

## 8. Verificación y aceptación

El comando `python3 herramientas/sistema_experto_demo.py --verificar` comprueba los casos de demostración y condiciones adversas, incluyendo que una preferencia no rescate una restricción incumplida. Los resultados y las dependencias pendientes se registran en [validación y pendientes](../validacion-y-pendientes.md).

Para aprobar la integración: backend revisa normalización, datos desconocidos, trazas y contratos; el profesor revisa la correspondencia con lógica proposicional. La fusión del pull request a `main` queda sujeta a la revisión del equipo.
