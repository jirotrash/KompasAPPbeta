// Servicios de mapas externos basados en OpenStreetMap (gratuitos, sin llave).
// - Búsqueda de direcciones mientras se escribe: Photon (https://photon.komoot.io)
// - Trazo por calles a pie y en auto: OSRM (https://routing.openstreetmap.de)
// Son servidores públicos de demostración: sirven para el prototipo, no para producción.
// El proveedor definitivo sigue pendiente (CONTEXTO.md §12).

import { estaDentroDeZona, ZONA, type Coordenada } from '@/constants/zona';
import type { GeoLinea } from '@/types/dominio';
import { normalizarTexto } from '@/utils/geo';

const GEOCODER_URL = process.env.EXPO_PUBLIC_GEOCODER_URL || 'https://photon.komoot.io/api/';
const ROUTER_URL = (process.env.EXPO_PUBLIC_ROUTER_URL || 'https://routing.openstreetmap.de').replace(/\/$/, '');

const MUNICIPIOS = ZONA.municipios.map(normalizarTexto);

export type Direccion = Coordenada & { id: string; nombre: string; detalle: string };

type PropiedadesPhoton = {
  osm_type: string;
  osm_id: number;
  osm_key?: string;
  name?: string;
  street?: string;
  housenumber?: string;
  district?: string;
  locality?: string;
  city?: string;
  county?: string;
};

function describir(p: PropiedadesPhoton) {
  const calle = [p.street, p.housenumber].filter(Boolean).join(' ');
  const nombre = p.name || calle || p.district || p.city || 'Sin nombre';
  const detalle = [p.name ? calle : null, p.district ?? p.locality, p.city ?? p.county]
    .filter((x, i, arr): x is string => !!x && x !== nombre && arr.indexOf(x) === i)
    .join(', ');
  return { nombre, detalle };
}

/** Busca direcciones y lugares de Toluca, Lerma y San Mateo Atenco. */
export async function buscarDirecciones(texto: string, signal?: AbortSignal): Promise<Direccion[]> {
  const { sur, oeste, norte, este } = ZONA.limites;
  const params = new URLSearchParams({
    q: texto,
    limit: '8',
    bbox: `${oeste},${sur},${este},${norte}`,
    lat: String(ZONA.centro.lat),
    lon: String(ZONA.centro.lng),
  });
  const respuesta = await fetch(`${GEOCODER_URL}?${params}`, { signal });
  if (!respuesta.ok) throw new Error('No se pudo buscar la dirección.');
  const { features = [] } = (await respuesta.json()) as {
    features?: { properties: PropiedadesPhoton; geometry: { coordinates: [number, number] } }[];
  };

  return (
    features
      .map((f) => {
        const [lng, lat] = f.geometry.coordinates;
        const p = f.properties;
        // Las localidades a veces no traen municipio: entonces su propio nombre cuenta como municipio
        const municipio = p.county ?? p.city ?? (p.osm_key === 'place' ? p.name : undefined);
        return { id: `osm_${p.osm_type}${p.osm_id}`, lat, lng, municipio, ...describir(p) };
      })
      // El rectángulo de la zona incluye partes de municipios vecinos (Metepec…): se filtra por municipio
      .filter((r) => estaDentroDeZona(r) && MUNICIPIOS.includes(normalizarTexto(r.municipio ?? '')))
      .filter((r, i, lista) => lista.findIndex((o) => o.nombre === r.nombre && o.detalle === r.detalle) === i)
      .map(({ municipio: _m, ...r }) => r)
  );
}

const PERFILES = { pie: 'routed-foot', auto: 'routed-car' } as const;

/** Trazo real por calles entre dos puntos, o null si el servicio no responde. */
export async function trazarPorCalles(
  origen: Coordenada,
  destino: Coordenada,
  modo: keyof typeof PERFILES,
): Promise<{ trazo: GeoLinea; distancia_km: number; duracion_min: number } | null> {
  const puntos = `${origen.lng},${origen.lat};${destino.lng},${destino.lat}`;
  try {
    const respuesta = await fetch(`${ROUTER_URL}/${PERFILES[modo]}/route/v1/driving/${puntos}?overview=full&geometries=geojson`);
    if (!respuesta.ok) return null;
    const { code, routes } = await respuesta.json();
    if (code !== 'Ok' || !routes?.length) return null;
    return {
      trazo: routes[0].geometry,
      distancia_km: routes[0].distance / 1000,
      duracion_min: Math.round(routes[0].duration / 60),
    };
  } catch {
    return null;
  }
}
