/**
 * Tooltip de Recharts con los colores del tema. El texto usa tokens de texto; el color de la serie
 * solo aparece en la muestra cuadrada junto al nombre.
 * @param {{formato?: (v, nombre, fila) => string, titulo?: (etiqueta, fila) => string, extra?: (fila) => string}} props
 */
export default function TooltipKompas({ active, payload, label, formato, titulo, extra }) {
  if (!active || !payload?.length) return null
  const fila = payload[0].payload
  const encabezado = titulo ? titulo(label, fila) : label
  return (
    <div className="max-w-72 rounded-xl border border-borde bg-superficie-elevada px-3 py-2 text-sm shadow-lg">
      {encabezado !== undefined && encabezado !== '' && <p className="mb-1 font-semibold">{encabezado}</p>}
      <ul className="space-y-0.5">
        {payload.map((p) => (
          <li key={`${p.dataKey}-${p.name}`} className="flex items-center gap-2">
            <span aria-hidden="true" className="size-2.5 shrink-0 rounded-sm" style={{ background: p.color ?? p.payload?.fill }} />
            <span className="text-texto-suave">{p.name}</span>
            <span className="ml-auto pl-3 font-semibold tabular-nums">{formato ? formato(p.value, p.name, fila) : p.value}</span>
          </li>
        ))}
      </ul>
      {extra && <p className="mt-1 text-xs text-texto-suave">{extra(fila)}</p>}
    </div>
  )
}
