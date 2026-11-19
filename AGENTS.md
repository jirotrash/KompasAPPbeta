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

   * `p01_grafo_bfs.py` y `bfs_y_reglas.py` $\rightarrow$ Búsqueda en anchura (BFS) para minimizar escalas/transbordos entre paradas de un plan y sistema heurístico base (`predecir_con_reglas`).

   * `p01_regla_fija.py` $\rightarrow$ Heurística determinista base (*baseline*) para recomendación de transporte.

   * `p02_pipeline_datos.py`, `datos_kompas.py` y `datos_y_limpieza.py` $\rightarrow$ Generación de 500 recorridos/planes turísticos del dominio de Kompás y etapas `a` (análisis), `b` (exploración), `c` (calidad de datos), `d` (limpieza e imputación por mediana) y `e` (selección de variables $X$ y $y$).

   * `p03_modelo_predictivo.py`, `entrenamiento_particiones.py` y `modelo_entrenamiento.py` $\rightarrow$ Entrenamiento con `DecisionTreeClassifier`, optimización experimental de particiones más allá del 70/30 tradicional (`80/20` y `60/20/20` con 5-Fold CV), control de *Underfitting* vs. *Overfitting* (`max_depth` 1 a 15), evaluación comparativa contra `p01_regla_fija` e inferencia en tiempo real (`/api/ia/metricas`, `/api/ia/simular`, `/api/ia/evaluacion-modelo`).

   * `app/src/app/laboratorio-ia.tsx` $\rightarrow$ Vista móvil/web del Laboratorio de IA con tarjetas comparativas, barras de particiones, monitor de subajuste/sobreajuste, matriz de confusión y simulador interactivo en vivo.

4. **No regresión:** Cualquier cambio en `rutas` o `itinerarios` debe mantener en verde las suites de pruebas `backend/tests/test_planes_guardados.py`, `backend/tests/test_transporte.py`, `backend/tests/test_ia_kompas.py` y `app/tests/transporte.test.cjs`.

