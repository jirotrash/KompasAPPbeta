import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import TarjetaGrafica from '../componentes/TarjetaGrafica.tsx'
import TooltipKompas from '../componentes/TooltipKompas.tsx'
import { CATEGORICO, COLOR, decimal, EJE, numero, REJILLA, TIPOS_PLAN } from '../estilo.ts'
import type { AhorroGenetico, Laboratorio } from '../tipos.ts'

const km = (v: number | null) => (v === null ? '—' : `${decimal(v)} km`)

/** km recorridos antes y después de que el genético ordenara las paradas de los planes reales, por tipo de plan. */
export default function GraficaAhorroGenetico({ laboratorio }: { laboratorio: Laboratorio }) {
  const filas = (laboratorio.genetico_ahorro ?? []).map((f) => ({ ...f, nombre: TIPOS_PLAN[f.tipo_plan] ?? f.tipo_plan }))
  const ahorro = filas.reduce((s, f) => s + f.km_ahorrados, 0)
  return (
    <TarjetaGrafica
      titulo="Km ahorrados por el genético"
      descripcion={`Suma de km de los planes antes y después de ordenar sus paradas. En total se ahorraron ${km(ahorro)}.`}
      archivo="ahorro-genetico"
      columnas={[
        { clave: 'nombre', titulo: 'Tipo de plan' },
        { clave: 'planes', titulo: 'Planes', formato: numero },
        { clave: 'reordenados', titulo: 'Reordenados', formato: numero },
        { clave: 'km_antes', titulo: 'Km antes', formato: km },
        { clave: 'km_despues', titulo: 'Km después', formato: km },
        { clave: 'km_ahorrados', titulo: 'Km ahorrados', formato: km },
      ]}
      filas={filas}
      vacio={!filas.length}
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={filas} margin={{ top: 8, right: 8, left: -8, bottom: 0 }} barGap={2}>
          <CartesianGrid {...REJILLA} />
          <XAxis dataKey="nombre" {...EJE} />
          <YAxis {...EJE} />
          <Tooltip
            content={<TooltipKompas formato={km} extra={(f: AhorroGenetico) => `${numero(f.reordenados)} de ${numero(f.planes)} planes reordenados`} />}
            cursor={{ fill: 'var(--color-fondo)' }}
          />
          <Legend wrapperStyle={{ fontSize: 12, color: COLOR.textoSuave }} />
          <Bar dataKey="km_antes" name="Antes" fill={CATEGORICO[3]} radius={[4, 4, 0, 0]} maxBarSize={40} stroke={COLOR.superficie} strokeWidth={2} />
          <Bar dataKey="km_despues" name="Después" fill={CATEGORICO[0]} radius={[4, 4, 0, 0]} maxBarSize={40} stroke={COLOR.superficie} strokeWidth={2} />
        </BarChart>
      </ResponsiveContainer>
    </TarjetaGrafica>
  )
}
