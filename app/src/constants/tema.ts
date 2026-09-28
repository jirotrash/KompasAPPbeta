// Identidad visual de Kompás App, tomada de los mockups de Valentín (versión 3, azul).
// Estos colores alimentan los temas de Tamagui (src/tamagui.config.ts): en los componentes se usan
// como "$primario", "$texto", etc. Donde se necesita el color directo (mapa, íconos, barra de pestañas)
// se usa `paleta` del contexto de tema. Cambia aquí y cambia en toda la app.

export const PALETAS = {
  claro: {
    primario: '#285582',
    primarioPresionado: '#1E4268',
    sobrePrimario: '#FFFFFF',
    suave: '#E8EEF5',
    fondo: '#F6F8FA',
    tarjeta: '#FFFFFF',
    borde: '#E2E8F0',
    texto: '#1B3448',
    textoSuave: '#687B8A',
    marcador: '#1F3445',
    ruta: '#2A8C87',
    estrella: '#E0A43A',
    ok: '#2F7D4F',
    aviso: '#A1620A',
    avisoFondo: '#FDF3DC',
    peligro: '#B42318',
    peligroFondo: '#FEF1F0',
  },
  oscuro: {
    primario: '#86AEDA',
    primarioPresionado: '#A3C2E4',
    sobrePrimario: '#0B1A29',
    suave: '#1A2B3E',
    fondo: '#0E1620',
    tarjeta: '#162230',
    borde: '#26374A',
    texto: '#E6EDF4',
    textoSuave: '#93A4B5',
    marcador: '#E6EDF4',
    ruta: '#5CC3BC',
    estrella: '#F0B955',
    ok: '#6BCB8E',
    aviso: '#F2B84B',
    avisoFondo: '#2E2410',
    peligro: '#F58A80',
    peligroFondo: '#35191A',
  },
} as const;

export type Esquema = keyof typeof PALETAS;
export type Paleta = (typeof PALETAS)[Esquema];

/** Ancho máximo del contenido en tablets y web, para que no se estire de más. */
export const ANCHO_MAXIMO = 720;
/** A partir de este ancho la app usa diseño de tablet (columnas, panel lateral en el mapa). */
export const ANCHO_TABLET = 768;
/** A partir de este ancho (tablet horizontal, web) las pestañas pasan a una barra lateral. */
export const ANCHO_BARRA_LATERAL = 1000;
