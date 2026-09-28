import { useMemo } from 'react';

import { useTema } from '@/context/Tema';
import { useUbicacion } from '@/context/Ubicacion';

import type { PropsMapa } from './tipos';

export type MensajeMapa =
  | { tipo: 'listo' }
  | { tipo: 'toque'; lat: number; lng: number }
  | { tipo: 'marcador'; id: string };

/** Lógica compartida del mapa en celular (WebView) y web (iframe): datos a dibujar y respuesta a los toques. */
export default function useMapa({ marcadores = [], lineas = [], onPressMapa, margen, mostrarMiUbicacion = true }: PropsMapa) {
  const { esquema, paleta } = useTema();
  const { posicion, estado } = useUbicacion();
  const miUbicacion = mostrarMiUbicacion && estado === 'gps' ? { lat: posicion.lat, lng: posicion.lng } : null;

  const datos = useMemo(() => {
    const puntos = [...lineas.flatMap((l) => l.coordenadas), ...marcadores].map((p) => [p.lat, p.lng]);
    return {
      tipo: 'datos' as const,
      esquema,
      colores: {
        primario: paleta.primario,
        // Color de las líneas de la ruta (verde azulado, como en el mockup del mapa)
        ruta: paleta.ruta,
        // "oscuro": marcadores numerados y línea de autobús (azul marino como en el mockup)
        oscuro: paleta.marcador,
        sobreOscuro: paleta.tarjeta,
        tarjeta: paleta.tarjeta,
        peligro: paleta.peligro,
      },
      lineas,
      marcadores: marcadores.map(({ onPress, ...m }) => ({ ...m, tocable: !!onPress })),
      miUbicacion,
      margen,
      // Si cambia, la página vuelve a encuadrar el mapa
      clave: JSON.stringify([puntos, margen]),
    };
  }, [esquema, paleta, lineas, marcadores, miUbicacion?.lat, miUbicacion?.lng, margen?.arriba, margen?.abajo, margen?.izquierda]); // eslint-disable-line react-hooks/exhaustive-deps

  const alMensaje = (msg: MensajeMapa) => {
    if (msg.tipo === 'toque') onPressMapa?.({ lat: msg.lat, lng: msg.lng });
    if (msg.tipo === 'marcador') marcadores.find((m) => m.id === msg.id)?.onPress?.();
  };

  return { datos, alMensaje, miUbicacion, fondo: paleta.fondo };
}
