# Kompás — API (FastAPI + MySQL)

Especificación completa en `../BACKEND.md`. Contrato de datos: `src/services/api.ts` y `src/types/dominio.ts` de la app.
Trabaja con las **8 tablas del dump de Sebas, sin modificarlas**.

## Arranque (Windows, PowerShell)

```powershell
cd backend
python -m venv venv                 # solo la primera vez
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env              # y pon tu usuario/contraseña de MySQL y un JWT_SECRET largo
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

## Qué NO hay todavía (falta en la base, BACKEND.md §10)

Horario, costo y calificación de lugares (van en `null`), líneas y paradas de autobús, y reportes
comunitarios (la app los sigue simulando). El presupuesto se recibe pero no se evalúa.

## Pruebas

```powershell
pytest
```

Usan el esquema `kompas_test` (se recrea en cada corrida; nunca tocan `kompas`).
`tests/test_motor.py` prueba el sistema experto sin API ni BD.

## Estructura

| Carpeta | Qué hay |
|---|---|
| `app/routers/` | Endpoints: cuenta (auth + residencia), catálogos, lugares, rutas, itinerarios + planes, historial |
| `app/esquemas/` | Modelos Pydantic de entrada y salida (lo que ve `/docs`) |
| `app/modelos.py` | Las 8 tablas de MySQL (SQLAlchemy) |
| `app/servicios/` | Distancias y zona piloto, tramos a pie/taxi, conversión a la forma de la app |
| `app/ia/` | **Sistema experto (Einar)**: `hechos.py`, `reglas.py` (encadenamiento hacia adelante), `motor.py` — versión TEMPORAL |
| `database/` | Dump de Sebas (no se modifica) y `datos_desarrollo.sql` |
| `scripts/` | `preparar_bd.py` y `generar_datos_desarrollo.py` |

## Para Einar

El router solo llama a `app.ia.motor.recomendar(solicitud, lugares)`: recibe diccionarios
(forma en `app/servicios/serializar.py` → `lugar()`) y regresa
`{datos_suficientes, mensaje, aviso, planes, descartados}`.
Las reglas están en `app/ia/reglas.py` como `Regla(id, si, entonces, motivo)`; reemplázalas conservando
esa firma y corre `pytest tests/test_motor.py`.
