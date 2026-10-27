import Histograma from './Histograma.tsx'
import type { Planes } from '../tipos.ts'

/** #8 Presupuesto máximo por persona (histograma). */
export default function GraficaPresupuesto({ planes }: { planes: Planes }) {
  return (
    <Histograma
      titulo="Presupuesto por persona"
      descripcion="Presupuesto máximo por persona que indicaron al crear el plan (MXN)."
      archivo="presupuesto"
      etiquetaRango="Presupuesto"
      filas={planes.presupuesto}
    />
  )
}
