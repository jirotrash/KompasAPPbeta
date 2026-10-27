# Kompás v0.5 — Resumen de cambios

> Rama `feature/v0.5-mongodb-dashboard` (17 commits sobre `main`, 211 archivos). Plan original:
> `PLAN_REFACTOR.md`, `ARQUITECTURA.md`, `MIGRACION_MONGODB.md` y `DASHBOARD.md`.

## 1. En una frase

La API pasó de MySQL a **MongoDB** y se reorganizó en **capas por módulos** (router → servicio → repositorio), la web
quedó como **panel de administración** con un **dashboard de 22 gráficas**, y todo quedó documentado en
`DOCS/manual-tecnico/`. El contrato de la API no cambió.

## 2. Qué cambia para cada quien

| Quién | Qué cambia |
|---|---|
| App móvil | Nada. Mismas rutas, campos, códigos y mensajes. Solo se cambió un comentario "(MySQL)" → "(MongoDB)" en `app/src/services/api.ts`. `rol` ahora viene de la base |
| Administrador | Nuevo panel web (`frontend/`): login y dashboard. Solo entran cuentas con `rol: "admin"` |
| Sebas (base de datos) | La base es MongoDB `kompas`: colecciones, validadores e índices en `backend/scripts/preparar_bd.py`. Regla 5 de `CONTEXTO.md`: no se cambia el esquema sin acuerdo con Sebas |
| Einar (IA) | `backend/app/ia/` no cambió de lógica: solo 2 líneas `import` (geo y traslados se movieron a `app/compartido/`) |
| Todo el equipo | Cada quien debe poner `MONGO_URI` y `MONGO_DB` en su `backend/.env` (ver `.env.example`) |

## 3. Backend: arquitectura en capas por módulos

```
backend/app/
├── main.py           crea la app, CORS, manejadores de error, registra routers
├── nucleo/           config · bd (MongoDB) · seguridad (bcrypt, JWT, requiere_admin) · errores · parametros · esquemas_comunes
├── compartido/       geo · traslados · texto
├── externos/         google_places (patrón Adaptador)
├── modulos/          cuenta · catalogos · lugares · rutas · historial · itinerarios · laboratorio · reportes · dashboard
│   └── <módulo>/     router.py · esquemas.py · servicio.py · repositorio.py
└── ia/               sin cambios de lógica
```

- Los archivos se movieron con `git mv` para conservar el historial.
- **Errores de negocio** (`nucleo/errores.py`): `NoEncontrado` 404, `Conflicto` 409, `NoAutorizado` 401, `Prohibido` 403,
  `DatosInvalidos` 422, `ServicioExterno` 503 y `ErrorDeDatos` 500. Los servicios no conocen HTTP; `main.py` los traduce
  con los mismos mensajes de antes.
- Un módulo usa el **servicio** de otro, nunca su repositorio. Por ejemplo, historial valida la ruta con `ServicioRutas`.
- **Borrados**: `modelos.py`, `db.py`, `servicios/consultas.py` y las carpetas vacías `routers/`, `esquemas/` y `servicios/`.
- **Criterios cumplidos**: no hay `HTTPException` en servicios ni repositorios, no queda `sqlalchemy` ni `pymysql` en la app
  ni en las pruebas, y los routers solo usan `Depends(get_bd)`.

## 4. Base de datos: MySQL → MongoDB

| Colección | Notas |
|---|---|
| `usuarios` | `residencia` **embebida**; `rol` (`usuario` o `admin`); `correo` único |
| `categorias`, `transportes` | `nombre` único |
| `lugares` | `ubicacion` GeoJSON `Point` (2dsphere); `categoria: {id, nombre}` (referencia extendida) |
| `rutas` | `trazo` GeoJSON `LineString` (2dsphere) |
| `historial_rutas` | `transporte: {id, nombre}` embebido |
| `planes` | Ahora guarda **todo** lo que eligió el usuario: `contexto`, `presupuesto`, `intereses[]`, `movilidad[]` y la `evaluacion` del sistema experto (tal como la regresó el motor, sin recalcular). No se guarda el origen exacto (privacidad) |
| `reportes` | **Nuevo.** Sin índice TTL: los vencidos se conservan para estadísticas |
| `bitacora_laboratorio` | **Nuevo.** Una entrada por consulta a DFS o a distancias (campo `tipo`) |
| `contadores` | Ids enteros consecutivos (la app espera `id: number`) |

- Validadores `$jsonSchema` en `usuarios`, `lugares`, `planes` y `reportes` (`validationLevel: "moderate"`).
- Las fechas se guardan con zona horaria y la API las regresa igual que MySQL: hora de Toluca, sin zona horaria y sin
  fracción de segundo.
- `requirements.txt`: se quitaron `sqlalchemy`, `pymysql` y `cryptography`, y se agregó `pymongo>=4.8`. Las librerías de
  MySQL quedaron en `requirements-migracion.txt`.
- Los archivos de MySQL quedaron como evidencia en `backend/database/mysql_legacy/`. Se borró el `Dump20260927.sql`
  de la raíz porque era idéntico.

## 5. API: endpoints nuevos (nada existente cambió)

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/reportes` 🔒 | Crea un reporte. La API calcula `vigente_hasta`: cierre total 6 h, accidente 2 h, manifestación 3 h, afluencia 1 h. Valida la zona piloto (422) |
| `GET` | `/api/reportes?ruta_id=` | Reportes vigentes |
| `GET` | `/api/dashboard/kpis` · `series` · `planes` · `sistema-experto` · `movilidad` · `reportes` · `lugares` · `laboratorio` 🔒 admin | Estadísticas con agregaciones de MongoDB (`$facet`, `$bucket`, `$dateTrunc`, `$unwind`…). Filtros `desde`, `hasta` e `incluir_demo`. Sin token 401, usuario normal 403 |

## 6. Scripts (`python -m scripts.<nombre>`, desde `backend/`)

| Script | Qué hace |
|---|---|
| `preparar_bd [--recrear] [--sin-datos]` | Reescrito: crea colecciones, validadores e índices, carga `database/datos_desarrollo.json` si la base está vacía e imprime la tabla de colecciones |
| `generar_datos_desarrollo` | Ahora genera el JSON con los mismos registros de antes. El demo `demo@kompas.mx` / `demo1234` tiene rol admin |
| `migrar_mysql_a_mongo [--limpiar]` | **Nuevo.** Copia MySQL → MongoDB una vez, conservando los ids, e imprime la tabla comparativa. Se probó con el MySQL local: 4 usuarios, 5 categorías, 4 transportes y 10 lugares |
| `crear_admin correo [--quitar]` | **Nuevo.** Da o quita el rol admin |
| `sembrar_actividad_demo [--borrar]` | **Nuevo.** Actividad sintética con `demo: true` y semilla fija. La evaluación de los planes demo sale del **motor real** |

## 7. Web (`frontend/`): solo panel de administración

- **Estructura**: `src/app/` (App, Layout, RutaPrivada, RutaAdmin), `src/compartido/` (cliente de API, componentes,
  hooks, utils), `src/mock/` y `src/modulos/` (cuenta, dashboard y los antiguos inicio, rutas, itinerarios y reportes).
  `services/api.js` se dividió en un `api.js` por módulo, con el mismo nombre, firma y JSDoc.
- **Solo dashboard**: la web tiene el login y el dashboard en `/`. Cualquier otra dirección lleva al panel. Se quitó el
  registro. El login rechaza las cuentas que no son admin, y una sesión guardada de otro rol ve "Sin acceso al panel".
- **Marca Kompás**: se cambió "Brújula Urbana" por **Kompás** en el título, el menú, el login y la app instalable. El
  **logo oficial** (`logo kompas.png`, reducido a 256 px) se usa en la barra lateral, el encabezado y el login, siempre
  sobre fondo claro (COLORIMETRIA §5). Con él se regeneraron el favicon y los íconos de la app instalable.
- **Diseño**:
  - Las 6 secciones del dashboard van en la barra lateral; en celular van como pestañas. Cada sección tiene su
    dirección (`/?seccion=planes`).
  - El encabezado muestra el nombre de la sección y una etiqueta "Incluye datos de demostración".
  - Los KPI llevan íconos, y las gráficas tienen botones de ícono para "ver como tabla" y "descargar CSV".
  - La tarjeta del usuario está al pie de la barra lateral.
- **Colores**: solo los de `COLORIMETRIA.md`. Se corrigieron la barra del navegador (era verde azulado) y el texto de la
  franja de modo demostración (dorado sobre crema → texto oscuro).

### Dashboard: 6 secciones, 22 gráficas (Recharts)

| Sección | Gráficas |
|---|---|
| Resumen | 6 KPI · % de planes con recomendación (medidor) · actividad en el tiempo · intereses en el tiempo (áreas apiladas) |
| Planes | por interés · contexto (dona) · movilidad · presupuesto y tiempo disponible (histogramas) · día × hora (mapa de calor) · perfil por contexto (radar) |
| Sistema experto | estados de la evaluación · reglas más activadas (descripción en el tooltip) · puntuación por tipo (promedio con mín–máx) |
| Movilidad | recorridos por transporte + tiempo promedio (doble eje, como pide `DASHBOARD.md`) · rutas más usadas |
| Reportes y lugares | reportes por tipo y estado · lugares por categoría (treemap) · mapa con capas de lugares y reportes |
| Laboratorio IA | DFS: nodos vs. límite (burbujas) · Euclidiana vs. Manhattan con línea y = x · pares DFS más consultados |

- Cada gráfica tiene tooltip en español, números con `es-MX`, estado vacío, **ver como tabla** y **descargar CSV**.
- Ninguna estadística se calcula en el navegador.
- Funciona en claro y oscuro, a 1366 px y a 390 px.
- La paleta categórica se validó en modo claro. En oscuro los tokens obligatorios de COLORIMETRIA se parecen entre sí
  para daltónicos, así que el color nunca es el único medio: siempre hay leyenda, etiquetas y tabla.

## 8. App móvil (`app/`)

No se reorganizó: Expo Router obliga a tener las pantallas en `src/app/`. Solo cambió un comentario. Sigue usando sus
reportes de ejemplo aunque `/api/reportes` ya existe.

## 9. Pruebas

| | Antes (MySQL) | Ahora (MongoDB 8) |
|---|---|---|
| `pytest` | 38 aprobadas | **59 aprobadas**: las 38 de antes, sin cambiar asserts, más 21 nuevas (`test_reportes.py`, `test_bitacora.py`, `test_dashboard.py`) |
| `npm run lint` / `npm run build` | — | En verde |

- Las pruebas usan la base `kompas_test`, que se recrea en cada corrida. Si MongoDB no responde, se omiten.
- También se revisó en el navegador: login, rechazo de usuarios que no son admin, las 6 secciones con datos en mock y con
  la API real, en escritorio y celular, sin errores de consola.

## 10. Cómo correrlo

```powershell
# MongoDB: el de WSL, Docker (docker run -d -p 27017:27017 mongo:8.0) o Atlas → MONGO_URI en backend/.env
cd backend; .\venv\Scripts\activate; pip install -r requirements.txt
python -m scripts.preparar_bd
python -m scripts.sembrar_actividad_demo          # opcional; se borra con --borrar
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pytest

cd ..\frontend; npm install; npm run dev          # VITE_USE_MOCK=false para usar la API real
# Entrar con demo@kompas.mx / demo1234, o dar rol admin: python -m scripts.crear_admin tu@correo
```

## 11. Pendientes

- [ ] **Abrir el Pull Request** de `feature/v0.5-mongodb-dashboard` a `main`. `gh` no está instalado en la PC; la
      descripción quedó lista aparte.
- [ ] `GOOGLE_MAPS_API_KEY` en `backend/.env`: sin ella, `POST /api/itinerarios` responde 503 (ya pasaba antes).
- [ ] Que la app móvil use `/api/reportes` en lugar de sus datos de ejemplo (requiere cambiar `app/`).
- [ ] Decidir si se borra de la web el código de inicio, rutas, itinerarios y reportes, que ya no se muestra.
- [ ] Limpieza local:
  - Contenedor Docker `kompas-mongo`, que no se usó: el MongoDB que respondía era el de WSL.
  - Bases de prueba `kompas_demo_prueba` y `kompas_migracion_prueba`.
  - `package-lock.json` suelto en la raíz.
- [ ] Con los lugares genéricos, el motor marca la mayoría de los planes demo como "pendiente de verificar" (~10 %
      recomendables). Es la decisión real del motor; no se ajustó a mano.

## 12. Documentación nueva o actualizada

| Archivo | Qué tiene |
|---|---|
| `DOCS/manual-tecnico/arquitectura.md` | Estilo arquitectónico, capas, patrones de diseño y 8 diagramas Mermaid: contexto, contenedores, capas, módulos, secuencia de itinerarios, login JWT, despliegue y carpetas |
| `DOCS/manual-tecnico/modelo-datos-mongodb.md` | Por qué MongoDB, embeber vs. referenciar, diagramas MySQL y MongoDB, diccionario de datos, índices, validadores, migración con su tabla comparativa y capturas sugeridas |
| `DOCS/manual-tecnico/dashboard.md` | Secuencia de una consulta, endpoints, pipelines explicados etapa por etapa, control por rol y datos demo |
| `AGENTS.md`, `CLAUDE.md` | Reglas nuevas del proyecto (arquitectura, zonas protegidas, git) |
| `CONTEXTO.md`, `README.md`, `backend/README.md` | Stack, arquitectura, instalación de MongoDB, scripts y endpoints nuevos |
