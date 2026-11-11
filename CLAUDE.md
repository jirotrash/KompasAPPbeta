@AGENTS.md
@CONTEXTO.md

## Referencia Rápida — Laboratorio de IA (`ia_kompas`)
- **Backend (`backend/app/modulos/ia_kompas/`):** Módulos `datos_kompas.py`, `datos_y_limpieza.py` (500 recorridos/planes limpios, Práctica 02), `bfs_y_reglas.py` (BFS + Reglas Fijas, Práctica 01), `entrenamiento_particiones.py` y `modelo_entrenamiento.py` (optimización de particiones `80/20` y `60/20/20` frente al `70/30` clásico y control de *Underfitting* vs. *Overfitting*, Práctica 03). Endpoints: `GET /api/ia/metricas`, `POST /api/ia/simular` y `GET /api/ia/evaluacion-modelo`.
- **Frontend (`app/src/app/laboratorio-ia.tsx`):** Vista interactiva del Laboratorio de IA conectada mediante `obtenerMetricasIA()` y `simularPrediccionIA()` en `app/src/services/api.ts` (con respaldo offline en `app/src/services/mock/laboratorioIa.ts`) y accesible desde `app/src/app/(tabs)/perfil.tsx`.
- **Documentación técnica:** `DOCS/manual-tecnico/laboratorio-ia-particiones.md`, `DOCS/manual-tecnico/laboratorio-ia.md` y `DOCS/manual-tecnico/modelo-ia-particiones.md`.

