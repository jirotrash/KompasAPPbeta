# Entregables de Einar Iván

**Proyecto:** Brújula Urbana. **Versión documental:** 0.4.0. **Versión de reglas:** 0.1.0. **Fecha de actualización:** 27 de septiembre de 2026, `America/Mexico_City`.

La asignación recibida corresponde a IA, sistema experto y manual técnico. Al iniciar esta entrega, `main` apuntaba a `83ae9356c85f6abbcab119b0d082c6923ff978b2` y solo contenía `.gitignore`; no había otras ramas, issues ni pull requests publicados. Esta observación describe ese momento, no el estado permanente del repositorio.

**Material y acuerdos posteriores:** modelo provisional de datos, primeros mockups, decisión de SQL y diagrama de endpoints. El último identifica FastAPI, MySQL, 15 operaciones y la llamada a la IA de Einar. Se transcribieron los dos diagramas y se revisaron textos y estructura de seis marcos de Figma. La apariencia y las transiciones siguen sin verificarse por la limitación de acceso descrita en la revisión de diseño.

**Para empezar:** la [guía del primer sprint](sprint-1/guia-de-entrega.md) explica qué mostrar en cada tarea, cómo abrir los documentos en VS Code y cómo ejecutar la demostración.

## Seguimiento de las seis tareas

| Tarea asignada | Entregable | Estado del trabajo | Condición para aceptarlo |
| --- | --- | --- | --- |
| Definir variables; 26 de septiembre | [Variables](sistema-experto/variables.md) | Borrador completo | Backend valida fuentes, vigencia y normalización de cada hecho. |
| Borrador de 15–20 reglas; 27 de septiembre | [20 reglas](sistema-experto/reglas.md) y [reglas.json](sistema-experto/reglas.json) | Borrador completo y ejecutable | Profesor y backend revisan restricciones y prioridades. |
| Ejemplo de inferencia; 28 de septiembre | [Caso de Toluca](sistema-experto/ejemplo-inferencia.md) | Inferencia resuelta con datos de demostración | Falta observar una salida real para acreditar tiempos, costos y apertura actuales. |
| Diccionario a partir del modelo de Sebas, actualizado a SQL/MySQL; 29 de septiembre | [Diccionario](manual-tecnico/diccionario-datos.md) | Ocho entidades y 39 campos transcritos; MySQL indicado en el nuevo diseño | Confirmar versión, rótulos, relaciones y esquema implementado con DDL/migraciones. |
| Sección «Sistema experto»; 29 de septiembre | [Sección del manual](manual-tecnico/sistema-experto.md) | Borrador completo | Aprobar variables, reglas y ejemplo. |
| Arquitectura, tecnologías, API e instalación con entregables de Jesús; 29 de septiembre | [Arquitectura e instalación](manual-tecnico/arquitectura-api-instalacion.md) | Diagrama incorporado, FastAPI/MySQL, 15 endpoints y conexión de IA documentados; instalación de demo disponible | Recibir versiones, esquemas HTTP, firma del motor, migraciones y comandos reales del servidor. |

**Borrador completo no significa aprobado ni integrado en la aplicación.** La demostración verifica reglas sobre hechos ya normalizados; no determina si una calle es transitable ni si una tarifa sigue vigente.

## Orden sugerido de lectura

1. [Descripción del sistema experto](manual-tecnico/sistema-experto.md).
2. [Variables](sistema-experto/variables.md), [reglas](sistema-experto/reglas.md) y [ejemplo](sistema-experto/ejemplo-inferencia.md).
3. [Contrato de datos y pendientes del modelo](manual-tecnico/diccionario-datos.md).
4. [Arquitectura, API e instalación](manual-tecnico/arquitectura-api-instalacion.md).
5. [Validación y decisiones pendientes](validacion-y-pendientes.md).

## Revisión del nuevo material

- [Diagrama original provisional](referencias/diagrama-bd-provisional-2026-09-27.png).
- [Revisión del modelo y correspondencia con IA](modelo-datos/revision-modelo-provisional.md).
- [Mockups y matriz de revisión del flujo](diseno/mockups-y-flujo.md).
- [Decisión vigente de almacenamiento SQL](decisiones/almacenamiento-sql.md).
- [Diagrama original de endpoints](referencias/diagrama-endpoints-2026-09-27.png).
- [Catálogo de los 15 endpoints](api/catalogo-endpoints.md).
- [Integración prevista del motor con backend](api/integracion-sistema-experto.md).

La revisión 0.4.0 incorpora el diagrama de endpoints y una guía de las seis tareas. Conserva el modelo provisional y las 20 reglas; no implementa un servidor ni aplica migraciones a una base de datos.

## Material ejecutable

- [Motor de demostración](../herramientas/sistema_experto_demo.py): encadenamiento hacia adelante, explicación y comprobaciones locales.
- [Base de reglas](sistema-experto/reglas.json): fuente de las 20 reglas, sin dependencia de un framework de backend.
- [Casos de demostración](sistema-experto/casos.json): datos sintéticos y resultados esperados.

La aprobación se registra mediante la revisión del pull request por el equipo. Esta entrega no autoriza fusionar cambios a `main`.
