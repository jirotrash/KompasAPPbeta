// Cliente HTTP común. Las páginas NUNCA llaman a fetch directamente: usan el api.ts de su módulo,
// que a su vez usa solicitud() de este archivo.
//
// VITE_USE_MOCK=true  → cada api.ts responde con datos de ejemplo (src/mock y mock.ts del dashboard)
// VITE_USE_MOCK=false → llama a la API FastAPI en VITE_API_URL
//
// Coordenadas: los parámetros de consulta van como "lat,lng" (como en CONTEXTO.md §8);
// las geometrías que regresa la API son GeoJSON ([lng, lat]), igual que en MongoDB.

import type { Coordenada, Sesion } from '../tipos/dominio.ts'

const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')
export const USA_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'

const CLAVE_SESION = 'bu_sesion'

const esSesion = (valor: unknown): valor is Sesion =>
  typeof valor === 'object' && valor !== null && typeof (valor as Sesion).token === 'string' && typeof (valor as Sesion).usuario === 'object'

export function leerSesion(): Sesion | null {
  try {
    const valor: unknown = JSON.parse(localStorage.getItem(CLAVE_SESION) ?? 'null')
    return esSesion(valor) ? valor : null
  } catch {
    return null
  }
}

export function guardarSesion(sesion: Sesion | null) {
  try {
    if (sesion) localStorage.setItem(CLAVE_SESION, JSON.stringify(sesion))
    else localStorage.removeItem(CLAVE_SESION)
  } catch {
    // Almacenamiento bloqueado (modo privado): la sesión solo dura mientras la pestaña esté abierta
  }
}

export class ErrorApi extends Error {
  estado: number

  constructor(mensaje: string, estado: number) {
    super(mensaje)
    this.estado = estado
  }
}

export const punto = ({ lat, lng }: Coordenada) => `${lat},${lng}`

type Parametros = Record<string, string | number | boolean | null | undefined>
type Opciones = { method?: string; params?: Parametros; body?: unknown }

const detalleDe = (datos: unknown) =>
  typeof datos === 'object' && datos !== null && typeof (datos as { detail?: unknown }).detail === 'string'
    ? (datos as { detail: string }).detail
    : 'Ocurrió un error en el servidor.'

export async function solicitud<T>(ruta: string, { method = 'GET', params, body }: Opciones = {}): Promise<T> {
  const url = new URL(`${API_URL}${ruta}`)
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, String(v))
  })

  const headers: Record<string, string> = { Accept: 'application/json' }
  if (body) headers['Content-Type'] = 'application/json'
  const token = leerSesion()?.token
  if (token) headers.Authorization = `Bearer ${token}`

  let respuesta: Response
  try {
    respuesta = await fetch(url, { method, headers, body: body ? JSON.stringify(body) : undefined })
  } catch {
    throw new ErrorApi('No hay conexión con el servidor. Intenta de nuevo.', 0)
  }

  const texto = await respuesta.text()
  const datos: unknown = texto ? JSON.parse(texto) : null
  if (!respuesta.ok) {
    // FastAPI regresa los errores en { detail }
    throw new ErrorApi(detalleDe(datos), respuesta.status)
  }
  return datos as T
}
