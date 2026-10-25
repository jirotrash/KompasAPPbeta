import { NavLink, Outlet } from 'react-router-dom'
import { USA_MOCK } from '../compartido/api/cliente.js'
import { IconoDashboard, IconoSalir } from '../compartido/componentes/Iconos.jsx'
import Logo from '../compartido/componentes/Logo.jsx'
import { BotonTema, SelectorTema } from '../compartido/componentes/SelectorTema.jsx'
import { useAuth } from '../modulos/cuenta'

export default function Layout() {
  const { usuario, logout } = useAuth()

  return (
    <div className="flex min-h-dvh flex-col md:pl-60">
      {/* Barra lateral: tablet y escritorio */}
      <aside className="fixed inset-y-0 left-0 z-[1100] hidden w-60 flex-col border-r border-borde bg-superficie p-4 md:flex">
        <div className="mb-8 flex items-center gap-3 px-2">
          <Logo />
          <div>
            <p className="font-bold leading-tight">Kompás</p>
            <p className="text-xs text-texto-suave">Panel de administración</p>
          </div>
        </div>
        <nav aria-label="Principal" className="flex flex-col gap-1">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `flex min-h-11 items-center gap-3 rounded-xl px-3 font-medium transition ${
                isActive ? 'bg-primario-claro text-primario-oscuro' : 'text-texto-suave hover:bg-fondo'
              }`
            }
          >
            <IconoDashboard className="size-5" />
            Dashboard
          </NavLink>
        </nav>
        <div className="mt-auto space-y-3 border-t border-borde pt-4">
          <SelectorTema />
          <p className="truncate px-2 text-sm text-texto-suave">{usuario?.email}</p>
          <button type="button" onClick={logout} className="boton-secundario w-full text-sm">
            <IconoSalir className="size-5" /> Cerrar sesión
          </button>
        </div>
      </aside>

      {/* Encabezado: celular */}
      <header className="sticky top-0 z-[1100] flex items-center gap-3 border-b border-borde bg-superficie/95 px-4 pb-2 pt-[max(0.5rem,env(safe-area-inset-top))] backdrop-blur md:hidden">
        <Logo className="size-8" />
        <p className="flex-1 font-bold">Kompás · Dashboard</p>
        <BotonTema />
        <button type="button" onClick={logout} className="boton px-2 text-texto-suave" aria-label="Cerrar sesión">
          <IconoSalir className="size-5" />
        </button>
      </header>

      {USA_MOCK && (
        <p className="bg-aviso-fondo px-4 py-1.5 text-center text-xs font-medium text-aviso">
          Modo demostración: se muestran datos de ejemplo.
        </p>
      )}

      <main className="flex flex-1 flex-col">
        <Outlet />
      </main>
    </div>
  )
}
