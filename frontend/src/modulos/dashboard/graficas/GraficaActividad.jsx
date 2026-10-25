import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import TarjetaGrafica from '../componentes/TarjetaGrafica.jsx'
import TooltipKompas from '../componentes/TooltipKompas.jsx'
import { COLOR, EJE, fechaCorta, numero, REJILLA } from '../estilo.js'

const SERIES = [
  { clave: 'planes', nombre: 'Planes', color: COLOR.primario },
  { clave: 'recorridos', nombre: 'Recorridos', color: COLOR.ok },
  { clave: 'usuarios', nombre: 'Usuarios nuevos', color: COLOR.detalle },
]

/** #3 Actividad en el tiempo: tres series en el mismo eje (todas son conteos). */
export default function GraficaActividad({ series }) {
  const filas = series.serie
  const vacio = filas.every((f) => !f.planes && !f.recorridos && !f.usuarios)
  return (
    <TarjetaGrafica
      titulo="Actividad en el tiempo"
      descripcion={`Usuarios nuevos, planes creados y recorridos guardados por ${series.agrupar === 'dia' ? 'día' : series.agrupar}.`}
      archivo="actividad"
      columnas={[{ clave: 'fecha', titulo: 'Periodo' }, ...SERIES.map((s) => ({ clave: s.clave, titulo: s.nombre, formato: numero }))]}
      filas={filas}
      vacio={vacio}
      alto="h-80"
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={filas} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
          <CartesianGrid {...REJILLA} />
          <XAxis dataKey="fecha" tickFormatter={fechaCorta} {...EJE} minTickGap={24} />
          <YAxis allowDecimals={false} {...EJE} />
          <Tooltip content={<TooltipKompas titulo={(l) => fechaCorta(l)} formato={numero} />} cursor={{ stroke: COLOR.textoSuave, strokeDasharray: '3 3' }} />
          <Legend iconType="plainline" wrapperStyle={{ fontSize: 12, color: COLOR.textoSuave }} />
          {SERIES.map((s) => (
            <Line
              key={s.clave}
              type="monotone"
              dataKey={s.clave}
              name={s.nombre}
              stroke={s.color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 5, stroke: COLOR.superficie, strokeWidth: 2 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </TarjetaGrafica>
  )
}
