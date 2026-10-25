import { COLOR, numero } from '../estilo.js'

/** Valor junto a cada rebanada, en color de texto (nunca el de la serie). */
export default function EtiquetaPie({ x, y, cx, value }) {
  if (!value) return null
  return (
    <text x={x} y={y} fill={COLOR.texto} fontSize={12} fontWeight={600} textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central">
      {numero(value)}
    </text>
  )
}
