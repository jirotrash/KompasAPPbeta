import { Bar, CartesianGrid, ComposedChart, ErrorBar, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import TarjetaGrafica from '../componentes/TarjetaGrafica.tsx'
import TooltipKompas from '../componentes/TooltipKompas.tsx'
import { COLOR, decimal, EJE, numero, REJILLA, TIPOS_PLAN } from '../estilo.ts'
import type { SistemaExperto } from '../tipos.ts'

/** #14 Puntuación por tipo de plan: promedio (barra) con el rango mínimo–máximo (bigotes). */
export default function GraficaPuntuacion({ sistema }: { sistema: SistemaExperto }) {
  const filas = sistema.puntuacion_por_tipo
    .flatMap((f) => (f.promedio !== null && f.minimo !== null && f.maximo !== null ? [{ ...f, promedio: f.promedio, minimo: f.minimo, maximo: f.maximo }] : []))
    .map((f) => ({
      ...f,
      nombre: TIPOS_PLAN[f.tipo] ?? f.tipo,
      // ErrorBar pide la distancia hacia abajo y hacia arriba desde el promedio
      rango: [f.promedio - f.minimo, f.maximo - f.promedio],
    }))
  type Fila = (typeof filas)[number]
  return (
    <TarjetaGrafica
      titulo="Puntuación por tipo de plan"
      descripcion="Puntuación de preferencias (0–6) de los planes recomendables: promedio y rango mínimo–máximo."
      archivo="puntuacion-por-tipo"
      columnas={[
        { clave: 'nombre', titulo: 'Tipo' },
        { clave: 'promedio', titulo: 'Promedio', formato: decimal },
        { clave: 'minimo', titulo: 'Mínimo', formato: numero },
        { clave: 'maximo', titulo: 'Máximo', formato: numero },
        { clave: 'total', titulo: 'Planes', formato: numero },
      ]}
      filas={filas}
      vacio={!filas.length}
    >
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={filas} margin={{ top: 12, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid {...REJILLA} />
          <XAxis dataKey="nombre" {...EJE} />
          <YAxis domain={[0, 6]} ticks={[0, 1, 2, 3, 4, 5, 6]} {...EJE} />
          <Tooltip
            content={<TooltipKompas formato={decimal} extra={(f: Fila) => `Mínimo ${f.minimo} · máximo ${f.maximo} · ${numero(f.total)} planes`} />}
            cursor={{ fill: 'var(--color-fondo)' }}
          />
          <Bar dataKey="promedio" name="Promedio" fill={COLOR.ok} radius={[4, 4, 0, 0]} maxBarSize={56}>
            <ErrorBar dataKey="rango" width={10} strokeWidth={2} stroke={COLOR.texto} direction="y" />
          </Bar>
        </ComposedChart>
      </ResponsiveContainer>
    </TarjetaGrafica>
  )
}
