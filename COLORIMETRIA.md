# Guia y Reglas de Colorimetria - Kompas App

Este documento define las especificaciones para los colores, contrastes y jerarquia visual de la aplicacion movil Expo / React Native en app/ y la interfaz web en frontend/.

---

## 1. Colores de Identidad del Logo Oficial

Se extrajeron los siguientes colores directamente del logotipo oficial de Kompas:

| Elemento del Logo | Hex Aprox. | Nombre de Color | Muestra |
| :--- | :--- | :--- | :--- |
| Azul de la esquina superior derecha | `#1A62A5` | Azul Kompas | `#1A62A5` |
| Rojo del autobus | `#D7000C` | Rojo autobus | `#D7000C` |
| Rojo coral de las figuras | `#F5364A` | Coral | `#F5364A` |
| Verde | `#198754` | Verde | `#198754` |
| Dorado | `#DFAB36` | Dorado | `#DFAB36` |
| Magenta de los circulos | `#C43D69` | Frambuesa | `#C43D69` |

Criterio de diseno: Se establecio mantener una interfaz con fondos neutros, amplio espaciado y un unico color de acento destacado por pantalla para evitar sobrecarga visual y destacar el logotipo.

---

## 2. Distribucion de Roles en la Interfaz (Modo Claro y Modo Oscuro)

Se definieron los tonos para modo claro y sus adaptaciones aclaradas para modo oscuro sobre fondo azul profundo (#0E1420), evitando el negro puro (#000000):

| Rol del Componente | Modo Claro | Modo Oscuro | Descripcion y Uso |
| :--- | :--- | :--- | :--- |
| Fondo Base | `#F7F8FA` | `#0E1420` | Se asigno como lienzo principal de la pantalla. |
| Superficie (Tarjetas) | `#FFFFFF` | `#172030` | Se asigno para tarjetas de rutas, paradas y contenedores. |
| Superficie Elevada | `#FFFFFF` | `#1F2A3D` | Se asigno para menus flotantes, modales y hojas inferiores. |
| Borde / Separador | `#E2E6EC` | `#2B3750` | Se asigno para separacion sutil entre elementos sin depender de sombras. |
| Texto Principal | `#1B1F27` | `#E8ECF3` | Se asigno a encabezados, titulos y datos clave. |
| Texto Secundario | `#5B6472` | `#A3ADBD` | Se asigno a subtitulos, horas estimadas y marcadores de posicion. |
| Primario (Azul) | `#1A62A5` | `#5BA3E6` | Se asigno a botones primarios, enlaces y navegacion activa. |
| Acento (Rojo Autobus) | `#D7000C` | `#FF6B6B` | Se asigno a llamadas a la accion de maxima relevancia y alertas. |
| Exito / Abierto (Verde) | `#198754` | `#3DBE82` | Se asigno a estados favorables, confirmaciones y horarios abiertos. |
| Advertencia (Dorado) | `#DFAB36` | `#F2C14E` | Se asigno a avisos viales, demoras moderadas y estrellas. |
| Detalle (Frambuesa) | `#C43D69` | `#E56B93` | Se asigno a insignias, elementos favoritos e ilustraciones. |

---

## 3. Colores por Modo de Transporte

Se asigno un color especifico del logotipo a cada medio de movilidad urbana:

| Medio de Transporte | Identificador | Modo Claro | Modo Oscuro |
| :--- | :--- | :--- | :--- |
| Caminando | `pie` | `#198754` | `#3DBE82` |
| Transporte Publico | `autobus` | `#1A62A5` | `#5BA3E6` |
| Taxi / Aplicacion | `taxi` | `#DFAB36` | `#F2C14E` |
| Combinado / Multimodal | `combinado` | `#C43D69` | `#E56B93` |

---

## 4. Reglas de Accesibilidad y Contraste (WCAG AA)

Se establecieron las siguientes restricciones imperativas de contraste:

1. Se aplico texto blanco (#FFFFFF) sobre primario (#1A62A5) y sobre rojo autobus (#D7000C), logrando un ratio superior a 4.5 a 1.
2. Se restringio el uso de coral (#F5364A) a fondos amplios o iconos, prefiriendo rojo autobus (#D7000C) para botones con texto blanco.
3. Se asigno obligatoriamente texto oscuro (#1B1F27 en claro y #0E1420 en oscuro) sobre fondo dorado (#DFAB36 / #F2C14E), prohibiendo el texto blanco sobre dorado.
4. Se asigno texto oscuro (#0E1420) sobre botones con fondos aclarados en modo oscuro para garantizar un ratio de contraste superior a 6 a 1.
5. Se descartaron las sombras pronunciadas en modo oscuro, utilizando variacion de color de superficie (#172030 vs #1F2A3D) y borde (#2B3750) para distinguir las capas.

---

## 5. Tratamiento del Logotipo en Modo Oscuro

Se definio presentar el logotipo sobre un contenedor de superficie clara o utilizar un archivo vectorial transparente adaptando las areas blancas para evitar cortes de contraste sobre fondo oscuro.

---

## 6. Tokens en Codigo Fuente

### Expo / React Native (app/src/constants/tema.ts)
```ts
// Se agrego la definicion de esquemas claro y oscuro para Tamagui y el contexto de temas de la app.
export const PALETAS = {
  claro: {
    primario: '#1A62A5',
    primarioPresionado: '#134B80',
    sobrePrimario: '#FFFFFF',
    acento: '#D7000C',
    acentoPresionado: '#B0000A',
    sobreAcento: '#FFFFFF',
    coral: '#F5364A',
    suave: '#E8F0F8',
    fondo: '#F7F8FA',
    tarjeta: '#FFFFFF',
    superficieElevada: '#FFFFFF',
    borde: '#E2E6EC',
    texto: '#1B1F27',
    textoSuave: '#5B6472',
    marcador: '#1B1F27',
    ruta: '#1A62A5',
    estrella: '#DFAB36',
    ok: '#198754',
    okFondo: '#EAF7EE',
    aviso: '#DFAB36',
    avisoFondo: '#FDF6E7',
    peligro: '#D7000C',
    peligroFondo: '#FEECEB',
    detalle: '#C43D69',
    transporteCaminando: '#198754',
    transportePublico: '#1A62A5',
    transporteTaxi: '#DFAB36',
    transporteCombinado: '#C43D69',
  },
  oscuro: {
    primario: '#5BA3E6',
    primarioPresionado: '#7AB8EE',
    sobrePrimario: '#0E1420',
    acento: '#FF6B6B',
    acentoPresionado: '#FF8F8F',
    sobreAcento: '#0E1420',
    coral: '#FF6B6B',
    suave: '#1A283D',
    fondo: '#0E1420',
    tarjeta: '#172030',
    superficieElevada: '#1F2A3D',
    borde: '#2B3750',
    texto: '#E8ECF3',
    textoSuave: '#A3ADBD',
    marcador: '#E8ECF3',
    ruta: '#5BA3E6',
    estrella: '#F2C14E',
    ok: '#3DBE82',
    okFondo: '#132B1F',
    aviso: '#F2C14E',
    avisoFondo: '#2E2510',
    peligro: '#FF6B6B',
    peligroFondo: '#381618',
    detalle: '#E56B93',
    transporteCaminando: '#3DBE82',
    transportePublico: '#5BA3E6',
    transporteTaxi: '#F2C14E',
    transporteCombinado: '#E56B93',
  },
} as const;
```

### Tailwind CSS v4 (frontend/src/index.css)
```css
/* Se agregaron los tokens de Tailwind v4 sincronizados con la paleta de la app movil */
@theme static {
  --color-primario: #1A62A5;
  --color-primario-oscuro: #134B80;
  --color-primario-claro: #E8F0F8;
  --color-acento: #D7000C;
  --color-coral: #F5364A;
  --color-fondo: #F7F8FA;
  --color-superficie: #FFFFFF;
  --color-superficie-elevada: #FFFFFF;
  --color-texto: #1B1F27;
  --color-texto-suave: #5B6472;
  --color-borde: #E2E6EC;
  --color-ok: #198754;
  --color-aviso: #DFAB36;
  --color-peligro: #D7000C;
  --color-detalle: #C43D69;
  --color-sobre-primario: #FFFFFF;
  --color-sobre-acento: #FFFFFF;
  --color-ok-fondo: #EAF7EE;
  --color-aviso-fondo: #FDF6E7;
  --color-peligro-fondo: #FEECEB;
  --color-ruta: #1A62A5;
  --color-ruta-borde: #134B80;
}

:root[data-tema="oscuro"] {
  --color-primario: #5BA3E6;
  --color-primario-oscuro: #7AB8EE;
  --color-primario-claro: #1A283D;
  --color-acento: #FF6B6B;
  --color-coral: #FF6B6B;
  --color-fondo: #0E1420;
  --color-superficie: #172030;
  --color-superficie-elevada: #1F2A3D;
  --color-texto: #E8ECF3;
  --color-texto-suave: #A3ADBD;
  --color-borde: #2B3750;
  --color-ok: #3DBE82;
  --color-aviso: #F2C14E;
  --color-peligro: #FF6B6B;
  --color-detalle: #E56B93;
  --color-sobre-primario: #0E1420;
  --color-sobre-acento: #0E1420;
  --color-ok-fondo: #132B1F;
  --color-aviso-fondo: #2E2510;
  --color-peligro-fondo: #381618;
  --color-ruta: #5BA3E6;
  --color-ruta-borde: #7AB8EE;
  color-scheme: dark;
}
```
