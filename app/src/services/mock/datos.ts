// DATOS DE EJEMPLO para desarrollar sin API.
// No son rutas, horarios ni lugares reales: tienen nombres genéricos y la app los marca
// como "Dato de ejemplo". Se reemplazan por los datos verificados que Sebas carga en MongoDB.
// Coordenadas en GeoJSON: [lng, lat].

import type { Lugar } from '@/types/dominio';
import type { Dia } from '@/utils/geo';

export const FUENTE_EJEMPLO = 'Dato de ejemplo (sin verificar)';

type RutaEjemplo = {
  _id: string;
  linea: string;
  sentido: string;
  tarifa: number | null;
  horario: { inicio: string; fin: string; frecuencia_min: number; tipo: 'programado' };
  paradas: { orden: number; nombre: string; ubicacion: { type: 'Point'; coordinates: [number, number] } }[];
  verificada: boolean;
  fuente: string;
  fecha_verificacion: string | null;
};

const parada = (orden: number, nombre: string, lng: number, lat: number) => ({
  orden,
  nombre: `Parada de ejemplo · ${nombre}`,
  ubicacion: { type: 'Point' as const, coordinates: [lng, lat] as [number, number] },
});

export const RUTAS: RutaEjemplo[] = [
  {
    _id: 'ruta_ejemplo_a',
    linea: 'Línea de ejemplo A',
    sentido: 'Lerma → Toluca',
    tarifa: null,
    horario: { inicio: '05:30', fin: '22:00', frecuencia_min: 15, tipo: 'programado' },
    paradas: [
      parada(1, 'Centro de Lerma', -99.511, 19.2847),
      parada(2, 'Lerma oriente', -99.527, 19.2815),
      parada(3, 'Límite San Mateo Atenco', -99.545, 19.279),
      parada(4, 'Poniente de San Mateo', -99.57, 19.278),
      parada(5, 'Oriente de Toluca', -99.61, 19.283),
      parada(6, 'Toluca centro-oriente', -99.64, 19.289),
      parada(7, 'Centro de Toluca', -99.6557, 19.2926),
    ],
    verificada: false,
    fuente: FUENTE_EJEMPLO,
    fecha_verificacion: null,
  },
  {
    _id: 'ruta_ejemplo_b',
    linea: 'Línea de ejemplo B',
    sentido: 'San Mateo Atenco → Toluca',
    tarifa: null,
    horario: { inicio: '06:00', fin: '21:00', frecuencia_min: 20, tipo: 'programado' },
    paradas: [
      parada(1, 'Centro de San Mateo Atenco', -99.533, 19.267),
      parada(2, 'San Mateo sur', -99.55, 19.265),
      parada(3, 'Oriente de Toluca sur', -99.59, 19.27),
      parada(4, 'Toluca sur', -99.625, 19.279),
      parada(5, 'Centro de Toluca sur', -99.652, 19.287),
    ],
    verificada: false,
    fuente: FUENTE_EJEMPLO,
    fecha_verificacion: null,
  },
];

const todaLaSemana = (abre: string, cierra: string) =>
  Object.fromEntries(
    (['lun', 'mar', 'mie', 'jue', 'vie', 'sab', 'dom'] as Dia[]).map((d) => [d, [abre, cierra]]),
  ) as Record<Dia, [string, string]>;

const calificacion = (valor: number) => ({ valor, fuente: FUENTE_EJEMPLO, fecha: '2026-09-20' });
const afluencia = (nivel: 'baja' | 'media' | 'alta') => ({ nivel, fuente: 'Reporte comunitario (ejemplo)', fecha: '2026-09-26' });
const punto = (lng: number, lat: number) => ({ type: 'Point' as const, coordinates: [lng, lat] as [number, number] });

export const LUGARES: Lugar[] = [
  {
    _id: 'lugar_01',
    nombre: 'Cafetería de ejemplo · Centro de Toluca',
    categoria: 'cafeteria',
    interes: 'cafe',
    municipio: 'Toluca',
    ubicacion: punto(-99.656, 19.292),
    horario: todaLaSemana('08:00', '21:00'),
    costo_promedio: 120,
    contextos: ['pareja', 'amigos', 'solo'],
    calificacion: calificacion(4.5),
    afluencia: afluencia('media'),
  },
  {
    _id: 'lugar_02',
    nombre: 'Restaurante familiar de ejemplo',
    categoria: 'restaurante',
    interes: 'comer',
    municipio: 'Toluca',
    ubicacion: punto(-99.64, 19.287),
    horario: todaLaSemana('09:00', '22:00'),
    costo_promedio: 250,
    contextos: ['familia', 'pareja', 'amigos'],
    calificacion: calificacion(4.3),
    afluencia: afluencia('baja'),
  },
  {
    _id: 'lugar_03',
    nombre: 'Parque de ejemplo · Toluca',
    categoria: 'parque',
    interes: 'aire_libre',
    municipio: 'Toluca',
    ubicacion: punto(-99.662, 19.296),
    horario: todaLaSemana('06:00', '19:00'),
    costo_promedio: 0,
    contextos: ['familia', 'amigos', 'pareja', 'solo'],
    calificacion: calificacion(4.6),
    afluencia: afluencia('alta'),
  },
  {
    _id: 'lugar_04',
    nombre: 'Museo de ejemplo',
    categoria: 'museo',
    interes: 'cultura',
    municipio: 'Toluca',
    ubicacion: punto(-99.658, 19.2935),
    horario: { ...todaLaSemana('10:00', '18:00'), lun: null },
    costo_promedio: 40,
    contextos: ['pareja', 'familia', 'solo'],
    calificacion: calificacion(4.7),
    afluencia: null,
  },
  {
    _id: 'lugar_05',
    nombre: 'Cine de ejemplo',
    categoria: 'cine',
    interes: 'entretenimiento',
    municipio: 'Toluca',
    ubicacion: punto(-99.61, 19.28),
    horario: todaLaSemana('11:00', '23:30'),
    costo_promedio: 90,
    contextos: ['amigos', 'pareja', 'familia'],
    calificacion: calificacion(4.2),
    afluencia: afluencia('alta'),
  },
  {
    _id: 'lugar_06',
    nombre: 'Cafetería de ejemplo · Centro de Lerma',
    categoria: 'cafeteria',
    interes: 'cafe',
    municipio: 'Lerma',
    ubicacion: punto(-99.5115, 19.285),
    horario: todaLaSemana('08:00', '20:00'),
    costo_promedio: 90,
    contextos: ['pareja', 'amigos', 'solo'],
    calificacion: calificacion(4.4),
    afluencia: null,
  },
  {
    _id: 'lugar_07',
    nombre: 'Fonda de ejemplo · San Mateo Atenco',
    categoria: 'restaurante',
    interes: 'comer',
    municipio: 'San Mateo Atenco',
    ubicacion: punto(-99.5335, 19.2675),
    horario: todaLaSemana('08:00', '18:00'),
    costo_promedio: 100,
    contextos: ['familia', 'amigos', 'solo'],
    calificacion: calificacion(4.1),
    afluencia: afluencia('baja'),
  },
  {
    _id: 'lugar_08',
    nombre: 'Plaza comercial de ejemplo · Lerma',
    categoria: 'plaza',
    interes: 'entretenimiento',
    municipio: 'Lerma',
    ubicacion: punto(-99.54, 19.28),
    horario: todaLaSemana('10:00', '21:00'),
    costo_promedio: 200,
    contextos: ['amigos', 'familia'],
    calificacion: calificacion(4.0),
    afluencia: null,
  },
  {
    _id: 'lugar_09',
    nombre: 'Restaurante de ejemplo · Toluca poniente',
    categoria: 'restaurante',
    interes: 'comer',
    municipio: 'Toluca',
    ubicacion: punto(-99.675, 19.29),
    horario: todaLaSemana('13:00', '17:00'),
    costo_promedio: 450,
    contextos: ['pareja', 'familia'],
    calificacion: calificacion(4.8),
    afluencia: null,
  },
  {
    _id: 'lugar_10',
    nombre: 'Jardín de ejemplo · Lerma',
    categoria: 'parque',
    interes: 'aire_libre',
    municipio: 'Lerma',
    ubicacion: punto(-99.514, 19.2875),
    horario: todaLaSemana('07:00', '20:00'),
    costo_promedio: 0,
    contextos: ['familia', 'pareja', 'amigos', 'solo'],
    calificacion: calificacion(4.3),
    afluencia: null,
  },
  {
    _id: 'lugar_11',
    nombre: 'Galería de ejemplo (sin horario registrado)',
    categoria: 'museo',
    interes: 'cultura',
    municipio: 'Lerma',
    ubicacion: punto(-99.515, 19.288),
    horario: null,
    costo_promedio: null,
    contextos: ['pareja', 'amigos'],
    calificacion: null,
    afluencia: null,
  },
];
