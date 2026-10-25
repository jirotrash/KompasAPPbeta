import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import EtiquetaPie from '../componentes/EtiquetaPie.jsx'
import TarjetaGrafica from '../componentes/TarjetaGrafica.jsx'
import TooltipKompas from '../componentes/TooltipKompas.jsx'
import { COLOR, ESTADOS, nombreDe, numero } from '../estilo.js'

/** #12 Resultado de la evaluación: estado de cada candidato que revisó el motor. */
export default function GraficaEstados({ sistema }) {
  const filas = sistema.por_estado.map((f) => ({ ...f, nombre: nombreDe(ESTADOS, f.estado) }))
  return (
    <TarjetaGrafica
      titulo="Resultado de la evaluación"
      descripcion="Cada plan genera hasta 3 candidatos; así los clasificó el sistema experto."
      archivo="estados-sistema-experto"
      columnas={[
        { clave: 'nombre', titulo: 'Estado' },
        { clave: 'total', titulo: 'Candidatos', formato: numero },
      ]}
      filas={filas}
      vacio={!filas.length}
    >
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={filas}
            dataKey="total"
            nameKey="nombre"
            outerRadius="78%"
            stroke={COLOR.superficie}
            strokeWidth={2}
            label={<EtiquetaPie />}
            labelLine={false}
          >
            {filas.map((f) => (
              <Cell key={f.estado} fill={ESTADOS[f.estado]?.color ?? COLOR.textoSuave} />
            ))}
          </Pie>
          <Tooltip content={<TooltipKompas formato={numero} />} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
        </PieChart>
      </ResponsiveContainer>
      <p className="sr-only">{`Planes sin datos suficientes: ${sistema.sin_datos_suficientes}`}</p>
    </TarjetaGrafica>
  )
}
