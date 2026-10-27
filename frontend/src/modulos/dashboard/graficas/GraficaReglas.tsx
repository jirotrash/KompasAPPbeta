import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import TarjetaGrafica from '../componentes/TarjetaGrafica.tsx'
import TooltipKompas from '../componentes/TooltipKompas.tsx'
import { COLOR, EJE, REJILLA, etiquetaNumero, numero } from '../estilo.ts'
import type { SistemaExperto } from '../tipos.ts'

/** #13 Reglas más activadas (R01–R20); la descripción de cada regla va en el tooltip. */
export default function GraficaReglas({ sistema }: { sistema: SistemaExperto }) {
  const filas = sistema.reglas_top
  return (
    <TarjetaGrafica
      titulo="Reglas más activadas"
      descripcion="¿Qué reglas del sistema experto se usan más? Pasa el cursor para leer qué dice cada una."
      archivo="reglas-activadas"
      columnas={[
        { clave: 'id', titulo: 'Regla' },
        { clave: 'descripcion', titulo: 'Descripción' },
        { clave: 'total', titulo: 'Veces', formato: numero },
      ]}
      filas={filas}
      vacio={!filas.length}
      alto="h-[26rem]"
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={filas} layout="vertical" margin={{ top: 0, right: 44, left: 0, bottom: 0 }}>
          <CartesianGrid {...REJILLA} horizontal={false} vertical />
          <XAxis type="number" allowDecimals={false} {...EJE} />
          <YAxis type="category" dataKey="id" width={44} interval={0} {...EJE} />
          <Tooltip content={<TooltipKompas formato={numero} extra={(f: SistemaExperto['reglas_top'][number]) => f.descripcion} />} cursor={{ fill: 'var(--color-fondo)' }} />
          <Bar dataKey="total" name="Veces activada" fill={COLOR.primario} radius={[0, 4, 4, 0]} maxBarSize={18}>
            <LabelList dataKey="total" position="right" formatter={etiquetaNumero} fill={COLOR.texto} fontSize={11} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </TarjetaGrafica>
  )
}
