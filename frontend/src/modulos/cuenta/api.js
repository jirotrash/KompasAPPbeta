import { solicitud, USA_MOCK } from '../../compartido/api/cliente.js'
import * as mock from '../../mock/index.js'

// ─────────────────────────── Autenticación (MongoDB) ──────────────────────────

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
