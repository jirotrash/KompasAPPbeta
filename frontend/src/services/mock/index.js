// Implementación de ejemplo de cada endpoint (misma forma de respuesta que la API real).

import { estaDentroDeZona } from '../../config/zona.js'
import { distanciaKm } from '../../utils/geo.js'
import { trazarPorCalles } from '../mapas.js'
import { LUGARES, RUTAS } from './datos.js'
import { inferirItinerarios } from './motorReglas.js'

const esperar = (ms = 450) => new Promise((r) => setTimeout(r, ms))

class ErrorMock extends Error {
  constructor(mensaje, estado) {
    super(mensaje)
    this.estado = estado
  }
}

const punto = (geo) => ({ lng: geo.coordinates[0], lat: geo.coordinates[1] })
const aMinutos = (hhmm) => {
  const [h, m] = hhmm.split(':').map(Number)
  return h * 60 + m
}

// ─────────────── Auth ───────────────

export async function login({ email, password }) {
  await esperar()
  if (!email || !password || password.length < 6) {
    throw new ErrorMock('Correo o contraseña incorrectos.', 401)
  }
  return {
    token: 'token-de-ejemplo',
    usuario: { id: 1, nombre: email.split('@')[0], email, rol: 'usuario' },
  }
}

export async function registrar({ nombre, email, password }) {
  await esperar()
  if (!nombre || !email || !password || password.length < 6) {
    throw new ErrorMock('Revisa los datos: la contraseña necesita al menos 6 caracteres.', 422)
  }
  return { token: 'token-de-ejemplo', usuario: { id: 1, nombre, email, rol: 'usuario' } }
}

// ─────────────── Reportes (en memoria) ───────────────

const ahora = () => new Date()
const enHoras = (h) => new Date(Date.now() + h * 3600_000).toISOString()

const reportes = [
  {
    _id: 'reporte_ejemplo_1',
    tipo: 'manifestacion',
    ubicacion: { type: 'Point', coordinates: [-99.625, 19.279] },
    ruta_id: 'ruta_ejemplo_b',
    observado_en: ahora().toISOString(),
    vigente_hasta: enHoras(3),
    usuario_id: 2,
    confirmaciones: 1,
    estado: 'pendiente',
    comentario: 'Reporte de ejemplo',
  },
]

const VIGENCIA_H = { cierre_total: 6, accidente: 2, manifestacion: 3, afluencia: 1 }

export async function crearReporte(datos) {
  await esperar()
  const observado = new Date(datos.observado_en || Date.now())
  const nuevo = {
    ...datos,
    _id: `reporte_${Date.now()}`,
    vigente_hasta: new Date(observado.getTime() + VIGENCIA_H[datos.tipo] * 3600_000).toISOString(),
    usuario_id: 1,
    confirmaciones: 0,
    estado: 'pendiente',
  }
  reportes.unshift(nuevo)
  return nuevo
}

export async function obtenerReportes(rutaId) {
  await esperar(250)
  const vigentes = reportes.filter((r) => new Date(r.vigente_hasta) > ahora())
  return rutaId ? vigentes.filter((r) => r.ruta_id === rutaId) : vigentes
}

// ─────────────── Rutas ───────────────

export async function obtenerRuta(id) {
  await esperar(250)
  const ruta = RUTAS.find((r) => r._id === id)
  if (!ruta) throw new ErrorMock('Ruta no encontrada.', 404)
  return ruta
}

const RADIO_CAMINATA_KM = 1.2
const VEL_PIE_KMH = 4.8
const VEL_BUS_KMH = 18
const VEL_AUTO_KMH = 25
const FACTOR_CALLES = 1.3 // la distancia real por calles es mayor que la línea recta

function paradaMasCercana(paradas, p) {
  return paradas
    .map((parada, i) => ({ parada, i, km: distanciaKm(p, punto(parada.ubicacion)) }))
    .sort((a, b) => a.km - b.km)[0]
}

function alternativaAutobus(ruta, origen, destino, hora) {
  const sube = paradaMasCercana(ruta.paradas, origen)
  const baja = paradaMasCercana(ruta.paradas, destino)
  if (sube.km > RADIO_CAMINATA_KM || baja.km > RADIO_CAMINATA_KM || sube.i >= baja.i) return null

  const tramo = ruta.paradas.slice(sube.i, baja.i + 1)
  let kmTramo = 0
  for (let i = 1; i < tramo.length; i++) kmTramo += distanciaKm(punto(tramo[i - 1].ubicacion), punto(tramo[i].ubicacion))

  const avisos = []
  const min = aMinutos(hora)
  if (min < aMinutos(ruta.horario.inicio) || min > aMinutos(ruta.horario.fin)) {
    avisos.push(`Fuera del horario programado (${ruta.horario.inicio}–${ruta.horario.fin}).`)
  }
  const reportesRuta = reportes.filter((r) => r.ruta_id === ruta._id && new Date(r.vigente_hasta) > ahora())
  reportesRuta.forEach((r) =>
    avisos.push(`Reporte ${r.estado === 'verificado' ? 'verificado' : 'sin verificar'}: ${r.tipo.replace('_', ' ')} en la ruta.`),
  )

  return {
    id: `bus_${ruta._id}`,
    modo: 'autobus',
    ruta_id: ruta._id,
    linea: ruta.linea,
    sentido: ruta.sentido,
    tarifa: ruta.tarifa,
    abordaje: { nombre: sube.parada.nombre, ubicacion: sube.parada.ubicacion },
    descenso: { nombre: baja.parada.nombre, ubicacion: baja.parada.ubicacion },
    transbordos: [],
    tiempos: {
      caminata: Math.round(((sube.km + baja.km) * FACTOR_CALLES * 60) / VEL_PIE_KMH),
      espera: Math.round(ruta.horario.frecuencia_min / 2),
      trayecto: Math.round(((kmTramo * FACTOR_CALLES) / VEL_BUS_KMH) * 60),
      transbordos: 0,
    },
    tipo_horario: ruta.horario.tipo,
    trazo: { type: 'LineString', coordinates: tramo.map((p) => p.ubicacion.coordinates) },
    fuente: ruta.fuente,
    fecha_verificacion: ruta.fecha_verificacion,
    avisos,
    ejemplo: true,
  }
}

export async function buscarRutas({ origen, destino, hora }) {
  await esperar()
  if (!estaDentroDeZona(origen.lat, origen.lng) || !estaDentroDeZona(destino.lat, destino.lng)) {
    return {
      datos_suficientes: false,
      mensaje: 'El origen o el destino está fuera de la zona piloto (Toluca, Lerma y San Mateo Atenco).',
      alternativas: [],
    }
  }

  const autobuses = RUTAS.map((r) => alternativaAutobus(r, origen, destino, hora)).filter(Boolean)

  // Trazo real por calles (OSRM); si el servicio no responde se estima por distancia en línea recta
  const [callesPie, callesAuto] = await Promise.all([
    trazarPorCalles(origen, destino, 'pie'),
    trazarPorCalles(origen, destino, 'auto'),
  ])
  const kmEstimados = distanciaKm(origen, destino) * FACTOR_CALLES
  const FUENTE_CALLES = 'OSRM · OpenStreetMap'

  const kmPie = callesPie?.distancia_km ?? kmEstimados
  const pie = {
    id: 'pie',
    modo: 'pie',
    distancia_km: kmPie,
    transbordos: [],
    tiempos: {
      caminata: callesPie?.duracion_min ?? Math.round((kmEstimados / VEL_PIE_KMH) * 60),
      espera: null,
      trayecto: null,
      transbordos: null,
    },
    tipo_horario: null,
    trazo: callesPie?.trazo,
    fuente: callesPie ? FUENTE_CALLES : 'Estimación por distancia',
    fecha_verificacion: null,
    avisos: kmPie > 4 ? ['Trayecto largo para hacerlo a pie.'] : [],
  }
  const auto = (modo) => ({
    id: modo,
    modo,
    distancia_km: callesAuto?.distancia_km ?? kmEstimados,
    transbordos: [],
    tiempos: {
      caminata: null,
      espera: 5,
      trayecto: callesAuto?.duracion_min ?? Math.round((kmEstimados / VEL_AUTO_KMH) * 60),
      transbordos: null,
    },
    tipo_horario: null,
    trazo: callesAuto?.trazo,
    fuente: callesAuto ? FUENTE_CALLES : 'Estimación por distancia',
    fecha_verificacion: null,
    avisos: [
      'El tiempo no considera el tráfico.',
      'La tarifa la define el proveedor; consúltala en su app o con el conductor.',
    ],
  })

  return {
    datos_suficientes: autobuses.length > 0,
    mensaje: autobuses.length ? undefined : 'No tenemos información suficiente de transporte público para esta ruta.',
    alternativas: [...autobuses, pie, auto('taxi'), auto('app')],
  }
}

// ─────────────── Lugares e itinerarios ───────────────

export async function buscarLugares({ cerca, categoria } = {}) {
  await esperar(250)
  let lista = categoria ? LUGARES.filter((l) => l.categoria === categoria) : [...LUGARES]
  if (cerca) lista.sort((a, b) => distanciaKm(cerca, punto(a.ubicacion)) - distanciaKm(cerca, punto(b.ubicacion)))
  return lista
}

export async function generarItinerarios(peticion) {
  await esperar(700)
  return inferirItinerarios(LUGARES, peticion)
}
