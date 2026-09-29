# Kompás — API (FastAPI + MySQL)

Especificación completa en `../BACKEND.md`. Contrato de datos: `src/services/api.ts` y `src/types/dominio.ts` de la app.
Trabaja con las **8 tablas del dump de Sebas, sin modificarlas**.

## Arranque (Windows, PowerShell)

```powershell
cd backend
python -m venv venv                 # solo la primera vez
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env              # MySQL, un JWT_SECRET largo y GOOGLE_MAPS_API_KEY
python -m scripts.preparar_bd       # crea `kompas`: Dump20260927.sql + datos_desarrollo.sql
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Documentación interactiva: <http://localhost:8000/docs>
- Usuario de prueba: `demo@kompas.mx` / `demo1234`
- En la app (`app/.env`): `EXPO_PUBLIC_API_URL=http://<IP-de-tu-PC>:8000` y `EXPO_PUBLIC_USE_MOCK=false`.
  Si el celular no conecta, abre el puerto 8000 en el firewall de Windows.
- `python -m scripts.preparar_bd --recrear` borra y vuelve a crear el esquema.
- `database/datos_desarrollo.sql` solo tiene INSERTs; se genera con `python -m scripts.generar_datos_desarrollo`
  (así los hashes de bcrypt nunca se escriben a mano). También se puede ejecutar directo en Workbench/HeidiSQL.

Funciona con **MySQL 8** y con **MariaDB** (el `LINESTRING` se lee y escribe según el motor).

## Qué NO hay todavía (BACKEND.md §10)

Líneas y paradas de autobús y reportes comunitarios (la app los sigue simulando).
`POST /api/itinerarios` usa **Google Places**: sin `GOOGLE_MAPS_API_KEY` responde `503` (no se inventan lugares).
`GET /api/lugares` ("Cerca de ti") todavía lee la tabla de MySQL.

## Pruebas

```powershell
pytest
```

Usan el esquema `kompas_test` (se recrea en cada corrida; nunca tocan `kompas`).
`tests/test_ia.py` prueba el sistema experto de Einar sin API, BD ni Google (casos de INTEGRAR_IA.md §4).
`tests/test_itinerarios.py` simula a Google Places; no gasta cuota ni necesita la llave.

Motor de Einar por separado:

```powershell
python ..\DOCS\Brujula-Urbana\herramientas\sistema_experto_demo.py --verificar   # 36 comprobaciones; 20/20 reglas
python -m app.ia.hechos --ejemplo                                                   # usa ejemplos/entrada_hechos.json
```

## Estructura

| Carpeta | Qué hay |
|---|---|
| `app/routers/` | Endpoints: cuenta (auth + residencia), catálogos, lugares, rutas, itinerarios + planes, historial |
| `app/esquemas/` | Modelos Pydantic de entrada y salida (lo que ve `/docs`) |
| `app/modelos.py` | Las 8 tablas de MySQL (SQLAlchemy) |
| `app/servicios/` | Google Places (`google_places.py`), distancias y zona piloto, tramos a pie/taxi, conversión a la forma de la app |
| `app/ia/` | **Sistema experto**: `motor.py` y `hechos.py` (Einar), `planificador.py` y `servicio.py` (conexión con la API) |
| `database/` | Dump de Sebas (no se modifica) y `datos_desarrollo.sql` |
| `scripts/` | `preparar_bd.py` y `generar_datos_desarrollo.py` |

## Sistema experto (INTEGRAR_IA.md)

```
POST /api/itinerarios → google_places.buscar_para_plan()      lugares con horario y priceRange
                      → servicio.recomendar()
                          ├─ planificador.armar_candidatos()  hasta 3: equilibrado, rápido, cercano
                          ├─ hechos.construir_hechos()        Einar: proposiciones true/false/null
                          └─ motor.evaluar()                  Einar: R01–R20 → estado, puntuación, traza
```

- `app/ia/motor.py` tiene el código de Einar **sin cambios** (`evaluar`, `validar_base`…) y `cargar_base()`,
  que lee `DOCS/Brujula-Urbana/docs/sistema-experto/reglas.json`. La demo de Einar lo importa de aquí:
  la demo y la API corren el mismo código.
- `hechos.py`, `reglas.json` y la lógica de `evaluar()` **no se modifican** desde el backend.
- `recomendable` → `planes` (ordenados por puntuación; el mayor es `mejor_opcion`). `descartado`,
  `pendiente_verificacion` y `requiere_correccion` → `descartados`, con sus reglas y `datos_faltantes`.
- `priceLevel` de Google no se convierte a pesos; sin `priceRange` el plan queda pendiente de verificación.
