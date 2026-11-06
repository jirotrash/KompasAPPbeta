import { router } from 'expo-router';
import { XStack, YStack } from 'tamagui';

import { BotonSecundario } from '@/components/Botones';
import Icono from '@/components/Icono';
import { Pildora, Tarjeta, Texto } from '@/components/ui';
import { useTema } from '@/context/Tema';
import type { DestinoProbable, RespuestaDestinosProbables } from '@/services/api';

const porcentaje = (p: number) => `${Math.round(p * 100)}%`;
const destinoDe = (d: DestinoProbable) => d.ultima_parada ?? d.nombre;

/** Destino que el usuario suele tomar a esta hora (GET /api/ia/destinos-probables). "Cómo llego" lo busca. */
export default function TarjetaPrediccion({ datos }: { datos: RespuestaDestinosProbables }) {
  const { paleta } = useTema();
  const [principal, ...otros] = datos.destinos;

  if (datos.estado !== 'ok' || !principal) {
    return (
      <Tarjeta p={14} gap={4}>
        <Texto tam="sm" peso="semi">
          Aprendiendo tus hábitos
        </Texto>
        <Texto tam="xs" suave>
          {datos.explicacion}
        </Texto>
      </Tarjeta>
    );
  }

  return (
    <Tarjeta destacada p={14} gap={8}>
      <XStack items="center" gap={10}>
        <YStack width={36} height={36} rounded={12} bg="$suave" items="center" justify="center">
          <Icono nombre="ruta" color={paleta.primario} tamano={18} />
        </YStack>
        <YStack flex={1}>
          <Texto tam="xs" suave>
            A esta hora sueles ir a
          </Texto>
          <Texto peso="semi" numberOfLines={2}>
            {destinoDe(principal)}
          </Texto>
        </YStack>
        <Texto tam="sm" peso="fuerte" acento aria-label={`Probabilidad estimada ${porcentaje(principal.probabilidad)}`}>
          {porcentaje(principal.probabilidad)}
        </Texto>
      </XStack>

      <XStack gap={6} flexWrap="wrap">
        <Pildora tono="suave">
          <Texto tam="xs">{principal.nombre}</Texto>
        </Pildora>
        <Pildora>
          <Texto tam="xs">Sueles salir ~{principal.hora_habitual}</Texto>
        </Pildora>
        <Pildora>
          <Texto tam="xs">{principal.viajes} viajes</Texto>
        </Pildora>
      </XStack>

      {otros.length > 0 && (
        <Texto tam="xs" suave numberOfLines={2}>
          También: {otros.map((d) => `${destinoDe(d)} (${porcentaje(d.probabilidad)})`).join(' · ')}
        </Texto>
      )}

      <Texto tam="xs" suave>
        {datos.aviso}
      </Texto>

      <BotonSecundario
        texto="¿Cómo llego?"
        onPress={() => router.push({ pathname: '/buscar', params: { q: destinoDe(principal) } })}
      />
    </Tarjeta>
  );
}
