# Manual técnico: diccionario de datos

**Estado:** revisión documental 0.4.0, con SQL vigente y MySQL indicado en el diagrama de endpoints del 27 de septiembre de 2026, fecha local de México. Incluye la transcripción de ocho entidades y 39 campos del modelo provisional, además del contrato de IA de la versión anterior. El modelo está sujeto a cambios; no se han recibido DDL ni migraciones que acrediten una implementación.

**Fuente:** [imagen original del modelo provisional](../referencias/diagrama-bd-provisional-2026-09-27.png). Los tipos se transcriben como se leen en la imagen. Las descripciones son interpretaciones funcionales y las correcciones se presentan como propuestas, sin alterar el modelo original.

## 1. Almacenamiento vigente

El usuario confirmó **SQL hasta nuevo aviso** y retiró MongoDB del alcance actual. El diagrama recibido emplea notación relacional: tablas, PK, FK, `INT`, `VARCHAR` y `LINESTRING`. El diccionario sigue esa estructura; no se propone una adaptación a colecciones ni una arquitectura con dos almacenes.

El nuevo diagrama de endpoints identifica MySQL como gestor de diseño. Faltan versión, controlador, configuración y migraciones. La [decisión de almacenamiento](../decisiones/almacenamiento-sql.md) registra esta precisión; las referencias técnicas a MySQL no acreditan una instalación ejecutada.

El [catálogo de endpoints](../api/catalogo-endpoints.md) relaciona las ocho entidades con las operaciones del sistema. Sus nombres aparecen en minúsculas, mientras el modelo provisional utiliza rótulos como `Usuarios`; el DDL debe fijar los nombres físicos exactos sin alterar la transcripción original.

## 2. Diccionario del material implementado en esta rama

Estos datos son archivos JSON locales de demostración. No son tablas de la aplicación ni implican usar una base de datos documental.

### 2.1 Base de conocimiento: `reglas.json`

| Campo | Tipo JSON | Obligatorio | Restricción / significado |
| --- | --- | --- | --- |
| `version` | String | Sí | Versión del conjunto; este borrador usa `0.1.0`. |
| `pesos_preferencias` | Objeto | Sí | Mapa de hecho derivado a entero no negativo; pesos de R17–R20. |
| `reglas` | Arreglo de objetos | Sí | Exactamente 20 reglas en esta versión. |
| `reglas[].id` | String | Sí | Identificador único entre `R01` y `R20`. |
| `reglas[].si` | Objeto | Sí | Mapa no vacío: nombre de proposición a booleano requerido. |
| `reglas[].entonces` | Arreglo de strings | Sí | Nombres de hechos derivados que se afirman como verdaderos. |
| `reglas[].explicacion` | String | Sí | Motivo legible de la regla activada. |

### 2.2 Casos: `casos.json`

| Campo | Tipo JSON | Obligatorio | Restricción / significado |
| --- | --- | --- | --- |
| `version_reglas` | String | Sí | Debe coincidir con `reglas.json`. |
| `naturaleza` | String | Sí | Identifica explícitamente los datos como sintéticos. |
| `hechos_comunes` | Objeto | Sí | Hechos de entrada compartidos; nombres y significado en el diccionario de variables. |
| `casos` | Arreglo de objetos | Sí | Tres candidatos de demostración. |
| `casos[].candidato_id` | String | Sí | Identificador del candidato dentro del ejercicio: A, B o C. |
| `casos[].descripcion` | String | Sí | Descripción del supuesto. |
| `casos[].hechos` | Objeto | Sí | Sustituciones sobre los hechos comunes; puede estar vacío. |
| `casos[].esperado.estado` | String | Sí | Estado esperado de la evaluación. |
| `casos[].esperado.puntuacion_preferencias` | Entero o `null` | Sí | De 0 a 6 si es recomendable; `null` en otro caso. |
| `casos[].esperado.reglas` | Arreglo de strings | Sí | Secuencia de reglas esperada con el orden actual de la base. |

Los valores de hechos son `true`, `false` o `null`. Un campo de entrada omitido se interpreta como desconocido, excepto `control_cierres_habilitado`, que requiere un booleano explícito. La lista de nombres aceptados y críticos se define en [variables.md](../sistema-experto/variables.md).

### 2.3 Resultado de `evaluar()`

| Campo | Tipo JSON | Nulabilidad | Significado |
| --- | --- | --- | --- |
| `version_reglas` | String | No | Base aplicada al candidato. |
| `estado` | String | No | `requiere_correccion`, `descartado`, `pendiente_verificacion` o `recomendable`. |
| `puntuacion_preferencias` | Entero | Sí | Suma de preferencias solo para recomendables. |
| `hechos_iniciales` | Objeto | No | Entrada normalizada más `datos_criticos_completos` calculado. |
| `hechos_derivados` | Arreglo de strings | No | Conclusiones afirmadas, ordenadas por nombre. |
| `traza` | Arreglo de objetos | No | Una entrada por regla activada. |
| `traza[].ronda` | Entero positivo | No | Ronda de activación. |
| `traza[].regla_id` | String | No | Identificador de la regla. |
| `traza[].conclusiones` | Arreglo de strings | No | Hechos afirmados por esa regla. |
| `traza[].explicacion` | String | No | Explicación asociada. |
| `advertencias` | Arreglo de strings | No | Limitaciones que deben acompañar el resultado. |

La salida CLI con `--json` envuelve los resultados con `naturaleza` y `resultados`, y añade `candidato_id` a cada resultado. Esa envoltura es de la demostración; no acredita un endpoint HTTP existente.

## 3. Contrato lógico propuesto para integrar evidencias

El motor recibe booleanos; el normalizador necesita valores y procedencia. Esta estructura de evidencia es una **propuesta para backend**, todavía sin persistencia ni validación implementadas:

| Campo | Tipo lógico | Requerido | Regla propuesta |
| --- | --- | --- | --- |
| `solicitud_id`, `candidato_id` | Identificadores | Sí | Vincular evidencia a una única evaluación. Tipo físico pendiente. |
| `proposicion` | String | Sí | Nombre de un hecho permitido. |
| `valor` | Booleano o nulo | Sí | Resultado lógico normalizado. |
| `fuente` | String | Sí | Usuario, configuración, proveedor, catálogo propio o cálculo. |
| `referencia_fuente` | String o nulo | Según fuente | Identificador trazable cuyo almacenamiento esté permitido. |
| `consultado_en` | Fecha y hora | Para datos externos | Momento real de consulta. |
| `caduca_en` | Fecha y hora o nulo | Según política | Un nulo significa caducidad sin definir, no vigencia ilimitada. |
| `naturaleza` | Enumeración | Sí | `verificado`, `estimado` o `simulado`. La producción debe excluir datos simulados. |
| `unidad` | String o nulo | Para magnitudes | Segundos, centavos, moneda u otra unidad explícita. |
| `detalle_calculo` | Objeto | Si es derivado | Componentes usados, cuando su conservación esté permitida. |

Los datos simulados no pueden mezclarse con una respuesta real sin una identificación inequívoca del modo de demostración. La aplicación debe distinguir «estimado» de «verificado» en sus resultados.

## 4. Preparación del esquema relacional SQL

El diagrama provisional es la fuente conceptual disponible; no hay tablas creadas por esta entrega. Para cada tabla aprobada deben definirse estos metadatos:

| Metadato | Contenido requerido |
| --- | --- |
| Nombre y propósito | Nombre exacto de la tabla y operación que respalda. |
| Columnas | Tipo del gestor elegido, longitud/precisión, nulabilidad y valores predeterminados. |
| Identificadores | PK, forma de generación y referencias FK con tipos compatibles. |
| Integridad | Unicidad, restricciones de dominio y comportamiento ante actualización o borrado. |
| Relaciones | Cardinalidad, obligatoriedad y tablas de asociación cuando correspondan. |
| Índices | Columnas y consultas que justifican cada índice, incluidos los espaciales si se usan. |
| Temporalidad | Fechas de creación, consulta y vigencia; distinguir duración de instante. |
| Procedencia | Fuente de datos y limitaciones de uso o persistencia. |

Las reglas JSON pueden permanecer versionadas en Git. Guardarlas además en SQL requiere justificar su administración y control de versiones; no es un requisito para ejecutar la demostración.

La futura implementación debe cubrir la secuencia de lugares y tramos de cada itinerario mediante relaciones explícitas. La [revisión del modelo](../modelo-datos/revision-modelo-provisional.md) distingue solicitud, itinerario, parada y tramo antes de proponer nuevas tablas.

Los resultados de Places no se convierten automáticamente en un catálogo permanente. Sus políticas restringen almacenamiento y caché, con excepciones como los identificadores de lugar; debe revisarse el uso de cada campo y su atribución. Elegir SQL no elimina esas condiciones. Referencia: [políticas de Places](https://developers.google.com/maps/documentation/places/web-service/policies).

## 5. Diccionario del diagrama relacional provisional

**Lectura de las tablas:** PK y FK son marcas visibles en la imagen. No se especifican `AUTO_INCREMENT`, valores predeterminados, nulabilidad de campos no PK, restricciones de unicidad, reglas de borrado ni índices adicionales. No se deducen como implementados. Las referencias destino de las FK se interpretan por nombres y conexiones y requieren confirmación con el modelo editable.

### 5.1 `Usuarios` — 7 campos

| Campo observado | Tipo observado | Marca | Descripción e interpretación pendiente |
| --- | --- | --- | --- |
| `id_usuario` | `INT` | PK | Identificador del usuario; generación pendiente. |
| `nombre` | `VARCHAR(100)` | — | Nombre de la persona. |
| `primer_apellido` | `VARCHAR(100)` | — | Primer apellido; confirmar si es necesario y obligatorio. |
| `segundo_apellido` | `VARCHAR(100)` | — | Segundo apellido; no asumir que todas las personas lo tienen. |
| `correo` | `VARCHAR(100)` | — | Correo; definir normalización, verificación y unicidad si se utiliza para acceso. |
| `contraseña` | `VARCHAR(100)` | — | El dibujo no define tratamiento criptográfico. Documentar un hash adecuado o eliminar el campo si se delega autenticación. |
| `fecha_nacimiento` | `DATE` | — | Fecha de nacimiento; justificar su uso en el alcance inicial. |

### 5.2 `Residencia` — 8 campos

| Campo observado | Tipo observado | Marca | Descripción e interpretación pendiente |
| --- | --- | --- | --- |
| `id_residencia` | `INT` | PK | Identificador de dirección guardada. |
| `calle` | `VARCHAR(100)` | — | Nombre de la calle. |
| `numero_interior` | `VARCHAR(10)` | — | Número interior, que puede no existir; nulabilidad por acordar. |
| `numero_exterior` | `VARCHAR(10)` | — | Número exterior como texto para admitir identificadores alfanuméricos. |
| `municipio` | `VARCHAR(100)` | — | Municipio. |
| `colonia` | `VARCHAR(100)` | — | Colonia. |
| `estado` | `VARCHAR(100)` | — | Entidad federativa, según interpretación del contexto de dirección. |
| `id_usuario` | `INT` | FK | Usuario relacionado; referencia esperada a `Usuarios.id_usuario`. |

No equivale automáticamente al origen actual de cada consulta. El usuario puede salir de otro lugar; debe poder elegir un origen manual sin registrar su domicilio completo.

### 5.3 `Lugares_de_interes` — 6 campos

| Campo observado | Tipo observado | Marca | Descripción e interpretación pendiente |
| --- | --- | --- | --- |
| `id_lugar` | `INT` | PK | Identificador interno del lugar. |
| `nombre` | `VARCHAR(100)` | — | Nombre del lugar. |
| `longitud` | `DECIMAL(11,8)` | — | Longitud geográfica; validar el rango acordado y la fuente. |
| `latitud` | `DECIMAL(102,8)` en la imagen | — | Posible error de escritura; confirmar en el archivo editable antes de implementar. |
| `id_usuario` | `INT` | FK | ¿Creador, propietario o usuario que lo guarda como favorito? Debe definirse. |
| `id_cat` | `INT` | FK | Referencia esperada a `Categorias.id_categoria`; nombre abreviado por revisar. |

Si la latitud es literalmente `DECIMAL(102,8)`, no es válida en MySQL, cuya precisión máxima es 65. Una propuesta para coordenadas geográficas es latitud `DECIMAL(10,8)` y longitud `DECIMAL(11,8)`, con validación adicional de rangos. El tipo por sí solo no limita latitud a ±90 ni longitud a ±180. Fuente: [precisión de DECIMAL en MySQL](https://dev.mysql.com/doc/refman/8.4/en/precision-math-decimal-characteristics.html).

### 5.4 `Categorias` — 3 campos

| Campo observado | Tipo observado | Marca | Descripción e interpretación pendiente |
| --- | --- | --- | --- |
| `id_categoria` | `INT` | PK | Identificador de categoría. |
| `nombre` | `VARCHAR(100)` | — | Nombre de categoría. |
| `descripcion` | `TEXT` | — | Descripción y criterio de uso. |

Un tipo de lugar, como museo, no es el mismo concepto que un contexto, como salida con amigos. Confirmar el significado del catálogo antes de conectarlo a `contexto_compatible` e `intereses_compatibles`.

### 5.5 `Transportes` — 2 campos

| Campo observado | Tipo observado | Marca | Descripción e interpretación pendiente |
| --- | --- | --- | --- |
| `id_transporte` | `INT` | PK | Identificador del elemento de transporte. |
| `nombre` | `VARCHAR(100)` | — | Nombre; falta precisar si identifica modo, línea u operador. |

Un solo nombre no basta para indicar al usuario en qué parada subir, qué sentido tomar o dónde transbordar. Esos datos pertenecen a los tramos y al proveedor de rutas cuando estén disponibles.

### 5.6 `Rutas` — 2 campos

| Campo observado | Tipo observado | Marca | Descripción e interpretación pendiente |
| --- | --- | --- | --- |
| `id_ruta` | `INT` | PK | Identificador de la ruta. |
| `ruta` | `LINESTRING` | — | Geometría; definir sistema de referencia, ejes, fuente y alcance. |

La geometría no contiene por sí sola horario, costo, modo, paradas ni instrucciones. Una línea dibujada tampoco prueba `ruta_calculada=true` para un modo y una hora concretos.

### 5.7 `Historial_rutas` — 5 campos

| Campo observado | Tipo observado | Marca | Descripción e interpretación pendiente |
| --- | --- | --- | --- |
| `id_historial` | `INT` | PK | Identificador de registro de historial. |
| `tiempo_estimado` | `INT` | — | Duración estimada; la imagen no indica unidad ni si incluye esperas. |
| `id_ruta` | `INT` | FK | Referencia esperada a `Rutas.id_ruta`. |
| `id_usuario` | `INT` | FK | Referencia esperada a `Usuarios.id_usuario`. |
| `id_transporte` | `INT` | FK | Referencia esperada a `Transportes.id_transporte`. |

Falta una fecha del evento para ordenar el historial y diferenciar consultas de viajes realizados. También debe decidirse cómo registrar una ruta con varios modos de transporte.

### 5.8 `Planes` — 6 campos

| Campo observado | Tipo observado | Marca | Descripción e interpretación pendiente |
| --- | --- | --- | --- |
| `id_plan` | `INT` | PK | Identificador de plan o solicitud; significado a confirmar. |
| `no_acompañantes` | `INT` | — | Número de acompañantes; precisar si excluye al usuario y validar no negativo. |
| `tiempo_disponible` | `INT` | — | Tiempo declarado por el usuario; unidad pendiente. |
| `id_transporte` | `INT` | FK | Transporte solicitado o elegido, pendiente de precisar. |
| `id_categoria` | `INT` | FK | Categoría elegida; referencia esperada a `Categorias.id_categoria`. |
| `id_usuario` | `INT` | FK | Referencia esperada a `Usuarios.id_usuario`; falta un conector claramente visible en el dibujo. |

Por sus campos, esta entidad podría representar la solicitud del usuario. Aún no aparecen presupuesto, hora de salida, regreso ni paradas ordenadas de un itinerario resultante. La interpretación como solicitud se propone para revisión; no se declara aprobada.

### 5.9 Relaciones interpretadas a partir de las FK

| FK observada | Destino esperado | Aspecto por confirmar |
| --- | --- | --- |
| `Residencia.id_usuario` | `Usuarios.id_usuario` | Una o varias direcciones; obligatoriedad. |
| `Lugares_de_interes.id_usuario` | `Usuarios.id_usuario` | Propiedad, creación o favorito. |
| `Lugares_de_interes.id_cat` | `Categorias.id_categoria` | Una o varias categorías por lugar. |
| `Historial_rutas.id_ruta` | `Rutas.id_ruta` | Una consulta de ruta o un tramo por registro. |
| `Historial_rutas.id_usuario` | `Usuarios.id_usuario` | Si se permite historial de consulta invitada y cómo se maneja. |
| `Historial_rutas.id_transporte` | `Transportes.id_transporte` | Varios modos en un mismo trayecto. |
| `Planes.id_transporte` | `Transportes.id_transporte` | Preferencia o modo efectivo. |
| `Planes.id_categoria` | `Categorias.id_categoria` | Contexto o clasificación de lugar. |
| `Planes.id_usuario` | `Usuarios.id_usuario` | Confirmar referencia y dibujar el conector faltante. |

Hay nueve campos marcados FK. En una interpretación relacional habitual, varias filas hijas pueden referirse a una fila padre si no existe una restricción de unicidad. La imagen no basta para certificar cardinalidades mínimas, unicidad, cascadas o todos los símbolos de sus conectores; verificarlos con el autor y el DDL.

No se ve una relación que enumere los lugares y rutas de cada plan. Si se requiere guardar itinerarios con varias visitas, debe diseñarse esa relación, como se propone en la [revisión del modelo](../modelo-datos/revision-modelo-provisional.md).

### 5.10 Verificación futura contra la implementación MySQL

El diagrama es la fuente provisional; el DDL será la fuente de implementación. Registrar también longitudes, nulabilidad, valores predeterminados, índices y restricciones que hoy no aparecen.

Consulta de solo lectura para obtener columnas de la base seleccionada en la conexión autorizada del equipo:

```sql
SELECT TABLE_NAME, ORDINAL_POSITION, COLUMN_NAME, COLUMN_TYPE,
       IS_NULLABLE, COLUMN_DEFAULT, COLUMN_KEY, EXTRA, COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
ORDER BY TABLE_NAME, ORDINAL_POSITION;
```

Esta consulta no se ejecutó en la entrega porque no se proporcionó una base. Debe complementarse con el DDL de cada tabla para documentar claves foráneas, índices compuestos y restricciones; `COLUMN_KEY` por sí solo no describe toda esa estructura. Referencia: [MySQL, INFORMATION_SCHEMA.COLUMNS](https://dev.mysql.com/doc/refman/8.4/en/information-schema-columns-table.html).

## 6. Información que falta para cerrar el diccionario físico

El diagrama provisional ya fue recibido y transcrito; SQL está confirmado y el diagrama de endpoints identifica MySQL. Faltan versión editable o confirmación de rótulos, versión y controlador de MySQL y, cuando exista implementación, DDL/migraciones, índices, relaciones, restricciones y ejemplos anonimizados. No hacen falta contraseñas ni un volcado de datos personales.

Cada cambio del modelo deberá actualizar estas tablas y registrar su versión. La transcripción del borrador está disponible; el diccionario físico queda pendiente de contrastar con los esquemas realmente implementados. Las propuestas de ajuste están registradas aparte en la [revisión del modelo](../modelo-datos/revision-modelo-provisional.md).
