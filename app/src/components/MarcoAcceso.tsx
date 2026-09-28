import { useState, type ReactNode } from 'react';
import { Separator, XStack, YStack } from 'tamagui';

import { MensajeInfo } from './Avisos';
import { BotonSecundario } from './Botones';
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

/** "o continúa con" + botones de Google y Apple. Todavía no hay inicio de sesión con terceros: se avisa. */
export function AccesoSocial() {
  const [aviso, setAviso] = useState('');
  const pendiente = (proveedor: string) =>
    setAviso(`El inicio de sesión con ${proveedor} todavía no está disponible. Usa tu correo por ahora.`);

  return (
    <YStack gap={16}>
      <XStack items="center" gap={12}>
        <Separator borderColor="$borde" />
        <Texto tam="sm" suave>
          o continúa con
        </Texto>
        <Separator borderColor="$borde" />
      </XStack>
      <XStack gap={12}>
        <BotonSecundario
          flex
          texto="Google"
          onPress={() => pendiente('Google')}
          prefijo={
            <Texto peso="fuerte" tam="lg" color="#4285F4">
              G
            </Texto>
          }
        />
        <BotonSecundario flex texto="Apple" icono="apple" onPress={() => pendiente('Apple')} />
      </XStack>
      <MensajeInfo>{aviso}</MensajeInfo>
    </YStack>
  );
}
