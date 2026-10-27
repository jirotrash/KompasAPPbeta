import { router, useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { XStack, YStack } from 'tamagui';

import { AvisoSinInformacion, Cargando, EtiquetaEjemplo, MensajeError } from '@/components/Avisos';
import { BotonPrimario } from '@/components/Botones';
import Icono from '@/components/Icono';
import Pantalla from '@/components/Pantalla';
import { Subtitulo, Texto, Titulo } from '@/components/ui';
import { useTema } from '@/context/Tema';
import { crearConversacion, estadoAsistente, listarConversaciones, USA_MOCK } from '@/services/api';
import type { EstadoAsistente, ResumenConversacion } from '@/types/dominio';
import { formatoFecha } from '@/utils/geo';

/** Conversaciones con el asistente (se guardan en la API) y botón para empezar una nueva. */
export default function ListaConversaciones() {
  const { paleta } = useTema();
  const [lista, setLista] = useState<ResumenConversacion[] | null>(null);
  const [estado, setEstado] = useState<EstadoAsistente | null>(null);
  const [error, setError] = useState('');
  const [creando, setCreando] = useState(false);

  // Se recarga cada vez que se vuelve a la pestaña (p. ej. después de borrar una conversación)
  useFocusEffect(
    useCallback(() => {
      let activo = true;
      listarConversaciones()
        .then((l) => activo && setLista(l))
        .catch((e: unknown) => activo && setError(e instanceof Error ? e.message : 'No se pudieron cargar las conversaciones.'));
      estadoAsistente()
        .then((e) => activo && setEstado(e))
        .catch(() => activo && setEstado({ disponible: false, modelo: '' }));
      return () => {
        activo = false;
      };
    }, []),
  );

  const nueva = async () => {
    setCreando(true);
    setError('');
    try {
      const c = await crearConversacion();
      router.push({ pathname: '/asistente/[id]', params: { id: c.id } });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo crear la conversación.');
    } finally {
      setCreando(false);
    }
  };

  return (
    <Pantalla>
      <Titulo>Asistente</Titulo>
      <Subtitulo mt={4}>Pregunta cómo llegar, busca lugares o arma una salida en Toluca, Lerma y San Mateo Atenco.</Subtitulo>

      <YStack mt={20} gap={12}>
        {USA_MOCK && <EtiquetaEjemplo />}
        {estado && !estado.disponible && <AvisoSinInformacion mensaje="El asistente no está disponible en este momento." />}
        <BotonPrimario texto="Nueva conversación" icono="mas" onPress={nueva} cargando={creando} />
        <MensajeError>{error}</MensajeError>

        {lista === null && !error && <Cargando texto="Cargando conversaciones…" />}
        {lista?.length === 0 && (
          <Texto tam="sm" suave>
            Todavía no tienes conversaciones.
          </Texto>
        )}
        {lista?.map((c) => (
          <XStack
            key={c.id}
            minH={64}
            items="center"
            gap={12}
            p={14}
            rounded={16}
            borderWidth={1}
            borderColor="$borde"
            bg="$tarjeta"
            role="button"
            aria-label={c.titulo ?? 'Conversación'}
            onPress={() => router.push({ pathname: '/asistente/[id]', params: { id: c.id } })}
            cursor="pointer"
            pressStyle={{ bg: '$suave' }}
          >
            <YStack width={40} height={40} rounded={999} bg="$suave" items="center" justify="center">
              <Icono nombre="chat" color={paleta.primario} tamano={20} />
            </YStack>
            <YStack flex={1} gap={2}>
              <Texto numberOfLines={1} peso="semi">
                {c.titulo ?? 'Conversación nueva'}
              </Texto>
              {!!c.ultimo_mensaje && (
                <Texto numberOfLines={1} tam="sm" suave>
                  {c.ultimo_mensaje}
                </Texto>
              )}
            </YStack>
            <Texto tam="xs" suave>
              {formatoFecha(c.fecha)}
            </Texto>
          </XStack>
        ))}
      </YStack>
    </Pantalla>
  );
}
