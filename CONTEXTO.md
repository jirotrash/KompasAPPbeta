# Kompás — Contexto del proyecto

> Léelo primero. Sirve para el equipo y para cualquier asistente de IA (Claude, Copilot) que trabaje en el repo.
> Si usas Claude Code, cópialo también como `CLAUDE.md`.

## 1. Qué es

**Kompás** (nombre académico en el documento autorizado: *Brújula Urbana*) es una **app móvil** que ayuda a planear salidas y traslados en **Toluca, Lerma y San Mateo Atenco**. El usuario indica con quién va, presupuesto, tiempo, intereses y cómo se mueve, y la app le propone **hasta 3 planes** con lugares reales y le **explica por qué** recomienda cada uno.

La **IA** es un **sistema experto con lógica proposicional** (20 reglas, encadenamiento hacia adelante).

Proyecto escolar: *Formulación de proyectos de tecnología* · UTVT · ITIID-D71 · Docente: Héctor Pérez Paulín.

## 2. Reglas que nunca se rompen
1. **No inventar** rutas, horarios, costos ni horas de llegada. Si falta un dato, se dice que falta.
2. Los tiempos son **estimaciones** y se marcan así.
3. Los datos de Google se muestran con su atribución y **no se guardan** en la base (solo `place_id`).
4. Llaves y contraseñas **nunca** en el repo: van en `.env` (se sube solo `.env.example`).
5. No se cambia el esquema de MySQL sin acuerdo con Sebas.

## 3. Equipo

| Integrante | Rol |
|---|---|
| **Jesús Iván Romero Ortega** (líder) | App móvil y API (FastAPI) |
| **Sebastián Yael Martínez Martínez** | Base de datos MySQL y repositorio |
| **Einar Iván Lazcano Luna** | Sistema experto (20 reglas) y manual técnico |
| **Valentín Carlos Esquila** | Identidad (nombre, logo, colores) y mockups en Figma |
| **Kevin Eduardo De La Cruz González** | Manual de usuario y pruebas |

## 4. Stack

| Capa | Tecnología |
|---|---|
| App móvil | **React Native + Expo SDK 57** (Expo Router), estilos con **Tamagui**, mapa **Leaflet** en WebView, **expo-location** |
| API | **FastAPI** (Python 3.11+), SQLAlchemy 2, PyMySQL, JWT, bcrypt |
| Base de datos | **MySQL 8**, esquema `kompas` (8 tablas, ver `database/`) |
| Lugares | **Google Places API (New)**, consultada solo desde la API |
| IA | Motor de reglas de Einar en Python (`backend/app/ia/`) |

## 5. Arquitectura

```
App (Expo) ──HTTP/JSON──► API FastAPI ──► MySQL kompas (usuarios, residencia, catálogos, planes, rutas, historial)
                              │
                              ├──► Google Places (lugares, horario, nivel de precio)
                              │
                              └──► Sistema experto (R01–R20) → planes recomendables + explicación
```

## 6. Documentos del repo

| Archivo | Qué tiene |
|---|---|
| `CONTEXTO.md` | Este archivo |
| `BACKEND.md` | Especificación completa de la API: endpoints, tablas, Google Places, fases de trabajo |
| `IA.md` | Cómo se conecta el sistema experto de Einar con la API |
| `database/Dump20260927.sql` | Esquema MySQL de Sebas |
| `app/README.md` | Cómo correr la app (cuando se suba el código de la app) |

## 7. Estado y próxima entrega

**Avance: miércoles 30 de septiembre de 2026** — app + manual de usuario + manual técnico.

Demo mínima:
1. Iniciar sesión (MySQL).
2. Ver lugares cercanos (Google Places).
3. Crear un plan → el sistema experto recomienda y explica.
4. Mostrar `/docs` de la API.

Pendientes:
- [ ] Llave de Google Maps con facturación activada (Jesús).
- [ ] `app/ia/motor.py` y `hechos.py` (Einar).
- [ ] Endpoints de la Fase 1 a la 5 de `BACKEND.md` (Jesús).
- [ ] Decidir el nombre oficial en los documentos: Kompás o Brújula Urbana.

## 8. Cómo trabajamos
- Ramas: `main` estable; cada quien en `feature/<tema>` o `docs/<tema>` y se integra por pull request.
- Commits en español e imperativo: `Agrega endpoint de login`.
- Antes de subir: nada de `.env`, `venv/`, `node_modules/` ni llaves.