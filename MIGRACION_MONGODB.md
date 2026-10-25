# Kompás — Migración de MySQL a MongoDB (v0.5)

> Parte de `PLAN_REFACTOR.md`. Se hace junto con la reorganización de ARQUITECTURA.md: los `repositorio.py`
> de cada módulo se escriben directamente con PyMongo. `app/ia/` no cambia (solo imports).

## 0. Por qué MongoDB

Se justifica así en el manual técnico y en la materia *Bases de datos en la nube*:

- **Modelo de documentos**: un plan guarda varios intereses y varios medios de transporte como arreglos, y su evaluación del sistema experto como subdocumento. En MySQL `planes` solo admitía una categoría y un transporte.
- **GeoJSON nativo**: lugares, rutas y reportes se guardan como `Point`/`LineString` con índice `2dsphere`. Desaparece la conversión manual a WKT (`LineaGeo` en `modelos.py`, ~80 líneas).
- **Agregaciones** (`$group`, `$facet`, `$bucket`, `$dateTrunc`) para el dashboard sin escribir SQL complejo.
- **Nube**: el mismo código funciona con MongoDB local o con **MongoDB Atlas** cambiando solo `MONGO_URI`.
- Esquema flexible con **validación `$jsonSchema`** para no perder control de los datos.

## 1. Dependencias (`backend/requirements.txt`)

Quitar: `sqlalchemy`, `pymysql`, `cryptography`. Agregar:

```
pymongo>=4.8
```

Crear `backend/requirements-migracion.txt` (solo para el script de §6.2, no lo necesita la API):

```
sqlalchemy>=2.0
pymysql
cryptography
```

## 2. Configuración

`backend/.env.example`:

```
# Local:  mongodb://localhost:27017
# Atlas:  mongodb+srv://USUARIO:PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
# (si la contraseña tiene @ : / ? # escríbela con urllib.parse.quote_plus)
MONGO_URI=mongodb://localhost:27017
MONGO_DB=kompas
JWT_SECRET=cambia-esto-por-algo-largo-y-aleatorio
JWT_EXPIRA_MINUTOS=10080
CORS_ORIGINS=*
GOOGLE_MAPS_API_KEY=tu-llave-de-google
GOOGLE_IDIOMA=es
GOOGLE_REGION=mx
```

En `nucleo/config.py`: quitar `database_url`; agregar `mongo_uri: str` y `mongo_db: str = "kompas"`.
Con Atlas, en **Network Access** hay que permitir la IP de la PC (o `0.0.0.0/0` solo para la demo).

## 3. Modelo de datos

### 3.1 Decisiones: embeber o referenciar

| Relación en MySQL | En MongoDB | Por qué |
|---|---|---|
| `residencia` (1:1 con usuario) | **Embebida** en `usuarios.residencia` | Siempre se lee junto con el usuario |
| `lugares_de_interes.id_cat` → `categorias` | **Referencia extendida**: `categoria: {id, nombre}` | Se lista mucho y así no hace falta "join"; el nombre de una categoría casi nunca cambia |
| `historial_rutas.id_transporte` | Referencia extendida `transporte: {id, nombre}` | Igual que arriba; agiliza el dashboard |
| `planes.id_categoria`, `id_transporte` | `categoria`/`transporte` extendidos **+ arreglos** `intereses`, `movilidad` | Se conserva lo que la API devuelve y se guarda todo lo que el usuario eligió |
| `historial_rutas.id_usuario`, `planes.id_usuario` | **Referencia** (`id_usuario`) | Crecen sin límite; no se embeben en el usuario |
| `rutas.ruta` (LINESTRING) | GeoJSON `LineString` | Formato estándar, igual al que ya usa la app (`[lng, lat]`) |

### 3.2 Identificadores

Se conservan **enteros** en `_id` para usuarios, categorías, transportes, lugares, rutas, historial y planes. Motivo: la app y la web ya esperan `id: number`, y la migración conserva los mismos números que había en MySQL.
Los ids nuevos salen de la colección `contadores`:

```python
from pymongo import ReturnDocument

def siguiente_id(bd, coleccion: str) -> int:
    doc = bd.contadores.find_one_and_update(
        {"_id": coleccion}, {"$inc": {"seq": 1}}, upsert=True, return_document=ReturnDocument.AFTER
    )
    return doc["seq"]
```

`reportes` y `bitacora_laboratorio` usan `ObjectId` (la app espera `_id: string` en reportes); el repositorio lo convierte con `str()` antes de devolverlo.

### 3.3 Fechas y borrado lógico

- Todas las fechas se guardan como `datetime` con zona horaria. El cliente se crea con `tz_aware=True, tzinfo=ZoneInfo("America/Mexico_City")`, así lo leído regresa en hora de Toluca.
- `fecha_nacimiento` (solo fecha): se guarda como `datetime` a las 00:00 y el repositorio la regresa como `date`.
- Se conserva el borrado lógico: todos los `find` filtran `{"deleted_at": None}`.

### 3.4 Colecciones (base `kompas`)

**`usuarios`**
```json
{
  "_id": 1,
  "nombre": "Demo", "primer_apellido": "Kompás", "segundo_apellido": null,
  "correo": "demo@kompas.mx",
  "password": "$2b$12$...",
  "fecha_nacimiento": "2004-05-10T00:00:00-06:00",
  "rol": "admin",
  "residencia": { "id": 1, "calle": "...", "numero_interior": null, "numero_exterior": "12",
                  "municipio": "Toluca", "colonia": "...", "estado": "México" },
  "created_at": "...", "updated_at": "...", "deleted_at": null
}
```
Índices: `correo` único. `rol` ∈ {`usuario`, `admin`}, por defecto `usuario` (nuevo; se usa en el dashboard).

**`categorias`** · `{_id, nombre, descripcion, created_at, updated_at, deleted_at}` · índice `nombre` único.
**`transportes`** · `{_id, nombre, ...tiempos}` · índice `nombre` único.

**`lugares`** (antes `lugares_de_interes`)
```json
{ "_id": 3, "nombre": "Cosmovitral", "ubicacion": { "type": "Point", "coordinates": [-99.6557, 19.2926] },
  "categoria": { "id": 2, "nombre": "Cultura" }, "id_usuario": 1, "created_at": "...", "deleted_at": null }
```
Índices: `ubicacion` 2dsphere, `categoria.id`.

**`rutas`** · `{_id, trazo: {type: "LineString", coordinates: [[lng, lat], ...]}, ...tiempos}` · índice `trazo` 2dsphere.

**`historial_rutas`**
```json
{ "_id": 10, "id_usuario": 1, "id_ruta": 2, "transporte": { "id": 1, "nombre": "Caminando" },
  "tiempo_estimado": 18, "created_at": "...", "deleted_at": null }
```
Índices: `{id_usuario: 1, _id: -1}`, `created_at`.

**`planes`**
```json
{
  "_id": 25, "id_usuario": 1,
  "contexto": "amigos", "no_acompanantes": 3,
  "presupuesto": { "min": 100, "max": 400 },
  "tiempo_disponible": 180,
  "intereses": ["comer", "cultura"], "movilidad": ["caminando", "transporte_publico"],
  "categoria": { "id": 1, "nombre": "Comer" }, "transporte": { "id": 1, "nombre": "Caminando" },
  "hora_salida": "18:00", "fecha_plan": "2026-10-28T18:00:00-06:00",
  "evaluacion": {
    "version_reglas": "1.0", "datos_suficientes": true,
    "candidatos": [
      { "tipo": "economico", "estado": "recomendable", "puntuacion": 7, "reglas": ["R01", "R04", "R12"] },
      { "tipo": "cultural", "estado": "no_recomendable", "puntuacion": null, "reglas": ["R02"] }
    ]
  },
  "created_at": "...", "deleted_at": null
}
```
Índices: `{id_usuario: 1, _id: -1}`, `created_at`.
`evaluacion` se llena con lo que **ya regresa** `app.ia.servicio.recomendar()`: de cada elemento de `planes` (tipo, estado, puntuacion, ids de `reglas_cumplidas`) y de `descartados` (tipo, estado, ids de `reglas`, `puntuacion: null`). **No se recalcula nada ni se toca `app/ia/`.**
No se guarda el `origen` exacto del usuario (privacidad).

**`reportes`** (nuevo, ver §7)
```json
{ "_id": "ObjectId", "tipo": "manifestacion", "ubicacion": { "type": "Point", "coordinates": [-99.625, 19.279] },
  "ruta_id": "2", "observado_en": "...", "vigente_hasta": "...", "confirmaciones": 0,
  "estado": "pendiente", "comentario": "...", "id_usuario": 1, "created_at": "..." }
```
Índices: `ubicacion` 2dsphere, `vigente_hasta`, `ruta_id`.
No se usa índice TTL a propósito: los reportes vencidos se conservan para las estadísticas del dashboard.

**`bitacora_laboratorio`** (nuevo): un documento por cada consulta a las demostraciones académicas. Colección **polimórfica** con campo discriminador `tipo`:
```json
{ "_id": "ObjectId", "tipo": "dfs", "creado_en": "...", "origen": "TerminalToluca", "destino": "PlazaSendero",
  "limite_profundidad": 5, "exito": true, "total_nodos_explorados": 8, "total_rutas": 2, "profundidad_maxima": 4 }
{ "_id": "ObjectId", "tipo": "distancia", "creado_en": "...", "modo": "geo",
  "euclidiana": 3.21, "manhattan": 4.10 }
```
Se escribe desde `modulos/laboratorio/servicio.py` **después** de obtener el resultado; si la escritura falla, se registra un `logging.warning` y la respuesta se devuelve igual. Los campos salen de la respuesta que ya calcula `app/ia/`.

**`contadores`** · `{_id: "<colección>", seq: <último id>}`.

### 3.5 Validación de esquema

`scripts/preparar_bd.py` crea `usuarios`, `lugares`, `planes` y `reportes` con `validator: {$jsonSchema: ...}` y `validationLevel: "moderate"`: campos obligatorios y `bsonType` de cada uno (por ejemplo, en `usuarios`: `correo` string, `password` string, `rol` enum `["usuario","admin"]`).

## 4. `nucleo/bd.py`

```python
"""Conexión a MongoDB con PyMongo. Un solo cliente para toda la app (pool de conexiones)."""
from functools import lru_cache
from zoneinfo import ZoneInfo

from pymongo import MongoClient
from pymongo.database import Database

from app.nucleo.config import get_settings

@lru_cache
def cliente() -> MongoClient:
    s = get_settings()
    return MongoClient(s.mongo_uri, tz_aware=True, tzinfo=ZoneInfo("America/Mexico_City"),
                       serverSelectionTimeoutMS=3000)

def get_bd() -> Database:
    """Dependencia de FastAPI: `bd: Database = Depends(get_bd)`."""
    return cliente()[get_settings().mongo_db]

def bd_disponible() -> bool:
    try:
        cliente().admin.command("ping")
        return True
    except Exception:
        return False

def siguiente_id(bd: Database, coleccion: str) -> int: ...   # §3.2
def ahora(): ...                                              # datetime aware en America/Mexico_City
```

`/api/salud` sigue regresando `{"ok": true, "bd": <bool>}`; solo cambia el docstring ("MongoDB responde").

## 5. Repositorios: equivalencias

| SQLAlchemy (antes) | PyMongo (ahora) |
|---|---|
| `select(Lugar).where(Lugar.deleted_at.is_(None)).order_by(Lugar.id_lugar)` | `bd.lugares.find({"deleted_at": None}).sort("_id", 1)` |
| `db.get(Ruta, id)` + revisar `deleted_at` | `bd.rutas.find_one({"_id": id, "deleted_at": None})` |
| `db.add(x); db.commit(); db.refresh(x)` | `doc["_id"] = siguiente_id(bd, "planes"); bd.planes.insert_one(doc)` |
| `IntegrityError` por correo repetido | `pymongo.errors.DuplicateKeyError` → `Conflicto(CORREO_EN_USO)` |
| `UPDATE residencia ...` | `bd.usuarios.update_one({"_id": id}, {"$set": {"residencia": {...}, "updated_at": ahora()}})` |
| `ST_AsText(ruta)` → lista | `doc["trazo"]["coordinates"]` (ya es `[[lng, lat], ...]`) |

Cada repositorio convierte el documento al **mismo `dict`** que hoy arma `servicios/serializar.py` (`id`, `_id` como texto, `lat`, `lng`, `ubicacion`, `categoria`, `interes`, los campos `null`…). Así la respuesta de la API no cambia.

Cambios por módulo:

| Módulo | Cambio |
|---|---|
| `cuenta` | Repositorio con `usuarios` (residencia embebida). `UsuarioSalida.rol` sale de la base (antes fijo en `"usuario"`). `get_usuario_actual` busca por `_id` del token. |
| `catalogos` | `find` con borrado lógico; `por_clave()` igual que antes usando `compartido.texto.clave`. |
| `lugares` | El filtro por distancia y el orden se quedan **en Python** como hoy, para que los resultados sean idénticos. El índice 2dsphere queda listo para mapa y uso futuro (`$near`). |
| `rutas` | Igual: lógica de `compartido.geo` sin cambios; solo cambia de dónde se leen los trazos. |
| `historial` | Guarda `transporte: {id, nombre}` embebido. |
| `itinerarios` | Guarda los campos nuevos de `planes` (§3.4). `GET /api/planes` devuelve exactamente los mismos campos que antes. |
| `laboratorio` | Nuevo `repositorio.py` que inserta en `bitacora_laboratorio`. |

## 6. Scripts (`backend/scripts/`)

### 6.1 `preparar_bd.py` (reescrito)

```
python -m scripts.preparar_bd              # crea colecciones, validadores e índices; carga datos de desarrollo si está vacía
python -m scripts.preparar_bd --recrear    # BORRA la base MONGO_DB y la crea de nuevo
python -m scripts.preparar_bd --sin-datos  # solo colecciones e índices
```

- Toma el nombre de la base de `MONGO_DB` (sirve para `kompas_test`).
- Carga `database/datos_desarrollo.json`, que se genera convirtiendo **los mismos registros** de `database/datos_desarrollo.sql` (usuario demo `demo@kompas.mx` / `demo1234`, categorías, transportes, los 10 lugares y las rutas). Adaptar `generar_datos_desarrollo.py` para que produzca el JSON.
- El usuario demo queda con `rol: "admin"` para poder abrir el dashboard.
- Al final pone cada `contadores.seq` en el `_id` máximo de su colección.
- Imprime una tabla: colección → documentos → índices.

### 6.2 `migrar_mysql_a_mongo.py` (nuevo, se usa una vez)

```
pip install -r requirements-migracion.txt
set MYSQL_URL=mysql+pymysql://root:pass@localhost:3306/kompas      # PowerShell: $env:MYSQL_URL="..."
python -m scripts.migrar_mysql_a_mongo [--limpiar]
```

- Lee MySQL con consultas `text()` de SQLAlchemy (no usa los modelos ORM, que ya no existen) y escribe en `MONGO_URI`/`MONGO_DB`.
- Conserva los ids, junta `residencia` dentro del usuario, convierte `LINESTRING` a GeoJSON (`ST_AsText(ruta, 'axis-order=long-lat')`) y lat/lng de lugares a `Point`.
- Si un trazo no es GeoJSON válido, lo reporta y sigue con los demás (no lo trunca ni lo inventa).
- Es idempotente: con `--limpiar` vacía las colecciones antes; sin él usa `replace_one(..., upsert=True)`.
- Al terminar imprime **tabla comparativa MySQL vs MongoDB** (registros por tabla/colección). Esa captura va en el manual.

### 6.3 `crear_admin.py` (nuevo)

`python -m scripts.crear_admin correo@dominio.com` → pone `rol: "admin"` a ese usuario.

### 6.4 Archivos de MySQL

Mover `database/Dump20260927.sql` y `database/datos_desarrollo.sql` a `database/mysql_legacy/` (evidencia histórica para el manual). Borrar el `Dump20260927.sql` duplicado de la raíz del repo solo si es idéntico al de `backend/database/`. Borrar `app/modelos.py` y `app/db.py`.

## 7. Módulo nuevo: `reportes`

La app móvil y la web ya llaman a `/api/reportes` (hoy solo funcionan en modo mock). Leer el contrato exacto en `app/src/types/dominio.ts` (`Reporte`, `NuevoReporte`, `TipoReporte`), `frontend/src/services/api.js` (o su nuevo `modulos/reportes/api.js`) y `app/src/services/mock/reportes.ts`, y respetarlo.

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/reportes` 🔒 | Crea un reporte. La API calcula `vigente_hasta` según el tipo: `cierre_total` 6 h, `accidente` 2 h, `manifestacion` 3 h, `afluencia` 1 h (los mismos valores del mock). Regresa `estado: "pendiente"` y `confirmaciones: 0`. |
| `GET` | `/api/reportes?ruta_id=` | Reportes vigentes (`vigente_hasta > ahora`); sin `ruta_id`, todos los vigentes de la zona. |

Validar que la ubicación esté dentro de la zona piloto con `compartido.geo.esta_dentro_de_zona` (mismo mensaje 422 que itinerarios). Prueba nueva: `tests/test_reportes.py`.

## 8. Pruebas

`tests/conftest.py`:

- Antes de importar la app: `os.environ["MONGO_DB"] = "kompas_test"` (mismo `MONGO_URI`). Nunca se toca la base `kompas`.
- Fixture `bd` de sesión: `preparar(recrear=True)` sobre `kompas_test`; si MongoDB no responde (ping con `serverSelectionTimeoutMS` corto), `pytest.skip("MongoDB no disponible para pruebas: ...")`.
- `registrar()`, `encabezado()` y `token_demo` se quedan igual.

Todas las pruebas existentes deben pasar sin cambiar sus asserts. Se agregan `test_reportes.py` y `test_bitacora.py` (que una búsqueda DFS deja un documento `tipo: "dfs"`).

## 9. Otros archivos

- `app/src/services/api.ts` y `frontend/.../api.js`: cambiar solo los comentarios "(MySQL)" por "(MongoDB)".
- `backend/README.md`: instalación de MongoDB (local o Atlas), `.env`, `preparar_bd`, `migrar_mysql_a_mongo`, `crear_admin`.
- `CONTEXTO.md` y `README.md`: ver PLAN_REFACTOR.md §3, paso 6.

## 10. Para el manual técnico (`DOCS/manual-tecnico/modelo-datos-mongodb.md`)

1. Justificación del cambio (§0) y tabla **embeber vs referenciar** (§3.1).
2. Diagrama Mermaid `erDiagram` del modelo anterior (MySQL, 8 tablas) y diagrama del modelo de documentos (colecciones, subdocumentos y referencias).
3. **Diccionario de datos** por colección: campo, tipo BSON, obligatorio, descripción, ejemplo.
4. Tabla de **índices** (colección, campos, tipo: único / 2dsphere / compuesto, para qué consulta).
5. Validadores `$jsonSchema`.
6. Pasos de migración y la tabla comparativa que imprime `migrar_mysql_a_mongo.py`.
7. Capturas sugeridas: MongoDB Compass o Atlas mostrando las colecciones, un documento de `planes` y los índices.

## 11. Criterios de aceptación

- [ ] `grep -rni "sqlalchemy\|pymysql" backend/app backend/tests` no encuentra nada.
- [ ] `python -m scripts.preparar_bd --recrear` funciona contra MongoDB local y contra Atlas.
- [ ] `pytest` verde: pasan todas las pruebas que pasaban antes del cambio, más las nuevas.
- [ ] App móvil y web funcionan contra la API real igual que con MySQL: registro, login, residencia, lugares cercanos, rutas, crear plan, mis planes, historial, reportes.
- [ ] `git diff main -- backend/app/ia/` vacío.
