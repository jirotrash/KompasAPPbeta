import { useState } from 'react';
import { XStack, YStack } from 'tamagui';

import { describirRegla } from '@/constants/catalogos';
import { useTema } from '@/context/Tema';
import type { Regla } from '@/types/dominio';

import Icono from './Icono';
import { Pildora, Texto } from './ui';

type Props = { reglas?: Regla[]; titulo?: string; tono?: 'ok' | 'peligro' };

/** Reglas del sistema experto que explican por qué se recomienda (o descarta) algo. Se despliega al tocar. */
export default function ExplicacionReglas({ reglas, titulo = '¿Por qué?', tono = 'ok' }: Props) {
  const { paleta } = useTema();
  const [abierto, setAbierto] = useState(false);
  if (!reglas?.length) return null;
  const lista = reglas.map(describirRegla);

  return (
    <YStack bg="$fondo" rounded={14}>
      <XStack
        minH={44}
        items="center"
        gap={8}
        px={12}
        role="button"
        aria-expanded={abierto}
        onPress={() => setAbierto((v) => !v)}
        cursor="pointer"
        pressStyle={{ opacity: 0.7 }}
      >
        <YStack style={{ transform: [{ rotate: abierto ? '90deg' : '0deg' }] }}>
          <Icono nombre="derecha" color={paleta.textoSuave} tamano={16} />
        </YStack>
        <Texto tam="sm" peso="semi">
          {titulo} ({lista.length} {lista.length === 1 ? 'regla' : 'reglas'})
        </Texto>
      </XStack>
      {abierto && (
        <YStack gap={8} px={12} pb={12}>
          {lista.map((r) => (
            <XStack key={r.id + r.descripcion} gap={8}>
              <Pildora tono={tono === 'ok' ? 'suave' : undefined} bg={tono === 'ok' ? '$suave' : '$peligroFondo'} rounded={6} px={6} py={1}>
                <Texto tam="xs" peso="fuerte" color={tono === 'ok' ? '$primario' : '$peligro'}>
                  {r.id}
                </Texto>
              </Pildora>
              <Texto flex={1} tam="xs" suave lineHeight={18}>
                {r.descripcion}
              </Texto>
            </XStack>
          ))}
        </YStack>
      )}
    </YStack>
  );
}
