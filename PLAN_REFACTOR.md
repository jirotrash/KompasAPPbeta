# Kompás — Plan v0.5: arquitectura modular + MongoDB + dashboard

> **Para Claude Code en VS Code.** Prompt sugerido:
> *"Lee PLAN_REFACTOR.md, ARQUITECTURA.md, MIGRACION_MONGODB.md y DASHBOARD.md e impleméntalo todo, de principio a fin, sin detenerte entre pasos. Al final dame el resumen de la §5."*

| Documento | Qué tiene |
|---|---|
| `PLAN_REFACTOR.md` | Este archivo: orden de trabajo, reglas y checklist |
| `ARQUITECTURA.md` | Arquitectura en capas por módulos (backend y frontend web), patrones y diagramas |
| `MIGRACION_MONGODB.md` | Cambio de MySQL a MongoDB: colecciones, índices, scripts y pruebas |
| `DASHBOARD.md` | Dashboard de estadísticas: endpoints con agregaciones y página con gráficas |

## 1. Objetivo

Todo en un solo trabajo:

1. **Reorganizar** el backend y el frontend web en una **arquitectura en capas por módulos**.
2. **Cambiar la base de datos de MySQL a MongoDB**: los repositorios se escriben directamente con PyMongo.
3. **Agregar un dashboard** en `frontend/` con gráficas de todo tipo alimentadas por agregaciones de MongoDB.
4. **Documentar todo para el manual técnico** (lo pidió el profesor Héctor): arquitectura, patrones, modelo de datos y dashboard.

## 2. Reglas para el asistente (obligatorias)

1. **`AGENTS.md` actual queda reemplazado** por decisión del líder del proyecto (Jesús, responsable de la API) con el contenido de la §4. La restricción de no tocar `backend/` ya no aplica.
2. **No cambiar la lógica de `backend/app/ia/`** (sistema experto de Einar, DFS y métricas de distancia): ni `reglas.json`, ni `evaluar()`, ni `hechos.py`, ni el algoritmo DFS. Solo se permite cambiar **líneas `import`** cuando un módulo del que dependen cambie de carpeta.
3. **El contrato de la API no cambia**: mismas rutas, mismos campos, mismos códigos HTTP y mismos mensajes. La app móvil (`app/`) no se modifica salvo comentarios que digan "MySQL". Excepciones permitidas: los endpoints nuevos (`/api/reportes`, `/api/dashboard/*`) y que `rol` venga de la base.
4. **No inventar datos** (CONTEXTO.md §2). Los datos sintéticos para probar el dashboard llevan `demo: true` y se pueden borrar con un comando.
5. **Secretos solo en `.env`**. Se actualiza `.env.example`, nunca se sube `.env`.
6. Trabajar en una sola rama: `feature/v0.5-mongodb-dashboard`, e integrar a `main` con un Pull Request al final.
7. Hacer commits pequeños conforme avanzas (uno por bloque de trabajo). **Commits en español e imperativo** (`Agrega repositorio de lugares`), **sin las líneas `Co-Authored-By: Claude` ni `Claude-Session:`** y sin mencionar a Claude en commits ni PR.
8. Mover archivos con `git mv` para conservar el historial.
9. No detenerse a pedir confirmación entre pasos. Solo parar si algo contradice estas reglas o falta un dato que no se puede deducir del repo (por ejemplo, la cadena de conexión de Atlas).

## 3. Orden de trabajo

Es el orden recomendado para que nada se rompa a medio camino; se hace todo seguido.

1. `git checkout main && git pull`, crear la rama, correr `pytest` en `backend/` y guardar el resultado para comparar al final.
2. Reemplazar `AGENTS.md` (§4) y crear `CLAUDE.md` en la raíz con dos líneas: `@AGENTS.md` y `@CONTEXTO.md`.
3. **Backend:** nueva estructura (ARQUITECTURA.md §3–§5) con repositorios en MongoDB (MIGRACION_MONGODB.md completo), incluidos el módulo `reportes`, la bitácora del laboratorio y los scripts.
4. **Frontend web:** nueva estructura (ARQUITECTURA.md §6).
5. **Dashboard:** backend y frontend (DASHBOARD.md completo) y el script de datos demo.
6. **Documentación:** crear `DOCS/manual-tecnico/` con `arquitectura.md` (ARQUITECTURA.md §8–§9), `modelo-datos-mongodb.md` (MIGRACION_MONGODB.md §10) y `dashboard.md` (DASHBOARD.md §4); diagramas en Mermaid. Actualizar `CONTEXTO.md` (§4 Stack, §5 Arquitectura y §2 regla 5: "No se cambia el esquema de MongoDB sin acuerdo con Sebas"), `README.md` y `backend/README.md`.
7. Verificar todo con la §5, abrir el Pull Request y dar el resumen final: archivos movidos, creados y borrados, comandos para correr el proyecto y cualquier pendiente.

## 4. Nuevo contenido de `AGENTS.md`

```markdown
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
```

## 5. Checklist final

- [ ] `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` arranca y `/api/salud` regresa `{"ok": true, "bd": true}` con MongoDB.
- [ ] `/docs` muestra los tags de todos los módulos, incluidos Reportes y Dashboard.
- [ ] La app móvil con `EXPO_PUBLIC_USE_MOCK=false` hace login, lista lugares, crea un plan y guarda un recorrido.
- [ ] El frontend web abre `/dashboard` con un usuario `admin` y todas las gráficas tienen datos.
- [ ] `pytest` verde con MongoDB: pasan todas las que pasaban al inicio, más las nuevas.
- [ ] `npm run lint` y `npm run build` verdes en `frontend/`.
- [ ] `DOCS/manual-tecnico/` tiene los diagramas y el diccionario de datos.
