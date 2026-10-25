import { solicitud, USA_MOCK } from '../../compartido/api/cliente.js'
import * as mock from '../../mock/index.js'

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
