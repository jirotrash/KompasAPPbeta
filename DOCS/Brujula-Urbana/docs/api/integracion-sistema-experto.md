# Integración del sistema experto con los endpoints

**Versión documental:** 0.4.0. **Estado:** diseño de integración para revisión de Einar y backend. Las 20 reglas y la demo conservan la versión 0.1.0.

## 1. Punto de conexión del diagrama

El [catálogo transcrito](catalogo-endpoints.md) identifica `POST /api/itinerarios` como la operación que obtiene candidatos, invoca `recomendar()` de `app/ia/motor.py`, guarda el plan y responde. Esa es la frontera de integración prevista para la IA.

| Elemento | Disponible en esta rama | Previsto por el diagrama |
| --- | --- | --- |
| Reglas | [20 reglas JSON](../sistema-experto/reglas.json), R01–R20. | Aplicarlas en el servidor conservando versión y significado. |
| Inferencia | `evaluar(entrada, base)` en [la demo](../../herramientas/sistema_experto_demo.py). | Invocarla desde una capa que gestione varios candidatos. |
| Entrada de la aplicación | [Variables y magnitudes propuestas](../sistema-experto/variables.md). | Cuerpo de `POST /api/itinerarios`, pendiente de contrato. |
| Función de integración | No implementada. | `recomendar()` en `app/ia/motor.py`; firma y resultado por acordar. |
| Datos y guardado | Casos sintéticos locales, sin conexión SQL. | Candidatos de `lugares_de_interes` y persistencia en `planes`. |

`recomendar()` no es un endpoint HTTP. Es una función interna del backend. No se necesita crear una ruta pública que acepte conclusiones lógicas del navegador.

## 2. Responsabilidades propuestas

| Responsable | Trabajo dentro del flujo |
| --- | --- |
| Interfaz | Capturar restricciones, mostrar datos estimados/desconocidos y explicar resultados. |
| Endpoint FastAPI | Validar solicitud e identidad, llamar al servicio, traducir resultados a la respuesta y coordinar el guardado acordado. |
| Servicio planificador | Construir itinerarios completos a partir de candidatos, con paradas, tramos y regreso cuando corresponda. |
| Adaptadores y normalizador | Obtener evidencias, comprobar vigencia y transformar magnitudes en hechos `true`, `false` o `null`. |
| Motor de Einar | Evaluar cada conjunto de hechos con las 20 reglas, resolver estado y devolver traza. |
| Acceso a MySQL | Consultar y guardar datos bajo el esquema aprobado y asociados al usuario autorizado. |

Las capas de planificación y normalización son necesarias para integrar la demo con datos reales; no se presentan como módulos que ya existan en el diagrama o en el código.

## 3. Secuencia propuesta para EP-10

1. Comprobar la identidad marcada como obligatoria en el diagrama y validar la solicitud.
2. Resolver origen, fecha/hora, presupuesto, duración, preferencias, movilidad e inclusión de regreso.
3. Obtener lugares candidatos. Cada lugar es una posible parada; no es por sí solo un itinerario evaluable.
4. Construir alternativas completas y calcular sus tramos, visitas, esperas y costos considerados.
5. Obtener las evidencias críticas y normalizar los hechos por candidato. Datos ausentes o vencidos permanecen desconocidos.
6. Aplicar `evaluar(entrada, base)` a cada candidato sin mezclar sus hechos.
7. Separar estados y ordenar únicamente los recomendables por preferencias. Conservar razones de descarte o falta de información.
8. Guardar según la política que se acuerde para `planes` y responder con las opciones, razones y advertencias.

La elección entre guardar candidatos, un borrador o el plan seleccionado sigue pendiente (API-02). La integración no debe convertir automáticamente una opción descartada o pendiente en un plan confirmado ni ocultar el fallo si el guardado prometido no se realizó.

## 4. Contrato lógico por acordar

Estos datos especifican necesidades de IA; **no son un esquema HTTP aprobado** ni un JSON que ya pueda enviarse a un servidor.

| Grupo | Datos y criterio |
| --- | --- |
| Identidad | Resuelta por backend desde la autenticación. Un `id_usuario` enviado por el cliente no acredita propiedad. |
| Solicitud | Origen/destino o contexto, intereses, fecha/hora y zona, presupuesto en centavos por persona, moneda, tiempo en segundos, modo, regreso y accesibilidad. |
| Candidato | Identificador, paradas y tramos ordenados, costos y duraciones completos con alcance explícito. |
| Evidencia | Fuente, instante de consulta, vigencia, unidad y naturaleza verificada/estimada. |
| Hechos para el motor | Solo los nombres de entrada admitidos en el [diccionario de variables](../sistema-experto/variables.md); nunca hechos derivados del cliente. |
| Resultado del motor | `estado`, `puntuacion_preferencias`, `version_reglas`, `traza`, `advertencias`, hechos iniciales y derivados. |
| Respuesta de aplicación | Vincular cada resultado a su candidato y a los totales mostrados. Identificar si fue guardado, si incluye regreso y qué datos faltan. |

La firma real de `evaluar()` y su retorno se describen en el [diccionario](../manual-tecnico/diccionario-datos.md). La firma de `recomendar()` queda pendiente; no se supone que los paréntesis vacíos del dibujo signifiquen una función sin entradas.

## 5. Estados que debe respetar la interfaz

| Estado del motor | Comportamiento propuesto de la app |
| --- | --- |
| `requiere_correccion` | Pedir corregir la solicitud; no mostrarla como un plan validado. |
| `descartado` | Explicar la restricción incumplida; excluir de las recomendaciones. |
| `pendiente_verificacion` | Mostrar el dato crítico faltante y la limitación; no etiquetar como confirmado o «Mejor opción». |
| `recomendable` | Mostrar como opción según la evidencia disponible, conservando estimaciones y advertencias. |

El estado lógico no determina automáticamente un código HTTP. Los códigos de validación, autenticación, ausencia de opciones y fallos de dependencias deben acordarse en el contrato de backend.

## 6. Verificaciones para aceptar la integración futura

- Una solicitud de cuatro horas descarta un candidato de cuatro horas y media aunque coincida con todos los intereses.
- Un costo crítico desconocido no se transforma en cero para cumplir el presupuesto.
- Leer coordenadas de un lugar o una geometría de ruta no demuestra apertura, modo disponible ni duración total.
- Un usuario solo consulta o modifica sus planes, residencia e historial conforme al contrato de propiedad aprobado.
- Un reintento de creación o de inicio de recorrido no genera duplicados indebidos; acordar el mecanismo con backend.
- La respuesta conserva versión de reglas, razones, advertencias y estado de guardado.

Estos son criterios de aceptación pendientes de pruebas con la API real. La demo actual verifica la inferencia sobre datos normalizados, no autenticación, MySQL, persistencia ni respuestas HTTP.
