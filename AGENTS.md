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
