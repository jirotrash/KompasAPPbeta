import { Image } from 'expo-image';
import { XStack, YStack } from 'tamagui';

import { CATEGORIAS, iconoDeInteres } from '@/constants/catalogos';
import type { Coordenada } from '@/constants/zona';
import { useTema } from '@/context/Tema';
import type { Lugar } from '@/types/dominio';
import { desdeGeoJSON, distanciaKm, formatoKm, minutosCaminando } from '@/utils/geo';

import { FuenteDato } from './Avisos';
import Icono from './Icono';
import { Pildora, Texto } from './ui';

type Props = { lugar: Lugar; desde: Coordenada; onPress?: () => void };

/** Tarjeta de "Cerca de ti": foto, categoría, nombre, calificación con fuente y distancia. */
export default function TarjetaLugar({ lugar, desde, onPress }: Props) {
  const { paleta } = useTema();
  const km = distanciaKm(desde, desdeGeoJSON(lugar.ubicacion.coordinates));

  return (
    <XStack
      gap={14}
      p={12}
      rounded={20}
      bg="$tarjeta"
      borderWidth={1}
      borderColor="$borde"
      role="button"
      aria-label={`${lugar.nombre}. Ver cómo llegar`}
      onPress={onPress}
      cursor="pointer"
      pressStyle={{ opacity: 0.8 }}
      style={{ boxShadow: '0 1px 3px rgba(18,48,71,0.06)' }}
    >
      {/* Sin foto verificada se muestra el ícono de la categoría (no se usan fotos inventadas) */}
      <YStack width={92} height={92} rounded={14} overflow="hidden" bg="$suave" items="center" justify="center">
        {lugar.foto_url ? (
          <Image source={{ uri: lugar.foto_url }} style={{ width: '100%', height: '100%' }} contentFit="cover" />
        ) : (
          <Icono nombre={iconoDeInteres(lugar.interes)} color={paleta.primario} tamano={34} />
        )}
      </YStack>

      <YStack flex={1} justify="center" gap={4}>
        <XStack items="flex-start" justify="space-between" gap={8}>
          <Pildora py={2} px={8}>
            <Texto tam="xs" peso="medio" suave>
              {CATEGORIAS[lugar.categoria] ?? lugar.categoria}
            </Texto>
          </Pildora>
          {lugar.calificacion && (
            <XStack items="center" gap={3}>
              <Icono nombre="estrella" color={paleta.estrella} tamano={13} />
              <Texto tam="sm" peso="fuerte">
                {lugar.calificacion.valor.toFixed(1)}
              </Texto>
            </XStack>
          )}
        </XStack>
        <Texto numberOfLines={2} peso="fuerte">
          {lugar.nombre}
        </Texto>
        <XStack items="center" gap={4}>
          <Icono nombre="mapa" color={paleta.textoSuave} tamano={12} />
          <Texto tam="xs" suave>
            A {formatoKm(km)} • Caminando {minutosCaminando(km)} min
          </Texto>
        </XStack>
        {lugar.calificacion && <FuenteDato fuente={lugar.calificacion.fuente} fecha={lugar.calificacion.fecha} />}
      </YStack>
    </XStack>
  );
}
