// Fondo suave + ícono del tono; el número va siempre en color de texto (nunca en el del acento)
import type { ComponentType, ReactNode } from 'react'
import type { PropsIcono } from '../../../compartido/componentes/Iconos.tsx'

export type Tono = 'primario' | 'ok' | 'aviso' | 'peligro' | 'detalle'

const TONOS: Record<Tono, string> = {
  primario: 'bg-primario-claro text-primario',
  ok: 'bg-ok-fondo text-ok',
  aviso: 'bg-aviso-fondo text-aviso',
  peligro: 'bg-peligro-fondo text-peligro',
  detalle: 'bg-primario-claro text-detalle',
}

/** Número principal del resumen. El valor ya viene calculado por la API. */
type Props = { titulo: string; valor: ReactNode; detalle?: ReactNode; Icono?: ComponentType<PropsIcono>; tono?: Tono }

export default function TarjetaKpi({ titulo, valor, detalle, Icono, tono = 'primario' }: Props) {
  return (
    <div className="tarjeta flex h-full flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <p className="pt-1 text-sm font-medium leading-snug text-texto-suave">{titulo}</p>
        {Icono && (
          <span aria-hidden="true" className={`grid size-9 place-items-center rounded-xl ${TONOS[tono]}`}>
            <Icono className="size-5" />
          </span>
        )}
      </div>
      <div className="mt-auto">
        <p className="text-3xl font-bold leading-none tracking-tight tabular-nums">{valor}</p>
        {detalle && <p className="mt-2 text-xs text-texto-suave">{detalle}</p>}
      </div>
    </div>
  )
}

export function EsqueletoKpi() {
  return (
    <div className="tarjeta flex animate-pulse flex-col gap-3" aria-hidden="true">
      <div className="flex justify-between">
        <span className="h-4 w-24 rounded bg-borde" />
        <span className="size-9 rounded-xl bg-borde" />
      </div>
      <span className="h-8 w-16 rounded bg-borde" />
    </div>
  )
}
