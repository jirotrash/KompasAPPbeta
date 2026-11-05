# Reglas del proyecto Kompás

## Arquitectura
- Backend: arquitectura en capas por módulos (ver ARQUITECTURA.md). Router → Servicio → Repositorio → MongoDB.
- Los routers no acceden a la base. Los repositorios no lanzan HTTPException ni devuelven documentos crudos con ObjectId.
- Un módulo no importa el repositorio de otro módulo: usa su servicio.

## Zonas protegidas
- `backend/app/ia/` (sistema experto, DFS y métricas): no se cambia su lógica sin acuerdo con Einar.
- El contrato de la API (rutas y campos) no cambia sin avisar al equipo de la app móvil.

## Frontend
- App móvil en `app/` (Expo): seguir `app/AGENTS.md`.
- Web en `frontend/`: módulos en `src/modulos/`, código común en `src/compartido/`.
- Colores y contraste: respetar estrictamente `COLORIMETRIA.md` en ambos clientes.

## Git
- Ramas `feature/*`, `refactor/*`, `docs/*` y Pull Request a `main`.
- Commits en español e imperativo, sin líneas Co-Authored-By ni Claude-Session.
- Nunca subir `.env`, `venv/`, `node_modules/` ni llaves.

## Módulo de Prácticas de IA y Modelo Predictivo (`ia_kompas`)

### Contexto Académico y de Negocio

El proyecto integra las prácticas de Inteligencia Artificial y Ciencia de Datos (`p01BFS`, `p01reglafija`, `p02` a-e, y `p03primermodelo`) aplicadas directamente al dominio de **KompasAPPbeta** (planificación de itinerarios turísticos y cálculo de transporte urbano).

### Reglas de Implementación para Agentes

1. **Prohibido el código genérico desconectado:** Ningún script de las prácticas debe quedar con nombres de variables genéricos (`nodo_a`, `feature_1`, `iris`, `titanic`). Todas las entidades deben pertenecer al dominio de Kompas (`parada_origen`, `distancia_km`, `presupuesto_mxn`, `clima_lluvia`, `rating_destino`, `modo_transporte_optimo`).

2. **Convención de idioma:** Mantener nombres de funciones, atributos de esquemas Pydantic, comentarios y documentación técnica en **español**, consistente con `modulos/itinerarios` y `modulos/rutas`.

3. **Trazabilidad de las prácticas:**

   * `p01_grafo_bfs.py` $\rightarrow$ Búsqueda en anchura para minimizar escalas/transbordos entre paradas de un plan.

   * `p01_regla_fija.py` $\rightarrow$ Heurística determinista base (*baseline*) para recomendación de transporte.

   * `p02_pipeline_datos.py` $\rightarrow$ Funciones explícitas para las etapas `a` (análisis), `b` (exploración), `c` (calidad de datos), `d` (limpieza y guardado CSV) y `e` (selección de variables $X$ y $y$).

   * `p03_modelo_predictivo.py` $\rightarrow$ Entrenamiento con `scikit-learn`, evaluación comparativa contra `p01_regla_fija` e inferencia en tiempo real para los endpoints de rutas e itinerarios.

4. **No regresión:** Cualquier cambio en `rutas` o `itinerarios` debe mantener en verde las suites de pruebas `backend/tests/test_planes_guardados.py`, `backend/tests/test_transporte.py` y `app/tests/transporte.test.cjs`.

