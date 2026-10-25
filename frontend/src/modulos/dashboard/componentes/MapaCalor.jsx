import { DIAS_SEMANA, numero } from '../estilo.js'

const PASOS = [0, 18, 36, 58, 80, 100] // % de azul mezclado con la superficie (un solo tono, claro → oscuro)

/**
 * Día de la semana × hora con CSS grid (Recharts no trae mapa de calor).
 * @param {{celdas: Array<{dia: number, hora: number, total: number}>}} props  dia 1 = lunes (ISO)
 */
export default function MapaCalor({ celdas }) {
  const maximo = Math.max(1, ...celdas.map((c) => c.total))
  const paso = (total) => (total === 0 ? 0 : Math.min(PASOS.length - 1, 1 + Math.floor(((total - 1) / maximo) * (PASOS.length - 1))))
  const fondo = (total) =>
    total === 0 ? 'var(--color-fondo)' : `color-mix(in srgb, var(--color-primario) ${PASOS[paso(total)]}%, var(--color-superficie))`

  return (
    <div className="flex h-full flex-col gap-2 overflow-x-auto">
      <div className="grid min-w-[36rem] flex-1 grid-cols-[2.5rem_repeat(24,minmax(0,1fr))] gap-0.5 text-[10px] text-texto-suave">
        <span />
        {Array.from({ length: 24 }, (_, h) => (
          <span key={h} className="text-center">
            {h % 3 === 0 ? h : ''}
          </span>
        ))}
        {DIAS_SEMANA.map((dia, i) => (
          <div key={dia} className="contents">
            <span className="self-center pr-1 text-right text-xs">{dia}</span>
            {Array.from({ length: 24 }, (_, h) => {
              const total = celdas.find((c) => c.dia === i + 1 && c.hora === h)?.total ?? 0
              const texto = `${dia} ${h}:00 — ${numero(total)} plan${total === 1 ? '' : 'es'}`
              return (
                <span
                  key={h}
                  role="img"
                  aria-label={texto}
                  title={texto}
                  className="min-h-5 rounded-[3px] border border-borde/40 transition hover:outline hover:outline-2 hover:outline-texto"
                  style={{ background: fondo(total) }}
                />
              )
            })}
          </div>
        ))}
      </div>
      <div className="flex items-center gap-2 text-xs text-texto-suave">
        <span>Menos</span>
        {PASOS.map((p, i) => (
          <span
            key={p}
            aria-hidden="true"
            className="size-3 rounded-[3px] border border-borde/40"
            style={{ background: i === 0 ? 'var(--color-fondo)' : `color-mix(in srgb, var(--color-primario) ${p}%, var(--color-superficie))` }}
          />
        ))}
        <span>Más (máx. {numero(maximo)})</span>
      </div>
    </div>
  )
}
