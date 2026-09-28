# Kompás App — App móvil

React Native + **Expo SDK 57** (Expo Router) + **Tamagui 2** (estilos y temas) + mapa **Leaflet** (en WebView) + **expo-location**.
Zona piloto: **Toluca, Lerma y San Mateo Atenco**. Pantallas según los mockups de Valentín, versión 3 (azul #285582).

## Correr en tu celular

```bash
npm install
cp .env.example .env        # la primera vez
npx expo start
```

1. Instala **Expo Go** en tu celular (Play Store / App Store).
2. Celular y PC en la **misma red wifi**.
3. Escanea el QR que aparece en la terminal (en iPhone, con la cámara).

En modo demostración entras con cualquier correo y una contraseña de 6 o más caracteres.
`npx expo start --web` abre la app en el navegador para revisar pantallas (el mapa también funciona ahí).

## Mapa

El mapa es **Leaflet** con mosaicos de **Esri / OpenStreetMap**, dentro de un `WebView` en el celular y de un
`iframe` en web ([`src/components/mapa/`](src/components/mapa/)). No se usa react-native-maps porque en
**Expo Go SDK 57 para Android el mapa de Google sale en blanco** (bug abierto:
[expo/expo#49323](https://github.com/expo/expo/issues/49323)). Ventajas: funciona en Expo Go, en iPhone y en web,
y **no necesita llave de Google** (tampoco en el APK). Necesita internet para cargar el mapa.

## Datos de ejemplo vs. API real

| Variable | Uso |
| --- | --- |
| `EXPO_PUBLIC_USE_MOCK` | `true`: datos de ejemplo y sistema experto simulado (`src/services/mock`). `false`: llama a la API. |
| `EXPO_PUBLIC_API_URL` | URL de FastAPI. En el celular **no** sirve `localhost`: usa la IP de tu PC, p. ej. `http://192.168.1.50:8000`. |

Levanta la API con `uvicorn app.main:app --host 0.0.0.0 --port 8000`. Después de cambiar `.env`, reinicia `npx expo start`.

Todas las llamadas pasan por [`src/services/api.ts`](src/services/api.ts), con los tipos en
[`src/types/dominio.ts`](src/types/dominio.ts). El planificador manda y recibe exactamente el JSON de CONTEXTO.md §6.1.
Además, la app aprovecha dos campos opcionales si la API los manda:

- `planes[].tramos`: cómo moverse entre paradas (a pie, **autobús con línea / dónde subir / dónde bajar**, taxi).
  Si no vienen, la app calcula tramos caminando.
- `descartados`: lugares que no pasaron las reglas y por qué (`reglas`).

`reglas_cumplidas` puede venir como `["R1", "R2"]` o como `[{ "id": "R1", "descripcion": "…" }]`.
La simulación del motor ([`src/services/mock/motor.ts`](src/services/mock/motor.ts)) sirve de referencia para Einar.

## Dónde cambiar cosas

- **Colores claro/oscuro** (Valentín): [`src/constants/tema.ts`](src/constants/tema.ts). Se cargan como temas de
  Tamagui en [`src/tamagui.config.ts`](src/tamagui.config.ts) y los componentes los usan como `$primario`, `$texto`…
  El usuario cambia el tema en **Perfil**.
- **Piezas de diseño** (textos, tarjetas, píldoras): [`src/components/ui.tsx`](src/components/ui.tsx), hechas con
  `styled()` de Tamagui. Tamagui v5 solo acepta abreviaturas: `p`, `px`, `bg`, `rounded`, `items`, `justify`…
- **Logotipo**: [`assets/images/logo-kompas.png`](assets/images/logo-kompas.png) (en la app) e `icon.png`,
  `android-icon-*.png`, `splash-icon.png` y `favicon.png` (ícono del celular, pantalla de carga y web).
  Si Valentín cambia el logo, hay que regenerar esos archivos con el mismo tamaño.
- **Íconos**: [`src/components/Icono.tsx`](src/components/Icono.tsx) (SF Symbols en iPhone, Material Symbols en Android/web).
- **Límites de la zona** (Sebas): [`src/constants/zona.ts`](src/constants/zona.ts).
- **Textos de opciones y reglas**: [`src/constants/catalogos.ts`](src/constants/catalogos.ts).

## Responsivo

- Celular: pestañas abajo y panel inferior en el mapa (como los mockups).
- Tablet vertical (≥ 768 px, `$md` en Tamagui): listas en 2 columnas y panel del mapa a la izquierda.
- Tablet horizontal / web (≥ 1000 px): pestañas en barra lateral.
- El contenido de formularios tiene ancho máximo para no estirarse en pantallas grandes.

## Estructura

```text
src/
├── app/                  # pantallas (Expo Router)
│   ├── (auth)/           # login, registro
│   ├── terminos.tsx      # términos y condiciones (desde el registro y el perfil)
│   ├── (tabs)/           # index (Inicio), planificar, mapa, perfil
│   ├── planes.tsx        # Tus planes (resultado del sistema experto)
│   ├── buscar.tsx        # buscar destino y ver cómo llegar
│   └── reportar.tsx      # reporte comunitario
├── components/           # ui.tsx (base Tamagui), ChipGroup, RangoPresupuesto, OpcionMovilidad, TarjetaLugar, TarjetaPlan, LineaRecorrido, mapa/…
├── context/              # sesión, tema, ubicación, viaje activo
├── tamagui.config.ts     # temas claro/oscuro con los colores de la marca
├── services/             # api.ts, mapas.ts (OpenStreetMap), mock/
├── constants/            # tema, zona, catálogos
└── utils/                # distancias, horas, conversión de planes a recorridos
```

## Comandos

```bash
npx expo lint        # revisar código
npx tsc --noEmit     # revisar tipos
npx expo-doctor      # revisar dependencias
```

## APK

`npx eas-cli@latest build -p android --profile preview` (ver CONTEXTO.md). Como el mapa es Leaflet, no hace falta
llave de Google Maps.
