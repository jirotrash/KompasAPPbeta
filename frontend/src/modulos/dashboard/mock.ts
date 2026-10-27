// Datos de ejemplo del dashboard con la MISMA forma que la API (VITE_USE_MOCK=true).
// Se generan con semilla fija: siempre salen iguales para el mismo periodo. Todo cuenta como dato demo,
// así que con "Incluir datos demo" apagado las gráficas quedan en cero (igual que la API sin actividad real).

import type { ArbolRuta, ParadaArbol, Ruta } from '../../compartido/tipos/dominio.ts'
import { distanciaKm } from '../../compartido/utils/geo.ts'
import { RUTAS } from '../../mock/datos.ts'
import type {
  ComparativoBusqueda,
  Contexto,
  EndpointDashboard,
  Filtros,
  Interes,
  Movilidad,
  ParadaRed,
  Periodo,
  RespuestasDashboard,
  TipoReporte,
} from './tipos.ts'

const esperar = (ms = 350) => new Promise((r) => setTimeout(r, ms))

function aleatorio(semilla: number) {
  let a = semilla >>> 0
  return () => {
    a = (a + 0x6d2b79f5) >>> 0
    let t = a
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

const INTERESES: Interes[] = ['comer', 'cafe', 'cultura', 'entretenimiento', 'aire_libre']
const MOVILIDADES: Movilidad[] = ['caminando', 'transporte_publico', 'taxi_app', 'combinado']
const CONTEXTOS: Contexto[] = ['solo', 'pareja', 'amigos', 'familia']
const TIPOS: TipoReporte[] = ['cierre_total', 'accidente', 'manifestacion', 'afluencia']
const REGLAS: Record<string, string> = {
  R11: 'La solicitud no exige comprobar accesibilidad.',
  R13: 'Esta versión no verifica cierres mediante una fuente integrada; la opción requiere esa advertencia.',
  R09: 'Falta información crítica para evaluar este candidato.',
  R15: 'El candidato cumple las restricciones básicas de la solicitud.',
  R16: 'El candidato es recomendable.',
  R17: 'El candidato es compatible con el contexto de la salida.',
  R18: 'El candidato coincide con los intereses del usuario.',
  R20: 'El recorrido tiene pocos transbordos.',
  R19: 'El recorrido implica poca caminata.',
  R04: 'El lugar no estará abierto durante la visita.',
}
const LUGARES: [string, string, number, number][] = [
  ['Cafetería de ejemplo · Centro de Toluca', 'Café', 19.292, -99.656],
  ['Restaurante familiar de ejemplo · Toluca', 'Comer', 19.287, -99.64],
  ['Parque de ejemplo · Toluca', 'Aire libre', 19.296, -99.662],
  ['Museo de ejemplo · Toluca', 'Cultura', 19.2935, -99.658],
  ['Cine de ejemplo · Toluca oriente', 'Entretenimiento', 19.28, -99.61],
  ['Cafetería de ejemplo · Centro de Lerma', 'Café', 19.285, -99.5115],
  ['Fonda de ejemplo · San Mateo Atenco', 'Comer', 19.2675, -99.5335],
  ['Plaza de ejemplo · Lerma', 'Entretenimiento', 19.28, -99.54],
  ['Jardín de ejemplo · Lerma', 'Aire libre', 19.2875, -99.514],
  ['Galería de ejemplo · Lerma', 'Cultura', 19.288, -99.515],
]

const hoy = () => new Date().toISOString().slice(0, 10)
const sumarDias = (iso: string, n: number) => {
  const [a, m, d] = iso.split('-').map(Number)
  const f = new Date(Date.UTC(a, m - 1, d + n))
  return f.toISOString().slice(0, 10)
}
const diasEntre = (a: string, b: string) => Math.round((Date.parse(b) - Date.parse(a)) / 86400000) + 1

function periodo({ desde, hasta, incluirDemo }: Filtros): Periodo {
  const fin = hasta || hoy()
  const inicio = desde || sumarDias(fin, -29)
  return { desde: inicio, hasta: fin, incluir_demo: incluirDemo !== false }
}

type Contexto_ = { p: Periodo; r: () => number; n: (base: number) => number; factor: number; base: { periodo: Periodo; incluye_demo: boolean } }

const CONSTRUCTORES: { [E in EndpointDashboard]: (c: Contexto_, filtros: Filtros) => RespuestasDashboard[E] } = {
  kpis: ({ n, factor, base }) => {
    const planes = n(300)
    return {
      ...base,
      usuarios_totales: 2 + n(40),
      usuarios_nuevos: n(40),
      planes,
      planes_evaluados: planes,
      porcentaje_con_recomendacion: planes ? 42.5 : 0,
      recorridos: n(240),
      tiempo_promedio_recorrido_min: factor ? 38.4 : null,
      reportes_vigentes: n(12),
      lugares: 10,
    }
  },
  series: ({ p, r, base }, filtros) => {
    const serie = []
    const intereses = []
    const paso = { dia: 1, semana: 7, mes: 30 }[filtros.agrupar] ?? 1
    for (let fecha = p.desde; fecha <= p.hasta; fecha = sumarDias(fecha, paso)) {
      const fin = new Date(fecha).getUTCDay() % 6 === 0 ? 1.5 : 1
      const k = (b: number) => (p.incluir_demo ? Math.round(b * paso * fin * (0.4 + r())) : 0)
      serie.push({ fecha, usuarios: k(0.7), planes: k(5), recorridos: k(4) })
      intereses.push({ fecha, comer: k(2), cafe: k(1.4), cultura: k(1), entretenimiento: k(1.3), aire_libre: k(1) })
    }
    return { ...base, agrupar: filtros.agrupar ?? 'dia', serie, planes_por_interes: intereses }
  },
  planes: ({ r, n, base }) => {
    const etiquetasP = ['$0–99', '$100–199', '$200–299', '$300–499', '$500–799', '$800–1199', '$1200 o más']
    const desdeP = [0, 100, 200, 300, 500, 800, 1200]
    const etiquetasT = ['0–1 h', '1–2 h', '2–3 h', '3–4 h', '4–6 h', '6–8 h', '8 h o más']
    const desdeT = [0, 60, 120, 180, 240, 360, 480]
    return {
      ...base,
      total: n(300),
      por_interes: INTERESES.map((interes, i) => ({ interes, total: n([150, 100, 75, 100, 75][i]) })).sort((a, b) => b.total - a.total),
      por_movilidad: MOVILIDADES.map((movilidad, i) => ({ movilidad, total: n([120, 95, 70, 45][i]) })),
      por_contexto: CONTEXTOS.map((contexto, i) => ({ contexto, total: n([40, 85, 105, 65][i]) })),
      presupuesto: etiquetasP.map((rango, i) => ({ rango, desde: desdeP[i], total: n([20, 45, 60, 70, 50, 30, 15][i]) })),
      tiempo_disponible: etiquetasT.map((rango, i) => ({ rango, desde_min: desdeT[i], total: n([15, 50, 70, 60, 55, 30, 20][i]) })),
      dia_hora: Array.from({ length: 7 * 24 }, (_, j) => {
        const dia = Math.floor(j / 24) + 1
        const hora = j % 24
        const pico = hora >= 17 && hora <= 21 ? 4 : hora >= 12 && hora <= 16 ? 2 : hora >= 9 ? 1 : 0
        return { dia, hora, total: pico ? n(pico * (dia >= 5 ? 2.2 : 1)) : 0 }
      }),
      interes_por_contexto: INTERESES.map((interes) => ({
        interes,
        solo: n(15 + r() * 40),
        pareja: n(15 + r() * 40),
        amigos: n(15 + r() * 40),
        familia: n(15 + r() * 40),
      })),
    }
  },
  'sistema-experto': ({ n, factor, base }) => ({
    ...base,
    por_estado: [
      { estado: 'pendiente_verificacion', total: n(380) },
      { estado: 'recomendable', total: n(260) },
      { estado: 'descartado', total: n(70) },
    ],
    reglas_top: Object.entries(REGLAS)
      .map(([id, descripcion], i) => ({ id, descripcion, total: n(700 - i * 60) }))
      .sort((a, b) => b.total - a.total),
    puntuacion_por_tipo: [
      { tipo: 'cercano', promedio: factor ? 4.1 : null, minimo: 2, maximo: 6, total: n(80) },
      { tipo: 'equilibrado', promedio: factor ? 4.8 : null, minimo: 3, maximo: 6, total: n(110) },
      { tipo: 'rapido', promedio: factor ? 3.6 : null, minimo: 1, maximo: 6, total: n(70) },
    ],
    sin_datos_suficientes: n(40),
    por_version: [{ version: '0.1.0', total: n(300) }],
  }),
  movilidad: ({ n, factor, base }) => {
    const transportes: [string, string, number, number, number, number][] = [
      ['Caminando', 'caminando', 64, 34.2, 8, 75],
      ['Transporte público', 'transporte_publico', 80, 41.7, 15, 90],
      ['Taxi/App', 'taxi_app', 35, 18.6, 6, 40],
      ['Combinado', 'combinado', 24, 29.9, 12, 60],
    ]
    return {
      ...base,
      por_transporte: transportes.map(([transporte, clave, total, promedio, minimo, maximo]) => ({
        transporte,
        clave,
        total: n(total),
        promedio: factor ? promedio : null,
        minimo: factor ? minimo : null,
        maximo: factor ? maximo : null,
      })),
      rutas_top: [2, 4, 1, 6, 3, 5].map((id, i) => ({ id_ruta: id, ruta: `Ruta ${id}`, total: n(50 - i * 6), promedio: 20 + i * 3 })),
      // Subidas y bajadas en las paradas de las rutas de ejemplo
      paradas_uso: factor
        ? RUTAS.flatMap((ruta, k) =>
            ruta.paradas.map((p, i) => {
              const subidas = n(i === 0 ? 30 : Math.max(0, 14 - i * 2))
              const bajadas = n(i === ruta.paradas.length - 1 ? 34 : i * 2)
              const [lng, lat] = p.ubicacion.coordinates
              return { id_ruta: k + 1, nombre: p.nombre, lat, lng, subidas, bajadas, total: subidas + bajadas }
            }),
          ).filter((p) => p.total > 0)
        : [],
    }
  },
  reportes: ({ r, n, factor, base }) => {
    const puntos = factor
      ? Array.from({ length: n(120) }, () => ({
          lat: 19.25 + r() * 0.1,
          lng: -99.68 + r() * 0.2,
          tipo: TIPOS[Math.floor(r() * 4)],
          estado: 'pendiente',
          vigente: r() < 0.1,
        }))
      : []
    return {
      ...base,
      por_tipo_estado: TIPOS.map((tipo, i) => ({ tipo, pendiente: n([12, 18, 16, 28][i]), verificado: n([6, 9, 8, 12][i]), descartado: n([2, 3, 2, 4][i]) })),
      vigentes_vs_vencidos: { vigentes: n(12), vencidos: n(108) },
      puntos,
    }
  },
  lugares: ({ base }) => {
    const conteo: Record<string, number> = {}
    LUGARES.forEach(([, c]) => (conteo[c] = (conteo[c] ?? 0) + 1))
    return {
      ...base,
      incluye_demo: false,
      por_categoria: Object.entries(conteo).map(([categoria, total]) => ({ categoria, total })),
      puntos: LUGARES.map(([nombre, categoria, lat, lng], i) => ({ id: i + 1, nombre, categoria, lat, lng })),
    }
  },
  laboratorio: ({ r, n, factor, base }) => {
    const pares: [string, number][] = [
      ['Terminal Toluca → Centro Toluca', 14],
      ['Terminal Toluca → Plaza Sendero', 11],
      ['Centro Lerma → Centro Toluca', 8],
      ['San Mateo Atenco → Terminal Toluca', 6],
    ]
    // Promedios reales de comparar_algoritmos() sobre las 64 parejas con camino de la red académica
    const algoritmos: [string, string | null, string, number, number, number][] = [
      ['dfs', null, 'DFS', 23.8, 1.683, 58],
      ['costo_uniforme', null, 'UCS', 5.5, 1, 100],
      ['voraz', 'euclidiana', 'Voraz (Euclidiana)', 3.4, 1.026, 88],
      ['voraz', 'manhattan', 'Voraz (Manhattan)', 3.4, 1.025, 88],
      ['a_estrella', 'euclidiana', 'A* (Euclidiana)', 3.4, 1, 100],
      ['a_estrella', 'manhattan', 'A* (Manhattan)', 3.4, 1.005, 95],
    ]
    return {
      ...base,
      dfs_puntos: factor
        ? [2, 3, 4, 5, 6, 7, 8].flatMap((limite) =>
            [0, 1].map((k) => ({ limite_profundidad: limite, nodos: limite * 2 + k * 3 + Math.round(r() * 3), rutas: Math.max(0, limite - 2 + k), consultas: 1 + Math.round(r() * 6) })),
          )
        : [],
      dfs_pares_top: pares.map(([par, total]) => ({ par, total: n(total) })),
      distancias_puntos: factor
        ? Array.from({ length: n(60) }, () => {
            const e = 0.5 + r() * 14
            return { modo: 'geo', euclidiana: Math.round(e * 1000) / 1000, manhattan: Math.round(e * (1 + r() * 0.41) * 1000) / 1000 }
          })
        : [],
      busqueda_algoritmos: factor
        ? algoritmos.map(([algoritmo, heuristica, etiqueta, nodos, razon, optimo]) => ({
            algoritmo,
            heuristica,
            etiqueta,
            consultas: n(40),
            nodos_promedio: nodos,
            costo_promedio_km: Math.round(7.2 * razon * 1000) / 1000,
            costo_optimo_promedio_km: 7.2,
            razon_vs_optimo: razon,
            porcentaje_optimo: optimo,
            ms_promedio: Math.round((0.02 + r() * 0.2) * 1000) / 1000,
          }))
        : [],
      genetico_convergencia: factor
        ? Array.from({ length: 150 }, (_, i) => {
            const mejor = 0.11 - 0.035 * Math.exp(-i / 6)
            return { generacion: i + 1, mejor: Math.round(mejor * 1e6) / 1e6, promedio: Math.round((mejor * (0.62 + 0.28 * (1 - Math.exp(-i / 25)))) * 1e6) / 1e6, ejecuciones: n(90) }
          })
        : [],
      genetico_ahorro: factor
        ? [
            ['equilibrado', 28, 18, 316.8, 290.1],
            ['rapido', 52, 31, 80.5, 70.7],
            ['cercano', 31, 4, 48.5, 47.9],
          ].map(([tipo_plan, planes, reordenados, antes, despues]) => ({
            tipo_plan: String(tipo_plan),
            planes: n(Number(planes)),
            reordenados: n(Number(reordenados)),
            km_antes: Number(antes),
            km_despues: Number(despues),
            km_ahorrados: Math.round((Number(antes) - Number(despues)) * 100) / 100,
          }))
        : [],
      transbordos: { consultas: n(50), encontrados: n(46), nodos_explorados_promedio: factor ? 240.3 : null, nodos_grafo_promedio: factor ? 519 : null, ms_promedio: factor ? 1.75 : null },
    }
  },
  asistente: ({ p, r, n, base }) => {
    const por_dia = []
    for (let fecha = p.desde; fecha <= p.hasta; fecha = sumarDias(fecha, 1)) {
      const conversaciones = p.incluir_demo ? Math.round(r() * 3) : 0
      por_dia.push({ fecha, conversaciones, mensajes: conversaciones * (1 + Math.round(r() * 3)) })
    }
    const respuestas = n(160)
    return {
      ...base,
      por_dia,
      herramientas: [
        { herramienta: 'como_llegar', total: n(70) },
        { herramienta: 'buscar_lugares', total: n(45) },
        { herramienta: 'armar_salida', total: n(25) },
        { herramienta: 'mis_planes', total: n(12) },
      ],
      tiempo_respuesta: { respuestas, promedio_ms: respuestas ? 4186 : null, p90_ms: respuestas ? 6786 : null },
      errores: { respuestas, errores: n(9), porcentaje_error: respuestas ? 5.6 : 0 },
      planes_por_origen: [
        { origen: 'planificador', total: n(250) },
        { origen: 'asistente', total: n(50) },
      ],
    }
  },
}

export async function responder<E extends EndpointDashboard>(endpoint: E, filtros: Filtros): Promise<RespuestasDashboard[E]> {
  await esperar()
  const p = periodo(filtros)
  const dias = diasEntre(p.desde, p.hasta)
  const factor = p.incluir_demo ? Math.min(1, dias / 60) : 0 // 60 días ≈ toda la actividad demo
  const r = aleatorio(28 + endpoint.length)
  const n = (base: number) => Math.round(base * factor * (0.7 + r() * 0.6))
  return CONSTRUCTORES[endpoint]({ p, r, n, factor, base: { periodo: p, incluye_demo: p.incluir_demo } }, filtros)
}

// ───────────── Endpoints de apoyo ─────────────

const RED: ParadaRed[] = [
  { id: 'TerminalToluca', nombre: 'Terminal de Autobuses de Toluca', lat: 19.2785, lng: -99.6455 },
  { id: 'CentroToluca', nombre: 'Centro Historico de Toluca', lat: 19.2926, lng: -99.6557 },
  { id: 'PinoSuarez', nombre: 'Av. Pino Suarez y Las Torres', lat: 19.274, lng: -99.635 },
  { id: 'CiudadUniversitaria', nombre: 'Ciudad Universitaria UAEMex', lat: 19.2838, lng: -99.6765 },
  { id: 'ParqueAlameda', nombre: 'Alameda Central de Toluca', lat: 19.289, lng: -99.664 },
  { id: 'GaleriasMetepec', nombre: 'Galerias Metepec', lat: 19.255, lng: -99.628 },
  { id: 'CentroMetepec', nombre: 'Centro Magico de Metepec', lat: 19.252, lng: -99.605 },
  { id: 'Tecnologico', nombre: 'Instituto Tecnologico de Toluca', lat: 19.258, lng: -99.585 },
  { id: 'PlazaSendero', nombre: 'Plaza Sendero Lerma', lat: 19.289, lng: -99.535 },
]

export async function paradasRed(): Promise<ParadaRed[]> {
  await esperar(150)
  return RED
}

/** Resultado real de la API para Terminal → Plaza Sendero (el modo de ejemplo solo trae esta pareja). */
export async function comparar(_origen: string, _destino: string): Promise<ComparativoBusqueda> {
  await esperar()
  const nombre = (id: string) => RED.find((p) => p.id === id)?.nombre ?? id
  const fila = (algoritmo: string, nombreAlg: string, heuristica: string | null, admisible: boolean | null, costo: number, nodos: number, camino: string[], ms: number) => ({
    algoritmo,
    nombre: nombreAlg,
    heuristica,
    es_admisible: admisible,
    costo_km: costo,
    nodos_explorados: nodos,
    longitud_camino: camino.length - 1,
    optimo: Math.abs(costo - 13.608) < 1e-6,
    ms,
    camino,
    paradas: camino.map(nombre),
  })
  const corto = ['TerminalToluca', 'PinoSuarez', 'CentroMetepec', 'PlazaSendero']
  return {
    exito: true,
    fuente: 'Red académica de demostración (sin verificación operativa)',
    datos_verificados: false,
    origen: RED[0],
    destino: RED[8],
    costo_optimo_km: 13.608,
    alcanzable: true,
    filas: [
      fila('dfs', 'DFS (profundidad)', null, null, 17.3433, 57, ['TerminalToluca', 'CentroToluca', 'PinoSuarez', 'CentroMetepec', 'Tecnologico', 'PlazaSendero'], 0.19),
      fila('costo_uniforme', 'Costo uniforme (UCS)', null, true, 13.608, 9, corto, 0.035),
      fila('voraz', 'Voraz (primero el mejor)', 'euclidiana', true, 13.608, 4, corto, 0.025),
      fila('voraz', 'Voraz (primero el mejor)', 'manhattan', false, 13.608, 4, corto, 0.024),
      fila('a_estrella', 'A*', 'euclidiana', true, 13.608, 4, corto, 0.024),
      fila('a_estrella', 'A*', 'manhattan', false, 16.4044, 5, ['TerminalToluca', 'CentroToluca', 'ParqueAlameda', 'PlazaSendero'], 0.029),
    ],
    heuristicas: {
      euclidiana: { es_admisible: true, nodos_sobreestimados: [] },
      manhattan: {
        es_admisible: false,
        nodos_sobreestimados: [
          { nodo: 'CentroMetepec', h: 11.446, h_real: 8.4161, exceso_km: 3.0299 },
          { nodo: 'GaleriasMetepec', h: 13.5309, h_real: 10.8029, exceso_km: 2.728 },
          { nodo: 'Tecnologico', h: 8.6812, h_real: 6.2728, exceso_km: 2.4084 },
          { nodo: 'CiudadUniversitaria', h: 15.4422, h_real: 14.9876, exceso_km: 0.4546 },
        ],
      },
    },
  }
}

export async function rutas(): Promise<Ruta[]> {
  await esperar(150)
  return RUTAS.map((r, i) => ({ id: i + 1, _id: String(i + 1), nombre: r.linea, trazo: r.paradas.map((p) => p.ubicacion.coordinates), paradas: r.paradas }))
}

export async function arbolRuta(id: number): Promise<ArbolRuta> {
  await esperar(150)
  const ruta = RUTAS[id - 1] ?? RUTAS[0]
  let km = 0
  const inorden: ParadaArbol[] = ruta.paradas.map((p, i) => {
    const [lng, lat] = p.ubicacion.coordinates
    if (i > 0) {
      const [lng0, lat0] = ruta.paradas[i - 1].ubicacion.coordinates
      km += distanciaKm({ lat: lat0, lng: lng0 }, { lat, lng })
    }
    return { km: Math.round(km * 1000) / 1000, id: `${id}-${i + 1}`, nombre: p.nombre, lat, lng }
  })
  return { id_ruta: id, nombre: ruta.linea, paradas_reales: true, raiz: null, altura: Math.ceil(Math.log2(inorden.length + 1)), total_nodos: inorden.length, inorden, preorden: [], postorden: [] }
}
