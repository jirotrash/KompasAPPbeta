import { COLOR, numero } from '../estilo.ts'

/** Valor junto a cada rebanada, en color de texto (nunca el de la serie). */
type Props = { x?: number; y?: number; cx?: number; value?: number }

export default function EtiquetaPie({ x = 0, y = 0, cx = 0, value }: Props) {
  if (!value) return null
  return (
    <text x={x} y={y} fill={COLOR.texto} fontSize={12} fontWeight={600} textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central">
      {numero(value)}
    </text>
  )
}
