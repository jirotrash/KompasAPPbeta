import { IconoInfo } from './Iconos.jsx'

/** Se muestra cuando no hay datos verificados. Nunca se inventan rutas ni horarios. */
export function AvisoSinInformacion({ mensaje }) {
  return (
    <div role="status" className="flex gap-3 rounded-2xl border border-aviso/30 bg-aviso-fondo p-4 text-aviso">
      <IconoInfo className="size-5 shrink-0" />
      <p className="text-sm font-medium">{mensaje || 'No tenemos información suficiente para esta ruta.'}</p>
    </div>
  )
}

export function MensajeError({ children }) {
  if (!children) return null
  return (
    <p role="alert" className="rounded-xl bg-peligro-fondo px-3 py-2 text-sm font-medium text-peligro">
      {children}
    </p>
  )
}

export function EtiquetaEjemplo() {
  return (
    <span className="inline-flex items-center rounded-full bg-aviso-fondo px-2 py-0.5 text-xs font-semibold text-aviso">
      Dato de ejemplo
    </span>
  )
}

export function Cargando({ texto = 'Cargando…' }) {
  return (
    <div role="status" className="flex items-center gap-3 py-6 text-texto-suave">
      <span className="size-5 animate-spin rounded-full border-2 border-primario border-t-transparent" />
      {texto}
    </div>
  )
}
