import Histograma from './Histograma.jsx'

/** #8 Presupuesto máximo por persona (histograma). */
export default function GraficaPresupuesto({ planes }) {
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
