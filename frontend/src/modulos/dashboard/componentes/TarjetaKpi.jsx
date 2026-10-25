/** Número principal del resumen. El valor ya viene calculado por la API. */
export default function TarjetaKpi({ titulo, valor, detalle }) {
  return (
    <div className="tarjeta flex flex-col gap-1">
      <p className="text-sm font-medium text-texto-suave">{titulo}</p>
      <p className="text-3xl font-bold tracking-tight tabular-nums">{valor}</p>
      {detalle && <p className="text-xs text-texto-suave">{detalle}</p>}
    </div>
  )
}

export function EsqueletoKpi() {
  return (
    <div className="tarjeta flex animate-pulse flex-col gap-2" aria-hidden="true">
      <span className="h-4 w-24 rounded bg-borde" />
      <span className="h-8 w-16 rounded bg-borde" />
    </div>
  )
}
