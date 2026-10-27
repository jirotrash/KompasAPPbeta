import { solicitud, USA_MOCK } from '../../compartido/api/cliente.ts'
import type { PeticionItinerario, RespuestaItinerarios } from '../../compartido/tipos/dominio.ts'
import * as mock from '../../mock/index.ts'

// ───────────────────────── Itinerarios (sistema experto) ──────────────────────

/**
 * POST /api/itinerarios — la API calcula los hechos y llama al motor de reglas (Einar).
 * Regresa hasta 3 itinerarios y los lugares descartados con las reglas que lo explican.
 */
export const generarItinerarios = (peticion: PeticionItinerario): Promise<RespuestaItinerarios> =>
  USA_MOCK ? mock.generarItinerarios(peticion) : solicitud<RespuestaItinerarios>('/api/itinerarios', { method: 'POST', body: peticion })
