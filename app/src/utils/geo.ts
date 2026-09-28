import type { Coordenada } from '@/constants/zona';

// Ojo: GeoJSON (MongoDB) usa [lng, lat]; los mapas usan {latitude, longitude}.
export type ParGeoJSON = [number, number];

export const desdeGeoJSON = ([lng, lat]: ParGeoJSON): Coordenada => ({ lat, lng });
export const aMapa = ({ lat, lng }: Coordenada) => ({ latitude: lat, longitude: lng });

/** Distancia en km en línea recta (fórmula de haversine). */
export function distanciaKm(a: Coordenada, b: Coordenada) {
  const rad = (g: number) => (g * Math.PI) / 180;
  const dLat = rad(b.lat - a.lat);
  const dLng = rad(b.lng - a.lng);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dLng / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(h));
}

/** La distancia por calles suele ser ~30 % mayor que la línea recta. */
export const FACTOR_CALLES = 1.3;
export const VELOCIDAD_KMH = { pie: 4.8, autobus: 18, auto: 25 };

export const minutosCaminando = (km: number) => Math.round(((km * FACTOR_CALLES) / VELOCIDAD_KMH.pie) * 60);

export function formatoMinutos(min?: number | null) {
  if (min == null) return '—';
  if (min < 60) return `${Math.round(min)} min`;
  const h = Math.floor(min / 60);
  const m = Math.round(min % 60);
  return m ? `${h} h ${m} min` : `${h} h`;
}

export const formatoKm = (km: number) => (km < 1 ? `${Math.round(km * 1000)} m` : `${km.toFixed(1)} km`);

export function formatoFecha(iso?: string | null) {
  if (!iso) return 'sin fecha';
  const fecha = new Date(iso.length === 10 ? `${iso}T12:00:00` : iso);
  return fecha.toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' });
}

export const aMinutosDelDia = (hhmm: string) => {
  const [h, m] = hhmm.split(':').map(Number);
  return h * 60 + m;
};

export const aHora = (minutos: number) => {
  const total = ((Math.round(minutos) % 1440) + 1440) % 1440;
  return `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`;
};

export const horaActual = () => aHora(new Date().getHours() * 60 + new Date().getMinutes());

const DIAS = ['dom', 'lun', 'mar', 'mie', 'jue', 'vie', 'sab'] as const;
export type Dia = (typeof DIAS)[number];
export const diaDeHoy = (): Dia => DIAS[new Date().getDay()];

/** Minúsculas y sin acentos, para comparar textos al buscar. */
export const normalizarTexto = (t: string) =>
  t
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .trim();

export function saludo() {
  const h = new Date().getHours();
  if (h < 12) return 'Buenos días';
  if (h < 19) return 'Buenas tardes';
  return 'Buenas noches';
}
