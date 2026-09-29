# Validación y decisiones pendientes

**Fecha:** 27 de septiembre de 2026, `America/Mexico_City`. **Versión documental:** 0.4.0. **Versión de reglas:** 0.1.0. La validación corresponde al material de esta rama, no a una aplicación desplegada.

## 1. Evidencia reproducible

Entorno utilizado: Python 3.12.14. Comandos desde la raíz del repositorio:

```bash
python3 herramientas/sistema_experto_demo.py --verificar
python3 herramientas/sistema_experto_demo.py
python3 herramientas/sistema_experto_demo.py --json
```

La verificación de la versión 0.1.0 resultó en **36 comprobaciones correctas**, con las **20 reglas activadas al menos una vez** entre los casos. Código, reglas y casos permanecen sin cambios en esta revisión documental. Se comprobó:

- Resultado y secuencia de inferencia de los candidatos A, B y C.
- Descarte por modo, ruta, apertura, presupuesto o tiempo incumplidos.
- Corrección de solicitudes inválidas y prioridad frente a otros estados.
- Datos críticos desconocidos y evidencia vencida.
- Cierre confirmado, ausencia evaluada de cierres y fuente habilitada sin información suficiente.
- Accesibilidad solicitada: verificada, incumplida o desconocida.
- Preferencias faltantes sin convertirlas en restricciones obligatorias.
- Rechazo de cadenas, números, configuración inconsistente e inyección de hechos derivados.
- Mismo estado, puntuación y conclusiones al invertir el orden de las reglas.

La revisión de archivos incluye enlaces locales, sintaxis JSON y diferencias de Git. No se ejecutaron consultas de rutas, cotizaciones, conexiones de base de datos ni pruebas de una aplicación, porque esas integraciones no existen en esta entrega.

La revisión documental 0.2.0 añade la lectura de la imagen de base de datos y su transcripción: ocho entidades, 39 campos, ocho marcas PK y nueve marcas FK. Se conserva la imagen original para cotejo. Las descripciones y propuestas se diferencian de los nombres y tipos observados; no se certifican restricciones ausentes de la imagen.

En la revisión 0.2.0 se verificaron 44 enlaces locales, los recuentos de campos y claves, y la igualdad de la imagen archivada con el archivo recibido. Las comprobaciones lógicas de la versión 0.1.0 se conservan como evidencia previa; no se presentan como nuevas pruebas de una aplicación.

La revisión 0.3.0 incorpora la decisión vigente de SQL y la lectura de metadatos de Figma: seis marcos principales, sus textos y estructura. La matriz de flujo ya compara esos contenidos con el sistema experto y el modelo provisional. No se comprobaron interacciones ni apariencia: la integración alcanzó su límite de consultas y tanto los enlaces de capturas como el navegador autorizado devolvieron «Site Unavailable». No se afirma haber visto las capturas ni se modificó el archivo de diseño.

En la revisión 0.3.0 se comprobaron 51 enlaces locales, el inventario de seis marcos y 13 hallazgos, y la conservación exacta de nombres, tipos y marcas de los 39 campos frente a la revisión anterior. El motor, las reglas, los casos y la imagen del modelo conservaron sus bytes. No se repitieron pruebas del motor para ese cambio documental.

La revisión 0.4.0 incorpora el diagrama de endpoints: seis módulos, 15 operaciones y siete candados. Se cotejaron los métodos y rutas con la imagen y se conserva el original. FastAPI y MySQL quedan identificados como tecnologías del diseño recibido. La consulta del repositorio remoto al preparar esta revisión mostró únicamente la rama `main`, en `83ae9356c85f6abbcab119b0d082c6923ff978b2`, sin código de aplicación que permitiera probar esas operaciones. Esta observación corresponde al momento de consulta, no garantiza el estado posterior del repositorio.

Se verificaron 89 enlaces locales en 15 archivos Markdown, cierre de bloques de código, catálogo de 15 operaciones, siete candados, diez acuerdos API y correspondencia de las seis tareas. La firma documentada `evaluar(entrada, base)` coincide con la demo. Se conservaron los 39 campos, ocho PK y nueve FK; la imagen de endpoints coincide byte por byte con el adjunto. Código, variables, reglas, casos y ejemplo no cambiaron. `git diff --check` no reportó errores. No se repitieron pruebas del motor ni se ejecutaron comandos de PowerShell en este entorno Linux; los pasos de Windows se entregan como instrucciones.

## 2. Límites de la evidencia

Las comprobaciones operan sobre proposiciones ya normalizadas. Todavía no prueban cálculos con respuestas reales, límites de fechas de apertura, cambios de zona horaria, tiempos de traslado ni vigencia de precios. La futura normalización debe comprobar esos aspectos con las fuentes aprobadas antes de utilizar el motor en resultados reales.

El caso de Toluca usa un destino existente, una referencia documental histórica y supuestos operativos explícitos. No debe presentarse al profesor como una salida observada ni como evidencia de precisión del sistema.

## 3. Dependencias concretas

| Responsable de referencia | Material pendiente | Permite completar |
| --- | --- | --- |
| Sebas / backend | El diagrama provisional ya fue recibido. Faltan confirmación de rótulos y relaciones, DDL/migraciones SQL y política de índices. | Contrastar el diccionario transcrito con el esquema implementado. |
| Sebas / backend | SQL está confirmado y el diagrama identifica MySQL; faltan versión y controlador. | Concretar conexión, tipos espaciales y migraciones. |
| Jesús / backend | Diagrama y 15 endpoints ya recibidos; FastAPI identificado. Faltan versiones, cuerpos/respuestas, firma de `recomendar()`, política de guardado, manifiestos y comandos. | Validar contratos e instalación de la aplicación. |
| Equipo de diseño | Estructura y textos de seis marcos revisados. Faltan vista legible, navegación y acuerdos sobre los hallazgos UI-01 a UI-13. | Validar apariencia, estados, variantes vigentes y transiciones del flujo. |
| Equipo de IA y backend | Fuentes, cobertura, política de vigencia y reglas de normalización. | Convertir respuestas externas en hechos sustentados. |
| Equipo de campo | Registro anonimizado de una salida real con costos, tiempos y horarios verificados. | Ejemplo observado y comparación con estimaciones. |
| Profesor y backend | Revisión de las 20 reglas, preferencias y tratamiento de desconocidos. | Aprobación de la especificación e integración posterior. |

Estos pendientes no requieren compartir contraseñas. Tampoco se han enviado solicitudes o mensajes a integrantes del equipo desde esta entrega.

## 4. Criterios propuestos de aceptación

1. Las variables tienen un significado único y una fuente o cálculo identificados.
2. Las 20 reglas coinciden entre la tabla y el archivo JSON.
3. El ejemplo produce la traza descrita y distingue datos reales de supuestos.
4. Un dato desconocido no se convierte en falso ni en un costo cero.
5. La ausencia del módulo de comunidad queda reflejada en la advertencia de cierres.
6. El diccionario conserva el diagrama provisional recibido y se contrasta después con el esquema implementado aprobado por Sebas/backend.
7. La arquitectura y los endpoints corresponden al material de Jesús, y su instalación se reproduce.
8. El desarrollador de backend revisa el pull request antes de cualquier integración a `main`.
9. Las opciones marcadas como recomendables respetan el presupuesto y tiempo acordados; el detalle distingue traslados de la duración total.
10. El registro, las preferencias y los tramos del mockup corresponden al contrato de API y al modelo SQL aprobado.

Del criterio 6 está completada la transcripción provisional; queda validar el esquema implementado. Del criterio 7 ya se documentaron arquitectura del dibujo y endpoints; faltan contratos detallados y ejecución de la instalación del servidor. La observación de campo del criterio 3 también debe completarse para presentar el caso como real.

## 5. Fuentes consultadas

Consulta documental realizada el 27 de septiembre de 2026. Las fuentes técnicas sustentan las limitaciones descritas; no prueban que se hayan contratado o integrado los servicios.

- [Sistema de Información Cultural: Cosmovitral](https://sic.cultura.gob.mx/ficha.php?table=museo&table_id=51). La ficha declara actualización de 2024; horario y precio se usan solo como referencia histórica.
- [MySQL: tabla INFORMATION_SCHEMA.COLUMNS](https://dev.mysql.com/doc/refman/8.4/en/information-schema-columns-table.html).
- [Google Routes: rutas de transporte público](https://developers.google.com/maps/documentation/routes/transit-route).
- [Google Places: detalles de lugares](https://developers.google.com/maps/documentation/places/web-service/place-details).
- [Google Places: políticas y atribución](https://developers.google.com/maps/documentation/places/web-service/policies).
- [FastAPI: características](https://fastapi.tiangolo.com/features/).

Fuentes adicionales de las revisiones documentales:

- [Diagrama provisional aportado por el equipo](referencias/diagrama-bd-provisional-2026-09-27.png): fuente primaria de la transcripción.
- [Revisión de los mockups](diseno/mockups-y-flujo.md): estructura y textos recuperados de Figma; apariencia y navegación sin verificar.
- [Decisión de almacenamiento SQL](decisiones/almacenamiento-sql.md): instrucción vigente del equipo.
- [MySQL: límites de precisión DECIMAL](https://dev.mysql.com/doc/refman/8.4/en/precision-math-decimal-characteristics.html).
- [OWASP: almacenamiento de contraseñas](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html).
- [Diagrama de endpoints aportado por el equipo](referencias/diagrama-endpoints-2026-09-27.png): fuente primaria de métodos, rutas, candados, FastAPI y MySQL.
- [Transcripción de endpoints](api/catalogo-endpoints.md) y [contrato lógico de integración](api/integracion-sistema-experto.md): observaciones y propuestas separadas.
- [VS Code: edición y vista previa Markdown](https://code.visualstudio.com/docs/languages/markdown): instrucciones para visualizar la entrega.
