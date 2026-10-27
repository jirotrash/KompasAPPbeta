// Forma de cada respuesta de /api/dashboard/* (backend/app/modulos/dashboard/esquemas.py)
// y de los endpoints de apoyo que usa el dashboard (/api/busqueda/comparar, /api/rutas/{id}/arbol).

export type Agrupar = 'dia' | 'semana' | 'mes'

/** Lo que manda el dashboard a la API (desde/hasta en YYYY-MM-DD, incluyen el día completo). */
export type Filtros = { desde?: string; hasta?: string; agrupar: Agrupar; incluirDemo: boolean }

export type Periodo = { desde: string; hasta: string; incluir_demo: boolean }

type Base = { periodo: Periodo; incluye_demo: boolean }

export type Kpis = Base & {
  usuarios_totales: number
  usuarios_nuevos: number
  planes: number
  planes_evaluados: number
  porcentaje_con_recomendacion: number
  recorridos: number
  tiempo_promedio_recorrido_min: number | null
  reportes_vigentes: number
  lugares: number
}

export type PuntoSerie = { fecha: string; usuarios: number; planes: number; recorridos: number }
export type InteresesSerie = { fecha: string; comer: number; cafe: number; cultura: number; entretenimiento: number; aire_libre: number }
export type Series = Base & { agrupar: Agrupar; serie: PuntoSerie[]; planes_por_interes: InteresesSerie[] }

export type Interes = 'comer' | 'cafe' | 'cultura' | 'entretenimiento' | 'aire_libre'
export type Movilidad = 'caminando' | 'transporte_publico' | 'taxi_app' | 'combinado'
export type Contexto = 'solo' | 'pareja' | 'amigos' | 'familia'

export type BarraPresupuesto = { rango: string; desde: number; total: number }
export type BarraTiempo = { rango: string; desde_min: number; total: number }
export type CeldaDiaHora = { dia: number; hora: number; total: number }
export type PerfilInteres = { interes: Interes } & Record<Contexto, number>

export type Planes = Base & {
  total: number
  por_interes: { interes: Interes; total: number }[]
  por_movilidad: { movilidad: Movilidad; total: number }[]
  por_contexto: { contexto: Contexto; total: number }[]
  presupuesto: BarraPresupuesto[]
  tiempo_disponible: BarraTiempo[]
  dia_hora: CeldaDiaHora[]
  interes_por_contexto: PerfilInteres[]
}

export type SistemaExperto = Base & {
  por_estado: { estado: string; total: number }[]
  reglas_top: { id: string; descripcion: string | null; total: number }[]
  puntuacion_por_tipo: { tipo: string; promedio: number | null; minimo: number | null; maximo: number | null; total: number }[]
  sin_datos_suficientes: number
  por_version: { version: string; total: number }[]
}

export type TiemposTransporte = {
  transporte: string
  clave: string
  total: number
  promedio: number | null
  minimo: number | null
  maximo: number | null
}

export type ParadaUso = { id_ruta: number | null; nombre: string; lat: number; lng: number; subidas: number; bajadas: number; total: number }

export type MovilidadDashboard = Base & {
  por_transporte: TiemposTransporte[]
  rutas_top: { id_ruta: number; ruta: string; total: number; promedio: number | null }[]
  /** Paradas donde más se sube y se baja (de "¿Cómo llego?"); opcional en la v0.5 */
  paradas_uso?: ParadaUso[]
}

export type TipoReporte = 'cierre_total' | 'accidente' | 'manifestacion' | 'afluencia'

export type PuntoReporte = { lat: number; lng: number; tipo: TipoReporte; estado?: string | null; vigente: boolean }

export type Reportes = Base & {
  por_tipo_estado: { tipo: TipoReporte; pendiente: number; verificado: number; descartado: number }[]
  vigentes_vs_vencidos: { vigentes: number; vencidos: number }
  puntos: PuntoReporte[]
}

export type PuntoLugar = { id: number; nombre: string; lat: number; lng: number; categoria: string | null }
export type Lugares = Base & { por_categoria: { categoria: string; total: number }[]; puntos: PuntoLugar[] }

export type BurbujaDFS = { limite_profundidad: number; nodos: number; rutas: number | null; consultas: number }

export type AlgoritmoBusqueda = {
  algoritmo: string
  heuristica: string | null
  etiqueta: string
  consultas: number
  nodos_promedio: number | null
  costo_promedio_km: number | null
  costo_optimo_promedio_km: number | null
  razon_vs_optimo: number | null
  porcentaje_optimo: number | null
  ms_promedio: number | null
}

export type PuntoConvergencia = { generacion: number; mejor: number; promedio: number | null; ejecuciones: number }
export type AhorroGenetico = { tipo_plan: string; planes: number; reordenados: number; km_antes: number; km_despues: number; km_ahorrados: number }
export type ResumenTransbordos = {
  consultas: number
  encontrados: number
  nodos_explorados_promedio: number | null
  nodos_grafo_promedio: number | null
  ms_promedio: number | null
}

export type Laboratorio = Base & {
  dfs_puntos: BurbujaDFS[]
  dfs_pares_top: { par: string; total: number }[]
  distancias_puntos: { modo: string | null; euclidiana: number; manhattan: number }[]
  // v0.6 (opcionales)
  busqueda_algoritmos?: AlgoritmoBusqueda[]
  genetico_convergencia?: PuntoConvergencia[]
  genetico_ahorro?: AhorroGenetico[]
  transbordos?: ResumenTransbordos | null
}

export type Asistente = Base & {
  por_dia: { fecha: string; conversaciones: number; mensajes: number }[]
  herramientas: { herramienta: string; total: number }[]
  tiempo_respuesta: { respuestas: number; promedio_ms: number | null; p90_ms: number | null }
  errores: { respuestas: number; errores: number; porcentaje_error: number }
  planes_por_origen: { origen: 'planificador' | 'asistente'; total: number }[]
}

/** Lo que regresa cada endpoint del dashboard, por nombre. */
export type RespuestasDashboard = {
  kpis: Kpis
  series: Series
  planes: Planes
  'sistema-experto': SistemaExperto
  movilidad: MovilidadDashboard
  reportes: Reportes
  lugares: Lugares
  laboratorio: Laboratorio
  asistente: Asistente
}
export type EndpointDashboard = keyof RespuestasDashboard

/** Todo lo que carga useDashboard (claves cortas de cada sección). */
export type DatosDashboard = {
  kpis: Kpis
  series: Series
  planes: Planes
  sistema: SistemaExperto
  movilidad: MovilidadDashboard
  reportes: Reportes
  lugares: Lugares
  laboratorio: Laboratorio
  asistente: Asistente
}

// ───────────── Endpoints de apoyo (solo admin) ─────────────

export type ParadaRed = { id: string; nombre: string; lat: number; lng: number }

export type FilaComparativo = {
  algoritmo: string
  nombre: string
  heuristica: string | null
  es_admisible: boolean | null
  costo_km: number | null
  nodos_explorados: number
  longitud_camino: number
  optimo: boolean
  ms: number
  camino: string[]
  paradas: string[]
}

export type ComparativoBusqueda = {
  exito: boolean
  fuente: string
  datos_verificados: boolean
  origen: { nombre: string; lat: number; lng: number }
  destino: { nombre: string; lat: number; lng: number }
  costo_optimo_km: number | null
  alcanzable: boolean
  filas: FilaComparativo[]
  heuristicas: Record<string, { es_admisible: boolean; nodos_sobreestimados: { nodo: string; h: number; h_real: number; exceso_km: number }[] }>
}
