// Datos de ejemplo del dashboard con la MISMA forma que la API (VITE_USE_MOCK=true).
// Se generan con semilla fija: siempre salen iguales para el mismo periodo. Todo cuenta como dato demo,
// así que con "Incluir datos demo" apagado las gráficas quedan en cero (igual que la API sin actividad real).

const esperar = (ms = 350) => new Promise((r) => setTimeout(r, ms))

function aleatorio(semilla) {
  let a = semilla >>> 0
  return () => {
    a = (a + 0x6d2b79f5) >>> 0
    let t = a
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

const INTERESES = ['comer', 'cafe', 'cultura', 'entretenimiento', 'aire_libre']
const MOVILIDADES = ['caminando', 'transporte_publico', 'taxi_app', 'combinado']
const CONTEXTOS = ['solo', 'pareja', 'amigos', 'familia']
const TIPOS = ['cierre_total', 'accidente', 'manifestacion', 'afluencia']
const REGLAS = {
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
const LUGARES = [
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
const sumarDias = (iso, n) => {
  const [a, m, d] = iso.split('-').map(Number)
  const f = new Date(Date.UTC(a, m - 1, d + n))
  return f.toISOString().slice(0, 10)
}
const diasEntre = (a, b) => Math.round((Date.parse(b) - Date.parse(a)) / 86400000) + 1

function periodo({ desde, hasta, incluirDemo }) {
  const fin = hasta || hoy()
  const inicio = desde || sumarDias(fin, -29)
  return { desde: inicio, hasta: fin, incluir_demo: incluirDemo !== false }
}

function construir(endpoint, filtros) {
  const p = periodo(filtros)
  const dias = diasEntre(p.desde, p.hasta)
  const factor = p.incluir_demo ? Math.min(1, dias / 60) : 0 // 60 días ≈ toda la actividad demo
  const r = aleatorio(28 + endpoint.length)
  const n = (base) => Math.round(base * factor * (0.7 + r() * 0.6))
  const base = { periodo: p, incluye_demo: p.incluir_demo }

  switch (endpoint) {
    case 'kpis': {
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
    }
    case 'series': {
      const serie = []
      const intereses = []
      const paso = { dia: 1, semana: 7, mes: 30 }[filtros.agrupar] ?? 1
      for (let fecha = p.desde; fecha <= p.hasta; fecha = sumarDias(fecha, paso)) {
        const fin = new Date(fecha).getUTCDay() % 6 === 0 ? 1.5 : 1
        const k = (b) => (p.incluir_demo ? Math.round(b * paso * fin * (0.4 + r())) : 0)
        serie.push({ fecha, usuarios: k(0.7), planes: k(5), recorridos: k(4) })
        intereses.push({ fecha, comer: k(2), cafe: k(1.4), cultura: k(1), entretenimiento: k(1.3), aire_libre: k(1) })
      }
      return { ...base, agrupar: filtros.agrupar ?? 'dia', serie, planes_por_interes: intereses }
    }
    case 'planes': {
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
          ...Object.fromEntries(CONTEXTOS.map((c) => [c, n(15 + r() * 40)])),
        })),
      }
    }
    case 'sistema-experto':
      return {
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
      }
    case 'movilidad':
      return {
        ...base,
        por_transporte: [
          ['Caminando', 'caminando', 64, 34.2, 8, 75],
          ['Transporte público', 'transporte_publico', 80, 41.7, 15, 90],
          ['Taxi/App', 'taxi_app', 35, 18.6, 6, 40],
          ['Combinado', 'combinado', 24, 29.9, 12, 60],
        ].map(([transporte, clave, total, promedio, minimo, maximo]) => ({
          transporte,
          clave,
          total: n(total),
          promedio: factor ? promedio : null,
          minimo: factor ? minimo : null,
          maximo: factor ? maximo : null,
        })),
        rutas_top: [2, 4, 1, 6, 3, 5].map((id, i) => ({ id_ruta: id, ruta: `Ruta ${id}`, total: n(50 - i * 6), promedio: 20 + i * 3 })),
      }
    case 'reportes': {
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
    }
    case 'lugares': {
      const conteo = {}
      LUGARES.forEach(([, c]) => (conteo[c] = (conteo[c] ?? 0) + 1))
      return {
        ...base,
        incluye_demo: false,
        por_categoria: Object.entries(conteo).map(([categoria, total]) => ({ categoria, total })),
        puntos: LUGARES.map(([nombre, categoria, lat, lng], i) => ({ id: i + 1, nombre, categoria, lat, lng })),
      }
    }
    case 'laboratorio':
      return {
        ...base,
        dfs_puntos: factor
          ? [2, 3, 4, 5, 6, 7, 8].flatMap((limite) =>
              [0, 1].map((k) => ({ limite_profundidad: limite, nodos: limite * 2 + k * 3 + Math.round(r() * 3), rutas: Math.max(0, limite - 2 + k), consultas: 1 + Math.round(r() * 6) })),
            )
          : [],
        dfs_pares_top: [
          ['Terminal Toluca → Centro Toluca', 14],
          ['Terminal Toluca → Plaza Sendero', 11],
          ['Centro Lerma → Centro Toluca', 8],
          ['San Mateo Atenco → Terminal Toluca', 6],
        ].map(([par, total]) => ({ par, total: n(total) })),
        distancias_puntos: factor
          ? Array.from({ length: n(60) }, () => {
              const e = 0.5 + r() * 14
              return { modo: 'geo', euclidiana: Math.round(e * 1000) / 1000, manhattan: Math.round(e * (1 + r() * 0.41) * 1000) / 1000 }
            })
          : [],
      }
    default:
      throw new Error(`Endpoint de ejemplo desconocido: ${endpoint}`)
  }
}

export async function responder(endpoint, filtros) {
  await esperar()
  return construir(endpoint, filtros)
}
