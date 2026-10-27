import { CartesianGrid, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from 'recharts'
import TarjetaGrafica from '../componentes/TarjetaGrafica.tsx'
import TooltipKompas from '../componentes/TooltipKompas.tsx'
import { COLOR, decimal, EJE, numero, REJILLA } from '../estilo.ts'
import type { BurbujaDFS, Laboratorio } from '../tipos.ts'

const NOMBRES = { limite_profundidad: 'Límite de profundidad', nodos: 'Nodos explorados', rutas: 'Rutas encontradas' }

/** #20 DFS: nodos explorados contra límite de profundidad; el tamaño de la burbuja = rutas encontradas. */
export default function GraficaDfs({ laboratorio }: { laboratorio: Laboratorio }) {
  const filas = laboratorio.dfs_puntos
  return (
    <TarjetaGrafica
      titulo="Búsqueda DFS: exploración vs. profundidad"
      descripcion="Cada burbuja junta consultas con el mismo límite y los mismos nodos explorados; más grande = más rutas encontradas."
      archivo="dfs-nodos-profundidad"
      columnas={[
        { clave: 'limite_profundidad', titulo: 'Límite de profundidad' },
        { clave: 'nodos', titulo: 'Nodos explorados', formato: numero },
        { clave: 'rutas', titulo: 'Rutas (promedio)', formato: decimal },
        { clave: 'consultas', titulo: 'Consultas', formato: numero },
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
            dataKey="limite_profundidad"
            name={NOMBRES.limite_profundidad}
            allowDecimals={false}
            domain={[1, 'dataMax + 1']}
            {...EJE}
            label={{ value: 'Límite de profundidad', position: 'insideBottom', offset: -4, fill: COLOR.textoSuave, fontSize: 12 }}
          />
          <YAxis type="number" dataKey="nodos" name={NOMBRES.nodos} allowDecimals={false} {...EJE} />
          <ZAxis type="number" dataKey="rutas" name={NOMBRES.rutas} range={[40, 600]} />
          <Tooltip
            content={<TooltipKompas formato={decimal} titulo={() => 'Consultas DFS'} extra={(f: BurbujaDFS) => `${numero(f.consultas)} consulta(s)`} />}
            cursor={{ strokeDasharray: '3 3' }}
          />
          <Scatter data={filas} name="Consultas" fill={COLOR.primario} fillOpacity={0.7} stroke={COLOR.superficie} strokeWidth={2} />
        </ScatterChart>
      </ResponsiveContainer>
    </TarjetaGrafica>
  )
}
