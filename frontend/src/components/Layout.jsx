import { NavLink, Outlet } from 'react-router-dom'
import { ZONA } from '../config/zona.js'
import { useAuth } from '../context/auth.js'
import { USA_MOCK } from '../services/api.js'
import { IconoInicio, IconoItinerario, IconoReporte, IconoRuta, IconoSalir } from './Iconos.jsx'
import Logo from './Logo.jsx'
import { BotonTema, SelectorTema } from './SelectorTema.jsx'

const SECCIONES = [
  { a: '/', texto: 'Inicio', Icono: IconoInicio },
  { a: '/buscar', texto: 'Rutas', Icono: IconoRuta },
  { a: '/itinerarios', texto: 'Itinerarios', Icono: IconoItinerario },
  { a: '/reportar', texto: 'Reportar', Icono: IconoReporte },
]

export default function Layout() {
  const { usuario, logout } = useAuth()

  return (
    <div className="flex min-h-dvh flex-col md:pl-60">
      {/* Barra lateral: tablet y escritorio */}
      <aside className="fixed inset-y-0 left-0 z-[1100] hidden w-60 flex-col border-r border-borde bg-superficie p-4 md:flex">
        <div className="mb-8 flex items-center gap-3 px-2">
          <Logo />
          <div>
            <p className="font-bold leading-tight">Brújula Urbana</p>
            <p className="text-xs text-texto-suave">{ZONA.nombre}</p>
          </div>
        </div>
        <nav aria-label="Principal" className="flex flex-col gap-1">
          {SECCIONES.map(({ a, texto, Icono }) => (
            <NavLink
              key={a}
              to={a}
              end={a === '/'}
              className={({ isActive }) =>
                `flex min-h-11 items-center gap-3 rounded-xl px-3 font-medium transition ${
                  isActive ? 'bg-primario-claro text-primario-oscuro' : 'text-texto-suave hover:bg-fondo'
                }`
              }
            >
              <Icono className="size-5" />
              {texto}
            </NavLink>
          ))}
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
        <p className="flex-1 font-bold">Brújula Urbana</p>
        <BotonTema />
        <button type="button" onClick={logout} className="boton px-2 text-texto-suave" aria-label="Cerrar sesión">
          <IconoSalir className="size-5" />
        </button>
      </header>

      {USA_MOCK && (
        <p className="bg-aviso-fondo px-4 py-1.5 text-center text-xs font-medium text-aviso">
          Modo demostración: se muestran datos de ejemplo, no rutas reales.
        </p>
      )}

      <main className="flex flex-1 flex-col pb-[calc(4rem+env(safe-area-inset-bottom))] md:pb-0">
        <Outlet />
      </main>

      {/* Navegación inferior: celular */}
      <nav
        aria-label="Principal"
        className="fixed inset-x-0 bottom-0 z-[1100] grid grid-cols-4 border-t border-borde bg-superficie pb-[env(safe-area-inset-bottom)] md:hidden"
      >
        {SECCIONES.map(({ a, texto, Icono }) => (
          <NavLink
            key={a}
            to={a}
            end={a === '/'}
            className={({ isActive }) =>
              `flex min-h-16 flex-col items-center justify-center gap-0.5 text-xs font-medium ${
                isActive ? 'text-primario' : 'text-texto-suave'
              }`
            }
          >
            <Icono className="size-6" />
            {texto}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
