import { Link, Outlet, useSearchParams } from 'react-router-dom'
import { USA_MOCK } from '../compartido/api/cliente.js'
import { IconoSalir } from '../compartido/componentes/Iconos.jsx'
import Logo from '../compartido/componentes/Logo.jsx'
import { BotonTema, SelectorTema } from '../compartido/componentes/SelectorTema.jsx'
import { useAuth } from '../modulos/cuenta'
import { SECCIONES, seccionDe } from '../modulos/dashboard'

const inicial = (texto = '') => texto.trim().charAt(0).toUpperCase() || '?'

export default function Layout() {
  const { usuario, logout } = useAuth()
  const [params] = useSearchParams()
  const activa = seccionDe(params.get('seccion')).id

  return (
    <div className="flex min-h-dvh flex-col md:pl-64">
      {/* Barra lateral: tablet y escritorio. Sus enlaces son las secciones del dashboard */}
      <aside className="fixed inset-y-0 left-0 z-[1100] hidden w-64 flex-col border-r border-borde bg-superficie md:flex">
        <div className="flex items-center gap-3 border-b border-borde px-5 py-5">
          <Logo className="size-11" alt="Logotipo de Kompás" />
          <div className="min-w-0">
            <p className="text-lg font-bold leading-tight tracking-tight">Kompás</p>
            <p className="text-xs font-medium text-texto-suave">Panel de administración</p>
          </div>
        </div>

        <nav aria-label="Secciones del dashboard" className="flex-1 overflow-y-auto px-3 py-4">
          <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-texto-suave">Dashboard</p>
          <ul className="space-y-0.5">
            {SECCIONES.map(({ id, texto, Icono }) => {
              const actual = id === activa
              return (
                <li key={id}>
                  <Link
                    to={id === 'resumen' ? '/' : `/?seccion=${id}`}
                    aria-current={actual ? 'page' : undefined}
                    className={`relative flex min-h-10 items-center gap-3 rounded-lg px-3 text-sm font-medium transition ${
                      actual ? 'bg-primario-claro text-primario-oscuro' : 'text-texto-suave hover:bg-fondo hover:text-texto'
                    }`}
                  >
                    {actual && <span aria-hidden="true" className="absolute inset-y-2 left-0 w-1 rounded-r-full bg-primario" />}
                    <Icono className="size-[18px]" />
                    {texto}
                  </Link>
                </li>
              )
            })}
          </ul>
        </nav>

        <div className="space-y-3 border-t border-borde p-4">
          <SelectorTema />
          <div className="flex items-center gap-3 rounded-xl bg-fondo p-2">
            <span aria-hidden="true" className="grid size-9 shrink-0 place-items-center rounded-full bg-primario font-semibold text-sobre-primario">
              {inicial(usuario?.nombre || usuario?.email)}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold">{usuario?.nombre || 'Administrador'}</p>
              <p className="truncate text-xs text-texto-suave">{usuario?.email}</p>
            </div>
            <button
              type="button"
              onClick={logout}
              className="grid size-9 shrink-0 place-items-center rounded-lg text-texto-suave transition hover:bg-superficie hover:text-peligro"
              aria-label="Cerrar sesión"
              title="Cerrar sesión"
            >
              <IconoSalir className="size-5" />
            </button>
          </div>
        </div>
      </aside>

      {/* Encabezado: celular */}
      <header className="sticky top-0 z-[1100] flex items-center gap-3 border-b border-borde bg-superficie/95 px-4 pb-2 pt-[max(0.5rem,env(safe-area-inset-top))] backdrop-blur md:hidden">
        <Logo className="size-9" alt="Logotipo de Kompás" />
        <div className="min-w-0 flex-1">
          <p className="font-bold leading-tight">Kompás</p>
          <p className="text-xs text-texto-suave">Panel de administración</p>
        </div>
        <BotonTema />
        <button type="button" onClick={logout} className="boton px-2 text-texto-suave" aria-label="Cerrar sesión">
          <IconoSalir className="size-5" />
        </button>
      </header>

      {USA_MOCK && (
        <p className="bg-aviso-fondo px-4 py-1.5 text-center text-xs font-medium text-texto">
          Modo demostración: se muestran datos de ejemplo, sin conexión a la API.
        </p>
      )}

      <main className="flex flex-1 flex-col">
        <Outlet />
      </main>
    </div>
  )
}
