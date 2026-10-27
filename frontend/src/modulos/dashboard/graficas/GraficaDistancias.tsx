import { CartesianGrid, ReferenceLine, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from 'recharts'
import TarjetaGrafica from '../componentes/TarjetaGrafica.tsx'
import TooltipKompas from '../componentes/TooltipKompas.tsx'
import { COLOR, decimal, EJE, REJILLA } from '../estilo.ts'
import type { Laboratorio } from '../tipos.ts'

/** #21 Euclidiana vs. Manhattan de cada consulta del laboratorio, con la línea y = x de referencia. */
export default function GraficaDistancias({ laboratorio }: { laboratorio: Laboratorio }) {
  const filas = laboratorio.distancias_puntos
  const tope = Math.ceil(Math.max(1, ...filas.map((f) => Math.max(f.euclidiana, f.manhattan))))
  return (
    <TarjetaGrafica
      titulo="Euclidiana vs. Manhattan"
      descripcion="Cada punto es una consulta. La línea punteada es y = x: Manhattan nunca queda debajo de ella."
      archivo="euclidiana-vs-manhattan"
      columnas={[
        { clave: 'modo', titulo: 'Modo' },
        { clave: 'euclidiana', titulo: 'Euclidiana', formato: decimal },
        { clave: 'manhattan', titulo: 'Manhattan', formato: decimal },
      ]}
      filas={filas}
      vacio={!filas.length}
      alto="h-80"
    >
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 12, right: 12, left: -8, bottom: 8 }}>
          <CartesianGrid {...REJILLA} vertical />
          <XAxis
            type="number"
            dataKey="euclidiana"
            name="Euclidiana"
            domain={[0, tope]}
            {...EJE}
            label={{ value: 'Euclidiana', position: 'insideBottom', offset: -4, fill: COLOR.textoSuave, fontSize: 12 }}
          />
          <YAxis type="number" dataKey="manhattan" name="Manhattan" domain={[0, tope]} {...EJE} />
          <ReferenceLine
            segment={[
              { x: 0, y: 0 },
              { x: tope, y: tope },
            ]}
            stroke={COLOR.textoSuave}
            strokeDasharray="4 4"
            label={{ value: 'y = x', position: 'insideTopLeft', fill: COLOR.textoSuave, fontSize: 12 }}
          />
          <Tooltip content={<TooltipKompas formato={decimal} titulo={() => 'Consulta de distancias'} />} cursor={{ strokeDasharray: '3 3' }} />
          <Scatter data={filas} name="Consultas" fill={COLOR.detalle} fillOpacity={0.75} stroke={COLOR.superficie} strokeWidth={1} />
        </ScatterChart>
      </ResponsiveContainer>
    </TarjetaGrafica>
  )
}
