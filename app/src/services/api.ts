// Único punto de acceso a la API. Las pantallas NUNCA llaman a fetch directamente.
//
// EXPO_PUBLIC_USE_MOCK=true  → responde con datos de ejemplo (src/services/mock)
// EXPO_PUBLIC_USE_MOCK=false → llama a la API FastAPI en EXPO_PUBLIC_API_URL
//
// En el celular "localhost" es el propio celular: usa la IP de tu PC, p. ej. http://192.168.1.50:8000
// Coordenadas en parámetros de consulta: "lat,lng". Geometrías que regresa la API: GeoJSON ([lng, lat]).

import type { Coordenada } from '@/constants/zona';
import type {
  Lugar,
  NuevoReporte,
  NuevoUsuario,
  PeticionPlan,
  RespuestaPlanes,
  RespuestaRutas,
  Sesion,
} from '@/types/dominio';

import * as mock from './mock';

const API_URL = (process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');
export const USA_MOCK = process.env.EXPO_PUBLIC_USE_MOCK !== 'false';
const TIEMPO_LIMITE_MS = 15000;

let token: string | null = null;
/** Lo llama el contexto de sesión al iniciar o cerrar sesión. */
export const usarToken = (nuevo: string | null) => {
  token = nuevo;
};

export class ErrorApi extends Error {
  constructor(
    mensaje: string,
    public estado: number,
  ) {
    super(mensaje);
  }
}

const punto = ({ lat, lng }: Coordenada) => `${lat},${lng}`;

async function solicitud<T>(
  ruta: string,
  { method = 'GET', params, body }: { method?: string; params?: Record<string, string | undefined>; body?: unknown } = {},
): Promise<T> {
  const consulta = new URLSearchParams(
    Object.entries(params ?? {}).filter((par): par is [string, string] => !!par[1]),
  ).toString();
  const url = `${API_URL}${ruta}${consulta ? `?${consulta}` : ''}`;

  const headers: Record<string, string> = { Accept: 'application/json' };
  if (body) headers['Content-Type'] = 'application/json';
  if (token) headers.Authorization = `Bearer ${token}`;

  const control = new AbortController();
  const temporizador = setTimeout(() => control.abort(), TIEMPO_LIMITE_MS);
  let respuesta: Response;
  try {
    respuesta = await fetch(url, { method, headers, body: body ? JSON.stringify(body) : undefined, signal: control.signal });
  } catch {
    throw new ErrorApi('No hay conexión con el servidor. Revisa tu internet o la IP de la API.', 0);
  } finally {
    clearTimeout(temporizador);
  }

  const texto = await respuesta.text();
  const datos = texto ? JSON.parse(texto) : null;
  if (!respuesta.ok) {
    // FastAPI regresa los errores en { detail }
    const detalle = typeof datos?.detail === 'string' ? datos.detail : 'Ocurrió un error en el servidor.';
    throw new ErrorApi(detalle, respuesta.status);
  }
  return datos as T;
}

// ─────────────────────────── Autenticación (MySQL) ───────────────────────────

/** POST /api/auth/login → { token, usuario } */
export const login = (datos: { email: string; password: string }) =>
  USA_MOCK ? mock.login(datos) : solicitud<Sesion>('/api/auth/login', { method: 'POST', body: datos });

/** POST /api/auth/register → { token, usuario } */
export const registrar = (datos: NuevoUsuario) =>
  USA_MOCK ? mock.registrar(datos) : solicitud<Sesion>('/api/auth/register', { method: 'POST', body: datos });

// ─────────────────────────────── Rutas (MongoDB) ──────────────────────────────

/**
 * GET /api/rutas?origen=lat,lng&destino=lat,lng&hora=HH:MM
 * Si no hay rutas verificadas, datos_suficientes = false y la app avisa (nunca se inventan).
 */
export const buscarRutas = (c: { origen: Coordenada; destino: Coordenada; hora: string }) =>
  USA_MOCK
    ? mock.buscarRutas(c)
    : solicitud<RespuestaRutas>('/api/rutas', { params: { origen: punto(c.origen), destino: punto(c.destino), hora: c.hora } });

// ────────────────────────────── Lugares (MongoDB) ─────────────────────────────

/** GET /api/lugares?cerca=lat,lng&categoria= → documentos de la colección `lugares` */
export const buscarLugares = (c: { cerca?: Coordenada; categoria?: string } = {}) =>
  USA_MOCK
    ? mock.buscarLugares(c)
    : solicitud<Lugar[]>('/api/lugares', { params: { cerca: c.cerca && punto(c.cerca), categoria: c.categoria } });

// ───────────────────────── Planes (sistema experto) ──────────────────────────

/**
 * POST /api/itinerarios — la API calcula los hechos y llama al motor de reglas de Einar.
 * Petición y respuesta: CONTEXTO.md §6.1 ("Del planificador a la API").
 * Extras opcionales que la app aprovecha si vienen: `tramos` en cada plan (traslados entre
 * paradas, incluido autobús) y `descartados` (lugares que no pasaron las reglas y por qué).
 */
export const generarPlanes = (peticion: PeticionPlan) =>
  USA_MOCK ? mock.generarPlanes(peticion) : solicitud<RespuestaPlanes>('/api/itinerarios', { method: 'POST', body: peticion });

// ─────────────────────────── Reportes comunitarios ────────────────────────────

// La base todavía no tiene tabla de reportes (BACKEND.md §10): por ahora SIEMPRE usan los datos
// de ejemplo, aunque EXPO_PUBLIC_USE_MOCK=false. Cuando exista el endpoint, volver a:
//   USA_MOCK ? mock.crearReporte(reporte) : solicitud<Reporte>('/api/reportes', { method: 'POST', body: reporte })
//   USA_MOCK ? mock.obtenerReportes(rutaId) : solicitud<Reporte[]>('/api/reportes', { params: { ruta_id: rutaId } })

/** POST /api/reportes → el reporte creado (estado "pendiente" y vigencia calculada por la API) */
export const crearReporte = (reporte: NuevoReporte) => mock.crearReporte(reporte);

/** GET /api/reportes?ruta_id= → reportes vigentes (sin ruta_id: todos los de la zona) */
export const obtenerReportes = (rutaId?: string) => mock.obtenerReportes(rutaId);
