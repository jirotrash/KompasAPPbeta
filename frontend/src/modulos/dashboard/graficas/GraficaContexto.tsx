import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import EtiquetaPie from '../componentes/EtiquetaPie.tsx'
import TarjetaGrafica from '../componentes/TarjetaGrafica.tsx'
import TooltipKompas from '../componentes/TooltipKompas.tsx'
import { COLOR, CONTEXTOS, nombreDe, numero } from '../estilo.ts'
import type { Planes } from '../tipos.ts'

/** #6 Con quién salen (dona). */
export default function GraficaContexto({ planes }: { planes: Planes }) {
  const filas = planes.por_contexto.map((f) => ({ ...f, nombre: nombreDe(CONTEXTOS, f.contexto) }))
  const total = filas.reduce((s, f) => s + f.total, 0)
  return (
    <TarjetaGrafica
      titulo="¿Con quién salen?"
      descripcion="Contexto elegido al crear el plan."
      archivo="planes-por-contexto"
      columnas={[
        { clave: 'nombre', titulo: 'Contexto' },
        { clave: 'total', titulo: 'Planes', formato: numero },
      ]}
      filas={filas}
      vacio={!total}
    >
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={filas}
            dataKey="total"
            nameKey="nombre"
            innerRadius="55%"
            outerRadius="78%"
            paddingAngle={1}
            stroke={COLOR.superficie}
            strokeWidth={2}
            label={<EtiquetaPie />}
            labelLine={false}
          >
            {filas.map((f) => (
              <Cell key={f.contexto} fill={CONTEXTOS[f.contexto]?.color ?? COLOR.primario} />
            ))}
          </Pie>
          <Tooltip content={<TooltipKompas formato={numero} />} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
        </PieChart>
      </ResponsiveContainer>
    </TarjetaGrafica>
  )
}
