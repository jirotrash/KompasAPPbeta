import { formatoFecha } from '../utils/geo.js'

/** Muestra de dónde viene un dato y qué tan reciente es (regla: siempre fuente y antigüedad). */
export default function FuenteDato({ fuente, fecha, tipo }) {
  return (
    <p className="text-xs text-texto-suave">
      Fuente: {fuente || 'sin fuente'} · {fecha ? `actualizado el ${formatoFecha(fecha)}` : 'sin fecha de verificación'}
      {tipo && ` · horario ${tipo}`}
    </p>
  )
}
