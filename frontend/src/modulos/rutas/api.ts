import { punto, solicitud, USA_MOCK } from '../../compartido/api/cliente.ts'
import type { Coordenada, RespuestaRutas, RutaEjemplo } from '../../compartido/tipos/dominio.ts'
import * as mock from '../../mock/index.ts'

// ─────────────────────────────── Rutas (MongoDB) ──────────────────────────────

/**
 * GET /api/rutas?origen=lat,lng&destino=lat,lng&hora=HH:MM
 * Opciones en autobús (directas o con transbordo, con parada_subida, parada_bajada, tramo_en_ruta y
 * paradas_intermedias), a pie y en taxi/app. Si no hay datos verificados, datos_suficientes = false.
 */
export const buscarRutas = ({ origen, destino, hora }: { origen: Coordenada; destino: Coordenada; hora: string }): Promise<RespuestaRutas> =>
  USA_MOCK
    ? mock.buscarRutas({ origen, destino, hora })
    : solicitud<RespuestaRutas>('/api/rutas', { params: { origen: punto(origen), destino: punto(destino), hora } })

/** GET /api/rutas/{id} → documento de la colección `rutas` (paradas, trazo, horario). */
export const obtenerRuta = (id: string): Promise<RutaEjemplo> =>
  USA_MOCK ? mock.obtenerRuta(id) : solicitud<RutaEjemplo>(`/api/rutas/${encodeURIComponent(id)}`)
