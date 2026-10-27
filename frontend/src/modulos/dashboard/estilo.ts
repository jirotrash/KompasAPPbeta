// Colores, etiquetas y formatos del dashboard. Colores SOLO de COLORIMETRIA.md (tokens de index.css),
// así funcionan en claro y oscuro. El color sigue a la entidad (un interés siempre tiene el mismo color).

import type { Contexto, Interes, Movilidad, TipoReporte } from './tipos.ts'

export type Entidad = { nombre: string; color: string }

export const COLOR = {
  primario: 'var(--color-primario)',
  acento: 'var(--color-acento)',
  ok: 'var(--color-ok)',
  aviso: 'var(--color-aviso)',
  detalle: 'var(--color-detalle)',
  peligro: 'var(--color-peligro)',
  texto: 'var(--color-texto)',
  textoSuave: 'var(--color-texto-suave)',
  borde: 'var(--color-borde)',
  superficie: 'var(--color-superficie)',
}

// Orden categórico validado (scripts de dataviz): azul, rojo, verde, dorado, frambuesa
export const CATEGORICO = [COLOR.primario, COLOR.acento, COLOR.ok, COLOR.aviso, COLOR.detalle]

export const INTERESES: Record<Interes, Entidad> = {
  comer: { nombre: 'Comer', color: CATEGORICO[0] },
  cafe: { nombre: 'Café', color: CATEGORICO[1] },
  cultura: { nombre: 'Cultura', color: CATEGORICO[2] },
  entretenimiento: { nombre: 'Entretenimiento', color: CATEGORICO[3] },
  aire_libre: { nombre: 'Aire libre', color: CATEGORICO[4] },
}

export const CONTEXTOS: Record<Contexto, Entidad> = {
  solo: { nombre: 'Solo', color: CATEGORICO[0] },
  pareja: { nombre: 'En pareja', color: CATEGORICO[1] },
  amigos: { nombre: 'Con amigos', color: CATEGORICO[2] },
  familia: { nombre: 'En familia', color: CATEGORICO[3] },
}

// COLORIMETRIA.md §3: pie verde, autobús azul, taxi dorado, combinado frambuesa
export const MOVILIDAD: Record<Movilidad, Entidad> = {
  caminando: { nombre: 'Caminando', color: COLOR.ok },
  transporte_publico: { nombre: 'Transporte público', color: COLOR.primario },
  taxi_app: { nombre: 'Taxi / App', color: COLOR.aviso },
  combinado: { nombre: 'Combinado', color: COLOR.detalle },
}

// Estados del sistema experto: recomendable verde, advertencia dorado, descartado rojo
export const ESTADOS: Record<string, Entidad> = {
  recomendable: { nombre: 'Recomendable', color: COLOR.ok },
  pendiente_verificacion: { nombre: 'Pendiente de verificar', color: COLOR.aviso },
  requiere_correccion: { nombre: 'Requiere corrección', color: COLOR.detalle },
  descartado: { nombre: 'Descartado', color: COLOR.peligro },
}

export const TIPOS_PLAN: Record<string, string> = { equilibrado: 'Equilibrado', rapido: 'Rápido', cercano: 'Cercano' }

export const TIPOS_REPORTE: Record<TipoReporte, Entidad> = {
  cierre_total: { nombre: 'Cierre total', color: COLOR.acento },
  accidente: { nombre: 'Accidente', color: COLOR.aviso },
  manifestacion: { nombre: 'Manifestación', color: COLOR.detalle },
  afluencia: { nombre: 'Afluencia', color: COLOR.primario },
}

export const ESTADOS_REPORTE: Record<'pendiente' | 'verificado' | 'descartado', Entidad> = {
  pendiente: { nombre: 'Pendiente', color: COLOR.aviso },
  verificado: { nombre: 'Verificado', color: COLOR.ok },
  descartado: { nombre: 'Descartado', color: COLOR.peligro },
}

export const CATEGORIAS_LUGAR: Record<string, string> = {
  Comer: INTERESES.comer.color,
  Café: INTERESES.cafe.color,
  Cultura: INTERESES.cultura.color,
  Entretenimiento: INTERESES.entretenimiento.color,
  'Aire libre': INTERESES.aire_libre.color,
}

export const DIAS_SEMANA = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

const ENTERO = new Intl.NumberFormat('es-MX')
const DECIMAL = new Intl.NumberFormat('es-MX', { maximumFractionDigits: 1 })

type Num = number | null | undefined

export const numero = (v: Num) => (v === null || v === undefined ? '—' : ENTERO.format(v))
export const decimal = (v: Num) => (v === null || v === undefined ? '—' : DECIMAL.format(v))
export const porcentaje = (v: Num) => (v === null || v === undefined ? '—' : `${DECIMAL.format(v)} %`)
/** Para LabelList de Recharts (recibe el valor sin tipo). */
export const etiquetaNumero = (v: unknown) => numero(typeof v === 'number' ? v : null)
export const minutos = (v: Num) => (v === null || v === undefined ? '—' : `${DECIMAL.format(v)} min`)

/** "2026-10-05" → "5 oct" (sin cambiar de día por la zona horaria del navegador). */
export function fechaCorta(iso: string) {
  const [a, m, d] = iso.split('-').map(Number)
  return new Date(a, m - 1, d).toLocaleDateString('es-MX', { day: 'numeric', month: 'short' })
}

export const nombreDe = (catalogo: Record<string, Entidad>, clave: string) => catalogo[clave]?.nombre ?? clave

// Estilo común de ejes y rejilla: recesivos
export const EJE = { stroke: COLOR.borde, tick: { fill: COLOR.textoSuave, fontSize: 12 }, tickLine: false }
export const REJILLA = { stroke: COLOR.borde, strokeDasharray: '3 3', vertical: false }
