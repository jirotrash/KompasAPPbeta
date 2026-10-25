import { PolarAngleAxis, RadialBar, RadialBarChart, ResponsiveContainer } from 'recharts'
import TarjetaGrafica from '../componentes/TarjetaGrafica.jsx'
import { COLOR, numero, porcentaje } from '../estilo.js'

/** #2 Medidor: % de planes evaluados con al menos una opción recomendable. */
export default function GraficaRecomendacion({ kpis }) {
  const valor = kpis.porcentaje_con_recomendacion
  const filas = [{ indicador: 'Planes con recomendación', valor, evaluados: kpis.planes_evaluados }]
  return (
    <TarjetaGrafica
      titulo="Planes con recomendación"
      descripcion="De los planes evaluados por el sistema experto, cuántos tuvieron al menos una opción recomendable."
      archivo="planes-con-recomendacion"
      columnas={[
        { clave: 'indicador', titulo: 'Indicador' },
        { clave: 'valor', titulo: '%', formato: porcentaje },
        { clave: 'evaluados', titulo: 'Planes evaluados', formato: numero },
      ]}
      filas={filas}
      vacio={!kpis.planes_evaluados}
    >
      <div className="relative h-full">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart data={[{ valor }]} innerRadius="72%" outerRadius="100%" startAngle={210} endAngle={-30}>
            <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
            <RadialBar dataKey="valor" fill={COLOR.ok} background={{ fill: 'var(--color-fondo)' }} cornerRadius={8} isAnimationActive={false} />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 grid place-content-center text-center">
          <p className="text-4xl font-bold tabular-nums">{porcentaje(valor)}</p>
          <p className="text-sm text-texto-suave">de {numero(kpis.planes_evaluados)} planes</p>
        </div>
      </div>
    </TarjetaGrafica>
  )
}
