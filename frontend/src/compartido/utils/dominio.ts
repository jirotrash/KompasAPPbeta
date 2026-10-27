// Catálogos y cálculos del dominio compartidos por varias pantallas.

import type { Dia, TipoReporte, Tiempos } from '../tipos/dominio.ts'

export const CATEGORIAS: Record<string, string> = {
  cafeteria: 'Cafetería',
  restaurante: 'Restaurante',
  parque: 'Parque',
  museo: 'Museo',
  cine: 'Cine',
  plaza: 'Plaza comercial',
}

export const nombreCategoria = (c: string) => CATEGORIAS[c] ?? c

export const CONTEXTOS: Record<string, string> = {
  cita: 'Cita',
  amigos: 'Amigos',
  familia: 'Familia',
  cotidiano: 'Cotidiano',
}

export const TIPOS_REPORTE: Record<TipoReporte, string> = {
  afluencia: 'Afluencia',
  cierre_total: 'Cierre total',
  accidente: 'Accidente',
  manifestacion: 'Manifestación',
}

/** Suma de caminata + espera + trayecto + transbordos (minutos estimados). */
export const tiempoTotal = ({ tiempos }: { tiempos: Tiempos }) =>
  (['caminata', 'espera', 'trayecto', 'transbordos'] as const).reduce((s, k) => s + (tiempos[k] ?? 0), 0)

const DIAS: Dia[] = ['dom', 'lun', 'mar', 'mie', 'jue', 'vie', 'sab']
export const diaDeHoy = (): Dia => DIAS[new Date().getDay()]

export const horaActual = () => new Date().toTimeString().slice(0, 5)

/** Minúsculas y sin acentos, para comparar textos al buscar. */
export const normalizarTexto = (t: string) =>
  t
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .trim()
