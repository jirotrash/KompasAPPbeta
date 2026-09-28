import { router } from 'expo-router';
import { useState } from 'react';
import { XStack, YStack } from 'tamagui';

import { MensajeError, TituloSeccion } from '@/components/Avisos';
import { BotonPrimario } from '@/components/Botones';
import { ChipGroup } from '@/components/Chips';
import OpcionMovilidad from '@/components/OpcionMovilidad';
import Pantalla from '@/components/Pantalla';
import RangoPresupuesto from '@/components/RangoPresupuesto';
import { Subtitulo, Texto, Titulo } from '@/components/ui';
import { CONTEXTOS, INTERESES, MOVILIDADES, TIEMPOS } from '@/constants/catalogos';
import { useUbicacion } from '@/context/Ubicacion';
import { useViaje } from '@/context/Viaje';
import { generarPlanes } from '@/services/api';
import type { Contexto, Interes, Movilidad, PeticionPlan } from '@/types/dominio';
import { diaDeHoy, horaActual } from '@/utils/geo';

const PRESUPUESTO = { min: 0, max: 2000, paso: 50 };
const pesos = (n: number) => `$${n.toLocaleString('es-MX')}`;

export default function Planificar() {
  const { posicion, estado } = useUbicacion();
  const { guardarPlanes } = useViaje();
  const [contexto, setContexto] = useState<Contexto>('pareja');
  const [presupuesto, setPresupuesto] = useState<[number, number]>([200, 1500]);
  const [horas, setHoras] = useState(4);
  const [intereses, setIntereses] = useState<Interes[]>(['comer', 'cafe', 'entretenimiento']);
  const [movilidad, setMovilidad] = useState<Movilidad[]>(['caminando', 'taxi_app']);
  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);

  const alternarMovilidad = (m: Movilidad) =>
    setMovilidad((lista) => (lista.includes(m) ? lista.filter((x) => x !== m) : [...lista, m]));

  async function crearPlan() {
    if (!movilidad.length) return setError('Elige al menos un medio de movilidad.');
    setError('');
    setEnviando(true);
    const peticion: PeticionPlan = {
      contexto,
      presupuesto: { min: presupuesto[0], max: presupuesto[1] },
      tiempo_horas: horas,
      intereses,
      movilidad,
      origen: { lat: posicion.lat, lng: posicion.lng },
      hora_salida: horaActual(),
      dia: diaDeHoy(),
    };
    try {
      guardarPlanes(peticion, await generarPlanes(peticion));
      router.push('/planes');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo crear el plan.');
    } finally {
      setEnviando(false);
    }
  }

  const tiempoTexto = horas === 10 ? 'Todo el día' : `${horas} horas`;

  return (
    <Pantalla>
      <Titulo>Planifica tu salida</Titulo>
      <Subtitulo mt={4}>Configura tu salida para un plan a la medida</Subtitulo>

      <YStack mt={28} gap={28}>
        <YStack>
          <TituloSeccion titulo="¿Con quién vas?" />
          <ChipGroup opciones={CONTEXTOS} valor={contexto} onCambiar={setContexto} estilo="relleno" estirar />
        </YStack>

        <YStack>
          <TituloSeccion titulo="Presupuesto estimado" derecha={`${pesos(presupuesto[0])} – ${pesos(presupuesto[1])} MXN`} />
          <RangoPresupuesto {...PRESUPUESTO} valor={presupuesto} onCambiar={setPresupuesto} />
        </YStack>

        <YStack>
          <TituloSeccion titulo="Tiempo disponible" derecha={tiempoTexto} />
          <ChipGroup
            opciones={TIEMPOS.map((t) => ({ valor: t.horas, texto: t.texto }))}
            valor={horas}
            onCambiar={setHoras}
            estilo="relleno"
            estirar
          />
        </YStack>

        <YStack>
          <TituloSeccion titulo="¿Qué te interesa hoy?" />
          <ChipGroup multiple opciones={INTERESES.map(({ icono: _i, ...o }) => o)} valor={intereses} onCambiar={setIntereses} estilo="suave" />
        </YStack>

        <YStack>
          <TituloSeccion titulo="Medio de movilidad" />
          <YStack gap={12}>
            {[MOVILIDADES.slice(0, 2), MOVILIDADES.slice(2)].map((fila, i) => (
              <XStack key={i} gap={12}>
                {fila.map((m) => (
                  <OpcionMovilidad
                    key={m.valor}
                    texto={m.texto}
                    icono={m.icono}
                    activo={movilidad.includes(m.valor)}
                    onPress={() => alternarMovilidad(m.valor)}
                  />
                ))}
              </XStack>
            ))}
          </YStack>
        </YStack>

        <YStack gap={12}>
          <Texto tam="xs" suave>
            Salida: ahora ({horaActual()}) desde {estado === 'gps' ? 'tu ubicación' : `${posicion.nombre} (referencia)`}.
          </Texto>
          <MensajeError>{error}</MensajeError>
          <BotonPrimario texto="Crear mi plan" onPress={crearPlan} cargando={enviando} />
        </YStack>
      </YStack>
    </Pantalla>
  );
}
