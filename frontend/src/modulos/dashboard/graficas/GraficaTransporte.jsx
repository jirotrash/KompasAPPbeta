import { Bar, CartesianGrid, Cell, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import TarjetaGrafica from '../componentes/TarjetaGrafica.jsx'
import TooltipKompas from '../componentes/TooltipKompas.jsx'
import { COLOR, EJE, MOVILIDAD, minutos, numero, REJILLA } from '../estilo.js'

/**
 * #15 Recorridos por transporte (barras, eje izquierdo) y tiempo promedio (línea, eje derecho).
 * DASHBOARD.md pide doble eje; para que no se confundan, cada eje dice su unidad y la tabla da los números.
 */
export default function GraficaTransporte({ movilidad }) {
  const filas = movilidad.por_transporte
  const formato = (v, nombre) => (nombre === 'Tiempo promedio' ? minutos(v) : numero(v))
  return (
    <TarjetaGrafica
      titulo="Recorridos por transporte"
      descripcion="Barras: cuántos recorridos se guardaron (eje izquierdo). Línea: minutos estimados en promedio (eje derecho)."
      archivo="recorridos-por-transporte"
      columnas={[
        { clave: 'transporte', titulo: 'Transporte' },
        { clave: 'total', titulo: 'Recorridos', formato: numero },
        { clave: 'promedio', titulo: 'Promedio (min)', formato: minutos },
        { clave: 'minimo', titulo: 'Mínimo (min)', formato: minutos },
        { clave: 'maximo', titulo: 'Máximo (min)', formato: minutos },
      ]}
      filas={filas}
      vacio={filas.every((f) => !f.total)}
      alto="h-80"
    >
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={filas} margin={{ top: 24, right: 4, left: 12, bottom: 0 }}>
          <CartesianGrid {...REJILLA} />
          <XAxis dataKey="transporte" {...EJE} interval={0} />
          <YAxis
            yAxisId="recorridos"
            allowDecimals={false}
            {...EJE}
            label={{ value: 'Recorridos', position: 'top', offset: 12, fill: COLOR.textoSuave, fontSize: 12 }}
          />
          <YAxis
            yAxisId="minutos"
            orientation="right"
            {...EJE}
            label={{ value: 'Minutos', position: 'top', offset: 12, fill: COLOR.textoSuave, fontSize: 12 }}
          />
          <Tooltip content={<TooltipKompas formato={formato} />} cursor={{ fill: 'var(--color-fondo)' }} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar yAxisId="recorridos" dataKey="total" name="Recorridos" radius={[4, 4, 0, 0]} maxBarSize={56} fill={COLOR.primario}>
            {filas.map((f) => (
              <Cell key={f.transporte} fill={MOVILIDAD[f.clave]?.color ?? COLOR.primario} />
            ))}
          </Bar>
          <Line
            yAxisId="minutos"
            dataKey="promedio"
            name="Tiempo promedio"
            stroke={COLOR.texto}
            strokeWidth={2}
            dot={{ r: 4, fill: COLOR.texto, stroke: COLOR.superficie, strokeWidth: 2 }}
            connectNulls
          />
        </ComposedChart>
      </ResponsiveContainer>
    </TarjetaGrafica>
  )
}
