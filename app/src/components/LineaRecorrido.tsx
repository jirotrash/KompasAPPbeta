import { Fragment } from 'react';
import { XStack, YStack } from 'tamagui';

import { iconoDeInteres, MODOS } from '@/constants/catalogos';
import { useTema } from '@/context/Tema';
import type { Recorrido, Tramo } from '@/types/dominio';
import { formatoKm, formatoMinutos } from '@/utils/geo';

import Icono from './Icono';
import { Recuadro, Texto } from './ui';

/** Descripción de un traslado: caminando, o autobús con línea, dónde subir y dónde bajar. */
function PasoTramo({ tramo }: { tramo: Tramo }) {
  const { paleta } = useTema();
  const modo = MODOS[tramo.modo];
  return (
    <XStack gap={12} py={6}>
      <YStack width={24} items="center">
        {/* Línea tenue a pie; sólida en vehículo */}
        <YStack width={3} flex={1} rounded={999} bg="$primario" opacity={tramo.modo === 'pie' ? 0.35 : 1} />
      </YStack>
      <Recuadro flex={1}>
        <XStack items="center" gap={8}>
          <Icono nombre={modo.icono} color={paleta.primario} tamano={16} />
          <Texto flex={1} tam="sm" peso="semi">
            {tramo.modo === 'autobus' ? (tramo.linea ?? 'Autobús') : modo.texto}
          </Texto>
          <Texto tam="xs" suave>
            {formatoMinutos(tramo.duracion_min)} aprox.
            {tramo.distancia_km ? ` · ${formatoKm(tramo.distancia_km)}` : ''}
          </Texto>
        </XStack>
        {tramo.modo === 'autobus' && (
          <>
            {tramo.sentido && (
              <Texto tam="xs" suave>
                Sentido {tramo.sentido}
              </Texto>
            )}
            <Texto tam="xs">
              <Texto tam="xs" peso="fuerte" color="$ok">
                ↑ Sube en:{' '}
              </Texto>
              {tramo.abordaje?.nombre ?? '—'}
            </Texto>
            <Texto tam="xs">
              <Texto tam="xs" peso="fuerte" color="$aviso">
                ↓ Baja en:{' '}
              </Texto>
              {tramo.descenso?.nombre ?? '—'}
            </Texto>
            <Texto tam="xs" suave>
              Incluye caminata a la parada y espera estimada.
            </Texto>
          </>
        )}
        {tramo.aviso && (
          <Texto tam="xs" color="$aviso">
            ⚠ {tramo.aviso}
          </Texto>
        )}
      </Recuadro>
    </XStack>
  );
}

/** "Detalles del recorrido": puntos con hora estimada y, entre ellos, cómo moverse. */
export default function LineaRecorrido({ recorrido }: { recorrido: Recorrido }) {
  const { paleta } = useTema();
  // Número de cada lugar (1, 2, 3…) sin contar origen ni paradas de autobús
  const numeros = recorrido.puntos.map((_, i) => recorrido.puntos.slice(0, i + 1).filter((x) => x.tipo === 'lugar').length);
  return (
    <YStack>
      {recorrido.puntos.map((p, i) => {
        return (
          <Fragment key={`${p.nombre}-${i}`}>
            <XStack items="center" gap={12}>
              <YStack width={24} items="center">
                <YStack
                  width={20}
                  height={20}
                  rounded={999}
                  borderWidth={3}
                  borderColor="$primario"
                  bg={p.tipo === 'origen' ? '$primario' : '$tarjeta'}
                />
              </YStack>
              <YStack flex={1}>
                <Texto numberOfLines={2} peso="fuerte">
                  {p.tipo === 'lugar' ? `${numeros[i]}. ` : ''}
                  {p.nombre}
                </Texto>
                {p.hora && (
                  <Texto tam="xs" suave>
                    {p.tipo === 'origen' ? 'Salida' : 'Llegada estimada'}: {p.hora}
                  </Texto>
                )}
              </YStack>
              {p.tipo === 'lugar' && <Icono nombre={iconoDeInteres(p.interes)} color={paleta.textoSuave} tamano={18} />}
              {p.tipo === 'parada' && <Icono nombre="autobus" color={paleta.textoSuave} tamano={18} />}
              {p.tipo === 'destino' && <Icono nombre="bandera" color={paleta.textoSuave} tamano={18} />}
            </XStack>
            {recorrido.tramos[i] && <PasoTramo tramo={recorrido.tramos[i]} />}
          </Fragment>
        );
      })}
    </YStack>
  );
}
