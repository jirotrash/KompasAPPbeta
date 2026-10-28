// Una función por endpoint de /api/admin/... Todos piden rol admin (403 para un usuario normal).
// Con VITE_USE_MOCK=true responde mock.ts, que guarda los cambios en memoria mientras la pestaña esté abierta.

import { solicitud, USA_MOCK } from '../../compartido/api/cliente.ts'
import * as mock from './mock.ts'
import type {
  Busqueda,
  CategoriaAdmin,
  CategoriaEntrada,
  EstadoReporte,
  EstadoSolicitud,
  LugarAdmin,
  LugarEntrada,
  ReporteAdmin,
  RutaAdmin,
  RutaEntrada,
  Solicitud,
  TransporteAdmin,
  TransporteEntrada,
} from './tipos.ts'

const guardar = <T>(ruta: string, id: number | undefined, body: unknown) =>
  solicitud<T>(id === undefined ? ruta : `${ruta}/${id}`, { method: id === undefined ? 'POST' : 'PUT', body })

const borrar = (ruta: string, id: number | string) => solicitud<null>(`${ruta}/${encodeURIComponent(id)}`, { method: 'DELETE' })

// ───────────── Rutas ─────────────

/** GET /api/admin/rutas → nombre, trazo [[lng, lat], ...] y paradas */
export const obtenerRutas = () => (USA_MOCK ? mock.rutas.listar() : solicitud<RutaAdmin[]>('/api/admin/rutas'))
/** POST /api/admin/rutas (sin id) o PUT /api/admin/rutas/{id} */
export const guardarRuta = (datos: RutaEntrada, id?: number) =>
  USA_MOCK ? mock.rutas.guardar(datos, id) : guardar<RutaAdmin>('/api/admin/rutas', id, datos)
/** DELETE /api/admin/rutas/{id} (borrado lógico) */
export const borrarRuta = (id: number) => (USA_MOCK ? mock.rutas.borrar(id) : borrar('/api/admin/rutas', id))

// ───────────── Lugares ─────────────

export const obtenerLugares = () => (USA_MOCK ? mock.lugares.listar() : solicitud<LugarAdmin[]>('/api/admin/lugares'))
export const guardarLugar = (datos: LugarEntrada, id?: number) =>
  USA_MOCK ? mock.lugares.guardar(datos, id) : guardar<LugarAdmin>('/api/admin/lugares', id, datos)
export const borrarLugar = (id: number) => (USA_MOCK ? mock.lugares.borrar(id) : borrar('/api/admin/lugares', id))

// ───────────── Categorías y transportes ─────────────

export const obtenerCategorias = () => (USA_MOCK ? mock.categorias.listar() : solicitud<CategoriaAdmin[]>('/api/admin/categorias'))
export const guardarCategoria = (datos: CategoriaEntrada, id?: number) =>
  USA_MOCK ? mock.categorias.guardar(datos, id) : guardar<CategoriaAdmin>('/api/admin/categorias', id, datos)
/** 409 si está protegida o si todavía hay lugares con esa categoría */
export const borrarCategoria = (id: number) => (USA_MOCK ? mock.categorias.borrar(id) : borrar('/api/admin/categorias', id))

export const obtenerTransportes = () => (USA_MOCK ? mock.transportes.listar() : solicitud<TransporteAdmin[]>('/api/admin/transportes'))
export const guardarTransporte = (datos: TransporteEntrada, id?: number) =>
  USA_MOCK ? mock.transportes.guardar(datos, id) : guardar<TransporteAdmin>('/api/admin/transportes', id, datos)
export const borrarTransporte = (id: number) => (USA_MOCK ? mock.transportes.borrar(id) : borrar('/api/admin/transportes', id))

// ───────────── Reportes ─────────────

/** GET /api/admin/reportes?estado= → vigentes y vencidos, del más reciente al más antiguo */
export const obtenerReportes = (estado?: EstadoReporte) =>
  USA_MOCK ? mock.reportes.listar(estado) : solicitud<ReporteAdmin[]>('/api/admin/reportes', { params: { estado } })
/** PATCH /api/admin/reportes/{id} → verificado, descartado o pendiente */
export const moderarReporte = (id: string, estado: EstadoReporte) =>
  USA_MOCK
    ? mock.reportes.moderar(id, estado)
    : solicitud<ReporteAdmin>(`/api/admin/reportes/${encodeURIComponent(id)}`, { method: 'PATCH', body: { estado } })
export const borrarReporte = (id: string) => (USA_MOCK ? mock.reportes.borrar(id) : borrar('/api/admin/reportes', id))

// ───────────── Lo que piden los usuarios ─────────────

/** GET /api/admin/busquedas?sin_autobus= → búsquedas de "¿Cómo llego?" */
export const obtenerBusquedas = (sinAutobus: boolean) =>
  USA_MOCK ? mock.busquedas(sinAutobus) : solicitud<Busqueda[]>('/api/admin/busquedas', { params: { sin_autobus: sinAutobus } })

/** GET /api/admin/solicitudes-rutas?estado= → rutas que la gente pidió desde la app */
export const obtenerSolicitudes = (estado?: EstadoSolicitud) =>
  USA_MOCK ? mock.solicitudes.listar(estado) : solicitud<Solicitud[]>('/api/admin/solicitudes-rutas', { params: { estado } })
export const atenderSolicitud = (id: string, estado: EstadoSolicitud, nota_admin: string | null) =>
  USA_MOCK
    ? mock.solicitudes.atender(id, estado, nota_admin)
    : solicitud<Solicitud>(`/api/admin/solicitudes-rutas/${encodeURIComponent(id)}`, { method: 'PATCH', body: { estado, nota_admin } })
export const borrarSolicitud = (id: string) => (USA_MOCK ? mock.solicitudes.borrar(id) : borrar('/api/admin/solicitudes-rutas', id))
