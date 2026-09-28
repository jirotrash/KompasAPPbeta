// Configuración de Tamagui: la base v5 (tokens, tipografía, breakpoints, abreviaturas como p, bg, rounded)
// más los colores de Kompás App en los temas claro ("light") y oscuro ("dark").
import { defaultConfig } from '@tamagui/config/v5';
import { createTamagui } from 'tamagui';

import { PALETAS, type Paleta } from '@/constants/tema';

/** Colores de la marca + los nombres base que usan los componentes de Tamagui. */
const colores = (p: Paleta) => ({
  ...p,
  background: p.fondo,
  backgroundHover: p.suave,
  backgroundPress: p.suave,
  color: p.texto,
  borderColor: p.borde,
  placeholderColor: p.textoSuave,
});

export const tamaguiConfig = createTamagui({
  ...defaultConfig,
  themes: {
    light: { ...defaultConfig.themes.light, ...colores(PALETAS.claro) },
    dark: { ...defaultConfig.themes.dark, ...colores(PALETAS.oscuro) },
  },
});

export default tamaguiConfig;

export type Conf = typeof tamaguiConfig;

// Tipos de Tamagui con nuestros colores ($primario, $texto…)
declare module 'tamagui' {
  // eslint-disable-next-line @typescript-eslint/no-empty-object-type
  interface TamaguiCustomConfig extends Conf {}
}
