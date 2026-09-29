# Decisión vigente de almacenamiento: SQL con MySQL en el diseño

**Fecha:** 27 de septiembre de 2026, `America/Mexico_City`. **Revisión documental:** 0.4.0. **Estado:** SQL confirmado por el usuario; MySQL identificado en el diagrama de endpoints recibido posteriormente.

El equipo utilizará una base de datos relacional SQL. MongoDB deja de formar parte del alcance vigente. Esta decisión sustituye la propuesta anterior de adaptar el modelo a colecciones o combinar ambos almacenes.

En la revisión 0.3.0, la instrucción de usar SQL todavía no identificaba un gestor. El nuevo [diagrama de endpoints](../referencias/diagrama-endpoints-2026-09-27.png) indica MySQL junto a FastAPI y el motor de IA. Por eso MySQL pasa a ser la referencia concreta de diseño en la revisión 0.4.0. Backend todavía debe fijar versión, controlador y proceso de migraciones antes de implementar la conexión.

## Consecuencias

- El diccionario se desarrolla sobre las ocho entidades del diagrama relacional provisional.
- Las relaciones se expresarán mediante claves y restricciones acordadas; los cambios se entregarán como migraciones del gestor elegido.
- La arquitectura documenta MySQL; no se añaden MongoDB, sincronización entre almacenes ni validadores de documentos.
- Los archivos JSON de reglas y casos siguen siendo recursos de la demostración. Su existencia no implica usar una base documental.
- Los tipos espaciales, sistema de referencia e índices se concretarán para la versión de MySQL acordada; `LINESTRING` aparece en ambos diagramas.
- El modelo continúa siendo provisional. La decisión de SQL no aprueba automáticamente sus campos, cardinalidades o restricciones.

Las propuestas MongoDB de las revisiones documentales 0.1.0 y 0.2.0 quedan como antecedentes en el historial de Git. Cualquier cambio posterior deberá actualizar este registro, la arquitectura y el diccionario en una rama para revisión.
