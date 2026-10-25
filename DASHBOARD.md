# Kompás — Dashboard de estadísticas (v0.5)

> Parte de `PLAN_REFACTOR.md`. Usa las colecciones de MIGRACION_MONGODB.md.
> Backend: módulo `app/modulos/dashboard/`. Frontend: `frontend/src/modulos/dashboard/`.

## 0. Qué es

Una sección **`/dashboard`** en la web (`frontend/`), visible solo para usuarios con `rol: "admin"`, que muestra cómo se usa Kompás y cómo decide la IA: usuarios, planes, intereses, presupuestos, decisiones del sistema experto, recorridos, reportes, lugares y las demostraciones académicas (DFS y distancias).
Todos los números salen de **agregaciones de MongoDB** calculadas en la API; la web solo dibuja.

## 1. Backend: módulo `dashboard`

```
app/modulos/dashboard/
├── router.py        # GET /api/dashboard/* — todos con Depends(requiere_admin)
├── servicio.py      # arma las respuestas, rellena días sin datos con 0, agrega descripciones de reglas
├── repositorio.py   # SOLO pipelines de agregación (aquí vive todo el $group/$facet/$bucket)
└── esquemas.py      # modelos de salida (Pydantic)
```

`nucleo/seguridad.py` agrega:

```python
def requiere_admin(usuario: dict = Depends(get_usuario_actual)) -> dict:
    if usuario.get("rol") != "admin":
        raise Prohibido("Solo un administrador puede ver el dashboard.")
    return usuario
```

### 1.1 Parámetros comunes

Todos los endpoints aceptan `desde` y `hasta` (fecha `YYYY-MM-DD`, opcionales; por defecto los últimos 30 días; `hasta` incluye el día completo) e `incluir_demo` (bool, por defecto `true`). Zona horaria fija: `America/Mexico_City`.
Filtro base de cada colección: `{"deleted_at": None, "created_at": {"$gte": desde, "$lt": hasta_mas_un_dia}}` y, si `incluir_demo=false`, `{"demo": {"$ne": True}}`.

### 1.2 Endpoints

| Ruta | Colecciones | Devuelve |
|---|---|---|
| `GET /api/dashboard/kpis` | todas | `usuarios_totales`, `usuarios_nuevos`, `planes`, `porcentaje_con_recomendacion`, `recorridos`, `tiempo_promedio_recorrido_min`, `reportes_vigentes`, `lugares` |
| `GET /api/dashboard/series?agrupar=dia\|semana\|mes` | usuarios, planes, historial_rutas | `[{fecha, usuarios, planes, recorridos}]` + `planes_por_interes: [{fecha, comer, cafe, cultura, entretenimiento, aire_libre}]` |
| `GET /api/dashboard/planes` | planes | `por_interes`, `por_movilidad`, `por_contexto`, `presupuesto` (histograma), `tiempo_disponible` (histograma), `dia_hora` (mapa de calor), `interes_por_contexto` (radar) |
| `GET /api/dashboard/sistema-experto` | planes | `por_estado`, `reglas_top` (id, descripción, total), `puntuacion_por_tipo` (promedio, mín, máx), `sin_datos_suficientes`, `por_version` |
| `GET /api/dashboard/movilidad` | historial_rutas | `por_transporte` (total, promedio, mín, máx de `tiempo_estimado`), `rutas_top` |
| `GET /api/dashboard/reportes` | reportes | `por_tipo_estado`, `vigentes_vs_vencidos`, `puntos` (máx. 500: lat, lng, tipo, vigente) |
| `GET /api/dashboard/lugares` | lugares | `por_categoria`, `puntos` (id, nombre, lat, lng, categoría) |
| `GET /api/dashboard/laboratorio` | bitacora_laboratorio | `dfs_puntos` (limite_profundidad, nodos, rutas), `dfs_pares_top`, `distancias_puntos` (euclidiana, manhattan) |

Las descripciones de reglas se leen con `app.ia.motor.cargar_base()` (solo lectura; no se modifica `app/ia/`).

### 1.3 Pipelines de referencia (`repositorio.py`)

Serie por día:

```python
[
    {"$match": filtro},
    {"$group": {
        "_id": {"$dateTrunc": {"date": "$created_at", "unit": unidad, "timezone": TZ}},
        "total": {"$sum": 1},
    }},
    {"$sort": {"_id": 1}},
]
```

Planes (una sola consulta con `$facet`):

```python
[
    {"$match": filtro},
    {"$facet": {
        "por_interes":   [{"$unwind": "$intereses"}, {"$group": {"_id": "$intereses", "total": {"$sum": 1}}}, {"$sort": {"total": -1}}],
        "por_movilidad": [{"$unwind": "$movilidad"}, {"$group": {"_id": "$movilidad", "total": {"$sum": 1}}}],
        "por_contexto":  [{"$group": {"_id": "$contexto", "total": {"$sum": 1}}}],
        "presupuesto":   [{"$bucket": {"groupBy": "$presupuesto.max", "boundaries": [0, 100, 200, 300, 500, 800, 1200],
                                       "default": "1200+", "output": {"total": {"$sum": 1}}}}],
        "tiempo_disponible": [{"$bucket": {"groupBy": "$tiempo_disponible", "boundaries": [0, 60, 120, 180, 240, 360, 480],
                                           "default": "8h+", "output": {"total": {"$sum": 1}}}}],
        "dia_hora": [{"$group": {
            "_id": {"dia": {"$isoDayOfWeek": {"date": "$fecha_plan", "timezone": TZ}},
                    "hora": {"$hour": {"date": "$fecha_plan", "timezone": TZ}}},
            "total": {"$sum": 1}}}],
        "interes_por_contexto": [{"$unwind": "$intereses"},
                                 {"$group": {"_id": {"contexto": "$contexto", "interes": "$intereses"}, "total": {"$sum": 1}}}],
    }},
]
```

Sistema experto:

```python
[
    {"$match": filtro},
    {"$unwind": "$evaluacion.candidatos"},
    {"$facet": {
        "por_estado": [{"$group": {"_id": "$evaluacion.candidatos.estado", "total": {"$sum": 1}}}],
        "reglas_top": [{"$unwind": "$evaluacion.candidatos.reglas"},
                       {"$group": {"_id": "$evaluacion.candidatos.reglas", "total": {"$sum": 1}}},
                       {"$sort": {"total": -1}}, {"$limit": 20}],
        "puntuacion_por_tipo": [{"$match": {"evaluacion.candidatos.puntuacion": {"$ne": None}}},
                                {"$group": {"_id": "$evaluacion.candidatos.tipo",
                                            "promedio": {"$avg": "$evaluacion.candidatos.puntuacion"},
                                            "minimo": {"$min": "$evaluacion.candidatos.puntuacion"},
                                            "maximo": {"$max": "$evaluacion.candidatos.puntuacion"}}}],
    }},
]
```

Movilidad: `$group` por `transporte.nombre` con `$sum`, `$avg`, `$min`, `$max` de `tiempo_estimado`.
Reportes: `$facet` con `$group` por `{tipo, estado}` y `$cond` sobre `vigente_hasta > ahora`.
El servicio **rellena con 0** los días/horas/categorías sin datos para que las gráficas no tengan huecos, y redondea a 1 decimal.

### 1.4 Datos demo: `scripts/sembrar_actividad_demo.py`

Con una base recién creada las gráficas salen vacías. Este script genera actividad sintética **marcada con `demo: true`**:

```
python -m scripts.sembrar_actividad_demo --dias 60 --usuarios 40 --planes 300   # genera
python -m scripts.sembrar_actividad_demo --borrar                               # borra todo lo que tenga demo: true
```

- Usuarios demo con correos `demo+N@kompas.mx`, planes con intereses/movilidad/contexto/presupuesto variados, `evaluacion` con ids de reglas **existentes** en `reglas.json`, recorridos sobre rutas existentes, reportes dentro de la zona piloto y registros de `bitacora_laboratorio`.
- Para que `evaluacion` sea realista, los planes demo se evalúan llamando a `app.ia.servicio.recomendar()` con lugares de ejemplo de `backend/ejemplos/` cuando sea posible; si no, se eligen reglas del catálogo real.
- Semilla fija (`random.seed(28)`) para que la demo sea reproducible.
- En el dashboard, si hay datos demo en el rango, se muestra la etiqueta **"Incluye datos de demostración"** y el interruptor *Incluir datos demo*.

## 2. Frontend: módulo `dashboard`

Librería de gráficas: **Recharts** (`npm i recharts@^3`). El mapa usa `react-leaflet`, que ya está instalado. El mapa de calor se hace con CSS grid (Recharts no lo trae).

```
src/modulos/dashboard/
├── index.js
├── api.js                     # una función por endpoint; usa compartido/api/cliente.js; modo mock igual que el resto
├── mock.js                    # datos de ejemplo con la MISMA forma que la API (para VITE_USE_MOCK=true)
├── hooks/useDashboard.js      # carga en paralelo, estado de carga/error, filtros
├── paginas/Dashboard.jsx      # pestañas + filtros
├── componentes/
│   ├── FiltrosDashboard.jsx   # rango (7 / 30 / 90 días / todo / personalizado), agrupar, incluir demo, Actualizar
│   ├── TarjetaGrafica.jsx     # marco común: título, descripción, estado vacío, "Ver como tabla", "Descargar CSV"
│   ├── TarjetaKpi.jsx
│   └── MapaCalor.jsx
└── graficas/                  # un componente por gráfica (lista en §2.2)
```

- Ruta `/dashboard` dentro del `Layout`, protegida con `RutaAdmin` (`app/RutaAdmin.jsx`): si `usuario.rol !== 'admin'`, redirige a `/`.
- En el menú lateral aparece **Dashboard** solo para admin.
- En pantallas anchas se usa todo el ancho; en celular, una columna.

### 2.1 Pestañas

1. **Resumen** · 2. **Planes** · 3. **Sistema experto** · 4. **Movilidad** · 5. **Reportes y lugares** · 6. **Laboratorio IA**

### 2.2 Gráficas

| # | Pestaña | Gráfica | Tipo (Recharts) | Fuente |
|---|---|---|---|---|
| 1 | Resumen | 6 tarjetas KPI | `TarjetaKpi` | `/kpis` |
| 2 | Resumen | % de planes con recomendación | Medidor `RadialBarChart` | `/kpis` |
| 3 | Resumen | Actividad en el tiempo (usuarios nuevos, planes, recorridos) | `LineChart` multiserie | `/series` |
| 4 | Resumen | Planes por interés en el tiempo | `AreaChart` apilada | `/series` |
| 5 | Planes | Planes por interés | `BarChart` vertical | `/planes` |
| 6 | Planes | Con quién salen (contexto) | `PieChart` dona | `/planes` |
| 7 | Planes | Movilidad elegida | `BarChart` horizontal (colores por transporte) | `/planes` |
| 8 | Planes | Presupuesto máximo por persona | Histograma (`BarChart` sin espacio entre barras) | `/planes` |
| 9 | Planes | Tiempo disponible | Histograma | `/planes` |
| 10 | Planes | Día de la semana × hora de salida | `MapaCalor` (CSS grid) | `/planes` |
| 11 | Planes | Perfil de intereses por contexto | `RadarChart` (una serie por contexto) | `/planes` |
| 12 | Sistema experto | Resultado de la evaluación (recomendable vs. otros estados) | `PieChart` | `/sistema-experto` |
| 13 | Sistema experto | Reglas más activadas (R01–R20) con descripción en el tooltip | `BarChart` horizontal | `/sistema-experto` |
| 14 | Sistema experto | Puntuación por tipo de plan (promedio con mín–máx) | `ComposedChart` (barra + `ErrorBar`) | `/sistema-experto` |
| 15 | Movilidad | Recorridos por transporte + tiempo promedio | `ComposedChart` (barras + línea, doble eje) | `/movilidad` |
| 16 | Movilidad | Rutas más usadas | `BarChart` | `/movilidad` |
| 17 | Reportes y lugares | Reportes por tipo y estado | `BarChart` apilada | `/reportes` |
| 18 | Reportes y lugares | Lugares por categoría | `Treemap` | `/lugares` |
| 19 | Reportes y lugares | Mapa: lugares y reportes (capas activables, color por tipo) | `react-leaflet` | `/lugares`, `/reportes` |
| 20 | Laboratorio IA | DFS: nodos explorados vs. límite de profundidad (tamaño = rutas encontradas) | `ScatterChart` burbujas | `/laboratorio` |
| 21 | Laboratorio IA | Euclidiana vs. Manhattan, con línea y = x | `ScatterChart` + `ReferenceLine` | `/laboratorio` |
| 22 | Laboratorio IA | Pares origen → destino más consultados en DFS | `BarChart` horizontal | `/laboratorio` |

### 2.3 Estilo y accesibilidad

- Colores **solo** de `COLORIMETRIA.md`: azul Kompás para la serie principal, transporte con sus colores (§3 de ese archivo: pie verde, autobús azul, taxi dorado, combinado frambuesa), estados (recomendable verde, advertencia dorado, descartado rojo). Funciona en modo claro y oscuro con los tokens que ya existen en `index.css`.
- Cada gráfica: título, una línea que explica qué se ve, tooltip en español, números con `Intl.NumberFormat('es-MX')`, estado vacío ("Sin datos en este periodo") y botón **Ver como tabla** (la tabla es la alternativa accesible).
- **Descargar CSV** por gráfica (se genera en el navegador con los mismos datos).
- Carga con esqueletos; si la API falla, aviso con el mensaje de `ErrorApi` y botón Reintentar.
- El color nunca es el único medio para distinguir series: también leyenda y etiquetas.

### 2.4 Modo mock

Con `VITE_USE_MOCK=true` el dashboard usa `mock.js` (datos generados con semilla fija, misma forma que la API) y se ve la franja "Modo demostración" que ya existe. En modo mock el usuario de ejemplo debe tener `rol: 'admin'` para poder entrar.

## 3. Pruebas

- `backend/tests/test_dashboard.py`: 401 sin token; 403 con usuario normal; 200 con el demo (admin); cada endpoint regresa las llaves documentadas; con `incluir_demo=false` no cuenta documentos `demo: true`; los días sin datos aparecen con 0.
- Frontend: `npm run lint` y `npm run build` verdes; revisar el dashboard en modo mock y con la API real en 1366 px y 390 px de ancho, claro y oscuro.

## 4. Para los manuales

**Manual técnico** (`DOCS/manual-tecnico/dashboard.md`):
1. Diagrama de secuencia: navegador → `/api/dashboard/planes` → `requiere_admin` → servicio → pipeline `$facet` → respuesta → Recharts.
2. Tabla de endpoints (§1.2) y los pipelines de §1.3 explicados etapa por etapa (`$match`, `$unwind`, `$group`, `$bucket`, `$facet`, `$dateTrunc`).
3. Control de acceso por rol y cómo crear un admin (`scripts/crear_admin.py`).
4. Cómo generar y borrar datos demo.

**Manual de usuario** (para Kevin): una captura por pestaña y, por cada gráfica, qué pregunta responde (ej. "¿Qué reglas del sistema experto se usan más?"), cómo usar los filtros, Ver como tabla y Descargar CSV.

## 5. Criterios de aceptación

- [ ] Las 22 gráficas se ven con datos (demo o reales) y sin errores en consola.
- [ ] Un usuario sin rol admin no ve el menú ni puede abrir `/dashboard` ni los endpoints (403).
- [ ] Los filtros de fecha y "Incluir datos demo" cambian los números.
- [ ] Ninguna gráfica calcula estadísticas en el navegador: todo viene agregado de la API.
- [ ] `pytest` verde; `npm run lint` y `npm run build` verdes.
