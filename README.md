# Kompás

App móvil para planear salidas y traslados en Toluca, Lerma y San Mateo Atenco, con un sistema experto que recomienda y explica cada plan
y un asistente con LLM local (Ollama). Por dentro usa A\*, un árbol binario de paradas y un algoritmo genético.
Incluye una web (TypeScript) con dashboard de estadísticas para administradores.

| Carpeta | Qué es | Cómo se corre |
|---|---|---|
| [`backend/`](backend/) | API FastAPI + MongoDB (capas por módulos) | [`backend/README.md`](backend/README.md) |
| [`app/`](app/) | App móvil React Native + Expo | `app/README.md` |
| [`frontend/`](frontend/) | Panel web de administración en TypeScript (solo dashboard, rol admin) | `cd frontend && npm install && npm run dev` |

**Empieza por [`CONTEXTO.md`](CONTEXTO.md).**

| Documento | Para quién |
|---|---|
| [`CONTEXTO.md`](CONTEXTO.md) | Todo el equipo |
| [`BACKEND.md`](BACKEND.md) | API (Jesús) |
| [`IA.md`](IA.md) | Sistema experto (Einar) |
| [`INTEGRAR_IA.md`](INTEGRAR_IA.md) | Integración del sistema experto con la API (Einar y API) |
| [`ARQUITECTURA.md`](ARQUITECTURA.md) | Arquitectura en capas por módulos (backend y web) |
| [`MIGRACION_MONGODB.md`](MIGRACION_MONGODB.md) | Cambio de MySQL a MongoDB (Sebas) |
| [`DASHBOARD.md`](DASHBOARD.md) | Dashboard de estadísticas |
| [`PLAN_V06.md`](PLAN_V06.md) | Plan v0.6: TypeScript, búsqueda heurística, genético, árbol de paradas y asistente |
| [`DOCS/manual-tecnico/`](DOCS/manual-tecnico/) | Manual técnico: diagramas, diccionario de datos, dashboard, algoritmos de IA y asistente |
| [`COLORIMETRIA.md`](COLORIMETRIA.md) | Diseño e interfaz móvil (equipo frontend) |
| [`AGENTS.md`](AGENTS.md) | Desarrollo asistido y reglas de trabajo del proyecto |
| [`modificaciones solicitadas hector 14-10-2026.md`](modificaciones%20solicitadas%20hector%2014-10-2026.md) | Profesor Héctor y equipo: entrega, integración y uso de la demostración DFS |
