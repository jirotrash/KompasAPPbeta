import Histograma from './Histograma.jsx'

/** #9 Tiempo disponible (histograma). */
export default function GraficaTiempoDisponible({ planes }) {
  return (
    <Histograma
      titulo="Tiempo disponible"
      descripcion="Cuántas horas tenían para su salida."
      archivo="tiempo-disponible"
      etiquetaRango="Tiempo"
      filas={planes.tiempo_disponible}
    />
  )
}
