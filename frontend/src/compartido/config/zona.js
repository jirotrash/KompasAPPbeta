// Zona piloto: Toluca, Lerma y San Mateo Atenco (Estado de México).
// Límites PROVISIONALES (rectángulo aproximado); Sebas define los definitivos.

export const ZONA = {
  nombre: 'Toluca · Lerma · San Mateo Atenco',
  municipios: ['Toluca', 'Lerma', 'San Mateo Atenco'],
  // [lat, lng] como los usa Leaflet
  centro: [19.29, -99.58],
  zoomInicial: 12,
  zoomMinimo: 11,
  limites: [
    [19.2, -99.76], // suroeste
    [19.42, -99.38], // noreste
  ],
}

export function estaDentroDeZona(lat, lng) {
  const [[sur, oeste], [norte, este]] = ZONA.limites
  return lat >= sur && lat <= norte && lng >= oeste && lng <= este
}

// Puntos de partida/llegada rápidos para el buscador (centros aproximados)
export const PUNTOS_REFERENCIA = [
  { id: 'ref_toluca', nombre: 'Centro de Toluca', lat: 19.2926, lng: -99.6557 },
  { id: 'ref_lerma', nombre: 'Centro de Lerma', lat: 19.2847, lng: -99.511 },
  { id: 'ref_smateo', nombre: 'Centro de San Mateo Atenco', lat: 19.267, lng: -99.533 },
]
