/** Lista de reglas del sistema experto: por qué se recomienda (o descarta) algo. */
export default function ExplicacionReglas({ reglas, titulo = '¿Por qué?', tono = 'ok' }) {
  if (!reglas?.length) return null
  const color = tono === 'ok' ? 'bg-ok-fondo text-ok' : 'bg-peligro-fondo text-peligro'
  return (
    <details className="group rounded-xl bg-fondo p-3">
      <summary className="cursor-pointer list-none text-sm font-semibold text-texto marker:hidden">
        <span className="mr-1 inline-block transition group-open:rotate-90">›</span>
        {titulo} ({reglas.length} {reglas.length === 1 ? 'regla' : 'reglas'})
      </summary>
      <ul className="mt-2 space-y-1.5">
        {reglas.map((r) => (
          <li key={r.id + r.descripcion} className="flex gap-2 text-sm">
            <span className={`h-fit shrink-0 rounded-md px-1.5 py-0.5 font-mono text-xs font-bold ${color}`}>{r.id}</span>
            <span className="break-words font-mono text-xs leading-5 text-texto-suave">{r.descripcion}</span>
          </li>
        ))}
      </ul>
    </details>
  )
}
