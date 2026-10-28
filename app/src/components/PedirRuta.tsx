import { useState } from 'react';
import { YStack } from 'tamagui';

import type { Coordenada } from '@/constants/zona';
import { pedirRuta } from '@/services/api';

import { MensajeError, MensajeInfo } from './Avisos';
import { BotonSecundario } from './Botones';
import CampoTexto from './CampoTexto';
import { Tarjeta, Texto } from './ui';

/** Va debajo del aviso "sin camión": la persona pide al equipo que agregue la ruta (se atiende en el panel web). */
export default function PedirRuta({ origen, destino }: { origen: Coordenada; destino: Coordenada }) {
  const [comentario, setComentario] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [enviada, setEnviada] = useState(false);
  const [error, setError] = useState('');

  async function pedir() {
    setEnviando(true);
    setError('');
    try {
      await pedirRuta(origen, destino, comentario);
      setEnviada(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo enviar la solicitud.');
    } finally {
      setEnviando(false);
    }
  }

  if (enviada) {
    return <MensajeInfo>Gracias: le pedimos al equipo de Kompás que revise esta ruta. Aparecerá aquí cuando la demos de alta.</MensajeInfo>;
  }

  return (
    <Tarjeta>
      <YStack gap={12}>
        <Texto peso="fuerte">¿Hace falta esta ruta?</Texto>
        <Texto tam="sm" suave>
          Pídela y el equipo de Kompás la revisa. Si conoces un camión o combi que haga este viaje, cuéntanos cuál.
        </Texto>
        <CampoTexto
          etiqueta="Comentario (opcional)"
          value={comentario}
          onChangeText={setComentario}
          maxLength={500}
          placeholder="Ej. La combi que pasa por Tollocan"
        />
        <MensajeError>{error}</MensajeError>
        <BotonSecundario texto="Pedir esta ruta" icono="enviar" cargando={enviando} onPress={pedir} />
      </YStack>
    </Tarjeta>
  );
}
