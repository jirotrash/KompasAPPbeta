import { Legend, PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer, Tooltip } from 'recharts'
import TarjetaGrafica from '../componentes/TarjetaGrafica.jsx'
import TooltipKompas from '../componentes/TooltipKompas.jsx'
import { COLOR, CONTEXTOS, INTERESES, nombreDe, numero } from '../estilo.js'

/** #11 Perfil de intereses por contexto (radar, una serie por contexto). */
export default function GraficaPerfilContexto({ planes }) {
  const filas = planes.interes_por_contexto.map((f) => ({ ...f, nombre: nombreDe(INTERESES, f.interes) }))
  const vacio = filas.every((f) => Object.keys(CONTEXTOS).every((c) => !f[c]))
  return (
    <TarjetaGrafica
      titulo="Intereses según con quién salen"
      descripcion="Cada línea es un contexto; mientras más lejos del centro, más veces se eligió ese interés."
      archivo="intereses-por-contexto"
      columnas={[{ clave: 'nombre', titulo: 'Interés' }, ...Object.entries(CONTEXTOS).map(([clave, c]) => ({ clave, titulo: c.nombre, formato: numero }))]}
      filas={filas}
      vacio={vacio}
      alto="h-80"
    >
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={filas} outerRadius="70%">
          <PolarGrid stroke={COLOR.borde} />
          <PolarAngleAxis dataKey="nombre" tick={{ fill: COLOR.textoSuave, fontSize: 12 }} />
          <PolarRadiusAxis tick={false} axisLine={false} />
          {Object.entries(CONTEXTOS).map(([clave, c]) => (
            <Radar key={clave} dataKey={clave} name={c.nombre} stroke={c.color} strokeWidth={2} fill={c.color} fillOpacity={0.08} dot={{ r: 3 }} />
          ))}
          <Tooltip content={<TooltipKompas formato={numero} />} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
        </RadarChart>
      </ResponsiveContainer>
    </TarjetaGrafica>
  )
}
