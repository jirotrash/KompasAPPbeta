# Brújula Urbana

Proyecto académico de movilidad y planeación de salidas mediante un sistema experto de reglas explicables.

## Entrega de IA y manual técnico

El [índice de entregables](docs/README.md) reúne las seis tareas asignadas a Einar Iván: variables, 20 reglas proposicionales, ejemplo de inferencia y apartados del manual técnico.

Para identificar cada tarea y abrirla en VS Code, comenzar por la [guía del primer sprint](docs/sprint-1/guia-de-entrega.md).

**Estado:** borrador para revisión del equipo. La aplicación todavía no está implementada en esta revisión del repositorio. Se incluye una demostración local del razonamiento, que no consulta mapas, servicios de transporte ni bases de datos.

```bash
python3 herramientas/sistema_experto_demo.py
python3 herramientas/sistema_experto_demo.py --verificar
```

En Windows puede utilizarse `py -3` en lugar de `python3`. La demostración usa únicamente la biblioteca estándar de Python.

## Acuerdos y dependencias

- El almacenamiento vigente es **SQL**; el nuevo diagrama identifica **MySQL** y **FastAPI**. Faltan versiones y configuración. MongoDB queda fuera del alcance actual.
- El módulo de comunidad se pospone. La versión inicial puede recomendar con una advertencia explícita de que no verifica reportes comunitarios de cierres.
- El modelo provisional y los 15 endpoints del equipo ya están transcritos. Faltan DDL/migraciones, contrato detallado de la API, firma de integración del motor y comandos de instalación del servidor.
- Se revisaron los textos, campos y estructura de seis marcos principales de Figma. La inspección visual y las transiciones interactivas no se pudieron verificar.
- Los cambios se presentan en ramas y requieren la revisión del desarrollador de backend antes de integrarse a `main`.

Las propuestas de arquitectura están identificadas como propuestas; la documentación no acredita integraciones, tarifas en tiempo real ni cobertura local de transporte que todavía no se hayan probado.

La [revisión del modelo provisional](docs/modelo-datos/revision-modelo-provisional.md) identifica los ajustes de datos necesarios para alimentar las reglas. La documentación está en versión 0.4.0; las reglas de la demo mantienen la versión 0.1.0. Consultar la [decisión de almacenamiento SQL/MySQL](docs/decisiones/almacenamiento-sql.md), la [revisión de mockups](docs/diseno/mockups-y-flujo.md) y el [catálogo de endpoints](docs/api/catalogo-endpoints.md).
