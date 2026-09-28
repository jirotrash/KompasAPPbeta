import type { Coordenada } from '@/constants/zona';
import type { ModoTramo } from '@/types/dominio';

export type MarcadorMapa = Coordenada & {
  id: string;
  /** Texto dentro del círculo (número de parada, "A"…). */
  etiqueta?: string;
  tipo: 'origen' | 'lugar' | 'parada' | 'destino' | 'reporte' | 'seleccion';
  titulo?: string;
  onPress?: () => void;
};

export type LineaMapa = { id: string; modo: ModoTramo; coordenadas: Coordenada[] };

export type PropsMapa = {
  marcadores?: MarcadorMapa[];
  lineas?: LineaMapa[];
  /** Tocar el mapa (para elegir un punto). */
  onPressMapa?: (p: Coordenada) => void;
  /** Espacio tapado por paneles encima del mapa, para encuadrar la ruta sin que quede debajo. */
  margen?: { arriba?: number; abajo?: number; izquierda?: number };
  mostrarMiUbicacion?: boolean;
};
