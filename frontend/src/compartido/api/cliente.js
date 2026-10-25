// Cliente HTTP común. Las páginas NUNCA llaman a fetch directamente: usan el api.js de su módulo,
// que a su vez usa solicitud() de este archivo.
//
// VITE_USE_MOCK=true  → cada api.js responde con datos de ejemplo (src/mock y mock.js del dashboard)
// VITE_USE_MOCK=false → llama a la API FastAPI en VITE_API_URL
//
// Coordenadas: los parámetros de consulta van como "lat,lng" (como en CONTEXTO.md §8);
// las geometrías que regresa la API son GeoJSON ([lng, lat]), igual que en MongoDB.

const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')
export const USA_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'

const CLAVE_SESION = 'bu_sesion'

export function leerSesion() {
  try {
    return JSON.parse(localStorage.getItem(CLAVE_SESION))
  } catch {
    return null
  }
}

export function guardarSesion(sesion) {
  try {
    if (sesion) localStorage.setItem(CLAVE_SESION, JSON.stringify(sesion))
    else localStorage.removeItem(CLAVE_SESION)
  } catch {
    // Almacenamiento bloqueado (modo privado): la sesión solo dura mientras la pestaña esté abierta
  }
}

export class ErrorApi extends Error {
  constructor(mensaje, estado) {
    super(mensaje)
    this.estado = estado
  }
}

export const punto = ({ lat, lng }) => `${lat},${lng}`

export async function solicitud(ruta, { method = 'GET', params, body } = {}) {
  const url = new URL(`${API_URL}${ruta}`)
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v)
  })

  const headers = { Accept: 'application/json' }
  if (body) headers['Content-Type'] = 'application/json'
  const token = leerSesion()?.token
  if (token) headers.Authorization = `Bearer ${token}`

  let respuesta
  try {
    respuesta = await fetch(url, { method, headers, body: body ? JSON.stringify(body) : undefined })
  } catch {
    throw new ErrorApi('No hay conexión con el servidor. Intenta de nuevo.', 0)
  }

  const texto = await respuesta.text()
  const datos = texto ? JSON.parse(texto) : null
  if (!respuesta.ok) {
    // FastAPI regresa los errores en { detail }
    const detalle = typeof datos?.detail === 'string' ? datos.detail : 'Ocurrió un error en el servidor.'
    throw new ErrorApi(detalle, respuesta.status)
  }
  return datos
}
