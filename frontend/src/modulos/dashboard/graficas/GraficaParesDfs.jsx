import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import useEsMovil from '../../../compartido/hooks/useEsMovil.js'
import TarjetaGrafica from '../componentes/TarjetaGrafica.jsx'
import TooltipKompas from '../componentes/TooltipKompas.jsx'
import { COLOR, EJE, numero, REJILLA } from '../estilo.js'

/** #22 Pares origen → destino más consultados en la demostración DFS. */
export default function GraficaParesDfs({ laboratorio }) {
  const filas = laboratorio.dfs_pares_top
  const esMovil = useEsMovil()
  return (
    <TarjetaGrafica
      titulo="Pares más consultados en DFS"
      descripcion="Origen → destino que más se buscaron en la demostración académica."
      archivo="pares-dfs"
      columnas={[
        { clave: 'par', titulo: 'Origen → destino' },
        { clave: 'total', titulo: 'Consultas', formato: numero },
      ]}
      filas={filas}
      vacio={!filas.length}
      alto="h-80"
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={filas} layout="vertical" margin={{ top: 0, right: 40, left: 8, bottom: 0 }}>
          <CartesianGrid {...REJILLA} horizontal={false} vertical />
          <XAxis type="number" allowDecimals={false} {...EJE} />
          <YAxis type="category" dataKey="par" width={esMovil ? 120 : 220} interval={0} {...EJE} fontSize={11} />
          <Tooltip content={<TooltipKompas formato={numero} />} cursor={{ fill: 'var(--color-fondo)' }} />
          <Bar dataKey="total" name="Consultas" fill={COLOR.primario} radius={[0, 4, 4, 0]} maxBarSize={22}>
            <LabelList dataKey="total" position="right" formatter={numero} fill={COLOR.texto} fontSize={12} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </TarjetaGrafica>
  )
}
