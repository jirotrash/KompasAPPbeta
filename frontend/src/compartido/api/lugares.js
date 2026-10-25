// Lugares: los usan varias pantallas (Inicio, Rutas y Reportar) a través de useLugares.

import * as mock from '../../mock/index.js'
import { punto, solicitud, USA_MOCK } from './cliente.js'

// ────────────────────────────── Lugares (MongoDB) ─────────────────────────────

/**
 * GET /api/lugares?cerca=lat,lng&categoria=
 * @returns {Promise<Array<Lugar>>} documentos de la colección `lugares`
 */
export const buscarLugares = ({ cerca, categoria } = {}) =>
  USA_MOCK
    ? mock.buscarLugares({ cerca, categoria })
    : solicitud('/api/lugares', { params: { cerca: cerca ? punto(cerca) : undefined, categoria } })
