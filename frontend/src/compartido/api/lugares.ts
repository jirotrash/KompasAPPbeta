// Lugares: los usan varias pantallas (Inicio, Rutas y Reportar) a través de useLugares.

import * as mock from '../../mock/index.ts'
import type { Coordenada, Lugar } from '../tipos/dominio.ts'
import { punto, solicitud, USA_MOCK } from './cliente.ts'

// ────────────────────────────── Lugares (MongoDB) ─────────────────────────────

/** GET /api/lugares?cerca=lat,lng&categoria= → documentos de la colección `lugares` */
export const buscarLugares = ({ cerca, categoria }: { cerca?: Coordenada; categoria?: string } = {}): Promise<Lugar[]> =>
  USA_MOCK
    ? mock.buscarLugares({ cerca, categoria })
    : solicitud<Lugar[]>('/api/lugares', { params: { cerca: cerca ? punto(cerca) : undefined, categoria } })
