// Servicios de mapas externos basados en OpenStreetMap (gratuitos, sin llave).
// - Búsqueda de direcciones mientras se escribe: Photon (https://photon.komoot.io)
// - Trazo por calles a pie y en auto: OSRM (https://routing.openstreetmap.de)
// Son servidores públicos de demostración: sirven para el prototipo, no para producción.
// El proveedor definitivo sigue pendiente (CONTEXTO.md §12); cámbialo aquí o con las variables .env.

import { estaDentroDeZona, ZONA } from '../config/zona.ts'
import type { Coordenada, Direccion, GeoLinea, TrazoCalles } from '../tipos/dominio.ts'
import { normalizarTexto } from '../utils/dominio.ts'

const GEOCODER_URL = import.meta.env.VITE_GEOCODER_URL || 'https://photon.komoot.io/api/'
const ROUTER_URL = (import.meta.env.VITE_ROUTER_URL || 'https://routing.openstreetmap.de').replace(/\/$/, '')

const [[SUR, OESTE], [NORTE, ESTE]] = ZONA.limites

const MUNICIPIOS = ZONA.municipios.map(normalizarTexto)

/** Propiedades de un resultado de Photon (las que se usan). */
type PropiedadesPhoton = {
  name?: string
  street?: string
  housenumber?: string
  district?: string
  locality?: string
  city?: string
  county?: string
  osm_key?: string
  osm_type?: string
  osm_id?: number
}
type RespuestaPhoton = { features?: { geometry: { coordinates: [number, number] }; properties: PropiedadesPhoton }[] }
type RespuestaOsrm = { code?: string; routes?: { geometry: GeoLinea; distance: number; duration: number }[] }

function describir(p: PropiedadesPhoton) {
  const calle = [p.street, p.housenumber].filter(Boolean).join(' ')
  const nombre = p.name || calle || p.district || p.city || 'Sin nombre'
  const detalle = [p.name ? calle : null, p.district ?? p.locality, p.city ?? p.county]
    .filter((x, i, arr) => x && x !== nombre && arr.indexOf(x) === i)
    .join(', ')
  return { nombre, detalle }
}

/** Busca direcciones y lugares dentro de la zona piloto. */
export async function buscarDirecciones(texto: string, { signal }: { signal?: AbortSignal } = {}): Promise<Direccion[]> {
  const url = new URL(GEOCODER_URL)
  url.searchParams.set('q', texto)
  url.searchParams.set('limit', '8')
  url.searchParams.set('bbox', `${OESTE},${SUR},${ESTE},${NORTE}`)
  url.searchParams.set('lat', String(ZONA.centro[0]))
  url.searchParams.set('lon', String(ZONA.centro[1]))

  const respuesta = await fetch(url, { signal })
  if (!respuesta.ok) throw new Error('No se pudo buscar la dirección.')
  const { features = [] } = (await respuesta.json()) as RespuestaPhoton

  return features
    .map((f) => {
      const [lng, lat] = f.geometry.coordinates
      const p = f.properties
      // Las localidades a veces no traen municipio: entonces su propio nombre cuenta como municipio
      const municipio = p.county ?? p.city ?? (p.osm_key === 'place' ? p.name : undefined)
      return { id: `osm_${p.osm_type}${p.osm_id}`, lat, lng, municipio, ...describir(p) }
    })
    // El rectángulo de la zona incluye partes de municipios vecinos (Metepec, Zinacantepec…): se filtra por municipio
    .filter((r) => estaDentroDeZona(r.lat, r.lng) && MUNICIPIOS.includes(normalizarTexto(r.municipio ?? '')))
    .filter((r, i, lista) => lista.findIndex((o) => o.nombre === r.nombre && o.detalle === r.detalle) === i)
}

const PERFILES = { pie: 'routed-foot', auto: 'routed-car' } as const

/** Trazo real por calles entre dos puntos; null si falla. */
export async function trazarPorCalles(origen: Coordenada, destino: Coordenada, modo: keyof typeof PERFILES): Promise<TrazoCalles | null> {
  const puntos = `${origen.lng},${origen.lat};${destino.lng},${destino.lat}`
  try {
    const respuesta = await fetch(
      `${ROUTER_URL}/${PERFILES[modo]}/route/v1/driving/${puntos}?overview=full&geometries=geojson`,
    )
    if (!respuesta.ok) return null
    const { code, routes } = (await respuesta.json()) as RespuestaOsrm
    if (code !== 'Ok' || !routes?.length) return null
    const [ruta] = routes
    return {
      trazo: ruta.geometry,
      distancia_km: ruta.distance / 1000,
      duracion_min: Math.round(ruta.duration / 60),
    }
  } catch {
    return null
  }
}
