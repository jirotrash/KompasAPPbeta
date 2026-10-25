# Kompás — API (FastAPI + MongoDB)

Especificación de endpoints en `../BACKEND.md`. Contrato de datos: `src/services/api.ts` y `src/types/dominio.ts` de la app.
Arquitectura en capas por módulos (`../ARQUITECTURA.md`): **router → servicio → repositorio → MongoDB**.
Modelo de datos: `../MIGRACION_MONGODB.md` y `../DOCS/manual-tecnico/modelo-datos-mongodb.md`.

## 1. MongoDB (elige una)

- **Local**: instala MongoDB Community Server (deja activado el servicio de Windows) → `mongodb://localhost:27017`.
- **Docker**: `docker run -d --name kompas-mongo -p 27017:27017 mongo:8.0` → `mongodb://localhost:27017`.
- **Atlas (nube)**: crea un clúster gratuito, un usuario de base de datos y en **Network Access** permite la IP
  de tu PC (o `0.0.0.0/0` solo para la demo). Copia la cadena `mongodb+srv://…`. Si la contraseña tiene
  `@ : / ? #`, escríbela con `urllib.parse.quote_plus`.

## 2. Arranque (Windows, PowerShell)

```powershell
cd backend
python -m venv venv                 # solo la primera vez
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env              # MONGO_URI, MONGO_DB, un JWT_SECRET largo y GOOGLE_MAPS_API_KEY
python -m scripts.preparar_bd       # colecciones, validadores, índices y datos de desarrollo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Documentación interactiva: <http://localhost:8000/docs> · salud: <http://localhost:8000/api/salud> → `{"ok": true, "bd": true}`
- Usuario de prueba: `demo@kompas.mx` / `demo1234` (rol **admin**: puede abrir el dashboard).
- En la app (`app/.env`): `EXPO_PUBLIC_API_URL=http://<IP-de-tu-PC>:8000` y `EXPO_PUBLIC_USE_MOCK=false`.
  Si el celular no conecta, abre el puerto 8000 en el firewall de Windows.
- En la web (`frontend/.env`): `VITE_API_URL=http://localhost:8000` y `VITE_USE_MOCK=false`.

## 3. Scripts (`python -m scripts.<nombre>`, desde `backend/`)

| Comando | Qué hace |
|---|---|
| `preparar_bd` | Crea colecciones, validadores `$jsonSchema` e índices; si la base está vacía carga `database/datos_desarrollo.json`. Imprime colección → documentos → índices |
| `preparar_bd --recrear` | **Borra** la base `MONGO_DB` y la crea de nuevo |
| `preparar_bd --sin-datos` | Solo colecciones e índices |
| `generar_datos_desarrollo` | Regenera `datos_desarrollo.json` (los hashes de bcrypt nunca se escriben a mano) |
| `crear_admin correo@dominio.com` | Da rol `admin` a ese usuario (`--quitar` lo regresa a `usuario`) |
| `sembrar_actividad_demo --dias 60 --usuarios 40 --planes 300` | Actividad sintética con `demo: true` para el dashboard (semilla fija) |
| `sembrar_actividad_demo --borrar` | Borra todo lo que tenga `demo: true` |
| `migrar_mysql_a_mongo [--limpiar]` | Copia una sola vez los datos del esquema MySQL anterior (ver abajo) |
| `distancias_clic` | Gráfica de escritorio de Euclidiana vs. Manhattan (requiere `pip install matplotlib`) |

Todos usan `MONGO_URI` y `MONGO_DB` del `.env`, así que sirven igual para local, Atlas o una base de pruebas
(`$env:MONGO_DB="otra_base"`).

### Migración desde MySQL (una vez)

```powershell
pip install -r requirements-migracion.txt
$env:MYSQL_URL="mysql+pymysql://root:pass@localhost:3306/kompas"
python -m scripts.migrar_mysql_a_mongo --limpiar
python -m scripts.crear_admin tu-correo@dominio.com
```

Conserva los ids, junta la residencia dentro del usuario, convierte el `LINESTRING` a GeoJSON y al final imprime la
tabla comparativa MySQL vs MongoDB. Los archivos de MySQL quedan en `database/mysql_legacy/` como evidencia.

## 4. Pruebas

```powershell
pytest
```

Usan la base `kompas_test` en el mismo servidor de `MONGO_URI` (se recrea en cada corrida; nunca tocan `kompas`).
Si MongoDB no responde, las pruebas que necesitan base se omiten. `TEST_MONGO_URI` permite usar otro servidor.
`tests/test_ia.py` prueba el sistema experto sin API, BD ni Google; `tests/test_itinerarios.py` simula a Google Places.

Motor de Einar por separado:

```powershell
python ..\DOCS\Brujula-Urbana\herramientas\sistema_experto_demo.py --verificar   # 36 comprobaciones; 20/20 reglas
python -m app.ia.hechos --ejemplo                                                   # usa ejemplos/entrada_hechos.json
```

## 5. Estructura

| Carpeta | Qué hay |
|---|---|
| `app/main.py` | Crea la app, CORS, manejadores de error y registra los routers |
| `app/nucleo/` | `config.py` (Settings), `bd.py` (cliente MongoDB único, `siguiente_id`), `seguridad.py` (bcrypt, JWT, `get_usuario_actual`, `requiere_admin`), `errores.py` (errores de negocio → HTTP), `parametros.py`, `esquemas_comunes.py` |
| `app/compartido/` | `geo.py` (distancias, zona piloto, horas), `traslados.py` (tramos a pie/taxi), `texto.py` (`clave()`) |
| `app/externos/` | `google_places.py` (Adaptador de Google Places) |
| `app/modulos/<módulo>/` | `router.py` (presentación), `esquemas.py` (DTO Pydantic), `servicio.py` (negocio), `repositorio.py` (MongoDB) |
| `app/ia/` | **Sistema experto** (`motor.py`, `hechos.py`), `planificador.py` y `servicio.py`; `busqueda_dfs.py` y `metricas_distancia.py` (laboratorios). No se cambia su lógica |
| `database/` | `datos_desarrollo.json` y `mysql_legacy/` (dump y datos de MySQL) |
| `scripts/` | Ver §3 |

Módulos: `cuenta` (auth + residencia), `catalogos`, `lugares`, `rutas`, `historial`, `itinerarios` (+ `GET /api/planes`),
`reportes`, `laboratorio` (DFS y distancias, escribe en `bitacora_laboratorio`) y `dashboard` (solo admin).

## 6. Endpoints nuevos en v0.5

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/reportes` 🔒 | Crea un reporte comunitario. La API calcula `vigente_hasta` (cierre total 6 h, accidente 2 h, manifestación 3 h, afluencia 1 h) |
| `GET` | `/api/reportes?ruta_id=` | Reportes vigentes |
| `GET` | `/api/dashboard/{kpis, series, planes, sistema-experto, movilidad, reportes, lugares, laboratorio}` 🔒 admin | Estadísticas con agregaciones de MongoDB (`../DOCS/manual-tecnico/dashboard.md`) |

`UsuarioSalida.rol` ahora sale de la base (`usuario` o `admin`). El resto del contrato no cambió.

## 7. Qué NO hay todavía

Líneas y paradas de autobús (la app las sigue simulando).
`POST /api/itinerarios` usa **Google Places**: sin `GOOGLE_MAPS_API_KEY` responde `503` (no se inventan lugares).
La app móvil todavía usa sus reportes de ejemplo aunque `/api/reportes` ya existe (`app/src/services/api.ts`).

## 8. Sistema experto (INTEGRAR_IA.md)

```
POST /api/itinerarios → itinerarios/servicio.py
                      → externos/google_places.buscar_para_plan()   lugares con horario y priceRange
                      → ia/servicio.recomendar()
                          ├─ planificador.armar_candidatos()        hasta 3: equilibrado, rápido, cercano
                          ├─ hechos.construir_hechos()              Einar: proposiciones true/false/null
                          └─ motor.evaluar()                        Einar: R01–R20 → estado, puntuación, traza
                      → itinerarios/repositorio.guardar()           plan + evaluación en `planes`
```

- `app/ia/motor.py` tiene el código de Einar **sin cambios** y `cargar_base()`, que lee
  `DOCS/Brujula-Urbana/docs/sistema-experto/reglas.json`. La demo de Einar y la API corren el mismo código.
- `recomendable` → `planes` (ordenados por puntuación; el mayor es `mejor_opcion`). `descartado`,
  `pendiente_verificacion` y `requiere_correccion` → `descartados`, con sus reglas y `datos_faltantes`.
- `priceLevel` de Google no se convierte a pesos; sin `priceRange` el plan queda pendiente de verificación.

## 9. Métricas de distancia: Euclidiana y Manhattan

`app/ia/metricas_distancia.py` tiene las dos fórmulas:

- **Cálculo real**: `compartido/geo.py` → `distancia_por_calles_km()` estima la distancia por calles con **Manhattan**
  sobre un plano local en km. La usan `/api/rutas`, los tramos a pie/taxi y el planificador.
- **API**: `GET /api/distancias/plano?a=1,2&b=5,5` y `GET /api/distancias/geo?origen=lat,lng&destino=lat,lng`
  (cada consulta queda en `bitacora_laboratorio` para el dashboard).
- **App**: pantalla *Distancias* (botón en Buscar). **Escritorio**: `python -m scripts.distancias_clic`.
