// Una función por endpoint de /api/dashboard. Todos piden rol admin (403 para un usuario normal).
// Parámetros comunes: desde, hasta (YYYY-MM-DD) e incluir_demo (bool).

import { solicitud, USA_MOCK } from '../../compartido/api/cliente.ts'
import type { ArbolRuta, Ruta } from '../../compartido/tipos/dominio.ts'
import * as mock from './mock.ts'
import type { ComparativoBusqueda, EndpointDashboard, Filtros, ParadaRed, RespuestasDashboard } from './tipos.ts'

const pedir = <E extends EndpointDashboard>(endpoint: E, filtros: Filtros, extra: Record<string, string> = {}): Promise<RespuestasDashboard[E]> =>
  USA_MOCK
    ? mock.responder(endpoint, filtros)
    : solicitud<RespuestasDashboard[E]>(`/api/dashboard/${endpoint}`, {
        params: { desde: filtros.desde, hasta: filtros.hasta, incluir_demo: filtros.incluirDemo, ...extra },
      })

/** GET /api/dashboard/kpis → usuarios, planes, % con recomendación, recorridos, reportes vigentes y lugares */
export const obtenerKpis = (filtros: Filtros) => pedir('kpis', filtros)

/** GET /api/dashboard/series?agrupar=dia|semana|mes → serie (usuarios, planes, recorridos) y planes_por_interes */
export const obtenerSeries = (filtros: Filtros) => pedir('series', filtros, { agrupar: filtros.agrupar })

/** GET /api/dashboard/planes → por_interes, por_movilidad, por_contexto, presupuesto, tiempo_disponible, dia_hora, interes_por_contexto */
export const obtenerPlanes = (filtros: Filtros) => pedir('planes', filtros)

/** GET /api/dashboard/sistema-experto → por_estado, reglas_top, puntuacion_por_tipo, sin_datos_suficientes, por_version */
export const obtenerSistemaExperto = (filtros: Filtros) => pedir('sistema-experto', filtros)

/** GET /api/dashboard/movilidad → por_transporte, rutas_top, paradas_uso */
export const obtenerMovilidad = (filtros: Filtros) => pedir('movilidad', filtros)

/** GET /api/dashboard/reportes → por_tipo_estado, vigentes_vs_vencidos, puntos */
export const obtenerReportesDashboard = (filtros: Filtros) => pedir('reportes', filtros)

/** GET /api/dashboard/lugares → por_categoria, puntos */
export const obtenerLugaresDashboard = (filtros: Filtros) => pedir('lugares', filtros)

/** GET /api/dashboard/laboratorio → DFS, distancias, búsqueda informada, genético y transbordos */
export const obtenerLaboratorio = (filtros: Filtros) => pedir('laboratorio', filtros)

/** GET /api/dashboard/asistente → uso agregado del asistente (nunca el contenido de los mensajes) */
export const obtenerAsistente = (filtros: Filtros) => pedir('asistente', filtros)

// ───────────── Endpoints de apoyo (solo admin, sin pantalla de usuario) ─────────────

/** GET /api/dfs/paradas → nodos de la red académica (para elegir origen y destino del comparativo) */
export const obtenerParadasRed = (): Promise<ParadaRed[]> => (USA_MOCK ? mock.paradasRed() : solicitud<ParadaRed[]>('/api/dfs/paradas'))

/** GET /api/busqueda/comparar?origen=&destino= → DFS, UCS, voraz y A* en una tabla */
export const compararBusqueda = (origen: string, destino: string): Promise<ComparativoBusqueda> =>
  USA_MOCK ? mock.comparar(origen, destino) : solicitud<ComparativoBusqueda>('/api/busqueda/comparar', { params: { origen, destino } })

/** GET /api/rutas → trazos de la colección `rutas` */
export const obtenerRutas = (): Promise<Ruta[]> => (USA_MOCK ? mock.rutas() : solicitud<Ruta[]>('/api/rutas'))

/** GET /api/rutas/{id}/arbol → paradas de la ruta en orden (recorrido inorden del árbol binario) */
export const obtenerArbolRuta = (id: number): Promise<ArbolRuta> =>
  USA_MOCK ? mock.arbolRuta(id) : solicitud<ArbolRuta>(`/api/rutas/${id}/arbol`)
