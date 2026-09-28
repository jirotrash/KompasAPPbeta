import { ZONA } from '../config/zona.js'
import Logo from './Logo.jsx'
import { BotonTema } from './SelectorTema.jsx'

/** Marco de login y registro: una columna en celular, dos en escritorio. */
export default function PantallaAcceso({ titulo, children }) {
  return (
    <div className="grid min-h-dvh lg:grid-cols-2">
      <section className="hidden flex-col justify-between bg-primario p-12 text-sobre-primario lg:flex">
        <div className="flex items-center gap-3">
          <Logo className="size-11 rounded-xl ring-2 ring-white/30" />
          <span className="text-xl font-bold">Brújula Urbana</span>
        </div>
        <div className="max-w-md space-y-4">
          <h2 className="text-4xl font-bold leading-tight">Decide cómo moverte y a dónde ir.</h2>
          <p className="text-lg text-sobre-primario/80">
            Rutas de transporte, tiempos estimados e itinerarios explicados para {ZONA.nombre}.
          </p>
        </div>
        <p className="text-sm text-sobre-primario/70">Proyecto escolar UTVT · ITIID-D71</p>
      </section>

      <section className="relative flex items-center justify-center px-4 py-10 sm:px-8">
        <BotonTema className="absolute right-3 top-[max(0.75rem,env(safe-area-inset-top))]" />
        <div className="w-full max-w-sm">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <Logo className="size-11" />
            <div>
              <p className="text-lg font-bold">Brújula Urbana</p>
              <p className="text-sm text-texto-suave">{ZONA.nombre}</p>
            </div>
          </div>
          <h1 className="mb-6 text-2xl font-bold">{titulo}</h1>
          {children}
        </div>
      </section>
    </div>
  )
}
