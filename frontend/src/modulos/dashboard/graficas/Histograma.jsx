import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import TarjetaGrafica from '../componentes/TarjetaGrafica.jsx'
import TooltipKompas from '../componentes/TooltipKompas.jsx'
import { COLOR, EJE, numero, REJILLA } from '../estilo.js'

/** Histograma: barras pegadas (solo el hueco de 2 px del color de la superficie). Los rangos vienen de $bucket. */
export default function Histograma({ titulo, descripcion, archivo, filas, etiquetaRango }) {
  return (
    <TarjetaGrafica
      titulo={titulo}
      descripcion={descripcion}
      archivo={archivo}
      columnas={[
        { clave: 'rango', titulo: etiquetaRango },
        { clave: 'total', titulo: 'Planes', formato: numero },
      ]}
      filas={filas}
      vacio={filas.every((f) => !f.total)}
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={filas} barCategoryGap={0} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
          <CartesianGrid {...REJILLA} />
          <XAxis dataKey="rango" {...EJE} interval={0} fontSize={11} />
          <YAxis allowDecimals={false} {...EJE} />
          <Tooltip content={<TooltipKompas formato={numero} />} cursor={{ fill: 'var(--color-fondo)' }} />
          <Bar dataKey="total" name="Planes" fill={COLOR.primario} stroke={COLOR.superficie} strokeWidth={2} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </TarjetaGrafica>
  )
}
