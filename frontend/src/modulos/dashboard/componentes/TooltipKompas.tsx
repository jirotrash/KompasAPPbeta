import type { ReactNode } from 'react'

type Entrada = { dataKey?: unknown; name?: unknown; value?: unknown; color?: string; payload?: { fill?: string } }

// Los parámetros son `never` para aceptar funciones con tipos concretos (numero, decimal, (f: Fila) => …):
// Recharts no sabe el tipo de cada fila, así que quien usa el tooltip anota el suyo.
type Props = {
  active?: boolean
  payload?: readonly Entrada[]
  label?: unknown
  formato?: (v: never, nombre: string, fila: never) => ReactNode
  titulo?: (etiqueta: never, fila: never) => ReactNode
  extra?: (fila: never) => ReactNode
}

/**
 * Tooltip de Recharts con los colores del tema. El texto usa tokens de texto; el color de la serie
 * solo aparece en la muestra cuadrada junto al nombre.
 */
export default function TooltipKompas({ active, payload, label, formato, titulo, extra }: Props) {
  if (!active || !payload?.length) return null
  const fila = payload[0].payload as never
  const encabezado = titulo ? titulo(label as never, fila) : (label as ReactNode)
  return (
    <div className="max-w-72 rounded-xl border border-borde bg-superficie-elevada px-3 py-2 text-sm shadow-lg">
      {encabezado !== undefined && encabezado !== '' && <p className="mb-1 font-semibold">{encabezado}</p>}
      <ul className="space-y-0.5">
        {payload.map((p) => (
          <li key={`${String(p.dataKey)}-${String(p.name)}`} className="flex items-center gap-2">
            <span aria-hidden="true" className="size-2.5 shrink-0 rounded-sm" style={{ background: p.color ?? p.payload?.fill }} />
            <span className="text-texto-suave">{String(p.name ?? '')}</span>
            <span className="ml-auto pl-3 font-semibold tabular-nums">{formato ? formato(p.value as never, String(p.name ?? ''), fila) : String(p.value ?? '')}</span>
          </li>
        ))}
      </ul>
      {extra && <p className="mt-1 text-xs text-texto-suave">{extra(fila)}</p>}
    </div>
  )
}
