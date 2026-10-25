import { cambiarTema, useTema } from '../utils/tema.js'
import { IconoLuna, IconoMonitor, IconoSol } from './Iconos.jsx'

const OPCIONES = [
  { valor: 'claro', texto: 'Claro', Icono: IconoSol },
  { valor: 'oscuro', texto: 'Oscuro', Icono: IconoLuna },
  { valor: 'sistema', texto: 'Sistema', Icono: IconoMonitor },
]

/** Control segmentado Claro / Oscuro / Sistema. */
export function SelectorTema({ className = '' }) {
  const { preferencia } = useTema()
  return (
    <div role="radiogroup" aria-label="Tema" className={`grid grid-cols-3 gap-1 rounded-xl bg-fondo p-1 ${className}`}>
      {OPCIONES.map(({ valor, texto, Icono }) => (
        <button
          key={valor}
          type="button"
          role="radio"
          aria-checked={preferencia === valor}
          onClick={() => cambiarTema(valor)}
          className={`flex min-h-9 flex-col items-center justify-center gap-0.5 rounded-lg text-[11px] font-medium transition ${
            preferencia === valor ? 'bg-superficie text-primario shadow-sm' : 'text-texto-suave hover:text-texto'
          }`}
        >
          <Icono className="size-4" />
          {texto}
        </button>
      ))}
    </div>
  )
}

/** Botón compacto (encabezado del celular): alterna entre claro y oscuro. */
export function BotonTema({ className = '' }) {
  const { tema } = useTema()
  const siguiente = tema === 'oscuro' ? 'claro' : 'oscuro'
  return (
    <button
      type="button"
      onClick={() => cambiarTema(siguiente)}
      className={`boton px-2 text-texto-suave ${className}`}
      aria-label={`Cambiar a modo ${siguiente}`}
      title={`Modo ${siguiente}`}
    >
      {tema === 'oscuro' ? <IconoSol className="size-5" /> : <IconoLuna className="size-5" />}
    </button>
  )
}
