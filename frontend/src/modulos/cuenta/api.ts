import { solicitud, USA_MOCK } from '../../compartido/api/cliente.ts'
import type { Credenciales, NuevoUsuario, Sesion } from '../../compartido/tipos/dominio.ts'
import * as mock from '../../mock/index.ts'

// ─────────────────────────── Autenticación (MongoDB) ──────────────────────────

/** POST /api/auth/login → { token, usuario } */
export const login = (datos: Credenciales): Promise<Sesion> =>
  USA_MOCK ? mock.login(datos) : solicitud<Sesion>('/api/auth/login', { method: 'POST', body: datos })

/** POST /api/auth/register → { token, usuario } */
export const registrar = (datos: NuevoUsuario): Promise<Sesion> =>
  USA_MOCK ? mock.registrar(datos) : solicitud<Sesion>('/api/auth/register', { method: 'POST', body: datos })
