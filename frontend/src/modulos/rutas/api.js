import { punto, solicitud, USA_MOCK } from '../../compartido/api/cliente.js'
import * as mock from '../../mock/index.js'

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
