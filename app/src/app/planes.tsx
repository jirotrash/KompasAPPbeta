import { router } from 'expo-router';
import { useState } from 'react';
import { XStack, YStack } from 'tamagui';

import { AvisoSinInformacion } from '@/components/Avisos';
import { BotonSecundario } from '@/components/Botones';
import ExplicacionReglas from '@/components/ExplicacionReglas';
import Icono from '@/components/Icono';
import Pantalla from '@/components/Pantalla';
import TarjetaPlan from '@/components/TarjetaPlan';
import { Subtitulo, Tarjeta, Texto, Titulo } from '@/components/ui';
import { ESTADOS_PLAN } from '@/constants/catalogos';
import { useTema } from '@/context/Tema';
import { useUbicacion } from '@/context/Ubicacion';
import { useViaje } from '@/context/Viaje';
import { USA_MOCK } from '@/services/api';
import type { Plan } from '@/types/dominio';
import { recorridoDesdePlan } from '@/utils/recorrido';

/** "Tus planes": hasta 3 planes del sistema experto; al tocar uno se ve su recorrido en el Mapa. */
export default function Planes() {
  const { paleta } = useTema();
  const { posicion } = useUbicacion();
  const { peticion, respuesta, setRecorrido } = useViaje();
  const [verDescartados, setVerDescartados] = useState(false);

  if (!respuesta || !peticion) {
    return (
      <Pantalla bordes={['left', 'right']}>
        <YStack gap={16}>
          <AvisoSinInformacion mensaje="Todavía no has creado un plan." />
          <BotonSecundario texto="Ir al planificador" onPress={() => router.navigate('/planificar')} />
        </YStack>
      </Pantalla>
    );
  }

  const verEnMapa = (plan: Plan) => {
    setRecorrido(recorridoDesdePlan(plan, posicion, peticion.hora_salida));
    router.navigate('/mapa');
  };

  const descartados = respuesta.descartados ?? [];

  return (
    <Pantalla ancho="amplio" bordes={['left', 'right']}>
      <Titulo>Tus planes</Titulo>
      <Subtitulo mt={4}>Hemos trazado las mejores opciones para ti hoy</Subtitulo>

      <YStack mt={24} gap={16}>
        {respuesta.datos_suficientes === false && <AvisoSinInformacion mensaje={respuesta.mensaje ?? undefined} />}

        <XStack flexWrap="wrap" justify="space-between" rowGap={16}>
          {respuesta.planes.map((plan) => (
            <YStack key={plan.tipo} width="100%" $md={{ width: '49%' }} $xl={{ width: '32.5%' }}>
              <TarjetaPlan plan={plan} onPress={() => verEnMapa(plan)} />
            </YStack>
          ))}
        </XStack>

        {respuesta.planes.length > 0 && (
          <Texto tam="xs" suave>
            Toca un plan para ver el recorrido en el mapa. Costos y horas son estimados; el costo no incluye transporte.
          </Texto>
        )}
        {respuesta.aviso && respuesta.datos_suficientes !== false && (
          <Texto tam="xs" color="$aviso">
            ⚠ {respuesta.aviso}
          </Texto>
        )}

        {descartados.length > 0 && (
          <YStack gap={12}>
            <XStack
              minH={44}
              items="center"
              justify="space-between"
              role="button"
              aria-expanded={verDescartados}
              onPress={() => setVerDescartados((v) => !v)}
              cursor="pointer"
            >
              <Texto tam="lg" peso="fuerte">
                No recomendados ({descartados.length})
              </Texto>
              <YStack style={{ transform: [{ rotate: verDescartados ? '90deg' : '0deg' }] }}>
                <Icono nombre="derecha" color={paleta.textoSuave} tamano={20} />
              </YStack>
            </XStack>
            {verDescartados &&
              descartados.map((d, i) => (
                <Tarjeta key={`${d.tipo ?? d.lugar?._id}-${i}`} p={12} gap={8}>
                  <Texto peso="semi">{d.nombre ?? d.lugar?.nombre}</Texto>
                  {d.estado && (
                    <Texto tam="xs" peso="semi" color={d.estado === 'pendiente_verificacion' ? '$aviso' : '$peligro'}>
                      {ESTADOS_PLAN[d.estado]}
                    </Texto>
                  )}
                  {d.datos_faltantes?.slice(0, 3).map((f) => (
                    <Texto key={f} tam="xs" suave>
                      • {f}
                    </Texto>
                  ))}
                  <ExplicacionReglas reglas={d.reglas} titulo="Reglas que se aplicaron" tono="peligro" />
                </Tarjeta>
              ))}
          </YStack>
        )}

        {USA_MOCK && (
          <Texto tam="xs" suave>
            Modo demostración: el sistema experto se simula en la app; el definitivo corre en la API (Python).
          </Texto>
        )}
      </YStack>
    </Pantalla>
  );
}
