# Integrar la IA de Einar en el backend

> Instrucciones para Claude en VS Code. Leer junto con `CONTEXTO.md`, `BACKEND.md` (secciones 6 y 7) e `IA.md`.
> **No modificar la lógica de Einar** (`hechos.py`, reglas y motor). Solo moverla, importarla y conectarla.

## 1. Archivos de Einar y dónde van

| Archivo | Destino | Nota |
|---|---|---|
| `hechos.py` | `backend/app/ia/hechos.py` | Tal cual. Expone `construir_hechos(solicitud, itinerario, *, ahora, zona_validada, politica)` y `PoliticaHechos` |
| `herramientas/sistema_experto_demo.py` | se queda en `herramientas/` | Su lógica `evaluar()` pasa a `backend/app/ia/motor.py` (abajo) |
| `docs/sistema-experto/reglas.json` y `casos.json` | se quedan en `docs/sistema-experto/` | `motor.py` los lee desde ahí |

## 2. Crear `backend/app/ia/motor.py`

`hechos.py` hace `from app.ia.motor import cargar_base, evaluar`, así que `motor.py` debe exponer exactamente:

```python
def cargar_base() -> dict: ...          # lee y valida docs/sistema-experto/reglas.json
def evaluar(entrada: dict, base: dict) -> dict: ...
```

- Mover `ENTRADAS`, `CRITICOS`, `DERIVADOS`, `exigir`, `validar_base` y `evaluar` **sin cambios** desde `herramientas/sistema_experto_demo.py`.
- Hacer que `herramientas/sistema_experto_demo.py` importe esas funciones desde `backend/app/ia/motor.py` (agregando `backend` al `sys.path`), para que la demo y la API corran el mismo código.
- Comprobar: `python herramientas/sistema_experto_demo.py --verificar` debe seguir dando **`OK: 36 comprobaciones; 20/20 reglas activadas al menos una vez.`**
- Crear `backend/ejemplos/entrada_hechos.json` (lo usa `python -m app.ia.hechos --ejemplo`) con un `reloj_demostracion`, una `solicitud` y un `itinerario` como los de la sección 4.

## 3. Crear `backend/app/ia/planificador.py` y `servicio.py`

`servicio.recomendar(solicitud_app, lugares_google, ahora)`:

1. **Traducir la solicitud de la app** al formato de `hechos.py`:

| App (`POST /api/itinerarios`) | `hechos.py` |
|---|---|
| `contexto` | `contexto` |
| `intereses` (`comer`, `cafe`, `cultura`, `entretenimiento`, `aire_libre`) | `intereses` |
| `movilidad` (`caminando`, `taxi_app`, `transporte_publico`, `combinado`) | `movilidad` |
| `presupuesto.max` | `presupuesto_por_persona` (MXN) |
| `tiempo_horas` | `tiempo_minutos` = horas × 60 |
| `hora_salida` ("18:00") | `fecha_hora_salida` ISO con zona, ej. `2026-09-30T18:00:00-06:00` |
| — | `incluir_regreso: false` (MVP) |

2. **Validar la zona piloto en el servidor** (Toluca, Lerma, San Mateo Atenco) y pasar `zona_validada=True/False`. Nunca tomarlo del JSON del usuario.

3. **Planificador:** armar hasta 3 itinerarios (equilibrado, rápido, cercano) con 2–3 lugares cada uno. Cada itinerario debe cumplir lo que valida `hechos.py`:
   - `visitas[]`: `place_id`, `nombre`, `categoria`, `llegada_estimada` (ISO con zona), `horario`, `rango_precio`, `consultado_en`.
     - `horario`: pasar **directo** el objeto `regularOpeningHours` de Google (con `periods`).
     - `rango_precio`: de `priceRange` de Google → `{"min": startPrice, "max": endPrice, "moneda": "MXN"}`; si Google no lo trae, `None`. **`priceLevel` no se convierte a pesos** (decisión de Einar).
     - `consultado_en`: hora en que se consultó Google (debe tener menos de 15 minutos).
     - `estancia_minutos` se puede omitir: `hechos.py` usa su tabla por categoría.
   - `tramos[]`: **uno por visita** (+1 si hay regreso) con `modo`, `km`, `minutos`, `estimado: true`. Si el modo es `taxi_app`, agregar `costo_por_persona` y `moneda: "MXN"` solo si hay un dato real; si no, omitirlo (el presupuesto queda desconocido).
   - Las `llegada_estimada` deben ser coherentes: salida + traslado ≤ llegada; siguiente llegada ≥ llegada anterior + estancia + traslado.
   - `regreso_incluido: false`.
   - Distancias y minutos a pie estimados por coordenadas (haversine × 1.3, ≈ 12 min/km).
   - **Preferir lugares que traigan `priceRange` y `regularOpeningHours`**: sin ellos el candidato sale `pendiente_verificacion`.

4. Por cada itinerario:
```python
r = construir_hechos(solicitud, itinerario, ahora=ahora, zona_validada=zona_ok)
e = evaluar(r["hechos"], BASE)          # BASE = cargar_base() una sola vez al iniciar
```

5. **Respuesta para la app** (ver `BACKEND.md` §6):
   - `recomendable` → `planes`, ordenados por `puntuacion_preferencias` (mayor = `mejor_opcion`), con `reglas_cumplidas` = `traza` (id + explicación) y `explicacion` en español.
   - `descartado` / `pendiente_verificacion` / `requiere_correccion` → `descartados`, con `estado`, reglas de la `traza` y `datos_faltantes`.
   - `aviso` = unión de `r["advertencias"]` y `e["advertencias"]` (incluye R13: no se verifican cierres).
   - Incluir `version_reglas`.

## 4. Prueba mínima que ya se comprobó

Con 2 visitas a pie (café y restaurante), horario 08:00–22:00, `rango_precio` 100–180 MXN, presupuesto 400, 4 horas, pareja:
- Resultado: **`recomendable`, 6 puntos**, reglas `R11, R13, R15, R16, R17, R18, R19, R20`.

Mismo itinerario **sin** `rango_precio`:
- Resultado: **`pendiente_verificacion`**, reglas `R09, R11, R13`.

Convertir ambos casos en `tests/test_ia.py` con `ahora` fijo (`2026-09-30T17:59:00-06:00`).

## 5. No hacer
- No cambiar `hechos.py`, `reglas.json` ni la lógica de `evaluar()`.
- No mandar hechos ni conclusiones desde la app.
- No convertir `priceLevel` en pesos ni poner costo 0 cuando no se sabe.
- No inventar horarios ni rutas.
