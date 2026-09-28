# Kompás — Backend (API + sistema experto)

> Especificación para construir el backend. Está pensada para dársela a Claude en VS Code:
> "Lee BACKEND.md y CONTEXTO.md y construye el backend paso por paso, empezando por la Fase 1".
> Colócala en la raíz del repo junto a `CONTEXTO.md`. Para el backend, si algo choca con `CONTEXTO.md`, **manda este archivo**.

## 0. Contexto rápido

- **Kompás** (antes "Brújula Urbana") es una app móvil de movilidad y planes de salida para **Toluca, Lerma y San Mateo Atenco**.
- La app ya existe: **React Native + Expo** (carpeta de la app, ver su `README.md`). Hoy funciona con datos de ejemplo (`EXPO_PUBLIC_USE_MOCK=true`).
- Este backend reemplaza esos datos de ejemplo. **Debe responder con los tipos que espera la app**:
  - Leer primero `src/services/api.ts` y `src/types/dominio.ts` de la app, y la simulación `src/services/mock/` (en especial `mock/motor.ts`).
  - Si la app espera un campo que la base no tiene (horario, costo, calificación, tramos en autobús), mandarlo como `null` o vacío. **No inventar el dato.**
- La base de datos es **MySQL 8**, esquema `kompas`, **tal como está en el diagrama y el dump de Sebas** (`database/Dump20260927.sql`). No se usa MongoDB.
- **No se modifica el esquema.** Nada de `ALTER TABLE` ni tablas nuevas: el backend trabaja con las 8 tablas que existen. Si se necesita un cambio, se habla con Sebas primero.
- La **IA** es un **sistema experto con lógica proposicional**, en Python, dentro de este mismo backend (`app/ia/`). La programa **Einar**; el backend solo la llama.

### Reglas que el código nunca debe romper
1. **No inventar rutas, horarios, costos ni horas de llegada.** Si faltan datos, responder que no hay información suficiente.
2. Los tiempos son **estimaciones** (calculados por distancia) y así se marcan.
3. Nunca guardar contraseñas en texto plano ni subir `.env` al repo.
4. No modificar el esquema de la base de datos sin acuerdo con Sebas.

## 1. Stack

| Pieza | Elección |
|---|---|
| Lenguaje | Python 3.11+ |
| Framework | **FastAPI** + **Uvicorn** |
| Base de datos | **MySQL 8** con **SQLAlchemy 2.0** (estilo `select()`) y **PyMySQL** |
| Validación | **Pydantic v2** (+ `pydantic-settings` para `.env`) |
| Contraseñas | `bcrypt` |
| Tokens | **JWT** con `PyJWT` (`Authorization: Bearer <token>`) |
| Pruebas | `pytest` + `httpx` (`TestClient`) |

`requirements.txt`:
```
fastapi
uvicorn[standard]
sqlalchemy>=2.0
pymysql
cryptography
pydantic>=2
pydantic-settings
bcrypt
pyjwt
python-dotenv
pytest
httpx
```

## 2. Estructura

```
backend/
├── app/
│   ├── main.py              # crea la app, CORS, incluye routers, /api/salud
│   ├── config.py            # Settings desde .env
│   ├── db.py                # engine, SessionLocal, get_db()
│   ├── seguridad.py         # hash de contraseña, crear/verificar JWT, get_usuario_actual()
│   ├── modelos.py           # modelos SQLAlchemy de las 8 tablas de kompas
│   ├── esquemas/            # modelos Pydantic de entrada/salida
│   │   ├── auth.py
│   │   ├── lugares.py
│   │   ├── rutas.py
│   │   ├── itinerarios.py
│   │   └── historial.py
│   ├── routers/
│   │   ├── auth.py          # registro, login, yo, residencia
│   │   ├── catalogos.py     # categorías y transportes
│   │   ├── lugares.py
│   │   ├── rutas.py
│   │   ├── itinerarios.py   # llama a ia.motor.recomendar() y guarda en planes
│   │   └── historial.py
│   ├── servicios/
│   │   └── geo.py           # distancia haversine, LINESTRING → lista de puntos
│   └── ia/                  # ← EINAR
│       ├── __init__.py
│       ├── hechos.py        # calcula los hechos booleanos por lugar
│       ├── reglas.py        # lista de reglas SI … ENTONCES …
│       └── motor.py         # recomendar(solicitud, lugares) -> respuesta
├── database/
│   ├── Dump20260927.sql     # esquema de Sebas (no se modifica)
│   └── datos_desarrollo.sql # solo INSERTs para probar (sección 5)
├── tests/
│   ├── test_auth.py
│   ├── test_itinerarios.py
│   └── test_motor.py        # pruebas del sistema experto sin API ni BD
├── .env.example
└── requirements.txt
```

## 3. Configuración

`.env.example`:
```
DATABASE_URL=mysql+pymysql://root:tu_password@localhost:3306/kompas
JWT_SECRET=cambia-esto-por-algo-largo-y-aleatorio
JWT_EXPIRA_MINUTOS=10080
CORS_ORIGINS=*
```

- **CORS** abierto en desarrollo (la app también corre con `npx expo start --web`).
- Levantar para que el celular lo vea:
  ```bash
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  ```
  En la app: `EXPO_PUBLIC_API_URL=http://<IP-de-tu-PC>:8000` y `EXPO_PUBLIC_USE_MOCK=false`. Abrir el puerto 8000 en el firewall de Windows si el celular no conecta.
- Documentación automática en `http://localhost:8000/docs` (sirve para el manual técnico).

## 4. Base de datos (diagrama de Sebas)

| Tabla | Campos | Relaciones |
|---|---|---|
| `usuarios` | id_usuario, nombre, primer_apellido, segundo_apellido, correo (único), password, fecha_nacimiento | — |
| `residencia` | id_residencia, calle, numero_interior, numero_exterior, municipio, colonia, estado | id_usuario → usuarios |
| `categorias` | id_categoria, nombre (único), descripcion | — |
| `lugares_de_interes` | id_lugar, nombre, longitud, latitud | id_usuario → usuarios, id_cat → categorias |
| `transportes` | id_transporte, nombre (único) | — |
| `rutas` | id_ruta, ruta (`LINESTRING`, SRID 4326) | — |
| `historial_rutas` | id_historial, tiempo_estimado | id_ruta → rutas, id_usuario → usuarios, id_transporte → transportes |
| `planes` | id_plan, no_acompanantes, tiempo_disponible, fecha_plan | id_transporte → transportes, id_categoria → categorias, id_usuario → usuarios |

- Todas tienen `created_at`, `updated_at` y `deleted_at` (**borrado lógico**: toda consulta filtra `deleted_at IS NULL`; "eliminar" = poner fecha en `deleted_at`).
- La columna de contraseña se llama **`password`** (VARCHAR 255): ahí va el hash de bcrypt.
- `lugares_de_interes.id_usuario` es **quien registró el lugar** (para los datos de prueba, el usuario administrador).

### Ojo con `LINESTRING` y SRID 4326 en MySQL 8
Con SRID 4326, MySQL usa el orden **latitud, longitud** por defecto. Para no confundirse, leer y escribir siempre así:
```sql
-- escribir (longitud primero, como GeoJSON)
ST_GeomFromText('LINESTRING(-99.49 19.28, -99.60 19.29)', 4326, 'axis-order=long-lat')
-- leer como GeoJSON: coordinates = [[lng, lat], ...]
SELECT id_ruta, ST_AsGeoJSON(ruta) FROM rutas;
```
En SQLAlchemy leer la columna con `func.ST_AsGeoJSON(...)`; no hace falta GeoAlchemy.

### Cómo se guarda un plan con las columnas que hay
El planificador manda más cosas de las que caben en `planes`. Se guarda lo que existe y el resto solo viaja en la respuesta:

| Del planificador | Columna de `planes` |
|---|---|
| `contexto` | `no_acompanantes`: solo = 0, pareja = 1, amigos = 3, familia = 3 |
| `tiempo_horas` | `tiempo_disponible` en **minutos** (`tiempo_horas × 60`) |
| primer valor de `movilidad` | `id_transporte` (buscar por nombre en `transportes`) |
| primer valor de `intereses` | `id_categoria` (buscar por nombre en `categorias`) |
| `hora_salida` de hoy | `fecha_plan` |
| usuario del token | `id_usuario` |

## 5. Datos de desarrollo — `database/datos_desarrollo.sql`
Solo `INSERT`, sin tocar la estructura.
- **Usuario administrador** (dueño de los lugares de prueba) y **usuario demo** `demo@kompas.mx` / `demo1234`. El hash de bcrypt se genera con un script, no a mano.
- **Categorías** con los mismos nombres que usa la app (revisar `src/constants/catalogos.ts`): Comer, Café, Cultura, Entretenimiento, Aire libre.
- **Transportes**: Caminando, Transporte público, Taxi/App, Combinado.
- **Lugares**: los reales los levanta Sebas en la zona piloto. Mientras llegan, 5–10 lugares de prueba con coordenadas dentro de Toluca / Lerma / San Mateo Atenco.
- **Rutas**: solo trazos que el equipo haya recorrido. No inventar recorridos de autobús.

## 6. Endpoints

Todos bajo `/api`. Los marcados con 🔒 requieren `Authorization: Bearer <token>`.
Errores con formato de FastAPI: `{"detail": "mensaje claro en español"}` y código HTTP correcto (400, 401, 404, 409, 422).

### Salud
| Método | Ruta | Respuesta |
|---|---|---|
| GET | `/api/salud` | `{"ok": true}` |

### Cuenta — tablas `usuarios` y `residencia`
| Método | Ruta | Entrada | Respuesta |
|---|---|---|---|
| POST | `/api/auth/registro` | `nombre, primer_apellido, segundo_apellido?, correo, password (≥6), fecha_nacimiento?` | `201` `{token, usuario}` · `409` si el correo existe |
| POST | `/api/auth/login` | `correo, password` | `{token, usuario}` · `401` si no coincide |
| GET 🔒 | `/api/auth/yo` | — | `usuario` |
| GET 🔒 | `/api/residencia` | — | residencia del usuario o `null` |
| PUT 🔒 | `/api/residencia` | `calle, numero_interior, numero_exterior, municipio, colonia, estado` (todos opcionales) | residencia guardada (la crea si no existe) |

`usuario` = `{id, nombre, primer_apellido, segundo_apellido, correo, fecha_nacimiento}` (**nunca** la contraseña).
> Confirmar nombres de rutas y campos contra `src/services/api.ts` de la app.

### Catálogos
| Método | Ruta | Respuesta |
|---|---|---|
| GET | `/api/categorias` | `[{id, nombre, descripcion}]` |
| GET | `/api/transportes` | `[{id, nombre}]` |

### Lugares — tabla `lugares_de_interes` (+ `categorias`)
| Método | Ruta | Uso |
|---|---|---|
| GET | `/api/lugares?lat=&lng=&radio_km=5&categoria=` | "Cerca de ti", ordenados por distancia |
| GET | `/api/lugares/{id}` | Detalle |

Cada lugar: `{id, nombre, lat, lng, categoria, distancia_km, minutos_caminando}`.
`minutos_caminando` ≈ 12 min por km, marcado como estimado. Campos que la app muestre y la base no tenga (`calificacion`, `horario`, `costo_promedio`, `foto`) van en `null` y la app muestra "Sin dato".

### Rutas — tabla `rutas`
| Método | Ruta | Uso |
|---|---|---|
| GET | `/api/rutas` | Lista `[{id, trazo: [[lng, lat], ...]}]` |
| GET | `/api/rutas/{id}` | Una ruta con su `trazo` para dibujarla en el mapa |

### Itinerarios (sistema experto) — tablas `lugares_de_interes`, `categorias`, `planes`
| Método | Ruta | Uso |
|---|---|---|
| POST 🔒 | `/api/itinerarios` | Recibe el JSON del planificador, carga los lugares, llama a `ia.motor.recomendar()`, guarda el plan en `planes` (tabla de la sección 4) y regresa la respuesta |
| GET 🔒 | `/api/planes` | Planes que ha creado el usuario (de la tabla `planes`) |

Entrada (igual a CONTEXTO.md §6.1):
```json
{
  "contexto": "pareja",
  "presupuesto": { "min": 200, "max": 1500 },
  "tiempo_horas": 4,
  "intereses": ["comer", "cafe", "entretenimiento"],
  "movilidad": ["caminando", "taxi_app"],
  "origen": { "lat": 19.28, "lng": -99.50 },
  "hora_salida": "18:00"
}
```
Salida:
```json
{
  "planes": [
    {
      "tipo": "equilibrado",
      "mejor_opcion": true,
      "costo": null,
      "duracion_horas": 3.5,
      "distancia_km": 3.2,
      "paradas": [{ "lugar_id": 1, "nombre": "…", "llegada_estimada": "18:20" }],
      "tramos": [{ "modo": "caminando", "desde": "…", "hasta": "…", "minutos": 8 }],
      "explicacion": "Los 3 lugares coinciden con tus intereses y el recorrido cabe en tus 4 horas…",
      "reglas_cumplidas": [{ "id": "R1", "descripcion": "coincide_intereses ∧ cerca → candidato" }]
    }
  ],
  "descartados": [
    { "lugar_id": 7, "nombre": "…", "reglas": [{ "id": "R4", "descripcion": "Queda demasiado lejos para el tiempo disponible" }] }
  ],
  "aviso": "Todavía no tenemos costos ni horarios de los lugares; revisa antes de ir."
}
```
- **`costo` va en `null`**: la base no tiene costos. El presupuesto se recibe pero todavía no se puede evaluar, y así lo dice el `aviso`.
- Los tramos son **caminando** (calculados por distancia) o en taxi si el usuario lo eligió; **no hay tramos en autobús** porque la base no tiene líneas ni paradas.
- Si no hay lugares suficientes: `planes: []` y `aviso: "No tenemos información suficiente para …"`. **Nunca rellenar con datos inventados.**
- `origen` debe estar dentro de la zona piloto; si no, `422` con mensaje claro.

### Historial — tabla `historial_rutas`
| Método | Ruta | Uso |
|---|---|---|
| POST 🔒 | `/api/historial` | Guarda un recorrido que el usuario inició (`id_ruta, id_transporte, tiempo_estimado` en minutos) |
| GET 🔒 | `/api/historial` | Recorridos del usuario |

## 7. Sistema experto (`app/ia/`) — contrato con Einar

El router **solo** hace esto:
```python
from app.ia.motor import recomendar
respuesta = recomendar(solicitud.model_dump(), lugares_como_dicts)
```

`motor.py` **no importa nada de FastAPI ni de la BD**: recibe diccionarios y regresa un diccionario. Así Einar lo prueba solo con `pytest tests/test_motor.py`.

### Hechos que sí se pueden calcular con la base actual
| Hecho | De dónde sale |
|---|---|
| `coincide_intereses` | categoría del lugar ∈ intereses del usuario |
| `cerca` | distancia del origen al lugar ≤ radio según movilidad (caminando ≈ 2 km, taxi/app ≈ 8 km) |
| `cabe_en_tiempo` | minutos de traslado + minutos de estancia por categoría ≤ tiempo disponible |
| `apto_contexto` | categoría adecuada para el contexto (ej. Aire libre ✔ familia, Café ✔ pareja) — tabla fija en `reglas.py` |
| `datos_suficientes` | el lugar tiene coordenadas y categoría |
| `hay_candidatos` | al menos 2 lugares recomendables |

Reglas de ejemplo (meta: 15–20):
```
R1: coincide_intereses ∧ cerca → candidato
R2: candidato ∧ apto_contexto → recomendable
R3: recomendable ∧ cabe_en_tiempo → incluir_en_plan
R4: ¬cerca → descartar ("queda lejos para tu forma de moverte")
R5: ¬datos_suficientes → descartar ("no tenemos información suficiente")
R6: ¬hay_candidatos → avisar_sin_informacion
R7: movilidad = caminando ∧ distancia > 2 km → descartar
…
```
Horario y presupuesto **no** se evalúan hasta que la base tenga esos datos (ver sección 10).

Estructura sugerida:
```python
# hechos.py — un hecho = función que regresa True/False
# reglas.py — Regla(id, descripcion, condicion, conclusion)
# motor.py
def recomendar(solicitud: dict, lugares: list[dict]) -> dict:
    # 1. calcular hechos por lugar
    # 2. encadenamiento hacia adelante: aplicar reglas hasta que no salga nada nuevo
    # 3. armar hasta 3 planes (equilibrado, rápido, cercano) con los lugares incluidos
    # 4. anotar reglas_cumplidas y una explicación en español por plan
    # 5. listar descartados con la regla que los sacó
```

**Mientras Einar termina:** crear `motor.py` como **traducción de `src/services/mock/motor.ts`** de la app, quitando lo que dependa de costo u horario, con un comentario `# TEMPORAL — Einar reemplaza con el motor de reglas`. Así la demo funciona desde el primer día.

## 8. Convenciones

- Nombres del dominio en español (`lugares`, `rutas`, `planes`); código limpio y con tipos.
- Una sesión de BD por petición (`Depends(get_db)`).
- Nada de SQL armado con f-strings: usar parámetros.
- Contraseñas con `bcrypt`; JWT con `sub = id_usuario` y expiración.
- Commits en español e imperativo: `Agrega endpoint de login`.
- `.env` en `.gitignore`; subir solo `.env.example`.

## 9. Orden de trabajo

| Fase | Qué | Listo cuando… |
|---|---|---|
| **1** | Proyecto base: `config`, `db`, `main`, `/api/salud`, CORS | `/docs` abre y `/api/salud` responde |
| **2** | Modelos SQLAlchemy de las 8 tablas + `datos_desarrollo.sql` | Los modelos leen todas las tablas sin error |
| **3** | Cuenta: registro, login, `yo`, residencia | La app con `USE_MOCK=false` inicia sesión desde el celular |
| **4** | Catálogos y lugares | "Cerca de ti" muestra lugares de la BD |
| **5** | `ia/motor.py` temporal + `POST /api/itinerarios` + `GET /api/planes` | "Crear mi plan" devuelve planes reales en la app ← **mínimo para la demo del miércoles** |
| **6** | Rutas | El mapa dibuja una ruta de la BD |
| **7** | Historial | Se guarda un recorrido iniciado |
| **8** | Pruebas (`pytest`) y revisar `/docs` para el manual técnico | Pruebas en verde |

## 10. Fuera por ahora (necesitan cambios en la base)

No se programan hasta que Sebas los agregue al diagrama:
- **Horario, costo, calificación y fuente de los lugares** → reglas de "está abierto" y "cabe en el presupuesto".
- **Línea, sentido, tarifa y paradas de las rutas** → instrucciones en autobús (dónde subir y dónde bajar).
- **Reportes comunitarios** → la pantalla Reportar sigue con datos de ejemplo.
- **Varios intereses y medios por plan** → hoy `planes` guarda solo el primero de cada uno.

## 11. Demo del miércoles 30

1. Iniciar sesión con `demo@kompas.mx` (MySQL).
2. Ver lugares "Cerca de ti" traídos de la BD.
3. Planificador → **Crear mi plan** → la API llama al sistema experto → la app muestra los planes con su explicación y los lugares descartados con la regla que los descartó.
4. Abrir `/docs` para mostrar los endpoints.