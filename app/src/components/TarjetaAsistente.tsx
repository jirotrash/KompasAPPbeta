import { router } from 'expo-router';
import { XStack, YStack } from 'tamagui';

import { EtiquetaEjemplo } from '@/components/Avisos';
import { BotonSecundario } from '@/components/Botones';
import Icono from '@/components/Icono';
import { Tarjeta, Texto } from '@/components/ui';
import { useTema } from '@/context/Tema';
import { useUbicacion } from '@/context/Ubicacion';
import { useViaje } from '@/context/Viaje';
import type { Plan, TarjetaAsistente as Datos } from '@/types/dominio';
import { aHora, aMinutosDelDia, formatoMinutos, horaActual } from '@/utils/geo';
import { recorridoDesdeAlternativa, recorridoDesdePlan } from '@/utils/recorrido';

/** Hora de salida de un plan: la llegada a la primera parada menos el primer traslado. */
const salidaDe = (plan: Plan) => {
  const llegada = plan.paradas[0]?.llegada_estimada;
  const traslado = plan.tramos?.[0]?.duracion_min;
  return llegada && traslado != null ? aHora(aMinutosDelDia(llegada) - traslado) : horaActual();
};

/** Ruta o plan que regresó el asistente. "Ver ruta" / "Ver plan" abren el recorrido en el Mapa. */
export default function TarjetaAsistente({ tarjeta }: { tarjeta: Datos }) {
  const { paleta } = useTema();
  const { posicion } = useUbicacion();
  const { setRecorrido } = useViaje();
  const esRuta = tarjeta.tipo === 'ruta';
  const alternativa = tarjeta.alternativa;
  const total = alternativa ? (alternativa.tiempos.caminata ?? 0) + (alternativa.tiempos.espera ?? 0) + (alternativa.tiempos.trayecto ?? 0) : null;

  const verRuta = () => {
    if (alternativa && tarjeta.origen && tarjeta.destino) {
      setRecorrido(recorridoDesdeAlternativa(alternativa, tarjeta.origen, tarjeta.destino, horaActual()));
      router.navigate('/mapa');
    } else {
      // Conversación guardada: no se guardan coordenadas, se busca de nuevo el destino
      router.push({ pathname: '/buscar', params: { q: tarjeta.destino_texto ?? '' } });
    }
  };

  const verPlan = () => {
    if (!tarjeta.plan) return;
    setRecorrido(recorridoDesdePlan(tarjeta.plan, posicion, salidaDe(tarjeta.plan)));
    router.navigate('/mapa');
  };

  return (
    <Tarjeta p={14} gap={8} maxW={420}>
      <XStack items="center" gap={10}>
        <YStack width={36} height={36} rounded={12} bg="$suave" items="center" justify="center">
          <Icono nombre={esRuta ? 'ruta' : 'planificar'} color={paleta.primario} tamano={18} />
        </YStack>
        <YStack flex={1}>
          <Texto peso="semi" numberOfLines={2}>
            {tarjeta.titulo}
          </Texto>
          {!!tarjeta.subtitulo && (
            <Texto tam="xs" suave numberOfLines={2}>
              {tarjeta.subtitulo}
            </Texto>
          )}
        </YStack>
        {total != null && (
          <Texto tam="sm" peso="fuerte" acento>
            {formatoMinutos(total)}
          </Texto>
        )}
      </XStack>
      {alternativa?.modo === 'autobus' && (
        <YStack gap={2}>
          <Texto tam="xs">
            <Texto tam="xs" peso="fuerte" color="$ok">
              ↑ Sube en:{' '}
            </Texto>
            {alternativa.parada_subida?.nombre ?? alternativa.abordaje?.nombre}
          </Texto>
          <Texto tam="xs">
            <Texto tam="xs" peso="fuerte" color="$aviso">
              ↓ Baja en:{' '}
            </Texto>
            {alternativa.parada_bajada?.nombre ?? alternativa.descenso?.nombre}
          </Texto>
        </YStack>
      )}
      {tarjeta.ejemplo && <EtiquetaEjemplo />}
      {esRuta ? (
        <BotonSecundario texto="Ver ruta" icono="mapa" onPress={verRuta} />
      ) : tarjeta.plan ? (
        <BotonSecundario texto="Ver plan" icono="mapa" onPress={verPlan} />
      ) : (
        <Texto tam="xs" suave>
          El plan quedó guardado en tu cuenta.
        </Texto>
      )}
    </Tarjeta>
  );
}
