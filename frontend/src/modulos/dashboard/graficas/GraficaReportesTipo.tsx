import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import TarjetaGrafica from '../componentes/TarjetaGrafica.tsx'
import TooltipKompas from '../componentes/TooltipKompas.tsx'
import { COLOR, EJE, ESTADOS_REPORTE, nombreDe, numero, REJILLA, TIPOS_REPORTE } from '../estilo.ts'
import type { Entidad } from '../estilo.ts'
import type { Reportes } from '../tipos.ts'

/** #17 Reportes por tipo y estado (barras apiladas). */
export default function GraficaReportesTipo({ reportes }: { reportes: Reportes }) {
  const filas = reportes.por_tipo_estado.map((f) => ({ ...f, nombre: nombreDe(TIPOS_REPORTE, f.tipo) }))
  const estados = Object.entries(ESTADOS_REPORTE) as [keyof typeof ESTADOS_REPORTE, Entidad][]
  const { vigentes, vencidos } = reportes.vigentes_vs_vencidos
  return (
    <TarjetaGrafica
      titulo="Reportes por tipo y estado"
      descripcion={`Reportes comunitarios del periodo: ${numero(vigentes)} siguen vigentes y ${numero(vencidos)} ya vencieron.`}
      archivo="reportes-por-tipo"
      columnas={[{ clave: 'nombre', titulo: 'Tipo' }, ...estados.map(([clave, e]) => ({ clave, titulo: e.nombre, formato: numero }))]}
      filas={filas}
      vacio={filas.every((f) => estados.every(([e]) => !f[e]))}
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={filas} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
          <CartesianGrid {...REJILLA} />
          <XAxis dataKey="nombre" {...EJE} interval={0} />
          <YAxis allowDecimals={false} {...EJE} />
          <Tooltip content={<TooltipKompas formato={numero} />} cursor={{ fill: 'var(--color-fondo)' }} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {estados.map(([clave, e], i) => (
            <Bar
              key={clave}
              dataKey={clave}
              name={e.nombre}
              stackId="estado"
              fill={e.color}
              stroke={COLOR.superficie}
              strokeWidth={2}
              maxBarSize={56}
              radius={i === estados.length - 1 ? [4, 4, 0, 0] : 0}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </TarjetaGrafica>
  )
}
