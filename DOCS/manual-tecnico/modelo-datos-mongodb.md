# Manual técnico — Modelo de datos en MongoDB (Kompás v0.6)

> Fuente: `MIGRACION_MONGODB.md`. Código: `backend/scripts/preparar_bd.py` (colecciones, validadores e índices),
> `backend/app/modulos/*/repositorio.py` (lectura y escritura) y `backend/scripts/migrar_mysql_a_mongo.py`.

## 1. Por qué MongoDB

- **Modelo de documentos**: un plan guarda varios intereses y varios medios de transporte como arreglos, y la
  evaluación del sistema experto como subdocumento. En MySQL `planes` solo admitía una categoría y un transporte.
- **GeoJSON nativo**: lugares, rutas y reportes se guardan como `Point`/`LineString` con índice `2dsphere`.
  Desapareció la conversión manual a WKT (`LineaGeo` en el antiguo `modelos.py`, ~80 líneas).
- **Agregaciones** (`$group`, `$facet`, `$bucket`, `$dateTrunc`) para el dashboard sin SQL complejo.
- **Nube**: el mismo código funciona con MongoDB local o con **MongoDB Atlas** cambiando solo `MONGO_URI`.
- Esquema flexible con **validación `$jsonSchema`** para no perder control de los datos.

### Embeber o referenciar

| Relación en MySQL | En MongoDB | Por qué |
|---|---|---|
| `residencia` (1:1 con usuario) | **Embebida** en `usuarios.residencia` | Siempre se lee junto con el usuario |
| `lugares_de_interes.id_cat` → `categorias` | **Referencia extendida** `categoria: {id, nombre}` | Se lista mucho y así no hace falta "join"; el nombre de una categoría casi nunca cambia |
| `historial_rutas.id_transporte` | Referencia extendida `transporte: {id, nombre}` | Igual que arriba; agiliza el dashboard |
| `planes.id_categoria`, `id_transporte` | `categoria`/`transporte` extendidos **+ arreglos** `intereses`, `movilidad` | Se conserva lo que la API devuelve y se guarda todo lo que eligió el usuario |
| `historial_rutas.id_usuario`, `planes.id_usuario` | **Referencia** (`id_usuario`) | Crecen sin límite; no se embeben en el usuario |
| `rutas.ruta` (LINESTRING) | GeoJSON `LineString` | Formato estándar, el mismo que ya usa la app (`[lng, lat]`) |

**Identificadores.** Usuarios, categorías, transportes, lugares, rutas, historial y planes conservan `_id` **entero**
(la app espera `id: number` y la migración conserva los números de MySQL). Los ids nuevos salen de la colección
`contadores` con `find_one_and_update({$inc: {seq: 1}})`. `reportes` y `bitacora_laboratorio` usan `ObjectId`
y el repositorio lo regresa como texto.

**Fechas y borrado lógico.** Todas las fechas se guardan como `date` (UTC) y el cliente de PyMongo las regresa en
hora de Toluca (`tz_aware=True, tzinfo=America/Mexico_City`). Todos los `find` filtran `{"deleted_at": None}`.

## 2. Diagramas

### 2.1 Modelo anterior (MySQL, 8 tablas)

```mermaid
erDiagram
  usuarios ||--o| residencia : "tiene"
  usuarios ||--o{ lugares_de_interes : "registra"
  categorias ||--o{ lugares_de_interes : "clasifica"
  usuarios ||--o{ historial_rutas : "recorre"
  rutas ||--o{ historial_rutas : "se usa en"
  transportes ||--o{ historial_rutas : "medio"
  usuarios ||--o{ planes : "crea"
  categorias ||--o{ planes : "categoria"
  transportes ||--o{ planes : "transporte"

  usuarios { int id_usuario PK
    varchar nombre
    varchar primer_apellido
    varchar segundo_apellido
    varchar correo UK
    varchar password
    date fecha_nacimiento }
  residencia { int id_residencia PK
    varchar calle
    varchar municipio
    varchar colonia
    varchar estado
    int id_usuario FK }
  categorias { int id_categoria PK
    varchar nombre UK
    text descripcion }
  transportes { int id_transporte PK
    varchar nombre UK }
  lugares_de_interes { int id_lugar PK
    varchar nombre
    decimal longitud
    decimal latitud
    int id_usuario FK
    int id_cat FK }
  rutas { int id_ruta PK
    linestring ruta }
  historial_rutas { int id_historial PK
    int tiempo_estimado
    int id_ruta FK
    int id_usuario FK
    int id_transporte FK }
  planes { int id_plan PK
    int no_acompanantes
    int tiempo_disponible
    int id_transporte FK
    int id_categoria FK
    int id_usuario FK
    datetime fecha_plan }
```

Todas las tablas tienen además `created_at`, `updated_at` y `deleted_at` (borrado lógico).

### 2.2 Modelo de documentos (MongoDB, base `kompas`)

```mermaid
erDiagram
  usuarios ||--o{ planes : "id_usuario"
  usuarios ||--o{ historial_rutas : "id_usuario"
  usuarios ||--o{ reportes : "id_usuario"
  usuarios ||--o{ lugares : "id_usuario"
  rutas ||--o{ historial_rutas : "id_ruta"
  usuarios ||--o{ conversaciones : "id_usuario"
  conversaciones }o--o{ planes : "planes_creados"

  usuarios { int _id PK
    string correo UK
    string password "hash bcrypt"
    string rol "usuario | admin"
    date fecha_nacimiento
    object residencia "EMBEBIDA {id, calle, municipio...}" }
  categorias { int _id PK
    string nombre UK
    string descripcion }
  transportes { int _id PK
    string nombre UK }
  lugares { int _id PK
    string nombre
    object ubicacion "GeoJSON Point"
    object categoria "ref. extendida {id, nombre}" }
  rutas { int _id PK
    object trazo "GeoJSON LineString"
    string nombre "opcional"
    array paradas "opcional [{nombre, ubicacion}]" }
  historial_rutas { int _id PK
    int id_usuario
    int id_ruta
    object transporte "ref. extendida {id, nombre}"
    int tiempo_estimado }
  planes { int _id PK
    int id_usuario
    string contexto
    object presupuesto "{min, max}"
    array intereses
    array movilidad
    object categoria "ref. extendida"
    object transporte "ref. extendida"
    date fecha_plan
    object evaluacion "subdocumento del sistema experto"
    string origen_solicitud "planificador | asistente" }
  reportes { ObjectId _id PK
    string tipo
    object ubicacion "GeoJSON Point"
    date vigente_hasta
    string estado }
  bitacora_laboratorio { ObjectId _id PK
    string tipo "dfs | distancia | busqueda | genetico | transbordo | abordaje" }
  conversaciones { ObjectId _id PK
    int id_usuario
    string titulo
    string modelo
    array mensajes "EMBEBIDOS {rol, contenido, ...}"
    array rutas_consultadas
    array planes_creados }
  contadores { string _id PK "nombre de colección"
    int seq }
```

Las líneas son **referencias** por id (no hay llaves foráneas: la integridad la cuida el servicio, por ejemplo
historial valida que la ruta y el transporte existan). `categoria` y `transporte` dentro de lugares, planes e
historial son **referencias extendidas** (copian el nombre) y `residencia` está **embebida**.

## 3. Diccionario de datos

Campos comunes en las colecciones con borrado lógico: `created_at` (date, sí), `updated_at` (date, sí),
`deleted_at` (date | null, sí: `null` = activo). Los documentos generados por `sembrar_actividad_demo.py` llevan
además `demo: true`.

### `usuarios`

| Campo | Tipo BSON | Oblig. | Descripción | Ejemplo |
|---|---|---|---|---|
| `_id` | int | sí | Id del usuario (el mismo de MySQL) | `2` |
| `nombre` | string | sí | Nombre | `"Demo"` |
| `primer_apellido` | string | sí | Primer apellido | `"Kompás"` |
| `segundo_apellido` | string \| null | no | Segundo apellido | `null` |
| `correo` | string | sí | Correo en minúsculas (único) | `"demo@kompas.mx"` |
| `password` | string | sí | Hash bcrypt (nunca texto plano) | `"$2b$12$…"` |
| `fecha_nacimiento` | date \| null | no | Fecha a las 00:00 de Toluca; la API la regresa como fecha | `2004-05-10` |
| `rol` | string | sí | `usuario` o `admin` (admin ve el dashboard) | `"admin"` |
| `residencia` | object \| null | no | `{id, calle, numero_interior, numero_exterior, municipio, colonia, estado}` | `{"id": 1, "municipio": "Lerma", …}` |

### `categorias` y `transportes`

| Campo | Tipo BSON | Oblig. | Descripción | Ejemplo |
|---|---|---|---|---|
| `_id` | int | sí | Id del catálogo | `2` |
| `nombre` | string | sí | Nombre único; la app usa su `clave` derivada (`Café` → `cafe`) | `"Café"` |
| `descripcion` | string | no (solo categorías) | Descripción | `"Cafeterías"` |

### `lugares`

| Campo | Tipo BSON | Oblig. | Descripción | Ejemplo |
|---|---|---|---|---|
| `_id` | int | sí | Id del lugar | `3` |
| `nombre` | string | sí | Nombre | `"Parque de ejemplo · Toluca"` |
| `ubicacion` | object (GeoJSON Point) | sí | `[longitud, latitud]` | `{"type": "Point", "coordinates": [-99.662, 19.296]}` |
| `categoria` | object | sí | Referencia extendida `{id, nombre}` | `{"id": 5, "nombre": "Aire libre"}` |
| `id_usuario` | int | no | Quién lo registró | `1` |

### `rutas`

| Campo | Tipo BSON | Oblig. | Descripción | Ejemplo |
|---|---|---|---|---|
| `_id` | int | sí | Id de la ruta | `1` |
| `trazo` | object (GeoJSON LineString) | sí | Trazo recorrido por el equipo `[[lng, lat], …]` | `{"type": "LineString", "coordinates": [[-99.511, 19.2847], …]}` |

### `historial_rutas`

| Campo | Tipo BSON | Oblig. | Descripción | Ejemplo |
|---|---|---|---|---|
| `_id` | int | sí | Id del recorrido | `10` |
| `id_usuario` | int | sí | Referencia a `usuarios` | `2` |
| `id_ruta` | int | sí | Referencia a `rutas` | `1` |
| `transporte` | object | sí | Referencia extendida `{id, nombre}` | `{"id": 1, "nombre": "Caminando"}` |
| `tiempo_estimado` | int | sí | Minutos (estimación) | `35` |

### `planes`

| Campo | Tipo BSON | Oblig. | Descripción | Ejemplo |
|---|---|---|---|---|
| `_id` | int | sí | Id del plan | `25` |
| `id_usuario` | int | sí | Referencia a `usuarios` | `2` |
| `contexto` | string | no* | `solo`, `pareja`, `amigos`, `familia` | `"amigos"` |
| `no_acompanantes` | int | sí | Derivado del contexto (0, 1, 3, 3) | `3` |
| `presupuesto` | object | no* | `{min, max}` por persona en MXN | `{"min": 100, "max": 400}` |
| `tiempo_disponible` | int | sí | Minutos | `180` |
| `intereses` | array\<string> | no* | Todos los intereses elegidos | `["comer", "cultura"]` |
| `movilidad` | array\<string> | no* | Todas las formas de moverse elegidas | `["caminando", "taxi_app"]` |
| `categoria` | object | sí | `{id, nombre}` del primer interés (lo que regresa `GET /api/planes`) | `{"id": 1, "nombre": "Comer"}` |
| `transporte` | object | sí | `{id, nombre}` de la primera movilidad | `{"id": 1, "nombre": "Caminando"}` |
| `hora_salida` | string | no | `HH:MM` | `"18:00"` |
| `fecha_plan` | date | sí | Día y hora de salida | `2026-10-28T18:00-06:00` |
| `evaluacion` | object | no* | `{version_reglas, datos_suficientes, candidatos: [{tipo, estado, puntuacion, reglas}]}` tal como lo regresó el motor | ver abajo |
| `origen_solicitud` | string | no | `planificador` o `asistente` (v0.6; los anteriores cuentan como planificador) | `"asistente"` |

\* Obligatorios para los planes creados desde v0.5; los migrados de MySQL no los tienen (MySQL no los guardaba y no se inventan).

```json
"evaluacion": {
  "version_reglas": "0.1.0", "datos_suficientes": true,
  "candidatos": [
    { "tipo": "equilibrado", "estado": "recomendable", "puntuacion": 5, "reglas": ["R11", "R13", "R15", "R16"] },
    { "tipo": "rapido", "estado": "pendiente_verificacion", "puntuacion": null, "reglas": ["R09", "R11", "R13"] }
  ]
}
```

### `reportes`

| Campo | Tipo BSON | Oblig. | Descripción | Ejemplo |
|---|---|---|---|---|
| `_id` | ObjectId | sí | La API lo regresa como texto | `"671b…"` |
| `tipo` | string | sí | `cierre_total`, `accidente`, `manifestacion`, `afluencia` | `"manifestacion"` |
| `nivel_afluencia` | string | no | `baja`, `media`, `alta` (solo afluencia) | `"alta"` |
| `ubicacion` | object (GeoJSON Point) | sí | Dentro de la zona piloto | `{"type": "Point", "coordinates": [-99.625, 19.279]}` |
| `ruta_id`, `lugar_id` | string | no | Ruta o lugar relacionado | `"2"` |
| `observado_en` | date | sí | Cuándo lo vio el usuario | `2026-10-25T18:00-06:00` |
| `vigente_hasta` | date | sí | Lo calcula la API: cierre 6 h, accidente 2 h, manifestación 3 h, afluencia 1 h | `2026-10-25T21:00-06:00` |
| `confirmaciones` | int | sí | Inicia en 0 | `0` |
| `estado` | string | sí | `pendiente`, `verificado`, `descartado` | `"pendiente"` |
| `comentario` | string | no | Máx. 500 caracteres | `"Bloqueo en Tollocan"` |
| `id_usuario` | int | sí | Quién lo reportó | `2` |
| `created_at` | date | sí | Alta en la base | |

Sin índice TTL a propósito: los reportes vencidos se conservan para las estadísticas.

### `bitacora_laboratorio` (polimórfica, discriminador `tipo`)

| Campo | Tipo BSON | Oblig. | Descripción | Ejemplo |
|---|---|---|---|---|
| `_id` | ObjectId | sí | | |
| `tipo` | string | sí | `dfs`, `distancia`, `busqueda`, `genetico`, `transbordo` o `abordaje` | `"dfs"` |
| `creado_en` | date | sí | Momento de la consulta | |
| `origen`, `destino` | string | dfs | Paradas del grafo académico | `"TerminalToluca"` |
| `limite_profundidad` | int | dfs | Límite pedido | `5` |
| `exito` | bool | dfs | Si las paradas existen | `true` |
| `total_nodos_explorados`, `total_rutas`, `profundidad_maxima` | int | dfs | Resultado de la búsqueda | `8`, `2`, `4` |
| `modo` | string | distancia | `plano` o `geo` | `"geo"` |
| `euclidiana`, `manhattan` | double | distancia | Resultado (unidades del plano o km) | `3.21`, `4.10` |
| `costo_optimo_km`, `algoritmos` | double, array | busqueda | Costo de UCS y, por algoritmo: `{algoritmo, heuristica, costo_km, nodos_explorados, longitud_camino, optimo, ms}` | `13.608` |
| `origen` | string | genetico | `itinerario` (plan real) o `endpoint` | `"itinerario"` |
| `tipo_plan`, `paradas`, `aplicado` | string, int, bool | genetico | Tipo de plan, número de paradas y si se cambió el orden | `"rapido"`, `2`, `true` |
| `km_antes`, `km_despues`, `generaciones`, `generacion_mejor`, `brecha_vs_optimo_pct` | double, int | genetico | Resultado del genético | `3.1`, `2.4`, `150`, `3`, `0` |
| `historial_mejor`, `historial_promedio` | array\<double> | genetico | Aptitud por generación (gráfica de convergencia) | |
| `encontrado`, `rutas_usadas`, `nodos_explorados`, `total_nodos` | bool, array, int | transbordo | Resultado de A\* para combinar rutas | `true`, `[2, 5]`, `240`, `519` |
| `tipo_opcion`, `id_ruta`, `subida`, `bajada` | string, int, object | abordaje | Paradas `{nombre, lat, lng, km}` de cada opción en autobús ofrecida (mapa de calor) | |
| `ms` | double | busqueda, genetico, transbordo | Milisegundos | `1.7` |

### `conversaciones` (v0.6, asistente)

| Campo | Tipo BSON | Oblig. | Descripción | Ejemplo |
|---|---|---|---|---|
| `_id` | ObjectId | sí | La API lo regresa como texto | `"671b…"` |
| `id_usuario` | int | sí | Dueño de la conversación (otro usuario recibe 404) | `2` |
| `titulo` | string \| null | no | Primeras 6 palabras del primer mensaje (sin LLM) | `"¿Cómo llego al Cosmovitral…"` |
| `modelo` | string | no | Modelo de Ollama con el que se creó | `"llama3.2:3b"` |
| `mensajes` | array\<object> | sí | Embebidos, se agregan con `$push`: `{rol: usuario \| asistente \| herramienta \| error, contenido?, nombre?, argumentos?, resultado_ref?, duracion_ms?, creado_en}` | ver `asistente-llm.md` |
| `rutas_consultadas` | array\<object> | no | `{id_ruta, origen, destino, transporte, consultado_en}` sin repetir | |
| `planes_creados` | array\<int> | no | Ids de `planes` creados desde el asistente (`$addToSet`) | `[31]` |
| `created_at`, `updated_at` | date | sí | | |
| `deleted_at` | date \| null | no | Borrado lógico | `null` |

No se guarda la ubicación del usuario ni datos de Google: `origen` y `destino` son los textos que escribió el usuario.

### `rutas`: campos opcionales que lee la v0.6

`nombre` (nombre de la línea) y `paradas: [{nombre, ubicacion: GeoJSON Point}]`. Si una ruta no tiene paradas,
"¿Cómo llego?" usa los puntos de su trazo como "Punto N" (no se inventan nombres). **Pendiente con Sebas:** capturar
las paradas reales de cada ruta y agregarlas al validador si se aprueban.

### `contadores`

| Campo | Tipo BSON | Oblig. | Descripción | Ejemplo |
|---|---|---|---|---|
| `_id` | string | sí | Nombre de la colección | `"planes"` |
| `seq` | int | sí | Último id entregado | `25` |

## 4. Índices

| Colección | Campos | Tipo | Para qué consulta |
|---|---|---|---|
| `usuarios` | `correo` | único | Login y "correo ya registrado" (409) |
| `categorias`, `transportes` | `nombre` | único | Evitar catálogos repetidos |
| `lugares` | `ubicacion` | 2dsphere | Mapa y búsquedas por cercanía (`$near`) |
| `lugares` | `categoria.id` | simple | Filtrar por categoría |
| `rutas` | `trazo` | 2dsphere | Rutas que pasan cerca de un punto |
| `historial_rutas` | `id_usuario` + `_id` desc | compuesto | `GET /api/historial` (del más reciente al más antiguo) |
| `historial_rutas` | `created_at` | simple | Filtros de fecha del dashboard |
| `planes` | `id_usuario` + `_id` desc | compuesto | `GET /api/planes` |
| `planes` | `created_at` | simple | Filtros de fecha del dashboard |
| `reportes` | `ubicacion` | 2dsphere | Reportes cercanos |
| `reportes` | `vigente_hasta` | simple | `GET /api/reportes` (solo vigentes) |
| `reportes` | `ruta_id` | simple | Reportes de una ruta |
| `bitacora_laboratorio` | `tipo` + `creado_en` | compuesto | Dashboard, pestañas Laboratorio IA y Movilidad |
| `conversaciones` | `id_usuario` + `updated_at` desc | compuesto | Lista de conversaciones del usuario |
| `conversaciones` | `created_at` | simple | Dashboard, pestaña Asistente |

## 5. Validadores `$jsonSchema`

`preparar_bd.py` crea `usuarios`, `lugares`, `planes`, `reportes` y `conversaciones` (v0.6) con `validator: {$jsonSchema: …}` y
`validationLevel: "moderate"` (los documentos que ya existían no se bloquean, los nuevos sí se validan).
Resumen (el detalle completo está en `VALIDADORES` dentro del script):

```js
// usuarios
{ bsonType: "object",
  required: ["_id", "nombre", "primer_apellido", "correo", "password", "rol"],
  properties: {
    _id: { bsonType: ["int", "long"] }, correo: { bsonType: "string" }, password: { bsonType: "string" },
    rol: { enum: ["usuario", "admin"] }, fecha_nacimiento: { bsonType: ["date", "null"] },
    residencia: { bsonType: ["object", "null"] }, deleted_at: { bsonType: ["date", "null"] } } }

// lugares
{ required: ["_id", "nombre", "ubicacion", "categoria"],
  properties: { ubicacion: { required: ["type", "coordinates"],
                             properties: { type: { enum: ["Point"] },
                                           coordinates: { bsonType: "array", minItems: 2, maxItems: 2 } } },
                categoria: { required: ["id", "nombre"] } } }

// planes
{ required: ["_id", "id_usuario", "no_acompanantes", "tiempo_disponible", "categoria", "transporte", "fecha_plan"],
  properties: { contexto: { enum: ["solo", "pareja", "amigos", "familia"] },
                intereses: { items: { enum: ["comer", "cafe", "cultura", "entretenimiento", "aire_libre"] } },
                movilidad: { items: { enum: ["caminando", "transporte_publico", "taxi_app", "combinado"] } },
                tiempo_disponible: { minimum: 1 }, fecha_plan: { bsonType: "date" } } }

// reportes
{ required: ["tipo", "ubicacion", "observado_en", "vigente_hasta", "confirmaciones", "estado"],
  properties: { tipo: { enum: ["afluencia", "cierre_total", "accidente", "manifestacion"] },
                estado: { enum: ["pendiente", "verificado", "descartado"] }, confirmaciones: { minimum: 0 } } }
```

## 6. Migración desde MySQL

1. Instalar MongoDB (local, Docker `docker run -d -p 27017:27017 mongo:8.0`, o crear un clúster en Atlas).
2. En `backend/.env`: `MONGO_URI` y `MONGO_DB` (ver `.env.example`).
3. Crear colecciones, validadores e índices: `python -m scripts.preparar_bd --sin-datos`.
4. Copiar los datos (una sola vez):

   ```powershell
   pip install -r requirements-migracion.txt
   $env:MYSQL_URL="mysql+pymysql://root:pass@localhost:3306/kompas"
   python -m scripts.migrar_mysql_a_mongo --limpiar
   ```

5. Dar rol admin a quien verá el dashboard: `python -m scripts.crear_admin correo@dominio.com`.

El script conserva los ids, junta la residencia dentro del usuario, convierte el `LINESTRING` a GeoJSON y
lat/lng a `Point`. Si un trazo no es GeoJSON válido lo reporta y lo omite. Es idempotente (`--limpiar` vacía
antes; sin él usa `replace_one(..., upsert=True)`). Lo que MySQL no guardaba (contexto, presupuesto, evaluación)
no se inventa.

Tabla comparativa que imprimió con el esquema de desarrollo (25 de octubre de 2026):

```
Migración MySQL → MongoDB (base `kompas_migracion_prueba`)

Tabla MySQL          Registros   Colección MongoDB     Documentos
------------------------------------------------------------------
usuarios                     4   usuarios                       4
residencia                   0   usuarios.residencia            0
categorias                   5   categorias                     5
transportes                  4   transportes                    4
lugares_de_interes          10   lugares                       10
rutas                        0   rutas                          0
historial_rutas              0   historial_rutas                0
planes                       0   planes                         0
```

Para una base nueva sin MySQL basta `python -m scripts.preparar_bd`, que carga `database/datos_desarrollo.json`
(usuario demo `demo@kompas.mx` / `demo1234` con rol admin, catálogos y los 10 lugares genéricos). Los archivos
originales de MySQL quedan como evidencia en `backend/database/mysql_legacy/`.

## 7. Capturas sugeridas para el manual

1. MongoDB Compass (o Atlas → *Browse Collections*) con la lista de colecciones de `kompas`.
2. Un documento de `planes` abierto, mostrando `intereses`, `movilidad` y el subdocumento `evaluacion`.
3. La pestaña *Indexes* de `lugares` (índice `ubicacion_2dsphere`) y de `usuarios` (`correo_unico`).
4. La pestaña *Validation* de `usuarios` con el `$jsonSchema`.
5. La salida de `python -m scripts.preparar_bd` (tabla colección → documentos → índices) y la de la migración.
