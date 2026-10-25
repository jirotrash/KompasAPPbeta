import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import TarjetaGrafica from '../componentes/TarjetaGrafica.jsx'
import TooltipKompas from '../componentes/TooltipKompas.jsx'
import { COLOR, EJE, minutos, numero, REJILLA } from '../estilo.js'

/** #16 Rutas más usadas en los recorridos guardados. */
export default function GraficaRutasTop({ movilidad }) {
  const filas = movilidad.rutas_top
  return (
    <TarjetaGrafica
      titulo="Rutas más usadas"
      descripcion="Las 10 rutas con más recorridos guardados."
      archivo="rutas-mas-usadas"
      columnas={[
        { clave: 'ruta', titulo: 'Ruta' },
        { clave: 'total', titulo: 'Recorridos', formato: numero },
        { clave: 'promedio', titulo: 'Promedio (min)', formato: minutos },
      ]}
      filas={filas}
      vacio={!filas.length}
      alto="h-80"
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={filas} margin={{ top: 20, right: 8, left: -12, bottom: 0 }}>
          <CartesianGrid {...REJILLA} />
          <XAxis dataKey="ruta" {...EJE} interval={0} />
          <YAxis allowDecimals={false} {...EJE} />
          <Tooltip content={<TooltipKompas formato={numero} extra={(f) => `Promedio: ${minutos(f.promedio)}`} />} cursor={{ fill: 'var(--color-fondo)' }} />
          <Bar dataKey="total" name="Recorridos" fill={COLOR.primario} radius={[4, 4, 0, 0]} maxBarSize={48}>
            <LabelList dataKey="total" position="top" formatter={numero} fill={COLOR.texto} fontSize={12} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </TarjetaGrafica>
  )
}
