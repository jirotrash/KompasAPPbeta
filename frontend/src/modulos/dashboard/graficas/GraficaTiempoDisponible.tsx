import Histograma from './Histograma.tsx'
import type { Planes } from '../tipos.ts'

/** #9 Tiempo disponible (histograma). */
export default function GraficaTiempoDisponible({ planes }: { planes: Planes }) {
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
