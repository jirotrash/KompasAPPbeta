import { solicitud, USA_MOCK } from '../../compartido/api/cliente.ts'
import type { NuevoReporte, Reporte } from '../../compartido/tipos/dominio.ts'
import * as mock from '../../mock/index.ts'

// ─────────────────────────── Reportes comunitarios ────────────────────────────

/** POST /api/reportes → el reporte con estado 'pendiente' y vigente_hasta calculado por la API */
export const crearReporte = (reporte: NuevoReporte): Promise<Reporte> =>
  USA_MOCK ? mock.crearReporte(reporte) : solicitud<Reporte>('/api/reportes', { method: 'POST', body: reporte })

/** GET /api/reportes?ruta_id= → reportes vigentes (sin ruta_id: todos los vigentes de la zona). */
export const obtenerReportes = (rutaId?: string): Promise<Reporte[]> =>
  USA_MOCK ? mock.obtenerReportes(rutaId) : solicitud<Reporte[]>('/api/reportes', { params: { ruta_id: rutaId } })
