# Manual técnico — Arquitectura de software (Kompás v0.6)

> Fuente: `ARQUITECTURA.md` (raíz del repositorio). Los diagramas están en Mermaid: GitHub y VS Code
> (extensión *Markdown Preview Mermaid Support*) los dibujan directamente.

## 1. Estilo arquitectónico

| Nivel | Estilo | Dónde se ve |
|---|---|---|
| Sistema | **Cliente-servidor** con API REST | La app móvil (Expo) y la web (React) consumen la API FastAPI por HTTP/JSON |
| Backend | **Arquitectura en capas (N capas)** | Presentación → Negocio → Acceso a datos → Infraestructura |
| Organización del código | **Monolito modular** (módulos por funcionalidad) | `backend/app/modulos/<módulo>/` y `frontend/src/modulos/<módulo>/` |

Un monolito modular se despliega como una sola API, pero cada funcionalidad (cuenta, lugares, itinerarios…)
vive en su propia carpeta con sus propias capas. Si un módulo crece, se puede separar como servicio sin reescribirlo.

### Capas y responsabilidades

| Capa | Archivo en cada módulo | Hace | No hace |
|---|---|---|---|
| **Presentación** | `router.py`, `esquemas.py` | Recibe la petición, valida con Pydantic (DTO), pide autenticación, llama al servicio y responde | Consultas a la base, reglas de negocio |
| **Negocio** | `servicio.py` | Reglas del caso de uso: validaciones, orquesta repositorios, IA y servicios externos; lanza errores de negocio | Conocer HTTP (no usa `HTTPException`) ni la base |
| **Acceso a datos** | `repositorio.py` | Lee y escribe en MongoDB; filtra el borrado lógico; convierte documentos a `dict` del dominio | Reglas de negocio, `HTTPException` |
| **Dominio IA** | `app/ia/` | Sistema experto (R01–R20), DFS, UCS, voraz y A\*, algoritmo genético, árbol binario de paradas, transbordos, métricas Euclidiana/Manhattan | Acceso a base o HTTP (es Python puro) |
| **Infraestructura** | `app/nucleo/`, `app/externos/`, `app/compartido/` | Configuración, conexión a MongoDB, JWT/bcrypt, errores, clientes de Google Places y Ollama, geografía | Lógica de un módulo en particular |

### Regla de dependencias

```
router  →  servicio  →  repositorio  →  nucleo.bd (MongoDB)
              │
              ├──→  app.ia (sin cambios de lógica)
              ├──→  app.externos (Google Places, Ollama)
              └──→  servicio de OTRO módulo (nunca su repositorio)
```

1. Un router nunca consulta la base: solo usa `Depends(get_bd)` para construir su servicio.
2. Un repositorio devuelve `dict` o `list[dict]` con las llaves del dominio, nunca documentos crudos con `ObjectId`.
   Gracias a esto el cambio de MySQL a MongoDB no tocó servicios ni routers.
3. Un servicio nunca lanza `HTTPException`: lanza un error de `nucleo/errores.py` (`NoEncontrado`, `Conflicto`,
   `NoAutorizado`, `Prohibido`, `DatosInvalidos`, `ServicioExterno`, `ErrorDeDatos`) y `registrar_manejadores()`
   lo traduce a la respuesta HTTP con el mismo mensaje de siempre.
4. `app/ia/` no importa nada de `modulos/`, de la base ni de FastAPI.

## 2. Patrones de diseño

| Patrón / principio | Dónde | Para qué |
|---|---|---|
| **Repositorio** | `modulos/*/repositorio.py` | Aísla la base de datos; permitió cambiar MySQL → MongoDB sin tocar servicios ni routers |
| **Inyección de dependencias** | `Depends(get_servicio)`, `Depends(get_usuario_actual)`, `Depends(requiere_admin)` | El router recibe el servicio ya construido; en pruebas se puede sustituir |
| **DTO** | `modulos/*/esquemas.py` (Pydantic) | Valida la entrada y define exactamente qué sale en la respuesta (nunca la contraseña) |
| **Fachada** | `app/ia/servicio.recomendar()` | Una sola función esconde hechos + planificador + motor de reglas |
| **Adaptador** | `externos/google_places.py`, `externos/ollama.py` | Convierten la respuesta de Google al formato de lugar que usa la IA y la de Ollama (incluidas las *tool calls*) al formato del asistente |
| **Singleton** | `get_settings()` con `lru_cache`, `nucleo.bd.cliente()` con `lru_cache` | Una sola configuración y un solo pool de conexiones a MongoDB |
| **Middleware / cadena** | `CORSMiddleware`, manejadores de errores | Comportamiento transversal sin repetir código |
| **Sistema experto (encadenamiento hacia adelante)** | `app/ia/motor.py` | Recomienda y explica cada plan con las reglas R01–R20 |
| **Estrategia** | `app/ia/busqueda_informada.py` | UCS, voraz y A\* comparten la misma búsqueda; solo cambia la función f(n) y la heurística |
| **Caché en memoria** | `app/ia/trazos.arbol_de_ruta()` | El árbol de paradas de cada ruta se construye una vez y se invalida si la ruta cambia |
| Principios | Todo el backend | Responsabilidad única, bajo acoplamiento, alta cohesión por módulo |

## 3. Diagramas

### 3.1 Contexto del sistema

```mermaid
flowchart LR
  U([Usuario]) -- usa --> APP[App móvil Kompás]
  A([Administrador]) -- consulta --> WEB[Panel web<br/>solo dashboard]
  APP & WEB -- HTTP/JSON --> K[[Kompás API]]
  K -- lugares, horarios, precios --> G[(Google Places API)]
  APP & WEB -- mapas y trazos por calles --> O[(OpenStreetMap / OSRM / Esri)]
```

El usuario planea salidas desde la app móvil; el administrador revisa estadísticas en el panel web, que solo tiene el dashboard. Ambos clientes
hablan solo con la API de Kompás. La API consulta Google Places para los lugares de un plan (la llave nunca sale
del servidor). Los mosaicos del mapa y el trazo por calles los piden los clientes directamente a servicios abiertos.

### 3.2 Contenedores

```mermaid
flowchart TB
  subgraph Clientes
    M[App móvil<br/>React Native + Expo Router]
    W[Panel web de administración<br/>React 19 + Vite + Recharts]
  end
  API[API Kompás<br/>FastAPI + Uvicorn · Python]
  DB[(MongoDB<br/>local o Atlas)]
  G[Google Places API]
  O[Ollama<br/>LLM local en la PC]
  M -- REST + JWT --> API
  W -- REST + JWT --> API
  API -- PyMongo --> DB
  API -- HTTPS --> G
  API -- HTTP localhost:11434 --> O
```

Hay cinco piezas que se despliegan por separado (Ollama corre en la misma PC que la API; la app nunca le habla directo). La app y la web son clientes "tontos": no calculan
estadísticas ni reglas, todo lo hace la API. La API es un solo proceso (monolito modular). MongoDB puede ser
local para desarrollo o Atlas en la nube; solo cambia la variable `MONGO_URI`.

### 3.3 Capas del backend

```mermaid
flowchart LR
  subgraph Clientes
    M[App móvil<br/>React Native + Expo]
    W[Panel web<br/>React + Vite]
  end
  subgraph API["API Kompás (FastAPI)"]
    direction TB
    P[Presentación<br/>routers + esquemas]
    N[Negocio<br/>servicios]
    D[Acceso a datos<br/>repositorios]
    IA[Dominio IA<br/>sistema experto · búsquedas · genético · árbol]
  end
  DB[(MongoDB)]
  G[Google Places API]
  O[Ollama]
  M & W -- HTTP/JSON + JWT --> P
  P --> N --> D --> DB
  N --> IA
  N --> G
  N --> O
```

Cada petición entra por la capa de presentación (router), que valida con Pydantic y delega en el servicio.
El servicio aplica las reglas del caso de uso y usa repositorios, la IA o Google. Solo los repositorios hablan
con MongoDB. Las flechas siempre van hacia abajo: una capa nunca llama a la de arriba.

### 3.4 Componentes (módulos del backend)

```mermaid
flowchart TB
  subgraph modulos
    cuenta[cuenta<br/>auth + residencia]
    catalogos[catalogos]
    lugares[lugares]
    rutas[rutas]
    historial[historial]
    itinerarios[itinerarios]
    reportes[reportes]
    laboratorio[laboratorio<br/>DFS · distancias · comparativo · genético]
    dashboard[dashboard]
    asistente[asistente<br/>Ollama + herramientas]
  end
  nucleo[nucleo<br/>config · bd · seguridad · errores]
  compartido[compartido<br/>geo · traslados · texto]
  externos[externos<br/>google_places · ollama]
  ia[ia<br/>motor · hechos · planificador · DFS · búsqueda informada<br/>genético · árbol de paradas · transbordos · métricas]

  historial -- ServicioRutas --> rutas
  historial -- ServicioCatalogos --> catalogos
  itinerarios -- ServicioCatalogos --> catalogos
  itinerarios --> externos
  itinerarios -- recomendar + orden óptimo --> ia
  itinerarios -- bitácora --> laboratorio
  rutas -- árbol + A* --> ia
  rutas -- bitácora --> laboratorio
  laboratorio --> ia
  asistente -- ServicioLugares --> lugares
  asistente -- ServicioRutas --> rutas
  asistente -- ServicioItinerarios --> itinerarios
  asistente --> externos
  dashboard -- ServicioCatalogos --> catalogos
  dashboard -- descripciones de reglas --> ia
  reportes --> compartido
  modulos -.-> nucleo
  nucleo -. get_usuario_actual .-> cuenta
```

Cada caja es una carpeta de `backend/app/modulos/` con su router, servicio y repositorio. Cuando un módulo
necesita datos de otro, usa el **servicio** de ese módulo (por ejemplo, historial valida la ruta con
`ServicioRutas`), nunca su repositorio. `nucleo` es infraestructura común; `get_usuario_actual` lee el usuario
con el repositorio de cuenta. `ia` no conoce a nadie: los módulos la llaman a ella.

### 3.5 Secuencia de `POST /api/itinerarios`

```mermaid
sequenceDiagram
  actor App
  participant R as itinerarios/router
  participant S as ServicioItinerarios
  participant C as ServicioCatalogos
  participant G as externos/google_places
  participant IA as ia/servicio.recomendar
  participant H as ia/hechos + ia/motor
  participant P as RepositorioPlanes
  participant DB as MongoDB

  App->>R: POST /api/itinerarios (JWT + PeticionPlan)
  R->>R: valida DTO y get_usuario_actual
  R->>S: crear(usuario, petición)
  S->>S: ¿origen dentro de la zona piloto? (si no, 422)
  S->>C: categoria_por_clave / transporte_por_clave
  C->>DB: find categorias / transportes
  S->>G: buscar_para_plan(origen, intereses, radio)
  G-->>S: lugares (o 503 si Google falla)
  S->>IA: recomendar(petición, lugares, ahora)
  IA->>H: construir_hechos() y evaluar() por candidato
  H-->>IA: estado, puntuación y traza de reglas
  IA-->>S: planes + descartados
  S->>P: guardar(plan con intereses, movilidad y evaluación)
  P->>DB: insert_one(planes)
  S-->>R: respuesta del motor
  R-->>App: 200 RespuestaPlanes
```

El router queda en unas cuantas líneas: valida y delega. El servicio orquesta la zona, los catálogos, Google y la
IA en ese orden, y solo guarda el plan si todo salió bien. La evaluación que se guarda es la misma que regresó
el motor (no se recalcula). El origen exacto del usuario no se guarda por privacidad.

### 3.6 Secuencia de login con JWT

```mermaid
sequenceDiagram
  actor Cliente
  participant R as cuenta/router
  participant S as ServicioCuenta
  participant Repo as RepositorioCuenta
  participant DB as MongoDB
  participant Seg as nucleo/seguridad

  Cliente->>R: POST /api/auth/login {email, password}
  R->>S: login(correo, password)
  S->>Repo: por_correo(correo)
  Repo->>DB: find_one({correo, deleted_at: null})
  DB-->>Repo: documento usuario
  Repo-->>S: dict usuario (sin ObjectId)
  S->>Seg: verificar_password (bcrypt)
  alt contraseña correcta
    S->>Seg: crear_token(id) (JWT HS256)
    S-->>R: {token, usuario}
    R-->>Cliente: 200 SesionSalida (sin contraseña, con rol)
  else incorrecta
    S-->>R: NoAutorizado
    R-->>Cliente: 401 "Correo o contraseña incorrectos."
  end
  Note over Cliente,Seg: En cada petición 🔒 get_usuario_actual decodifica el JWT y busca el usuario por _id
```

La contraseña se guarda con bcrypt y nunca sale de la API. El token JWT lleva el id del usuario y una fecha de
expiración (`JWT_EXPIRA_MINUTOS`). Los endpoints protegidos reciben el usuario ya validado por inyección de
dependencias; el dashboard además pide `requiere_admin` (rol `admin`).

### 3.7 Despliegue (demostración en red local)

```mermaid
flowchart LR
  subgraph PC["PC del equipo (Windows)"]
    U[Uvicorn :8000<br/>app.main:app]
    V[Vite :5173<br/>frontend web]
    M[(MongoDB :27017<br/>local o Docker)]
    U --> M
  end
  subgraph Nube
    A[(MongoDB Atlas)]
    G[Google Places]
  end
  Cel[Celular con Expo Go] -- "http://IP-de-la-PC:8000" --> U
  Nav[Navegador] --> V
  V -- VITE_API_URL --> U
  U -. MONGO_URI=mongodb+srv:// .-> A
  U --> G
```

En la demo todo corre en una PC: Uvicorn escucha en `0.0.0.0:8000` para que el celular (Expo Go) entre por la
IP de la red local, y Vite sirve la web. La base puede ser MongoDB local (o en Docker) o Atlas; para Atlas hay
que permitir la IP de la PC en *Network Access*.

### 3.8 Estructura de carpetas

```
backend/app/
├── main.py                    # crea la app, CORS, manejadores de error, registra routers
├── nucleo/                    # config.py · bd.py · seguridad.py · errores.py · parametros.py · esquemas_comunes.py
├── compartido/                # geo.py · traslados.py · texto.py
├── externos/                  # google_places.py (Adaptador)
├── modulos/
│   ├── cuenta/                # router · esquemas · servicio · repositorio
│   ├── catalogos/  lugares/  rutas/  historial/  itinerarios/
│   ├── laboratorio/           # DFS, distancias, comparativo de búsqueda y genético + bitácora
│   ├── reportes/              # nuevo en v0.5
│   ├── dashboard/             # nuevo en v0.5 (solo agregaciones)
│   └── asistente/             # nuevo en v0.6: router · esquemas · servicio · repositorio · herramientas · prompt
└── ia/                        # sistema experto, planificador, DFS, métricas (sin cambios de lógica)
                               # v0.6 (archivos nuevos): busqueda_informada · algoritmo_genetico · orden_optimizado
                               #                        arbol_binario · trazos · transbordos

frontend/src/                  # TypeScript desde la v0.6 (strict, sin any)
├── main.tsx
├── app/                       # App.tsx · Layout.tsx · RutaPrivada.tsx · RutaAdmin.tsx
├── compartido/                # api/ (cliente, lugares, mapas) · tipos/dominio.ts · componentes/ · hooks/ · utils/ · config/
├── mock/                      # datos de ejemplo (VITE_USE_MOCK=true)
└── modulos/
    ├── cuenta/  inicio/  rutas/  itinerarios/  reportes/
    └── dashboard/             # api · tipos · mock · hooks · paginas · componentes · graficas (28 gráficas y paneles)
```

## 4. App móvil (`app/`)

No se reorganizó: Expo Router obliga a que las pantallas vivan en `src/app/`. Ya sigue una separación en
capas equivalente:

| Capa | Carpeta |
|---|---|
| Presentación (pantallas y navegación) | `src/app/` (Expo Router) |
| Componentes de interfaz | `src/components/` |
| Estado global | `src/context/` (Sesión, Tema, Ubicación, Viaje) |
| Acceso a la API | `src/services/api.ts` (+ `mock/`) |
| Modelo de dominio (tipos) | `src/types/dominio.ts` |

## 5. Frontend web: reglas de módulos

1. `compartido/api/cliente.js` tiene `solicitud()`, la sesión y `ErrorApi`; cada endpoint vive en el `api.js` de su
   módulo con el mismo nombre, firma y JSDoc que antes. Con `VITE_USE_MOCK=true` responden los datos de ejemplo.
2. Un módulo importa de `compartido/` libremente, pero de otro módulo solo a través de su `index.js`
   (por ejemplo `import { useAuth } from '../cuenta'`).
3. Las páginas nunca llaman `fetch` directo.
4. La web es **solo el panel de administración**: login y dashboard en `/`. Las rutas, itinerarios y reportes para
   usuarios viven en la app móvil; los módulos `inicio`, `rutas`, `itinerarios` y `reportes` de la web ya no están
   en el enrutador. El login rechaza cuentas que no son admin.
