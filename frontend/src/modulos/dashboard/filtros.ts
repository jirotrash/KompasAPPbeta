// Periodo del dashboard: lo que elige el usuario → parámetros de la API.

import type { Agrupar, Filtros } from './tipos.ts'

export type Rango = '7' | '30' | '90' | 'todo' | 'personalizado'
export type Seleccion = { rango: Rango; desde: string; hasta: string; agrupar: Agrupar; incluirDemo: boolean }

// La API acepta periodos de hasta 3 años: "Todo" pide ese máximo
const DIAS_TODO = 3 * 365

const hoyLocal = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
const restarDias = (iso: string, n: number) => {
  const [a, m, d] = iso.split('-').map(Number)
  const f = new Date(a, m - 1, d - n)
  return `${f.getFullYear()}-${String(f.getMonth() + 1).padStart(2, '0')}-${String(f.getDate()).padStart(2, '0')}`
}

/** Convierte lo que eligió el usuario en los parámetros de la API (desde/hasta incluyen el día completo). */
export function filtrosDesde({ rango, desde, hasta, agrupar, incluirDemo }: Seleccion): Filtros {
  const hoy = hoyLocal()
  if (rango === 'personalizado') return { desde, hasta, agrupar, incluirDemo }
  const dias = rango === 'todo' ? DIAS_TODO : Number(rango)
  return { desde: restarDias(hoy, dias - 1), hasta: hoy, agrupar, incluirDemo }
}

export const SELECCION_INICIAL: Seleccion = { rango: '30', desde: restarDias(hoyLocal(), 29), hasta: hoyLocal(), agrupar: 'dia', incluirDemo: true }
