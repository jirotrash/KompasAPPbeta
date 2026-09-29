# Primer sprint: tareas de Einar y guía para VS Code

**Proyecto:** Brújula Urbana. **Revisión documental:** 0.4.0. **Fecha:** 27 de septiembre de 2026, `America/Mexico_City`.

Este índice explica qué entregar y mostrar para cada una de las seis tareas asignadas. Los documentos están preparados para revisión; la aprobación corresponde al equipo. No equivale a haber terminado la aplicación.

## 1. Qué corresponde a cada tarea

| N.º | Tarea y fecha asignada | Archivo principal | Qué contiene y qué mostrar | Estado para revisión |
| --- | --- | --- | --- | --- |
| 1 | Definir variables del sistema experto — 26 de septiembre | [variables.md](../sistema-experto/variables.md) | Datos del usuario, 15 proposiciones de entrada, fuentes, unidades y tratamiento de desconocidos. Explicar presupuesto, tiempo y apertura. | Borrador completo; backend valida fuentes y normalización. |
| 2 | Redactar entre 15 y 20 reglas — 27 de septiembre | [reglas.md](../sistema-experto/reglas.md) y [reglas.json](../sistema-experto/reglas.json) | 20 reglas R01–R20; restricciones, preferencias y prioridad de estados. Mostrar por qué una preferencia no rescata una restricción incumplida. | Borrador ejecutable; pendiente aprobación de profesor/backend. |
| 3 | Desarrollar un ejemplo de inferencia — 28 de septiembre | [ejemplo-inferencia.md](../sistema-experto/ejemplo-inferencia.md) | Salida al Cosmovitral, hechos, cálculos, reglas activadas y tres candidatos. Ejecutar la demo y explicar los estados. | Ejemplo resuelto con supuestos explícitos; falta observar una salida real si se exige evidencia de campo. |
| 4 | Elaborar el diccionario desde el modelo de Sebas — 29 de septiembre | [diccionario-datos.md](../manual-tecnico/diccionario-datos.md) | Ocho entidades, 39 campos, PK/FK, relaciones interpretadas y contratos de IA. MySQL según el nuevo diagrama. | Transcripción completa; pendiente contraste con DDL/migraciones y correcciones del modelo. |
| 5 | Redactar la sección «Sistema experto» del manual — 29 de septiembre | [sistema-experto.md](../manual-tecnico/sistema-experto.md) | Propósito, componentes, encadenamiento hacia adelante, explicación, límites y conexión con backend. | Borrador completo; integración con la aplicación pendiente. |
| 6 | Redactar arquitectura, tecnologías, API e instalación con el material de Jesús — 29 de septiembre | [arquitectura-api-instalacion.md](../manual-tecnico/arquitectura-api-instalacion.md) | Diagrama recibido, FastAPI, MySQL, 15 endpoints, motor, flujo y comandos reales de la demo. | Diseño documentado; faltan contratos detallados, versiones y ejecución de la aplicación para cerrar instalación. |

Los números anteriores organizan esta entrega; no se presentan como identificadores oficiales de un tablero Scrum.

## 2. Qué se añadió con el diagrama de endpoints

- [Catálogo de endpoints](../api/catalogo-endpoints.md): transcripción de las 15 operaciones, siete candados y diez acuerdos pendientes de contrato.
- [Integración del sistema experto](../api/integracion-sistema-experto.md): relación entre `POST /api/itinerarios`, `recomendar()` y la función disponible `evaluar(entrada, base)`.
- [Imagen original de endpoints](../referencias/diagrama-endpoints-2026-09-27.png): se conserva para cotejar la documentación.
- [Decisión de almacenamiento](../decisiones/almacenamiento-sql.md): SQL sigue vigente y MySQL queda identificado por el diseño recibido.

Este material complementa principalmente la tarea 6 y precisa la conexión de las tareas 4 y 5. No cambia las 20 reglas, no implementa los endpoints y no crea una base de datos.

## 3. Abrir el paquete en VS Code

Descargar `Entregables_Brujula_Urbana_Einar_v0_4.zip` en Descargas. En Windows, abrir una terminal **PowerShell** y ejecutar:

```powershell
Set-Location "$env:USERPROFILE\Downloads"
Expand-Archive -LiteralPath ".\Entregables_Brujula_Urbana_Einar_v0_4.zip" -DestinationPath ".\Entrega-Brujula-v04"
code ".\Entrega-Brujula-v04\Brujula-Urbana"
```

La carpeta de destino es nueva para esta versión; no sobrescribir el trabajo de una versión anterior. Si el ZIP se descargó con otro nombre o en otra ubicación, ajustar la ruta. Si `code` no está disponible, usar **Archivo → Abrir carpeta** y seleccionar `Entrega-Brujula-v04\Brujula-Urbana`.

Para leer:

1. Abrir `docs/README.md` o este archivo `docs/sprint-1/guia-de-entrega.md` desde el explorador de VS Code.
2. Presionar **Ctrl + Shift + V** para la vista previa Markdown. Para verla al lado del texto, usar **Ctrl + K**, soltar y luego **V**.
3. Seguir los enlaces a cada tarea. Para buscar un archivo directamente, usar **Ctrl + P** y escribir su nombre.
4. Abrir los PNG de `docs/referencias` para ver los diagramas originales. También aparecen dentro de la vista previa donde están insertados.

La vista previa Markdown viene integrada; no es necesario instalar una extensión para leer estos documentos y la imagen del diagrama. Referencia: [documentación oficial de VS Code](https://code.visualstudio.com/docs/languages/markdown).

## 4. Mostrar la parte ejecutable

En **Terminal → Nueva terminal**, comprobar que la carpeta actual sea la raíz del proyecto, donde aparecen `docs` y `herramientas`. Con Python disponible en Windows:

```powershell
py -3 .\herramientas\sistema_experto_demo.py
py -3 .\herramientas\sistema_experto_demo.py --verificar
```

La primera orden muestra los candidatos y su razonamiento. La segunda comprueba las reglas. El resultado esperado, ya registrado en la evidencia previa, es:

```text
OK: 36 comprobaciones; 20/20 reglas activadas al menos una vez.
```

Para leer la salida estructurada:

```powershell
py -3 .\herramientas\sistema_experto_demo.py --json
```

Si tu instalación utiliza `python` en lugar de `py`, sustituir `py -3` por `python`. El entorno comprobado fue Python 3.12.14. La demo usa la biblioteca estándar: no requiere instalar FastAPI, MySQL ni claves de mapas para ejecutarse.

## 5. Orden de exposición sugerido

1. Explicar las variables y la diferencia entre falso y desconocido.
2. Mostrar las 20 reglas y una restricción concreta, como el tiempo máximo.
3. Recorrer el ejemplo de inferencia y ejecutar la demo.
4. Mostrar el diccionario, diferenciando campos del dibujo de correcciones propuestas.
5. Explicar los componentes y límites del sistema experto.
6. Abrir el diagrama de endpoints, ubicar EP-10 y explicar cómo backend preparará los hechos y utilizará el resultado.

Para la tarea 6, decir con precisión: «El diseño usa FastAPI y MySQL; crear un itinerario llama al motor de IA. La inferencia local ya se puede demostrar; falta integrar la normalización, la API y el guardado».

## 6. Qué sigue pendiente y qué se entrega

Se entregan documentos, fuentes gráficas, reglas y demo. La observación de una salida real, la validación del esquema MySQL y la instalación del servidor requieren evidencia adicional del equipo. No se marcan como terminadas solo por tener un diagrama.

La copia del ZIP sirve para lectura y ejecución local, pero no incluye el directorio de Git. Para incorporar cambios al repositorio, el paquete trae instrucciones y dos parches: uno completo desde el estado inicial y otro incremental desde la revisión 0.3.0. Elegir el que corresponda; no aplicar ambos a la misma historia. Trabajar en una rama y dejar la integración a `main` para la aprobación de backend.
