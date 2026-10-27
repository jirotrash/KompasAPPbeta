// Qué dibuja el mapa para una opción de "¿Cómo llego?" (lo mismo que hace la app móvil):
// en autobús, el tramo entre subida y bajada resaltado, el resto de la ruta tenue, las paradas
// intermedias como puntos chicos y la caminata (origen → subida, bajada → destino) punteada.

import type { LineaMapa, MarcadorMapa } from '../../compartido/componentes/Mapa.tsx'
import type { Alternativa, Coordenada, ParadaRuta, ParLeaflet, TramoOpcion } from '../../compartido/tipos/dominio.ts'
import { aLeaflet } from '../../compartido/utils/geo.ts'

export type DibujoOpcion = { trazo?: ParLeaflet[]; lineas: LineaMapa[]; marcadores: MarcadorMapa[] }

const punto = (p: Coordenada): ParLeaflet => [p.lat, p.lng]
const marcador = (id: string, tipo: MarcadorMapa['tipo'], p: ParadaRuta, titulo: string): MarcadorMapa => ({ id, tipo, lat: p.lat, lng: p.lng, titulo })

/** Tramos de autobús de la opción; las opciones del modo mock o de la v0.5 solo traen abordaje/descenso y trazo. */
function tramosDe(a: Alternativa): TramoOpcion[] {
  if (a.tramos?.length) return a.tramos
  if (!a.parada_subida || !a.parada_bajada) return []
  return [
    {
      modo: 'autobus',
      linea: a.linea,
      distancia_km: a.distancia_km ?? 0,
      duracion_min: a.tiempos.trayecto ?? 0,
      parada_subida: a.parada_subida,
      parada_bajada: a.parada_bajada,
      tramo_en_ruta: a.tramo_en_ruta ?? a.trazo?.coordinates,
      paradas_intermedias: a.paradas_intermedias,
    },
  ]
}

export function dibujoOpcion(a: Alternativa | undefined, origen: Coordenada, destino: Coordenada): DibujoOpcion {
  if (!a) return { lineas: [], marcadores: [] }
  const buses = tramosDe(a).filter((t) => t.modo === 'autobus' && t.parada_subida && t.parada_bajada)

  if (a.modo !== 'autobus' || !buses.length) {
    // A pie, taxi o app: el trazo por calles que manda la API (o nada)
    return { trazo: a.trazo?.coordinates.map(aLeaflet), lineas: [], marcadores: [] }
  }

  const lineas: LineaMapa[] = []
  const marcadores: MarcadorMapa[] = []
  buses.forEach((t, i) => {
    const subida = t.parada_subida as ParadaRuta
    const bajada = t.parada_bajada as ParadaRuta
    if (t.trazo_ruta?.length) lineas.push({ id: `ruta_${i}`, puntos: t.trazo_ruta.map(aLeaflet), estilo: 'trazo-tenue' })
    if (t.tramo_en_ruta?.length) lineas.push({ id: `bus_${i}`, puntos: t.tramo_en_ruta.map(aLeaflet), estilo: 'trazo-ruta' })
    marcadores.push(marcador(`subida_${i}`, i === 0 ? 'abordaje' : 'transbordo', subida, `${i === 0 ? 'Sube' : 'Transbordo: sube'} en ${subida.nombre}${t.linea ? ` (${t.linea})` : ''}`))
    marcadores.push(marcador(`bajada_${i}`, i === buses.length - 1 ? 'descenso' : 'transbordo', bajada, `Baja en ${bajada.nombre}`))
    t.paradas_intermedias?.forEach((p, j) => marcadores.push(marcador(`intermedia_${i}_${j}`, 'intermedia', p, p.nombre)))
  })

  // Caminatas punteadas: las que manda la API (incluye las de transbordo) o, si no vienen, origen → subida y bajada → destino
  const caminatas = (a.tramos ?? []).filter((t) => t.modo === 'pie' && t.desde && t.hasta)
  if (caminatas.length) {
    caminatas.forEach((t, i) => lineas.push({ id: `pie_${i}`, puntos: [punto(t.desde as Coordenada), punto(t.hasta as Coordenada)], estilo: 'trazo-a-pie' }))
  } else {
    lineas.push({ id: 'pie_ida', puntos: [punto(origen), punto(buses[0].parada_subida as ParadaRuta)], estilo: 'trazo-a-pie' })
    lineas.push({ id: 'pie_vuelta', puntos: [punto(buses[buses.length - 1].parada_bajada as ParadaRuta), punto(destino)], estilo: 'trazo-a-pie' })
  }
  return { lineas, marcadores }
}
