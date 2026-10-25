import MapaCalor from '../componentes/MapaCalor.jsx'
import TarjetaGrafica from '../componentes/TarjetaGrafica.jsx'
import { DIAS_SEMANA, numero } from '../estilo.js'

/** #10 Día de la semana × hora de salida (mapa de calor). */
export default function GraficaDiaHora({ planes }) {
  const filas = planes.dia_hora.filter((c) => c.total).map((c) => ({ ...c, nombre_dia: DIAS_SEMANA[c.dia - 1], hora_texto: `${c.hora}:00` }))
  return (
    <TarjetaGrafica
      titulo="¿Cuándo salen?"
      descripcion="Día de la semana y hora de salida de los planes. Más oscuro = más planes."
      archivo="dia-hora"
      columnas={[
        { clave: 'nombre_dia', titulo: 'Día' },
        { clave: 'hora_texto', titulo: 'Hora' },
        { clave: 'total', titulo: 'Planes', formato: numero },
      ]}
      filas={filas}
      vacio={!filas.length}
    >
      <MapaCalor celdas={planes.dia_hora} />
    </TarjetaGrafica>
  )
}
