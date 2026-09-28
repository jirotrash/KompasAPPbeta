import { useEffect, useRef, useState } from 'react';
import { View } from 'react-native';
import { WebView, type WebViewMessageEvent } from 'react-native-webview';

import { useUbicacion } from '@/context/Ubicacion';

import BotonMiUbicacion from './BotonMiUbicacion';
import { HTML_MAPA } from './html';
import type { PropsMapa } from './tipos';
import useMapa, { type MensajeMapa } from './useMapa';

/** Mapa en el celular: Leaflet dentro de un WebView (funciona en Expo Go sin llave de Google). */
export default function Mapa(props: PropsMapa) {
  const { datos, alMensaje, fondo } = useMapa(props);
  const { posicion, estado, actualizar } = useUbicacion();
  const web = useRef<WebView>(null);
  const [listo, setListo] = useState(false);

  // Cada vez que cambian los datos (o la página termina de cargar) se mandan a Leaflet
  useEffect(() => {
    if (listo) web.current?.injectJavaScript(`window.recibir(${JSON.stringify(datos)}); true;`);
  }, [listo, datos]);

  const recibir = (e: WebViewMessageEvent) => {
    const msg = JSON.parse(e.nativeEvent.data) as MensajeMapa;
    if (msg.tipo === 'listo') setListo(true);
    else alMensaje(msg);
  };

  const irAMiUbicacion = () => {
    actualizar();
    if (estado === 'gps') web.current?.injectJavaScript(`window.centrar(${posicion.lat}, ${posicion.lng}); true;`);
  };

  return (
    <View style={{ flex: 1, backgroundColor: fondo }}>
      <WebView
        ref={web}
        source={{ html: HTML_MAPA }}
        originWhitelist={['*']}
        onMessage={recibir}
        style={{ flex: 1, backgroundColor: fondo }}
        // Al recargar (p. ej. si el sistema libera memoria) hay que volver a mandar los datos
        onLoadStart={() => setListo(false)}
        setSupportMultipleWindows={false}
        overScrollMode="never"
        bounces={false}
      />
      {props.mostrarMiUbicacion !== false && <BotonMiUbicacion onPress={irAMiUbicacion} abajo={props.margen?.abajo} />}
    </View>
  );
}
