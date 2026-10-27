// Único punto de acceso a la API. Las pantallas NUNCA llaman a fetch directamente.
//
// EXPO_PUBLIC_USE_MOCK=true  → responde con datos de ejemplo (src/services/mock)
// EXPO_PUBLIC_USE_MOCK=false → llama a la API FastAPI en EXPO_PUBLIC_API_URL
//
// En el celular "localhost" es el propio celular: usa la IP de tu PC, p. ej. http://192.168.1.50:8000
// Coordenadas en parámetros de consulta: "lat,lng". Geometrías que regresa la API: GeoJSON ([lng, lat]).

import type { Coordenada } from '@/constants/zona';
import type {
  ComparacionDistancias,
  ComparacionGeo,
  Conversacion,
  EstadoAsistente,
  Lugar,
  NuevoReporte,
  NuevoUsuario,
  ParadaDFS,
  PeticionPlan,
  PuntoPlano,
  RespuestaDFS,
  RespuestaMensaje,
  RespuestaPlanes,
  RespuestaRutas,
  ResumenConversacion,
  Sesion,
} from '@/types/dominio';

import * as mock from './mock';
import * as mockAsistente from './mock/asistente';

const API_URL = (process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');
export const USA_MOCK = process.env.EXPO_PUBLIC_USE_MOCK !== 'false';
const TIEMPO_LIMITE_MS = 15000;
// El modelo local puede tardar (sobre todo la primera respuesta, mientras Ollama lo carga)
const TIEMPO_LIMITE_ASISTENTE_MS = 120000;

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
  {
    method = 'GET',
    params,
    body,
    tiempoLimiteMs = TIEMPO_LIMITE_MS,
  }: { method?: string; params?: Record<string, string | undefined>; body?: unknown; tiempoLimiteMs?: number } = {},
): Promise<T> {
  const consulta = new URLSearchParams(
    Object.entries(params ?? {}).filter((par): par is [string, string] => !!par[1]),
  ).toString();
  const url = `${API_URL}${ruta}${consulta ? `?${consulta}` : ''}`;

  const headers: Record<string, string> = { Accept: 'application/json' };
  if (body) headers['Content-Type'] = 'application/json';
  if (token) headers.Authorization = `Bearer ${token}`;

  const control = new AbortController();
  const temporizador = setTimeout(() => control.abort(), tiempoLimiteMs);
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

// ─────────────────────────── Autenticación (MongoDB) ─────────────────────────

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

// ───────────────── Demostración académica DFS ─────────────────

/**
 * Estos endpoints se consultan siempre en el backend: el modo mock no contiene
 * la red DFS. Requiere EXPO_PUBLIC_API_URL apuntando al servidor local.
 */
export const listarParadasDfs = () => solicitud<ParadaDFS[]>('/api/dfs/paradas');

export const buscarRutasDfs = (origen: string, destino: string, limiteProfundidad: number) =>
  solicitud<RespuestaDFS>('/api/dfs/buscar', {
    params: { origen, destino, limite_profundidad: String(limiteProfundidad) },
  });

// ──────────────── Laboratorio de métricas de distancia ────────────────

/** GET /api/distancias/plano?a=x,y&b=x,y → Euclidiana vs. Manhattan entre dos puntos del plano */
export const compararDistancias = (a: PuntoPlano, b: PuntoPlano) =>
  USA_MOCK
    ? mock.compararDistancias(a, b)
    : solicitud<ComparacionDistancias>('/api/distancias/plano', { params: { a: `${a.x},${a.y}`, b: `${b.x},${b.y}` } });

/** GET /api/distancias/geo?origen=lat,lng&destino=lat,lng → Euclidiana vs. Manhattan en el mapa (km) */
export const compararDistanciasGeo = (origen: Coordenada, destino: Coordenada) =>
  USA_MOCK
    ? mock.compararDistanciasGeo(origen, destino)
    : solicitud<ComparacionGeo>('/api/distancias/geo', { params: { origen: punto(origen), destino: punto(destino) } });

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

// ─────────────────────── Asistente (Ollama, siempre a través de la API) ───────────────────────

/** GET /api/asistente/estado → { disponible, modelo } (la API hace ping a Ollama) */
export const estadoAsistente = () => (USA_MOCK ? mockAsistente.estado() : solicitud<EstadoAsistente>('/api/asistente/estado'));

/** GET /api/asistente/conversaciones → conversaciones del usuario, de la más reciente a la más antigua */
export const listarConversaciones = () =>
  USA_MOCK ? mockAsistente.listar() : solicitud<ResumenConversacion[]>('/api/asistente/conversaciones');

/** POST /api/asistente/conversaciones → conversación vacía */
export const crearConversacion = () =>
  USA_MOCK ? mockAsistente.crear() : solicitud<Conversacion>('/api/asistente/conversaciones', { method: 'POST' });

/** GET /api/asistente/conversaciones/{id} → conversación completa (404 si no es del usuario) */
export const obtenerConversacion = (id: string) =>
  USA_MOCK ? mockAsistente.obtener(id) : solicitud<Conversacion>(`/api/asistente/conversaciones/${encodeURIComponent(id)}`);

/**
 * POST /api/asistente/conversaciones/{id}/mensajes → respuesta del asistente y tarjetas de rutas o planes.
 * `ubicacion` sirve para "desde aquí" y para armar salidas; la API no la guarda. 503 si Ollama no responde.
 */
export const enviarMensaje = (id: string, texto: string, ubicacion?: Coordenada) =>
  USA_MOCK
    ? mockAsistente.enviar(id, texto, ubicacion)
    : solicitud<RespuestaMensaje>(`/api/asistente/conversaciones/${encodeURIComponent(id)}/mensajes`, {
        method: 'POST',
        body: { texto, ubicacion },
        tiempoLimiteMs: TIEMPO_LIMITE_ASISTENTE_MS,
      });

/** DELETE /api/asistente/conversaciones/{id} → borrado lógico */
export const borrarConversacion = (id: string) =>
  USA_MOCK ? mockAsistente.borrar(id) : solicitud<null>(`/api/asistente/conversaciones/${encodeURIComponent(id)}`, { method: 'DELETE' });
