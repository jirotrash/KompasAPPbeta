import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import TarjetaGrafica from '../componentes/TarjetaGrafica.tsx'
import TooltipKompas from '../componentes/TooltipKompas.tsx'
import { CATEGORICO, COLOR, EJE, numero, REJILLA } from '../estilo.ts'
import type { Laboratorio } from '../tipos.ts'

const aptitud = (v: number | null) => (v === null ? '—' : v.toFixed(4))

/** Convergencia promedio del algoritmo genético: mejor aptitud y aptitud promedio de la población por generación. */
export default function GraficaConvergencia({ laboratorio }: { laboratorio: Laboratorio }) {
  const filas = laboratorio.genetico_convergencia ?? []
  const ejecuciones = filas[0]?.ejecuciones ?? 0
  return (
    <TarjetaGrafica
      titulo="Convergencia del algoritmo genético"
      descripcion={`Aptitud = 1 / (1 + km + penalización), promediada en ${numero(ejecuciones)} ejecuciones (ordenar las paradas de los planes).`}
      archivo="convergencia-genetico"
      columnas={[
        { clave: 'generacion', titulo: 'Generación' },
        { clave: 'mejor', titulo: 'Mejor aptitud', formato: aptitud },
        { clave: 'promedio', titulo: 'Aptitud promedio', formato: aptitud },
        { clave: 'ejecuciones', titulo: 'Ejecuciones', formato: numero },
      ]}
      filas={filas}
      vacio={!filas.length}
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={filas} margin={{ top: 8, right: 12, left: -4, bottom: 0 }}>
          <CartesianGrid {...REJILLA} />
          <XAxis dataKey="generacion" {...EJE} minTickGap={24} />
          <YAxis {...EJE} tickFormatter={(v: number) => v.toFixed(3)} domain={['auto', 'auto']} />
          <Tooltip content={<TooltipKompas titulo={(g: number) => `Generación ${g}`} formato={aptitud} />} cursor={{ stroke: COLOR.textoSuave, strokeDasharray: '3 3' }} />
          <Legend iconType="plainline" wrapperStyle={{ fontSize: 12, color: COLOR.textoSuave }} />
          <Line type="monotone" dataKey="mejor" name="Mejor aptitud" stroke={CATEGORICO[0]} strokeWidth={2} dot={false} activeDot={{ r: 5, stroke: COLOR.superficie, strokeWidth: 2 }} />
          <Line type="monotone" dataKey="promedio" name="Aptitud promedio" stroke={CATEGORICO[1]} strokeWidth={2} dot={false} activeDot={{ r: 5, stroke: COLOR.superficie, strokeWidth: 2 }} />
        </LineChart>
      </ResponsiveContainer>
    </TarjetaGrafica>
  )
}
