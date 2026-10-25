/** Leyenda con el orden y los colores de la entidad (el texto va en color de texto, la muestra en el de la serie). */
export default function LeyendaKompas({ items }) {
  return (
    <ul className="flex flex-wrap justify-center gap-x-4 gap-y-1 pt-2 text-xs text-texto-suave">
      {items.map((i) => (
        <li key={i.nombre} className="flex items-center gap-1.5">
          <span aria-hidden="true" className="size-2.5 rounded-sm" style={{ background: i.color }} />
          {i.nombre}
        </li>
      ))}
    </ul>
  )
}
