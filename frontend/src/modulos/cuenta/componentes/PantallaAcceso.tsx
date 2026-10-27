import type { ReactNode } from 'react'
import Logo from '../../../compartido/componentes/Logo.tsx'
import { BotonTema } from '../../../compartido/componentes/SelectorTema.tsx'

/** Marco del login: una columna en celular, dos en escritorio. */
export default function PantallaAcceso({ titulo, children }: { titulo: string; children: ReactNode }) {
  return (
    <div className="grid min-h-dvh lg:grid-cols-2">
      <section className="hidden flex-col justify-between bg-primario p-12 text-sobre-primario lg:flex">
        <div className="flex items-center gap-3">
          <Logo className="size-11 rounded-xl ring-2 ring-white/30" />
          <span className="text-xl font-bold">Kompás</span>
        </div>
        <div className="max-w-md space-y-6">
          <Logo className="size-40 rounded-[2rem] shadow-xl" alt="Logotipo de Kompás" />
          <h2 className="text-4xl font-bold leading-tight">Panel de administración</h2>
          <p className="text-lg text-sobre-primario/80">
            Cómo se usa Kompás y cómo decide su sistema experto, con datos agregados desde la API.
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
              <p className="text-lg font-bold">Kompás</p>
              <p className="text-sm text-texto-suave">Panel de administración</p>
            </div>
          </div>
          <h1 className="mb-6 text-2xl font-bold">{titulo}</h1>
          {children}
        </div>
      </section>
    </div>
  )
}
