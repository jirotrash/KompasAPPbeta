// Una función por endpoint de /api/dashboard. Todos piden rol admin (403 para un usuario normal).
// Parámetros comunes: desde, hasta (YYYY-MM-DD) e incluir_demo (bool).

import { solicitud, USA_MOCK } from '../../compartido/api/cliente.js'
import * as mock from './mock.js'

const pedir = (endpoint, filtros, extra = {}) =>
  USA_MOCK
    ? mock.responder(endpoint, { ...filtros, ...extra })
    : solicitud(`/api/dashboard/${endpoint}`, {
        params: { desde: filtros.desde, hasta: filtros.hasta, incluir_demo: filtros.incluirDemo, ...extra },
      })

/**
 * GET /api/dashboard/kpis
 * @param {{desde?: string, hasta?: string, incluirDemo: boolean}} filtros
 * @returns {Promise<{usuarios_totales: number, usuarios_nuevos: number, planes: number,
 *   porcentaje_con_recomendacion: number, recorridos: number, tiempo_promedio_recorrido_min: number|null,
 *   reportes_vigentes: number, lugares: number, incluye_demo: boolean}>}
 */
export const obtenerKpis = (filtros) => pedir('kpis', filtros)

/**
 * GET /api/dashboard/series?agrupar=dia|semana|mes
 * @returns {Promise<{serie: Array<{fecha, usuarios, planes, recorridos}>, planes_por_interes: Array<{fecha, comer, cafe, cultura, entretenimiento, aire_libre}>}>}
 */
export const obtenerSeries = (filtros) => pedir('series', filtros, { agrupar: filtros.agrupar })

/** GET /api/dashboard/planes → por_interes, por_movilidad, por_contexto, presupuesto, tiempo_disponible, dia_hora, interes_por_contexto */
export const obtenerPlanes = (filtros) => pedir('planes', filtros)

/** GET /api/dashboard/sistema-experto → por_estado, reglas_top, puntuacion_por_tipo, sin_datos_suficientes, por_version */
export const obtenerSistemaExperto = (filtros) => pedir('sistema-experto', filtros)

/** GET /api/dashboard/movilidad → por_transporte, rutas_top */
export const obtenerMovilidad = (filtros) => pedir('movilidad', filtros)

/** GET /api/dashboard/reportes → por_tipo_estado, vigentes_vs_vencidos, puntos */
export const obtenerReportesDashboard = (filtros) => pedir('reportes', filtros)

/** GET /api/dashboard/lugares → por_categoria, puntos */
export const obtenerLugaresDashboard = (filtros) => pedir('lugares', filtros)

/** GET /api/dashboard/laboratorio → dfs_puntos, dfs_pares_top, distancias_puntos */
export const obtenerLaboratorio = (filtros) => pedir('laboratorio', filtros)
