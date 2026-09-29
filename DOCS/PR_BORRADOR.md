# Documentar endpoints y completar la guía del primer sprint

El equipo compartió el diagrama que conecta pantallas, API, base de datos y sistema experto. La documentación anterior aún utilizaba rutas tentativas y dejaba pendiente identificar el gestor SQL y el framework. Esta actualización documenta el diseño recibido y hace explícito qué requiere backend para integrar las reglas de Einar.

## Cambios

- Conservar la imagen fuente y transcribir sus 15 operaciones, seis módulos y siete candados.
- Identificar FastAPI y MySQL como tecnologías del diseño, dejando versiones e instalación pendientes.
- Sustituir las rutas tentativas por las del diagrama y documentar `POST /api/itinerarios` como punto de conexión con `recomendar()`.
- Distinguir el motor disponible `evaluar(entrada, base)` de la función de integración que aún no existe en esta rama.
- Documentar acuerdos sobre cuerpos/respuestas, identidad, procedencia de evidencias, guardado de opciones y eventos del historial.
- Añadir una guía de las seis tareas del primer sprint, archivos correspondientes e instrucciones de VS Code.

## Validación

89 enlaces internos, catálogo de endpoints cotejado, bloques de código cerrados y guía con seis tareas. La fuente PNG coincide con el adjunto. Los 39 campos, ocho PK y nueve FK del modelo provisional se conservan; motor, variables, reglas, casos y ejemplo no cambiaron. Git no reportó errores de formato.

Las 36 comprobaciones de inferencia y las 20 reglas ejercitadas pertenecen a la evidencia previa. Este cambio es documental: no se ejecutaron pruebas HTTP, SQL ni comandos de PowerShell.

## Pendientes concretos

Backend debe entregar contratos de entrada/salida, esquema de autenticación, firma de `recomendar()`, política de guardado y versiones/migraciones/comandos. La selección entre varias opciones del mockup debe alinearse con el guardado descrito por el endpoint. Para acreditar el ejemplo como salida real sigue pendiente el registro de campo.

Solicitar revisión de backend antes de integrar a main. Este texto es un borrador local; no acredita la publicación de un pull request.
