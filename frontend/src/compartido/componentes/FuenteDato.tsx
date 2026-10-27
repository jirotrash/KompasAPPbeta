import { formatoFecha } from '../utils/geo.ts'

/** Muestra de dónde viene un dato y qué tan reciente es (regla: siempre fuente y antigüedad). */
type Props = { fuente?: string | null; fecha?: string | null; tipo?: string | null }

export default function FuenteDato({ fuente, fecha, tipo }: Props) {
  return (
    <p className="text-xs text-texto-suave">
      Fuente: {fuente || 'sin fuente'} · {fecha ? `actualizado el ${formatoFecha(fecha)}` : 'sin fecha de verificación'}
      {tipo && ` · horario ${tipo}`}
    </p>
  )
}
