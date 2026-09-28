// Único punto de acceso a la API. Las páginas NUNCA llaman a fetch directamente.
//
// VITE_USE_MOCK=true  → responde con datos de ejemplo (src/services/mock)
// VITE_USE_MOCK=false → llama a la API FastAPI en VITE_API_URL
//
// Coordenadas: los parámetros de consulta van como "lat,lng" (como en CONTEXTO.md §8);
// las geometrías que regresa la API son GeoJSON ([lng, lat]), igual que en MongoDB.

import * as mock from './mock/index.js'

const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')
export const USA_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'

const CLAVE_SESION = 'bu_sesion'

export function leerSesion() {
  try {
    return JSON.parse(localStorage.getItem(CLAVE_SESION))
  } catch {
    return null
  }
}

export function guardarSesion(sesion) {
  try {
    if (sesion) localStorage.setItem(CLAVE_SESION, JSON.stringify(sesion))
    else localStorage.removeItem(CLAVE_SESION)
  } catch {
    // Almacenamiento bloqueado (modo privado): la sesión solo dura mientras la pestaña esté abierta
  }
}

export class ErrorApi extends Error {
  constructor(mensaje, estado) {
    super(mensaje)
    this.estado = estado
  }
}

const punto = ({ lat, lng }) => `${lat},${lng}`

async function solicitud(ruta, { method = 'GET', params, body } = {}) {
  const url = new URL(`${API_URL}${ruta}`)
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v)
  })

  const headers = { Accept: 'application/json' }
  if (body) headers['Content-Type'] = 'application/json'
  const token = leerSesion()?.token
  if (token) headers.Authorization = `Bearer ${token}`

  let respuesta
  try {
    respuesta = await fetch(url, { method, headers, body: body ? JSON.stringify(body) : undefined })
  } catch {
    throw new ErrorApi('No hay conexión con el servidor. Intenta de nuevo.', 0)
  }

  const texto = await respuesta.text()
  const datos = texto ? JSON.parse(texto) : null
  if (!respuesta.ok) {
    // FastAPI regresa los errores en { detail }
    const detalle = typeof datos?.detail === 'string' ? datos.detail : 'Ocurrió un error en el servidor.'
    throw new ErrorApi(detalle, respuesta.status)
  }
  return datos
}

// ─────────────────────────── Autenticación (MySQL) ───────────────────────────

/**
 * POST /api/auth/login
 * @param {{email: string, password: string}} datos
 * @returns {Promise<{token: string, usuario: {id: number, nombre: string, email: string, rol: string}}>}
 */
export const login = (datos) => (USA_MOCK ? mock.login(datos) : solicitud('/api/auth/login', { method: 'POST', body: datos }))

/**
 * POST /api/auth/register
 * @param {{nombre: string, email: string, password: string}} datos
 * @returns {Promise<{token: string, usuario: object}>}
 */
export const registrar = (datos) =>
  USA_MOCK ? mock.registrar(datos) : solicitud('/api/auth/register', { method: 'POST', body: datos })

// ─────────────────────────────── Rutas (MongoDB) ──────────────────────────────

/**
 * GET /api/rutas?origen=lat,lng&destino=lat,lng&hora=HH:MM
 * @param {{origen: {lat,lng}, destino: {lat,lng}, hora: string}} consulta
 * @returns {Promise<{
 *   datos_suficientes: boolean,
 *   mensaje?: string,
 *   alternativas: Array<{
 *     id: string,
 *     modo: 'pie' | 'autobus' | 'taxi' | 'app',
 *     ruta_id?: string, linea?: string, sentido?: string, tarifa?: number,
 *     abordaje?: {nombre: string, ubicacion: GeoJSONPoint},
 *     descenso?: {nombre: string, ubicacion: GeoJSONPoint},
 *     transbordos: Array<{nombre: string, ubicacion: GeoJSONPoint, linea: string}>,
 *     tiempos: {caminata: number|null, espera: number|null, trayecto: number|null, transbordos: number|null},
 *     tipo_horario: 'programado' | 'actualizado' | null,
 *     trazo?: GeoJSONLineString,        // por calles en pie/taxi/app; por paradas en autobús
 *     distancia_km?: number,
 *     fuente: string, fecha_verificacion: string|null,
 *     reglas_cumplidas?: Array<{id: string, descripcion: string}>,
 *     avisos?: string[],
 *     ejemplo?: boolean
 *   }>
 * }>}
 */
export const buscarRutas = ({ origen, destino, hora }) =>
  USA_MOCK
    ? mock.buscarRutas({ origen, destino, hora })
    : solicitud('/api/rutas', { params: { origen: punto(origen), destino: punto(destino), hora } })

/** GET /api/rutas/{id} → documento de la colección `rutas` (paradas, trazo, horario). */
export const obtenerRuta = (id) => (USA_MOCK ? mock.obtenerRuta(id) : solicitud(`/api/rutas/${encodeURIComponent(id)}`))

// ────────────────────────────── Lugares (MongoDB) ─────────────────────────────

/**
 * GET /api/lugares?cerca=lat,lng&categoria=
 * @returns {Promise<Array<Lugar>>} documentos de la colección `lugares`
 */
export const buscarLugares = ({ cerca, categoria } = {}) =>
  USA_MOCK
    ? mock.buscarLugares({ cerca, categoria })
    : solicitud('/api/lugares', { params: { cerca: cerca ? punto(cerca) : undefined, categoria } })

// ───────────────────────── Itinerarios (sistema experto) ──────────────────────

/**
 * POST /api/itinerarios — la API calcula los hechos y llama al motor de reglas (Einar).
 * @param {{
 *   contexto: 'cita' | 'amigos' | 'familia' | 'cotidiano',
 *   presupuesto: number, tiempo_min: number, gustos: string[],
 *   hora: string, dia: 'lun'|'mar'|'mie'|'jue'|'vie'|'sab'|'dom',
 *   origen: {lat, lng}
 * }} peticion
 * @returns {Promise<{
 *   datos_suficientes: boolean,
 *   mensaje?: string,
 *   itinerarios: Array<{
 *     id: string, titulo: string,
 *     lugares: Array<Lugar>,
 *     costo_total: number, tiempo_total_min: number,
 *     reglas_cumplidas: Array<{id: string, descripcion: string}>,
 *     explicacion: string
 *   }>,                               // máximo 3
 *   descartados: Array<{
 *     lugar: Lugar,
 *     reglas: Array<{id: string, descripcion: string}>   // por qué se descartó
 *   }>
 * }>}
 */
export const generarItinerarios = (peticion) =>
  USA_MOCK ? mock.generarItinerarios(peticion) : solicitud('/api/itinerarios', { method: 'POST', body: peticion })

// ─────────────────────────── Reportes comunitarios ────────────────────────────

/**
 * POST /api/reportes
 * @param {{
 *   tipo: 'cierre_total' | 'accidente' | 'manifestacion' | 'afluencia',
 *   nivel_afluencia?: 'baja' | 'media' | 'alta',
 *   ubicacion: GeoJSONPoint, ruta_id?: string, lugar_id?: string,
 *   observado_en: string, comentario?: string
 * }} reporte
 * @returns {Promise<Reporte>} con estado 'pendiente' y vigente_hasta calculado por la API
 */
export const crearReporte = (reporte) =>
  USA_MOCK ? mock.crearReporte(reporte) : solicitud('/api/reportes', { method: 'POST', body: reporte })

/** GET /api/reportes?ruta_id= → reportes vigentes (sin ruta_id: todos los vigentes de la zona). */
export const obtenerReportes = (rutaId) =>
  USA_MOCK ? mock.obtenerReportes(rutaId) : solicitud('/api/reportes', { params: { ruta_id: rutaId } })
