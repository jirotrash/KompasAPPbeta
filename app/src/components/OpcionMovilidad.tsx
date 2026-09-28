import { XStack } from 'tamagui';

import { useTema } from '@/context/Tema';

import Icono, { type NombreIcono } from './Icono';
import { Texto } from './ui';

type Props = { texto: string; icono: NombreIcono; activo: boolean; onPress: () => void };

/** Tarjeta de medio de movilidad (Caminando, Transp. público…), de selección múltiple. */
export default function OpcionMovilidad({ texto, icono, activo, onPress }: Props) {
  const { paleta } = useTema();
  return (
    <XStack
      flex={1}
      minH={52}
      items="center"
      gap={10}
      px={14}
      py={12}
      rounded={14}
      borderWidth={1}
      borderColor={activo ? '$primario' : '$borde'}
      bg={activo ? '$suave' : '$tarjeta'}
      role="checkbox"
      aria-checked={activo}
      aria-label={texto}
      onPress={onPress}
      cursor="pointer"
      pressStyle={{ opacity: 0.75 }}
    >
      <Icono nombre={icono} color={activo ? paleta.primario : paleta.texto} tamano={20} />
      <Texto flex={1} numberOfLines={1} tam="sm" peso="semi" color={activo ? '$primario' : '$texto'}>
        {texto}
      </Texto>
    </XStack>
  );
}
