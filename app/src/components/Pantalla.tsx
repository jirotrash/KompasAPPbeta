import type { ReactNode } from 'react';
import { KeyboardAvoidingView, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ScrollView, YStack } from 'tamagui';

import { ANCHO_MAXIMO } from '@/constants/tema';
import { useTema } from '@/context/Tema';

type Props = {
  children: ReactNode;
  /** false para pantallas que manejan su propio scroll. */
  scroll?: boolean;
  /** "amplio" deja usar todo el ancho en tablets (listas en columnas). */
  ancho?: 'normal' | 'amplio' | 'angosto';
  /** Bordes con margen seguro; las pantallas con encabezado de navegación no necesitan el de arriba. */
  bordes?: ('top' | 'bottom' | 'left' | 'right')[];
};

const ANCHOS = { angosto: 460, normal: ANCHO_MAXIMO, amplio: 1200 };

/** Marco estándar: margen seguro (notch), fondo del tema, scroll y ancho máximo en tablets. */
export default function Pantalla({ children, scroll = true, ancho = 'normal', bordes = ['top', 'left', 'right'] }: Props) {
  const { paleta } = useTema();
  const contenido = (
    <YStack width="100%" self="center" maxW={ANCHOS[ancho]} px={20} pt={12} pb={32} $md={{ px: 32, pt: 24 }}>
      {children}
    </YStack>
  );

  return (
    <SafeAreaView edges={bordes} style={{ flex: 1, backgroundColor: paleta.fondo }}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        {scroll ? (
          <ScrollView keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
            {contenido}
          </ScrollView>
        ) : (
          contenido
        )}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
