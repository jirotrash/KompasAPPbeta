import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import TarjetaGrafica from '../componentes/TarjetaGrafica.jsx'
import TooltipKompas from '../componentes/TooltipKompas.jsx'
import { COLOR, EJE, INTERESES, nombreDe, numero, REJILLA } from '../estilo.js'

/** #5 Planes por interés (barras verticales, de mayor a menor). */
export default function GraficaPlanesInteres({ planes }) {
  const filas = planes.por_interes.map((f) => ({ ...f, nombre: nombreDe(INTERESES, f.interes) }))
  return (
    <TarjetaGrafica
      titulo="Planes por interés"
      descripcion="¿Qué buscan las personas cuando salen? Cada plan cuenta una vez por interés elegido."
      archivo="planes-por-interes"
      columnas={[
        { clave: 'nombre', titulo: 'Interés' },
        { clave: 'total', titulo: 'Planes', formato: numero },
      ]}
      filas={filas}
      vacio={filas.every((f) => !f.total)}
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={filas} margin={{ top: 20, right: 8, left: -12, bottom: 0 }}>
          <CartesianGrid {...REJILLA} />
          <XAxis dataKey="nombre" {...EJE} interval={0} />
          <YAxis allowDecimals={false} {...EJE} />
          <Tooltip content={<TooltipKompas formato={numero} />} cursor={{ fill: 'var(--color-fondo)' }} />
          <Bar dataKey="total" name="Planes" radius={[4, 4, 0, 0]} maxBarSize={56}>
            {filas.map((f) => (
              <Cell key={f.interes} fill={INTERESES[f.interes]?.color ?? COLOR.primario} />
            ))}
            <LabelList dataKey="total" position="top" formatter={numero} fill={COLOR.texto} fontSize={12} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </TarjetaGrafica>
  )
}
