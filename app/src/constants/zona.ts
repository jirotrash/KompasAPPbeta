// Zona piloto: Toluca, Lerma y San Mateo Atenco (Estado de México).
// Límites PROVISIONALES (rectángulo aproximado); Sebas define los definitivos.

export type Coordenada = { lat: number; lng: number };

export const ZONA = {
  nombre: 'Toluca · Lerma · San Mateo Atenco',
  municipios: ['Toluca', 'Lerma', 'San Mateo Atenco'],
  centro: { lat: 19.29, lng: -99.58 },
  limites: { sur: 19.2, oeste: -99.76, norte: 19.42, este: -99.38 },
};

export function estaDentroDeZona({ lat, lng }: Coordenada) {
  const { sur, oeste, norte, este } = ZONA.limites;
  return lat >= sur && lat <= norte && lng >= oeste && lng <= este;
}

/** Puntos de partida rápidos (centros aproximados). También se usan si no hay GPS. */
export const PUNTOS_REFERENCIA = [
  { id: 'ref_toluca', nombre: 'Centro de Toluca', lat: 19.2926, lng: -99.6557 },
  { id: 'ref_lerma', nombre: 'Centro de Lerma', lat: 19.2847, lng: -99.511 },
  { id: 'ref_smateo', nombre: 'Centro de San Mateo Atenco', lat: 19.267, lng: -99.533 },
];
