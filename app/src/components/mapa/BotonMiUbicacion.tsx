import { YStack } from 'tamagui';

import { useTema } from '@/context/Tema';

import Icono from '../Icono';

/** Botón flotante "Mi ubicación", encima de los botones de zoom (abajo a la derecha). */
export default function BotonMiUbicacion({ onPress, abajo = 0 }: { onPress: () => void; abajo?: number }) {
  const { paleta } = useTema();
  return (
    <YStack
      position="absolute"
      r={10}
      b={104 + abajo}
      width={40}
      height={40}
      rounded={10}
      bg="$tarjeta"
      items="center"
      justify="center"
      role="button"
      aria-label="Ir a mi ubicación"
      onPress={onPress}
      cursor="pointer"
      pressStyle={{ opacity: 0.7 }}
      style={{ boxShadow: '0 1px 5px rgba(0,0,0,0.3)' }}
    >
      <Icono nombre="miUbicacion" color={paleta.texto} tamano={20} />
    </YStack>
  );
}
