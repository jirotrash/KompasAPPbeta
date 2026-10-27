import { Area, AreaChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import LeyendaKompas from '../componentes/LeyendaKompas.tsx'
import TarjetaGrafica from '../componentes/TarjetaGrafica.tsx'
import TooltipKompas from '../componentes/TooltipKompas.tsx'
import { COLOR, EJE, fechaCorta, INTERESES, numero, REJILLA } from '../estilo.ts'
import type { Entidad } from '../estilo.ts'
import type { Interes, Series } from '../tipos.ts'

/** #4 Planes por interés en el tiempo (áreas apiladas; un plan puede tener varios intereses). */
export default function GraficaInteresesTiempo({ series }: { series: Series }) {
  const filas = series.planes_por_interes
  const intereses = Object.entries(INTERESES) as [Interes, Entidad][]
  const vacio = filas.every((f) => intereses.every(([i]) => !f[i]))
  return (
    <TarjetaGrafica
      titulo="Intereses en el tiempo"
      descripcion="Cuántas veces se eligió cada interés al crear un plan (un plan puede tener varios)."
      archivo="intereses-en-el-tiempo"
      columnas={[{ clave: 'fecha', titulo: 'Periodo' }, ...intereses.map(([clave, i]) => ({ clave, titulo: i.nombre, formato: numero }))]}
      filas={filas}
      vacio={vacio}
      alto="h-80"
    >
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={filas} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
          <CartesianGrid {...REJILLA} />
          <XAxis dataKey="fecha" tickFormatter={fechaCorta} {...EJE} minTickGap={24} />
          <YAxis allowDecimals={false} {...EJE} />
          <Tooltip content={<TooltipKompas titulo={(l) => fechaCorta(l)} formato={numero} />} cursor={{ stroke: COLOR.textoSuave, strokeDasharray: '3 3' }} />
          <Legend content={<LeyendaKompas items={Object.values(INTERESES)} />} />
          {Object.entries(INTERESES).map(([clave, i]) => (
            <Area
              key={clave}
              type="monotone"
              dataKey={clave}
              name={i.nombre}
              stackId="intereses"
              stroke={COLOR.superficie}
              strokeWidth={2}
              fill={i.color}
              fillOpacity={0.9}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </TarjetaGrafica>
  )
}
