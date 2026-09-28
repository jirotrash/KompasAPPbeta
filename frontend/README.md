# Brújula Urbana — Frontend (PWA)

React + Vite + Tailwind CSS v4 + react-leaflet (OpenStreetMap) + vite-plugin-pwa.
Zona piloto: **Toluca, Lerma y San Mateo Atenco**.

## Correr en local

```bash
npm install
cp .env.example .env     # la primera vez
npm run dev              # http://localhost:5173
```

Para probar en el celular dentro de la misma red: `npm run dev -- --host` y abre la IP que muestra Vite.
Para probar la instalación como app: `npm run build && npm run preview`.

## Datos de ejemplo vs. API real

| Variable | Valor | Efecto |
| --- | --- | --- |
| `VITE_USE_MOCK` | `true` | Usa `src/services/mock/` (datos de ejemplo y motor de reglas simulado). En pantalla aparece "Modo demostración". |
| `VITE_USE_MOCK` | `false` | Llama a la API FastAPI en `VITE_API_URL`. |
| `VITE_API_URL` | `http://localhost:8000` | URL base de la API. |

Para conectar el backend solo hay que poner `VITE_USE_MOCK=false` y reiniciar `npm run dev`.
La API debe permitir CORS desde el origen del frontend (`CORSMiddleware` en FastAPI).

## Mapa, buscador y trazo por calles

- El mapa usa mosaicos de **Esri World Street Map** (claro) y **Esri Dark Gray** (oscuro): gratuitos, sin llave,
  con estilo parecido a Google Maps. Las rutas se dibujan en azul, a pie con puntos, y el botón ◎ muestra tu ubicación.
  Se cambian en `MOSAICOS` de [`src/components/Mapa.jsx`](src/components/Mapa.jsx).
  (Los mosaicos de CARTO ya piden llave; el Google Maps oficial requiere llave de API con tarjeta.)

- El buscador (Inicio, Rutas, Itinerarios y Reportar) sugiere mientras escribes: primero puntos de referencia y
  lugares de la BD, y luego direcciones de OpenStreetMap vía **Photon**. Solo muestra resultados de Toluca, Lerma
  y San Mateo Atenco.
- Las rutas a pie, en taxi y por app se dibujan siguiendo las calles con **OSRM** (routing.openstreetmap.de).
  Si el servicio no responde, se estima por distancia.
- Son servidores públicos de demostración (sirven para el prototipo). Se cambian con `VITE_GEOCODER_URL` y
  `VITE_ROUTER_URL`, o en [`src/services/mapas.js`](src/services/mapas.js).

## Modo claro / oscuro

Se cambia en la barra lateral (Claro / Oscuro / Sistema) o con el botón de sol/luna en el celular y en el login.
Por defecto sigue la configuración del dispositivo. Los colores de ambos temas están en [`src/index.css`](src/index.css).

## Contrato con la API y el sistema experto

Todo pasa por [`src/services/api.js`](src/services/api.js): ahí está documentado (JSDoc) qué recibe y qué
regresa cada endpoint de CONTEXTO.md §8. Lo más importante para el backend:

- Autenticación: `POST /api/auth/login` y `/register` regresan `{ token, usuario }`; el frontend manda
  `Authorization: Bearer <token>` en las siguientes peticiones. Los errores se leen de `{ detail }` (formato FastAPI).
- `GET /api/rutas` regresa `{ datos_suficientes, mensaje?, alternativas: [...] }`. Si `datos_suficientes` es `false`
  se muestra "No tenemos información suficiente…" (nunca se inventan rutas).
- `POST /api/itinerarios` regresa `{ datos_suficientes, itinerarios (máx. 3), descartados }`, con
  `reglas_cumplidas: [{ id: 'R1', descripcion }]` en cada itinerario y `reglas` en cada descartado, para mostrar la explicación.
- Geometrías en GeoJSON (`[lng, lat]`), igual que en MongoDB. Los parámetros de consulta van como `lat,lng`.

[`src/services/mock/motorReglas.js`](src/services/mock/motorReglas.js) es una simulación en JS del motor de reglas
(R1–R11 de ejemplo) que sirve de referencia para la forma de la respuesta; el motor real es el de Python.

## Dónde cambiar cosas

- **Colores y tipografía** (Valentín): bloque `@theme` (tema claro) y `:root[data-tema="oscuro"]` (tema oscuro) en [`src/index.css`](src/index.css).
- **Logotipo e íconos de la PWA**: `public/favicon.svg`; luego regenera los PNG con
  `npx @vite-pwa/assets-generator --preset minimal-2023 public/favicon.svg`.
- **Límites de la zona piloto** (Sebas): [`src/config/zona.js`](src/config/zona.js).

## Estructura

```text
src/
├── config/zona.js        # límites y puntos de referencia de la zona piloto
├── context/              # sesión del usuario
├── services/api.js       # único acceso a la API (o a los datos mock)
├── services/mock/        # datos de ejemplo + motor de reglas simulado
├── components/           # Layout, Mapa, TarjetaRuta, TarjetaLugar, SelectorPunto, ExplicacionReglas…
├── pages/                # Login, Registro, Inicio, BuscarDestino, ResultadosRuta, Itinerarios, Reportar
└── utils/                # geo (distancias, formatos) y catálogos del dominio
```
