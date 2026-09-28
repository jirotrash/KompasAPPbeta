export default function Chip({ activo, children, ...props }) {
  return (
    <button
      type="button"
      aria-pressed={activo}
      className={`inline-flex min-h-11 items-center gap-2 rounded-full border px-4 text-sm font-medium transition ${
        activo
          ? 'border-primario bg-primario-claro text-primario-oscuro'
          : 'border-borde bg-superficie text-texto-suave hover:border-primario'
      }`}
      {...props}
    >
      {children}
    </button>
  )
}
