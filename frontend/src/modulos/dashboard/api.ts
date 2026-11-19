// Una función por endpoint de /api/dashboard. Todos piden rol admin (403 para un usuario normal).
// Parámetros comunes: desde, hasta (YYYY-MM-DD) e incluir_demo (bool).

import { solicitud, USA_MOCK } from '../../compartido/api/cliente.ts'
import type { ArbolRuta, Ruta } from '../../compartido/tipos/dominio.ts'
import * as mock from './mock.ts'
import * as mockML from './mockML.ts'
import type { ComparacionAlgoritmos, DiagnosticoAjuste, OptimizacionHiperparametros } from './tiposML.ts'
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

// ───────────── Machine Learning supervisado (prácticas P04, P05 y P06 en /api/ia) ─────────────
// No usan los filtros de fecha: entrenan sobre el CSV limpio del pipeline de datos.

/** GET /api/ia/diagnostico-ajuste → partición 60/20/20, árboles de profundidad 1/4/libre y curva de complejidad */
export const obtenerDiagnosticoAjuste = (): Promise<DiagnosticoAjuste> =>
  USA_MOCK ? mockML.diagnosticoAjuste() : solicitud<DiagnosticoAjuste>('/api/ia/diagnostico-ajuste')

/** GET /api/ia/comparar-algoritmos → Árbol de decisión vs. Random Forest vs. KNN */
export const obtenerComparacionAlgoritmos = (): Promise<ComparacionAlgoritmos> =>
  USA_MOCK ? mockML.compararAlgoritmos() : solicitud<ComparacionAlgoritmos>('/api/ia/comparar-algoritmos')

/** GET /api/ia/optimizar-hiperparametros → GridSearchCV con 5 pliegues (tarda unos segundos) */
export const obtenerOptimizacionHiperparametros = (): Promise<OptimizacionHiperparametros> =>
  USA_MOCK ? mockML.optimizarHiperparametros() : solicitud<OptimizacionHiperparametros>('/api/ia/optimizar-hiperparametros')

/** GET /api/busqueda/comparar?origen=&destino= → DFS, UCS, voraz y A* en una tabla */
export const compararBusqueda = (origen: string, destino: string): Promise<ComparativoBusqueda> =>
  USA_MOCK ? mock.comparar(origen, destino) : solicitud<ComparativoBusqueda>('/api/busqueda/comparar', { params: { origen, destino } })

/** GET /api/rutas → trazos de la colección `rutas` */
export const obtenerRutas = (): Promise<Ruta[]> => (USA_MOCK ? mock.rutas() : solicitud<Ruta[]>('/api/rutas'))

/** GET /api/rutas/{id}/arbol → paradas de la ruta en orden (recorrido inorden del árbol binario) */
export const obtenerArbolRuta = (id: number): Promise<ArbolRuta> =>
  USA_MOCK ? mock.arbolRuta(id) : solicitud<ArbolRuta>(`/api/rutas/${id}/arbol`)

// ───────────── Machine Learning Avanzado y Deep Learning (P14 a P27 en /api/ia) ─────────────

/** POST /api/ia/motor-recomendacion-integral → Random Forest + K-Means + PCA + Directivas de Movilidad (P14) */
export const evaluarRecomendacionIntegral = (datos: {
  distancia_km: number
  hora_dia: number
  duracion_min: number
  presupuesto_mxn: number
  es_hora_pico?: number
  clima_lluvia?: number
}) => solicitud<any>('/api/ia/motor-recomendacion-integral', { metodo: 'POST', cuerpo: datos })

/** GET /api/ia/analitica/reporte-clusters → Estadísticas de los 4 clusters de viajeros en MongoDB Atlas (P16) */
export const obtenerReporteClusters = () => solicitud<any[]>('/api/ia/analitica/reporte-clusters')

/** GET /api/ia/analitica/horas-pico → Demanda y congestión por hora (P16) */
export const obtenerHorasPicoAnalitica = () => solicitud<any[]>('/api/ia/analitica/horas-pico')

/** GET /api/ia/deep-learning/comparar-modelos → Benchmark Decision Tree vs Random Forest vs CNN 1D (P25) */
export const obtenerBenchmarkDL = () => solicitud<any>('/api/ia/deep-learning/comparar-modelos')

/** POST /api/ia/deep-learning/clasificar-congestion → Diagnóstico de congestión con CNN 1D en PyTorch (P24) */
export const clasificarCongestionCNN = (secuencia: number[][]) =>
  solicitud<any>('/api/ia/deep-learning/clasificar-congestion', { metodo: 'POST', cuerpo: { secuencia } })

/** POST /api/ia/deep-learning/predecir-eta → Tiempo continuo de llegada con CNN 1D regresora (P27) */
export const predecirEtaCNN = (secuencia: number[][]) =>
  solicitud<any>('/api/ia/deep-learning/predecir-eta', { metodo: 'POST', cuerpo: { secuencia } })

