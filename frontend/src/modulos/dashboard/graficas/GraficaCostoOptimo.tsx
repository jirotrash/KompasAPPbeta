import { Bar, BarChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import TarjetaGrafica from '../componentes/TarjetaGrafica.tsx'
import TooltipKompas from '../componentes/TooltipKompas.tsx'
import { COLOR, decimal, EJE, numero, porcentaje, REJILLA } from '../estilo.ts'
import type { AlgoritmoBusqueda, Laboratorio } from '../tipos.ts'

/** Costo del camino ÷ costo óptimo (1 = óptimo) por algoritmo y heurística, promediado en las corridas guardadas. */
export default function GraficaCostoOptimo({ laboratorio }: { laboratorio: Laboratorio }) {
  const filas = (laboratorio.busqueda_algoritmos ?? []).filter((f) => f.razon_vs_optimo !== null)
  return (
    <TarjetaGrafica
      titulo="Costo del camino vs. óptimo"
      descripcion="Cuántas veces más largo que el óptimo (1 = óptimo) salió el camino de cada algoritmo, en promedio. La línea marca el óptimo."
      archivo="costo-vs-optimo"
      columnas={[
        { clave: 'etiqueta', titulo: 'Algoritmo' },
        { clave: 'razon_vs_optimo', titulo: 'Costo ÷ óptimo', formato: decimal },
        { clave: 'porcentaje_optimo', titulo: '% de veces óptimo', formato: porcentaje },
        { clave: 'nodos_promedio', titulo: 'Nodos explorados (promedio)', formato: decimal },
        { clave: 'consultas', titulo: 'Corridas', formato: numero },
      ]}
      filas={filas}
      vacio={!filas.length}
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={filas} layout="vertical" margin={{ top: 8, right: 24, left: 8, bottom: 0 }}>
          <CartesianGrid {...REJILLA} horizontal={false} vertical />
          <XAxis type="number" domain={[0, 'auto']} {...EJE} tickFormatter={(v: number) => decimal(v)} />
          <YAxis type="category" dataKey="etiqueta" width={130} {...EJE} />
          <Tooltip
            content={<TooltipKompas formato={decimal} extra={(f: AlgoritmoBusqueda) => `Óptimo en ${porcentaje(f.porcentaje_optimo)} de ${numero(f.consultas)} corridas`} />}
            cursor={{ fill: 'var(--color-fondo)' }}
          />
          <ReferenceLine x={1} stroke={COLOR.texto} strokeDasharray="4 4" label={{ value: 'Óptimo', position: 'top', fill: COLOR.textoSuave, fontSize: 11 }} />
          <Bar dataKey="razon_vs_optimo" name="Costo ÷ óptimo" fill={COLOR.primario} radius={[0, 4, 4, 0]} maxBarSize={22} />
        </BarChart>
      </ResponsiveContainer>
    </TarjetaGrafica>
  )
}
