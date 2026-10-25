import { solicitud, USA_MOCK } from '../../compartido/api/cliente.js'
import * as mock from '../../mock/index.js'

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
