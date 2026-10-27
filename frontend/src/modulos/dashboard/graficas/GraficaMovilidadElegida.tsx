import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import TarjetaGrafica from '../componentes/TarjetaGrafica.tsx'
import TooltipKompas from '../componentes/TooltipKompas.tsx'
import { COLOR, EJE, MOVILIDAD, nombreDe, REJILLA, etiquetaNumero, numero } from '../estilo.ts'
import type { Planes } from '../tipos.ts'

/** #7 Movilidad elegida (barras horizontales con el color de cada transporte). */
export default function GraficaMovilidadElegida({ planes }: { planes: Planes }) {
  const filas = planes.por_movilidad.map((f) => ({ ...f, nombre: nombreDe(MOVILIDAD, f.movilidad) }))
  return (
    <TarjetaGrafica
      titulo="Movilidad elegida"
      descripcion="Cómo piensan moverse al crear el plan (se pueden elegir varias formas)."
      archivo="movilidad-elegida"
      columnas={[
        { clave: 'nombre', titulo: 'Movilidad' },
        { clave: 'total', titulo: 'Planes', formato: numero },
      ]}
      filas={filas}
      vacio={filas.every((f) => !f.total)}
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={filas} layout="vertical" margin={{ top: 0, right: 40, left: 8, bottom: 0 }}>
          <CartesianGrid {...REJILLA} horizontal={false} vertical />
          <XAxis type="number" allowDecimals={false} {...EJE} />
          <YAxis type="category" dataKey="nombre" width={130} {...EJE} />
          <Tooltip content={<TooltipKompas formato={numero} />} cursor={{ fill: 'var(--color-fondo)' }} />
          <Bar dataKey="total" name="Planes" radius={[0, 4, 4, 0]} maxBarSize={32}>
            {filas.map((f) => (
              <Cell key={f.movilidad} fill={MOVILIDAD[f.movilidad]?.color ?? COLOR.primario} />
            ))}
            <LabelList dataKey="total" position="right" formatter={etiquetaNumero} fill={COLOR.texto} fontSize={12} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </TarjetaGrafica>
  )
}
