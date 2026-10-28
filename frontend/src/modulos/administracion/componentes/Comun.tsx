// Piezas que comparten las pantallas del panel de administración.

import type { ButtonHTMLAttributes, ComponentType, ReactNode } from 'react'
import type { PropsIcono } from '../../../compartido/componentes/Iconos.tsx'

type Tono = 'ok' | 'aviso' | 'peligro' | 'primario' | 'neutro'

// Sobre dorado el texto va oscuro (COLORIMETRIA.md §4): el aviso usa fondo claro y texto normal
const TONOS: Record<Tono, string> = {
  ok: 'bg-ok-fondo text-ok',
  aviso: 'bg-aviso-fondo text-texto',
  peligro: 'bg-peligro-fondo text-peligro',
  primario: 'bg-primario-claro text-primario-oscuro',
  neutro: 'bg-fondo text-texto-suave border border-borde',
}

export function Insignia({ tono = 'neutro', children }: { tono?: Tono; children: ReactNode }) {
  return <span className={`inline-flex items-center whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-semibold ${TONOS[tono]}`}>{children}</span>
}

type PropsBotonIcono = ButtonHTMLAttributes<HTMLButtonElement> & { Icono: ComponentType<PropsIcono>; etiqueta: string; peligro?: boolean }

/** Botón cuadrado solo con ícono (editar, borrar…). `etiqueta` es lo que lee el lector de pantalla. */
export function BotonIcono({ Icono, etiqueta, peligro, className = '', ...props }: PropsBotonIcono) {
  return (
    <button
      type="button"
      aria-label={etiqueta}
      title={etiqueta}
      className={`grid size-9 shrink-0 place-items-center rounded-lg text-texto-suave transition hover:bg-fondo disabled:opacity-50 ${peligro ? 'hover:text-peligro' : 'hover:text-primario'} ${className}`}
      {...props}
    >
      <Icono className="size-[18px]" />
    </button>
  )
}

export function Vacio({ children }: { children: ReactNode }) {
  return <p className="rounded-xl border border-dashed border-borde px-4 py-6 text-center text-sm text-texto-suave">{children}</p>
}
