# Brújula Urbana (nombre provisional) — Contexto del proyecto

> Archivo de contexto para el equipo y para asistentes de IA en VS Code (Copilot, Claude, etc.).
> Colócalo en la raíz del repositorio. Si usas Claude Code puedes copiarlo como `CLAUDE.md`.

## 1. Qué es

**Brújula Urbana** (nombre provisional; el definitivo lo propone Valentín) es una **aplicación móvil** de movilidad para la zona **Lerma–Toluca**, hecha con **React Native + Expo**. El usuario indica su ubicación u origen, un destino y una hora de salida, y la app:

- Propone alternativas de traslado: a pie, autobús, taxi o transporte por aplicación.
- En autobús indica **línea, sentido, punto de abordaje, descenso y transbordos**.
- Estima tiempos: caminata, espera, trayecto y transbordos.
- Genera **hasta 3 itinerarios** para una salida (cita, amigos, familia o traslado cotidiano) combinando lugares según tiempo, presupuesto y gustos.
- Muestra horarios, calificaciones y afluencia de lugares, siempre con **fuente y antigüedad del dato**.
- Recibe **reportes comunitarios**: afluencia baja/media/alta, accidentes, manifestaciones y cierres, con verificación y vigencia.

La **IA** es un **sistema experto basado en lógica proposicional**: relaciona los parámetros anteriores con reglas y explica por qué recomienda cada opción.

Proyecto escolar: *Formulación de proyectos de tecnología*, UTVT, grupo ITIID-D71. Docente: Héctor Pérez Paulín.

## 2. Reglas que el código NUNCA debe romper

Vienen de las delimitaciones del proyecto autorizado:

1. **No inventar rutas, horarios ni horas de llegada.** Si no hay datos verificados, la app lo dice ("No tenemos información suficiente para esta ruta").
2. Los tiempos son **estimaciones**. Distinguir horario programado de dato actualizado por un proveedor.
3. No prometer conteo de personas en vivo ni todas las reseñas de un lugar.
4. Tarifas de apps externas (Uber, DiDi…) solo si hay integración autorizada.
5. Los reportes comunitarios **no** son servicio de emergencias.
6. La app orienta decisiones; contratar, cobrar y prestar el transporte le corresponde al proveedor.

## 3. Alcance del prototipo

- Zona piloto dentro de Lerma y Toluca (límites por definir con Sebas).
- 20–30 lugares, 3 contextos de salida, 15–20 reglas.
- Solo rutas de transporte documentadas y probadas por el equipo.

## 4. Equipo y responsabilidades

| Integrante | Matrícula | Rol |
|---|---|---|
| **Jesús Iván Romero Ortega** | 222410828 | Líder · **API** y programación de la **app móvil** (React Native + Expo) |
| **Sebastián Yael Martínez Martínez** | 222410905 | Bases de datos: **MongoDB** (rutas) y **MySQL** (usuarios) · repositorio · levantamiento de datos de campo |
| **Einar Iván Lazcano Luna** | 222411190 | **IA / sistema experto** (variables, reglas, motor de inferencia) · **manual técnico** |
| **Valentín Carlos Esquila** | 222410922 | **Identidad de la app** (nombre, logotipo, colores, tipografía, íconos) · **mockups** y diseño de interfaz · capturas para manuales |
| **Kevin Eduardo De La Cruz González** | 222310594 | **Manual de usuario** · formato institucional de manuales · módulo de reportes comunitarios · pruebas |

## 5. Stack

| Capa | Tecnología | Estado |
|---|---|---|
| App móvil | **React Native + Expo** (Expo Router para las pantallas), estilos con **NativeWind** (Tailwind para React Native), mapa con **react-native-maps**, ubicación con **expo-location** | **Decidido** |
| IA (sistema experto) | **Python** | **Decidido** |
| API | **FastAPI (Python)**, para que llame directo al motor de reglas de Einar | Propuesto |
| BD de usuarios | **MySQL**: usuarios, roles, sesiones (`SQLAlchemy`) | Decidido |
| BD de rutas | **MongoDB**: rutas, paradas, tramos, transbordos (`pymongo`) | Decidido |
| Lugares y reportes | **MongoDB** sugerido (índices geoespaciales `2dsphere`, documentos flexibles) | Por confirmar |
| Apoyo del equipo | Perplexity (consultas con fuentes), NotebookLM (revisar documentación) | Fuera de la app |

### Estructura del repositorio (propuesta)
```
brujula-urbana/            # renombrar cuando se defina el nombre final
├── CONTEXTO.md
├── app/                      # App móvil: React Native + Expo + NativeWind (Jesús)
│   ├── app/                  # pantallas con Expo Router (según los mockups)
│   │   ├── (auth)/           # login.jsx, registro.jsx
│   │   ├── (tabs)/           # index.jsx (Inicio), planificar.jsx, mapa.jsx, perfil.jsx
│   │   ├── planes.jsx        # Tus planes (resultado del sistema experto)
│   │   └── reportar.jsx      # reporte comunitario
│   ├── components/           # ver sección 6.1
│   ├── services/api.js       # llamadas a la API (fetch/axios)
│   ├── assets/               # logotipo e íconos (Valentín)
│   ├── app.json              # nombre, ícono y permisos de la app
│   └── tailwind.config.js
├── backend/                  # FastAPI (Jesús)
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/          # auth.py, rutas.py, lugares.py, itinerarios.py, reportes.py
│   │   ├── db/               # mysql.py, mongo.py (Sebas)
│   │   └── ia/               # motor de reglas (Einar)
│   │       ├── hechos.py     # calcula las variables booleanas
│   │       ├── reglas.py     # reglas SI…ENTONCES
│   │       └── motor.py      # inferencia + explicación
│   ├── requirements.txt
│   └── .env.example
├── database/                 # scripts MySQL y datos semilla de MongoDB (Sebas)
└── docs/                     # manual de usuario (Kevin) y manual técnico (Einar)
```

### Arranque rápido de la app (Expo)
```bash
npx create-expo-app@latest app
cd app
npx expo install react-native-maps expo-location
npx expo start            # escanea el QR con la app Expo Go en tu celular
```
- **NativeWind:** sigue la guía oficial "NativeWind + Expo" (instala `nativewind` y `tailwindcss`, y agrega `tailwind.config.js`, `global.css`, `babel.config.js` y `metro.config.js`). Revisa la versión compatible con tu Expo SDK.
- **Probar:** con **Expo Go** en el celular no necesitas Android Studio. El celular y la PC deben estar en la misma red wifi.
- **APK para entregar:** `npm install -g eas-cli` → `eas login` → `eas build -p android --profile preview` (en `eas.json`, el perfil `preview` con `"buildType": "apk"`). Requiere cuenta gratuita de Expo y se compila en la nube.
- **iPhone:** también se prueba con Expo Go, sin Mac.

> En el celular `localhost` **no** apunta a tu PC. La app debe llamar a la API con la IP de tu computadora en la red (ej. `http://192.168.1.50:8000`); guárdala en `.env` como `EXPO_PUBLIC_API_URL`. Levanta FastAPI con `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
> React Native no usa `div` ni HTML: se usan `View`, `Text`, `Pressable`, `TextInput`. Lo que ya tengas en web (lógica, llamadas a la API, datos) se reutiliza; los componentes visuales se reescriben.

## 6.1 Diseño de la app (mockups de Valentín)

Los **mockups de Valentín son la referencia** para programar las pantallas. Si algo no coincide, manda el mockup.

### Pantallas
| Mockup | Archivo | Contenido | Estado |
|---|---|---|---|
| — | `(auth)/login.jsx` | Correo, contraseña, botón entrar, enlace a registro | Falta mockup |
| — | `(auth)/registro.jsx` | Nombre, correo, contraseña | Falta mockup |
| inicio-descubrir | `(tabs)/index.jsx` | Saludo con nombre, ubicación actual, buscador de destino, accesos "Ir a un lugar" / "Planear una salida" / "Comer", lista **Cerca de ti** | Listo |
| planificador-inteligente | `(tabs)/planificar.jsx` | ¿Con quién vas? · presupuesto (rango) · tiempo disponible · intereses · medio de movilidad · botón **Crear mi plan** | Listo |
| planes-recomendados | `planes.jsx` | Hasta 3 planes (equilibrado, rápido, económico) con costo, duración, km, paradas, etiqueta **Mejor opción** y explicación | Listo |
| mapa-ruta-comunidad | `(tabs)/mapa.jsx` | Mapa con la ruta numerada y **Detalle del recorrido** con horas estimadas | Listo, falta el tramo en autobús |
| — | `reportar.jsx` | Tipo (afluencia, cierre, accidente, manifestación), nivel, ubicación | Falta mockup |
| — | `(tabs)/perfil.jsx` | Datos del usuario y cerrar sesión | Falta mockup |

Barra inferior (tabs): **Inicio · Planificar · Mapa · Perfil**.

### Componentes a crear
- `ChipGroup`: selección única (Solo / Pareja / Amigos / Familia, 2 hrs / 4 hrs / 6 hrs / Todo el día) o múltiple (Comer, Café, Cultura, Entretenimiento, Aire libre).
- `RangoPresupuesto`: slider de dos puntas ($200 – $1,500 MXN).
- `OpcionMovilidad`: tarjeta con ícono y selección múltiple (Caminando, Transp. público, Taxi/App, Combinado).
- `BotonPrimario`: botón verde de ancho completo.
- `TarjetaLugar`: foto, categoría, nombre, calificación **con fuente**, distancia y minutos caminando.
- `TarjetaPlan`: título, costo, duración, km, paradas, etiqueta "Mejor opción" y texto de explicación.
- `LineaRecorrido`: lista de paradas con hora estimada; debe soportar tramos **caminando** y **en autobús** (línea, dónde subir, dónde bajar).

### Colores (aproximados de la captura; Valentín confirma los valores exactos)
```js
// tailwind.config.js → theme.extend.colors
colors: {
  primario:  '#1BA39C', // verde azulado: botones, chips activos, montos
  oscuro:    '#16323F', // chip seleccionado y títulos
  fondo:     '#F5F7F8',
  tarjeta:   '#FFFFFF',
  borde:     '#E3E8EB',
  suave:     '#E6F6F4', // fondo de chips de interés activos
  estrella:  '#F5A524',
}
```

### Del planificador a la API
El botón **Crear mi plan** manda esto a `POST /api/itinerarios`, y el sistema experto de Einar devuelve los planes de la pantalla "Tus planes":
```json
{
  "contexto": "pareja",
  "presupuesto": { "min": 200, "max": 1500 },
  "tiempo_horas": 4,
  "intereses": ["comer", "cafe", "entretenimiento"],
  "movilidad": ["caminando", "taxi_app"],
  "origen": { "lat": 19.28, "lng": -99.50 },
  "hora_salida": "18:00"
}
```
Respuesta esperada:
```json
{
  "planes": [
    {
      "tipo": "equilibrado",
      "mejor_opcion": true,
      "costo": 550, "duracion_horas": 4.5, "distancia_km": 3.2,
      "paradas": [
        { "lugar_id": "…", "nombre": "…", "llegada_estimada": "18:20" }
      ],
      "explicacion": "Cumple presupuesto, todos los lugares abren a esa hora…",
      "reglas_cumplidas": ["R1", "R2"]
    }
  ]
}
```
> Los mockups dicen "CDMX" y "Coyoacán" solo como ejemplo: en la app todo va en **Lerma–Toluca**.

## 6. Arquitectura

```
[App móvil — React Native + Expo + NativeWind]
      │  HTTP/JSON
      ▼
[API — FastAPI (Python)]
  ├── Auth ────────────► MySQL   (usuarios, roles)
  ├── Rutas/Lugares ───► MongoDB (rutas, paradas, lugares, reportes)
  └── Motor de reglas en Python (sistema experto)
         └── recibe hechos → aplica reglas → devuelve recomendación + explicación
```

## 7. Modelo de datos (borrador)

### MySQL
```sql
usuarios (id, nombre, email, password_hash, rol_id, creado_en)
roles    (id, nombre)            -- usuario, moderador, admin
```

### MongoDB — colección `rutas`
```json
{
  "_id": "ruta_lerma_toluca_01",
  "linea": "Nombre/número de la línea",
  "sentido": "Lerma → Toluca",
  "tarifa": 15,
  "horario": { "inicio": "05:30", "fin": "22:00", "frecuencia_min": 15, "tipo": "programado" },
  "paradas": [
    { "orden": 1, "nombre": "…", "ubicacion": { "type": "Point", "coordinates": [-99.5, 19.28] } }
  ],
  "trazo": { "type": "LineString", "coordinates": [[-99.5, 19.28], [-99.6, 19.29]] },
  "verificada": true,
  "fuente": "Levantamiento de campo del equipo",
  "fecha_verificacion": "2026-10-10"
}
```
> Las coordenadas son de ejemplo. Solo se cargan rutas recorridas y verificadas por el equipo.

### MongoDB — colección `lugares` (si se confirma)
```json
{
  "nombre": "…", "categoria": "cafeteria",
  "ubicacion": { "type": "Point", "coordinates": [-99.6, 19.29] },
  "horario": { "lun": ["08:00", "21:00"] },
  "costo_promedio": 120,
  "contextos": ["cita", "amigos"],
  "calificacion": { "valor": 4.5, "fuente": "…", "fecha": "…" }
}
```

### MongoDB — colección `reportes` (si se confirma)
```json
{
  "tipo": "cierre_total | accidente | manifestacion | afluencia",
  "nivel_afluencia": "baja | media | alta",
  "ubicacion": { "type": "Point", "coordinates": [0, 0] },
  "ruta_id": "…", "lugar_id": "…",
  "observado_en": "2026-10-01T18:30:00-06:00",
  "vigente_hasta": "2026-10-01T21:30:00-06:00",
  "usuario_id": 12,
  "confirmaciones": 3,
  "estado": "pendiente | verificado | descartado"
}
```

## 8. Endpoints de la API (borrador, lo cierra Jesús)

| Método | Ruta | Uso |
|---|---|---|
| POST | `/api/auth/register` | Crear cuenta |
| POST | `/api/auth/login` | Iniciar sesión |
| GET | `/api/rutas?origen=lat,lng&destino=lat,lng&hora=HH:MM` | Alternativas de traslado |
| GET | `/api/rutas/{id}` | Detalle: paradas, trazo, horario |
| GET | `/api/lugares?cerca=lat,lng&categoria=` | Lugares cercanos |
| POST | `/api/itinerarios` | Recibe contexto, presupuesto, tiempo y gustos; devuelve hasta 3 itinerarios con explicación |
| POST | `/api/reportes` | Crear reporte comunitario |
| GET | `/api/reportes?ruta_id=` | Reportes vigentes de una ruta |

## 9. Sistema experto (Einar)

**Hechos / variables** (booleanos que la API calcula antes de evaluar):
`abierto`, `dentro_presupuesto`, `cabe_en_tiempo`, `coincide_contexto`, `coincide_gustos`, `ruta_verificada`, `cierre_total_vigente`, `reporte_verificado`, `afluencia_alta`, `datos_suficientes`.

**Ejemplos de reglas** (meta: 15–20):
- R1: `abierto ∧ dentro_presupuesto ∧ cabe_en_tiempo → candidato`
- R2: `candidato ∧ coincide_contexto → recomendable`
- R3: `cierre_total_vigente ∧ reporte_verificado → descartar_ruta`
- R4: `descartar_ruta → buscar_alternativa_documentada`
- R5: `¬datos_suficientes → avisar_sin_informacion` (nunca inventar)
- R6: `afluencia_alta ∧ contexto_cita → penalizar_lugar`

Cada recomendación debe devolver **qué reglas se cumplieron**, para mostrar la explicación al usuario.

## 10. Meta del avance: miércoles 30 de septiembre de 2026

Entregables: **avance funcional + manual de usuario + manual técnico**.

**Demo de punta a punta** (aunque sea con pocos datos):
1. El usuario inicia sesión (MySQL).
2. Escribe un destino y la app llama a la API.
3. La API trae una de las 2 rutas reales de MongoDB y la app la dibuja en el mapa (línea, dónde subir y dónde bajar).
4. El sistema experto evalúa 3–4 lugares, descarta los que no cumplen y explica por qué.

### Calendario del avance
| Día | Tareas |
|---|---|
| **Sáb 26** | ✅ Repo (Sebas) · ✅ tablero compartido (Jesús) |
| **Dom 27 (hoy)** | Diagrama de arquitectura y documento de endpoints, y pasárselos a Einar (Jesús) · diseño de datos, scripts de MySQL y MongoDB con 2 rutas, zona piloto, y pasar el modelo a Einar (Sebas) · variables y borrador de reglas (Einar) · nombre, logotipo, identidad y mockups de 6 pantallas: inicio de sesión, registro, inicio, buscar destino, resultados e itinerarios (Valentín) · flujo de reportes (Kevin) |
| **Lun 28** | API en FastAPI con registro/inicio de sesión y primeros endpoints y app base en React + Tailwind con pantalla de login conectada, corriendo en el celular con Expo Go; revisar e integrar (Jesús) · ejemplo de inferencia y manual técnico completo (Einar) · exportar pantallas y aplicar logo en manuales y presentación (Valentín) · manual de usuario, formato de manuales y plan de pruebas (Kevin) |
| **Mar 29** | Solo correcciones |
| **Mié 30** | Presentación |

### Contenido de los manuales
- **Manual de usuario (Kevin):** requisitos, crear cuenta e iniciar sesión, instalar la app (Expo Go o APK), buscar destino y ver rutas, generar y comparar itinerarios, enviar un reporte.
- **Manual técnico (Einar):** arquitectura y tecnologías, instalación, API y endpoints, MySQL + MongoDB + diccionario de datos, sistema experto y reglas.

## 11. Después del avance (fechas aproximadas)
- **Hasta 16 oct:** levantamiento de campo de rutas y 20–30 lugares (Sebas); prototipo completo en Figma (Valentín, 9 oct).
- **Hasta 23 oct:** motor de inferencia conectado a la API (Einar); endpoints de itinerarios; app con API real y geolocalización del celular (Jesús).
- **Hasta 13 nov:** explicaciones automáticas y 3 contextos (Einar); APK final y comparativa de itinerarios (Jesús); servicio de mapas externo.
- **Hasta 6 nov:** módulo de reportes con verificación y vigencia (Kevin).
- **Hasta 27 nov:** pruebas de campo y manuales finales (Kevin, Einar); prueba de usabilidad con 5 usuarios (Valentín, 20 nov).

## 12. Pendientes por decidir
- [x] Plataforma: app móvil con React Native + Expo.
- [ ] Avisar al profe del cambio: el documento autorizado dice "aplicación web".
- [ ] Nombre final y logotipo de la app (Valentín).
- [x] App: React Native + Expo + NativeWind.
- [ ] Confirmar FastAPI para la API.
- [ ] ¿Lugares y reportes en MongoDB? (sugerido: sí)
- [ ] Límites exactos de la zona piloto.
- [ ] Servicio de mapas/rutas externo (OSM/OSRM, Google Maps u otro).

## 13. Convenciones de trabajo
- Ramas: `main` (estable), `develop`, y `feature/<nombre>` por tarea (ej. `feature/api-rutas`).
- Commits en español y en imperativo: `Agrega endpoint de rutas`.
- No subir contraseñas ni cadenas de conexión: usar `.env` y un `.env.example` en el repo.
- Código y comentarios en español para nombres del dominio (`rutas`, `lugares`, `reportes`).