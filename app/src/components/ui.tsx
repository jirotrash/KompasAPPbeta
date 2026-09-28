// Piezas base de la interfaz hechas con styled() de Tamagui. Usan los colores del tema ($primario, $texto…)
// y los breakpoints de Tamagui ($md = 768 px o más) para adaptarse a tablets.
import { styled, Text, XStack, YStack } from 'tamagui';

export const Titulo = styled(Text, {
  fontFamily: '$heading',
  fontSize: 28,
  lineHeight: 34,
  fontWeight: '800',
  letterSpacing: -0.5,
  color: '$texto',
  $md: { fontSize: 32, lineHeight: 40 },
});

export const Subtitulo = styled(Text, {
  fontFamily: '$body',
  fontSize: 15,
  lineHeight: 21,
  color: '$textoSuave',
});

export const Texto = styled(Text, {
  fontFamily: '$body',
  color: '$texto',
  variants: {
    tam: {
      xs: { fontSize: 11, lineHeight: 15 },
      sm: { fontSize: 13, lineHeight: 18 },
      md: { fontSize: 15, lineHeight: 21 },
      lg: { fontSize: 18, lineHeight: 24 },
      xl: { fontSize: 20, lineHeight: 26 },
    },
    peso: {
      normal: { fontWeight: '400' },
      medio: { fontWeight: '500' },
      semi: { fontWeight: '600' },
      fuerte: { fontWeight: '700' },
    },
    suave: { true: { color: '$textoSuave' } },
    acento: { true: { color: '$primario' } },
  } as const,
  defaultVariants: { tam: 'md', peso: 'normal' },
});

export const Tarjeta = styled(YStack, {
  bg: '$tarjeta',
  rounded: 20,
  borderWidth: 1,
  borderColor: '$borde',
  p: 16,
  gap: 12,
  variants: {
    destacada: { true: { borderWidth: 2, borderColor: '$primario' } },
  } as const,
});

/** Caja gris clara dentro de tarjetas (explicaciones, tramos). */
export const Recuadro = styled(YStack, {
  bg: '$fondo',
  rounded: 14,
  p: 12,
  gap: 4,
});

/** Píldora pequeña (categoría, "Mejor opción", minutos). */
export const Pildora = styled(XStack, {
  self: 'flex-start',
  items: 'center',
  gap: 4,
  rounded: 999,
  px: 10,
  py: 4,
  bg: '$fondo',
  variants: {
    tono: {
      neutro: { bg: '$fondo' },
      primario: { bg: '$primario' },
      suave: { bg: '$suave' },
      aviso: { bg: '$avisoFondo' },
    },
  } as const,
});

export const Fila = styled(XStack, { items: 'center', gap: 8 });
