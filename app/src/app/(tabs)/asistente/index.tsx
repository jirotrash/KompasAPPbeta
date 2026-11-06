import { useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { XStack, YStack } from 'tamagui';

import { AvisoSinInformacion, Cargando, MensajeError, TituloSeccion } from '@/components/Avisos';
import { ChipGroup } from '@/components/Chips';
import Pantalla from '@/components/Pantalla';
import TarjetaPrediccion from '@/components/TarjetaPrediccion';
import { Recuadro, Subtitulo, Tarjeta, Texto, Titulo } from '@/components/ui';
import { destinosProbables, type MisHabitos, misHabitos, type RespuestaDestinosProbables, USA_MOCK } from '@/services/api';

type Momento = 'ahora' | 7 | 15 | 20;
const MOMENTOS: { valor: Momento; texto: string }[] = [
  { valor: 'ahora', texto: 'Ahora' },
  { valor: 7, texto: 'Mañana · 7:00' },
  { valor: 15, texto: 'Tarde · 15:00' },
  { valor: 20, texto: 'Noche · 20:00' },
];
const FRANJAS: Record<string, string> = { madrugada: 'Madrugada', manana: 'Mañana', tarde: 'Tarde', noche: 'Noche' };
const METODOS: Record<string, string> = { frecuencia_franja: 'Frecuencia por franja horaria', knn: 'Modelo KNN (vecinos más cercanos)' };

const porcentaje = (p: number) => `${Math.round(p * 100)}%`;

/** Barra horizontal con el conteo (solo tokens del tema: $suave de fondo, $primario de relleno). */
function Barra({ etiqueta, valor, maximo }: { etiqueta: string; valor: number; maximo: number }) {
  return (
    <YStack gap={4} aria-label={`${etiqueta}: ${valor} viajes`}>
      <XStack justify="space-between">
        <Texto tam="sm">{etiqueta}</Texto>
        <Texto tam="sm" peso="semi">
          {valor}
        </Texto>
      </XStack>
      <YStack height={8} rounded={999} bg="$suave" overflow="hidden">
        <YStack height={8} rounded={999} bg="$primario" width={`${Math.max(4, (valor / maximo) * 100)}%`} />
      </YStack>
    </YStack>
  );
}

/**
 * Asistente con machine learning: aprende de los recorridos que el usuario inicia (historial_rutas)
 * y le dice a dónde suele ir a cada hora. Sustituye al chat con Ollama.
 */
export default function Asistente() {
  const [momento, setMomento] = useState<Momento>('ahora');
  const [prediccion, setPrediccion] = useState<RespuestaDestinosProbables | null>(null);
  const [habitos, setHabitos] = useState<MisHabitos | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');

  // Se recarga al volver a la pestaña: el usuario pudo iniciar un recorrido nuevo
  useFocusEffect(
    useCallback(() => {
      let activo = true;
      setCargando(true);
      setError('');
      const ahora = new Date();
      Promise.all([destinosProbables(ahora, momento === 'ahora' ? ahora.getHours() : momento), misHabitos()])
        .then(([p, h]) => {
          if (!activo) return;
          setPrediccion(p);
          setHabitos(h);
        })
        .catch((e: unknown) => activo && setError(e instanceof Error ? e.message : 'No se pudieron cargar tus hábitos.'))
        .finally(() => activo && setCargando(false));
      return () => {
        activo = false;
      };
    }, [momento]),
  );

  const maxFranja = Math.max(1, ...Object.values(habitos?.por_franja ?? {}));
  const maxRuta = Math.max(1, ...(habitos?.rutas_frecuentes ?? []).map((r) => r.viajes));

  return (
    <Pantalla>
      <Titulo>Asistente</Titulo>
      <Subtitulo mt={4}>Aprende de tus recorridos y te dice a dónde sueles ir a cada hora.</Subtitulo>

      <YStack mt={20} gap={16}>
        {USA_MOCK && <AvisoSinInformacion mensaje="En modo demostración no hay historial real: el asistente aprende de los recorridos que guardas con la API." />}
        <MensajeError>{error}</MensajeError>

        <YStack gap={8}>
          <Texto peso="semi">¿Para qué hora?</Texto>
          <ChipGroup opciones={MOMENTOS} valor={momento} onCambiar={setMomento} />
        </YStack>

        {cargando && <Cargando texto="Analizando tus recorridos…" />}
        {!cargando && prediccion && <TarjetaPrediccion datos={prediccion} />}

        {!cargando && prediccion?.estado === 'ok' && (
          <Tarjeta p={14} gap={6}>
            <Texto peso="semi">Cómo lo calculé</Texto>
            <Texto tam="sm" suave>
              {prediccion.explicacion}
            </Texto>
            <XStack gap={8} flexWrap="wrap">
              <Recuadro flex={1} minW={140}>
                <Texto tam="xs" suave>
                  Método
                </Texto>
                <Texto tam="sm" peso="semi">
                  {METODOS[prediccion.metodo ?? ''] ?? '—'}
                </Texto>
              </Recuadro>
              {prediccion.exactitud_validacion != null && prediccion.exactitud_baseline != null && (
                <Recuadro flex={1} minW={140}>
                  <Texto tam="xs" suave>
                    Aciertos en validación
                  </Texto>
                  <Texto tam="sm" peso="semi">
                    {porcentaje(prediccion.exactitud_validacion)} · la opción simple, {porcentaje(prediccion.exactitud_baseline)}
                  </Texto>
                </Recuadro>
              )}
            </XStack>
          </Tarjeta>
        )}

        {!cargando && habitos && habitos.total_viajes > 0 && (
          <Tarjeta p={14} gap={14}>
            <TituloSeccion titulo="Tus hábitos" derecha={`${habitos.total_viajes} recorridos`} />

            <YStack gap={10}>
              <Texto tam="sm" peso="semi">
                Rutas que más usas
              </Texto>
              {habitos.rutas_frecuentes.map((r) => (
                <Barra key={r.id_ruta} etiqueta={r.ultima_parada ? `${r.nombre} → ${r.ultima_parada}` : r.nombre} valor={r.viajes} maximo={maxRuta} />
              ))}
            </YStack>

            <YStack gap={10}>
              <Texto tam="sm" peso="semi">
                ¿A qué hora sales?
              </Texto>
              {Object.entries(habitos.por_franja).map(([franja, n]) => (
                <Barra key={franja} etiqueta={FRANJAS[franja] ?? franja} valor={n} maximo={maxFranja} />
              ))}
            </YStack>

            <YStack gap={6}>
              <Texto tam="sm" peso="semi">
                Cómo te mueves
              </Texto>
              <Texto tam="sm" suave>
                {Object.entries(habitos.transportes)
                  .map(([t, n]) => `${t}: ${n}`)
                  .join(' · ')}
              </Texto>
            </YStack>
          </Tarjeta>
        )}

        <Recuadro>
          <Texto tam="xs" suave>
            Cada vez que eliges una ruta en “Compara tu transporte”, Kompás guarda cuál tomaste y a qué hora. Con 5 recorridos el
            asistente empieza a sugerir; con 20 o más usa un modelo de machine learning que se pone a prueba solo. Son estimaciones
            de tus hábitos, no datos verificados.
          </Texto>
        </Recuadro>
      </YStack>
    </Pantalla>
  );
}
