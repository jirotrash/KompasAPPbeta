import { useEffect, useRef, useState } from 'react';
import { View } from 'react-native';

import { useUbicacion } from '@/context/Ubicacion';

import BotonMiUbicacion from './BotonMiUbicacion';
import { HTML_MAPA } from './html';
import type { PropsMapa } from './tipos';
import useMapa, { type MensajeMapa } from './useMapa';

/** Mapa en web: la misma página de Leaflet dentro de un iframe (react-native-webview no funciona en web). */
export default function Mapa(props: PropsMapa) {
  const { datos, alMensaje, fondo } = useMapa(props);
  const { posicion, estado, actualizar } = useUbicacion();
  const marco = useRef<HTMLIFrameElement>(null);
  const [listo, setListo] = useState(false);

  const enviar = (msg: object) => marco.current?.contentWindow?.postMessage({ ...msg, fuente: 'brujula-app' }, '*');

  // Mensajes que manda la página del mapa (solo los de este iframe)
  const manejador = useRef(alMensaje);
  useEffect(() => {
    manejador.current = alMensaje;
  });
  useEffect(() => {
    const escuchar = (e: MessageEvent) => {
      if (e.source !== marco.current?.contentWindow || e.data?.fuente !== 'brujula-mapa') return;
      const msg = e.data as MensajeMapa;
      if (msg.tipo === 'listo') setListo(true);
      else manejador.current(msg);
    };
    window.addEventListener('message', escuchar);
    return () => window.removeEventListener('message', escuchar);
  }, []);

  useEffect(() => {
    if (listo) marco.current?.contentWindow?.postMessage({ ...datos, fuente: 'brujula-app' }, '*');
  }, [listo, datos]);

  const irAMiUbicacion = () => {
    actualizar();
    if (estado === 'gps') enviar({ tipo: 'centrar', lat: posicion.lat, lng: posicion.lng });
  };

  return (
    <View style={{ flex: 1, backgroundColor: fondo }}>
      <iframe
        ref={marco}
        title="Mapa"
        srcDoc={HTML_MAPA}
        style={{ border: 0, width: '100%', height: '100%', flex: 1, backgroundColor: fondo }}
      />
      {props.mostrarMiUbicacion !== false && <BotonMiUbicacion onPress={irAMiUbicacion} abajo={props.margen?.abajo} />}
    </View>
  );
}
