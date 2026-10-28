import type { ReactNode } from 'react';
import { XStack, YStack } from 'tamagui';

import Logo from './Logo';
import Pantalla from './Pantalla';
import { Subtitulo, Texto, Titulo } from './ui';

/** Marco de login y registro (mockups "Hola de nuevo" y "Crea tu cuenta"). Angosto también en tablets. */
export default function MarcoAcceso({ titulo, subtitulo, children }: { titulo: string; subtitulo: string; children: ReactNode }) {
  return (
    <Pantalla ancho="angosto" bordes={['top', 'bottom', 'left', 'right']}>
      <YStack gap={28} pt={8} $md={{ pt: 48 }}>
        <XStack items="center" gap={10}>
          <Logo tamano={40} />
          <Texto tam="lg" peso="fuerte">
            Kompás App
          </Texto>
        </XStack>
        <YStack gap={8}>
          <Titulo text="center">{titulo}</Titulo>
          <Subtitulo>{subtitulo}</Subtitulo>
        </YStack>
        {children}
      </YStack>
    </Pantalla>
  );
}

