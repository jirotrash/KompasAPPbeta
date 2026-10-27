// Implementación de ejemplo de cada endpoint (misma forma de respuesta que la API real).

import { estaDentroDeZona } from '../compartido/config/zona.ts'
import { distanciaKm } from '../compartido/utils/geo.ts'
import { trazarPorCalles } from '../compartido/api/mapas.ts'
import type {
  Alternativa,
  Coordenada,
  Credenciales,
  GeoPunto,
  Lugar,
  NuevoReporte,
  NuevoUsuario,
  ParadaRuta,
  PeticionItinerario,
  Reporte,
  RespuestaItinerarios,
  RespuestaRutas,
  RutaEjemplo,
  Sesion,
  TipoReporte,
} from '../compartido/tipos/dominio.ts'
import { LUGARES, RUTAS } from './datos.ts'
import { inferirItinerarios } from './motorReglas.ts'

const esperar = (ms = 450) => new Promise((r) => setTimeout(r, ms))

class ErrorMock extends Error {
  estado: number

  constructor(mensaje: string, estado: number) {
    super(mensaje)
    this.estado = estado
  }
}

const punto = (geo: GeoPunto): Coordenada => ({ lng: geo.coordinates[0], lat: geo.coordinates[1] })
const aMinutos = (hhmm: string) => {
  const [h, m] = hhmm.split(':').map(Number)
  return h * 60 + m
}

// ─────────────── Auth ───────────────

export async function login({ email, password }: Credenciales): Promise<Sesion> {
  await esperar()
  if (!email || !password || password.length < 6) {
    throw new ErrorMock('Correo o contraseña incorrectos.', 401)
  }
  return {
    token: 'token-de-ejemplo',
    // En modo demostración el usuario de ejemplo es admin para poder abrir el dashboard
    usuario: { id: 1, nombre: email.split('@')[0], email, rol: 'admin' },
  }
}

export async function registrar({ nombre, email, password }: NuevoUsuario): Promise<Sesion> {
  await esperar()
  if (!nombre || !email || !password || password.length < 6) {
    throw new ErrorMock('Revisa los datos: la contraseña necesita al menos 6 caracteres.', 422)
  }
  return { token: 'token-de-ejemplo', usuario: { id: 1, nombre, email, rol: 'admin' } }
}

// ─────────────── Reportes (en memoria) ───────────────

const ahora = () => new Date()
const enHoras = (h: number) => new Date(Date.now() + h * 3600_000).toISOString()

const reportes: Reporte[] = [
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

const VIGENCIA_H: Record<TipoReporte, number> = { cierre_total: 6, accidente: 2, manifestacion: 3, afluencia: 1 }

export async function crearReporte(datos: NuevoReporte): Promise<Reporte> {
  await esperar()
  const observado = new Date(datos.observado_en || Date.now())
  const nuevo: Reporte = {
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

export async function obtenerReportes(rutaId?: string): Promise<Reporte[]> {
  await esperar(250)
  const vigentes = reportes.filter((r) => new Date(r.vigente_hasta) > ahora())
  return rutaId ? vigentes.filter((r) => r.ruta_id === rutaId) : vigentes
}

// ─────────────── Rutas ───────────────

export async function obtenerRuta(id: string): Promise<RutaEjemplo> {
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

function paradaMasCercana(paradas: RutaEjemplo['paradas'], p: Coordenada) {
  return paradas
    .map((parada, i) => ({ parada, i, km: distanciaKm(p, punto(parada.ubicacion)) }))
    .sort((a, b) => a.km - b.km)[0]
}

function alternativaAutobus(ruta: RutaEjemplo, origen: Coordenada, destino: Coordenada, hora: string): Alternativa | null {
  const sube = paradaMasCercana(ruta.paradas, origen)
  const baja = paradaMasCercana(ruta.paradas, destino)
  if (sube.km > RADIO_CAMINATA_KM || baja.km > RADIO_CAMINATA_KM || sube.i >= baja.i) return null

  const tramo = ruta.paradas.slice(sube.i, baja.i + 1)
  // km acumulado desde la primera parada de la ruta (la misma clave que usa el árbol de paradas de la API)
  const acumulado = [0]
  for (let i = 1; i < ruta.paradas.length; i++) {
    acumulado.push(acumulado[i - 1] + distanciaKm(punto(ruta.paradas[i - 1].ubicacion), punto(ruta.paradas[i].ubicacion)))
  }
  const kmTramo = acumulado[baja.i] - acumulado[sube.i]
  const paradaRuta = (i: number): ParadaRuta => ({ nombre: ruta.paradas[i].nombre, ...punto(ruta.paradas[i].ubicacion), km: acumulado[i] })

  const avisos: string[] = []
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
    tipo: 'directo',
    ruta_id: ruta._id,
    linea: ruta.linea,
    sentido: ruta.sentido,
    tarifa: ruta.tarifa,
    abordaje: { nombre: sube.parada.nombre, ubicacion: sube.parada.ubicacion },
    descenso: { nombre: baja.parada.nombre, ubicacion: baja.parada.ubicacion },
    parada_subida: paradaRuta(sube.i),
    parada_bajada: paradaRuta(baja.i),
    paradas_intermedias: tramo.slice(1, -1).map((_, j) => paradaRuta(sube.i + 1 + j)),
    tramo_en_ruta: tramo.map((p) => p.ubicacion.coordinates),
    transbordos: [],
    numero_transbordos: 0,
    tiempos: {
      caminata: Math.round(((sube.km + baja.km) * FACTOR_CALLES * 60) / VEL_PIE_KMH),
      espera: Math.round(ruta.horario.frecuencia_min / 2),
      trayecto: Math.round(((kmTramo * FACTOR_CALLES) / VEL_BUS_KMH) * 60),
      transbordos: 0,
    },
    tipo_horario: ruta.horario.tipo,
    trazo: { type: 'LineString', coordinates: tramo.map((p) => p.ubicacion.coordinates) },
    tramos: [
      {
        modo: 'autobus',
        linea: ruta.linea,
        distancia_km: kmTramo,
        duracion_min: Math.round(((kmTramo * FACTOR_CALLES) / VEL_BUS_KMH) * 60),
        parada_subida: paradaRuta(sube.i),
        parada_bajada: paradaRuta(baja.i),
        tramo_en_ruta: tramo.map((p) => p.ubicacion.coordinates),
        paradas_intermedias: tramo.slice(1, -1).map((_, j) => paradaRuta(sube.i + 1 + j)),
        trazo_ruta: ruta.paradas.map((p) => p.ubicacion.coordinates),
      },
    ],
    fuente: ruta.fuente,
    fecha_verificacion: ruta.fecha_verificacion,
    avisos,
    ejemplo: true,
  }
}

export async function buscarRutas({ origen, destino, hora }: { origen: Coordenada; destino: Coordenada; hora: string }): Promise<RespuestaRutas> {
  await esperar()
  if (!estaDentroDeZona(origen.lat, origen.lng) || !estaDentroDeZona(destino.lat, destino.lng)) {
    return {
      datos_suficientes: false,
      mensaje: 'El origen o el destino está fuera de la zona piloto (Toluca, Lerma y San Mateo Atenco).',
      alternativas: [],
    }
  }

  const autobuses = RUTAS.map((r) => alternativaAutobus(r, origen, destino, hora)).filter((a): a is Alternativa => a !== null)

  // Trazo real por calles (OSRM); si el servicio no responde se estima por distancia en línea recta
  const [callesPie, callesAuto] = await Promise.all([
    trazarPorCalles(origen, destino, 'pie'),
    trazarPorCalles(origen, destino, 'auto'),
  ])
  const kmEstimados = distanciaKm(origen, destino) * FACTOR_CALLES
  const FUENTE_CALLES = 'OSRM · OpenStreetMap'

  const kmPie = callesPie?.distancia_km ?? kmEstimados
  const pie: Alternativa = {
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
  const auto = (modo: 'taxi' | 'app'): Alternativa => ({
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

export async function buscarLugares({ cerca, categoria }: { cerca?: Coordenada; categoria?: string } = {}): Promise<Lugar[]> {
  await esperar(250)
  const lista = categoria ? LUGARES.filter((l) => l.categoria === categoria) : [...LUGARES]
  if (cerca) lista.sort((a, b) => distanciaKm(cerca, punto(a.ubicacion)) - distanciaKm(cerca, punto(b.ubicacion)))
  return lista
}

export async function generarItinerarios(peticion: PeticionItinerario): Promise<RespuestaItinerarios> {
  await esperar(700)
  return inferirItinerarios(LUGARES, peticion)
}
