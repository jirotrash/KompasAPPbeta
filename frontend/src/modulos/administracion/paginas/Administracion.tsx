import { useRef, type ComponentType, type KeyboardEvent } from 'react'
import { useSearchParams } from 'react-router-dom'
import PanelBusquedas from '../componentes/PanelBusquedas.tsx'
import PanelCatalogos from '../componentes/PanelCatalogos.tsx'
import PanelLugares from '../componentes/PanelLugares.tsx'
import PanelReportes from '../componentes/PanelReportes.tsx'
import PanelRutas from '../componentes/PanelRutas.tsx'
import PanelSolicitudes from '../componentes/PanelSolicitudes.tsx'
import { SECCIONES_ADMIN, seccionAdminDe, type IdSeccionAdmin } from '../secciones.ts'

const CONTENIDO: Record<IdSeccionAdmin, ComponentType> = {
  rutas: PanelRutas,
  lugares: PanelLugares,
  catalogos: PanelCatalogos,
  reportes: PanelReportes,
  busquedas: PanelBusquedas,
  solicitudes: PanelSolicitudes,
}

/** Altas, cambios y bajas de lo que usa la app, y lo que piden los usuarios. Solo rol admin (la API responde 403). */
export default function Administracion() {
  const [params, setParams] = useSearchParams()
  const seccion = seccionAdminDe(params.get('seccion'))
  const botones = useRef<Partial<Record<IdSeccionAdmin, HTMLButtonElement | null>>>({})
  const Contenido = CONTENIDO[seccion.id]

  const irA = (id: IdSeccionAdmin) => setParams({ seccion: id })

  function moverConTeclado(e: KeyboardEvent<HTMLButtonElement>, indice: number) {
    const teclas: Record<string, number> = { ArrowRight: indice + 1, ArrowLeft: indice - 1, Home: 0, End: SECCIONES_ADMIN.length - 1 }
    const siguiente = teclas[e.key]
    if (siguiente === undefined) return
    e.preventDefault()
    const destino = SECCIONES_ADMIN[(siguiente + SECCIONES_ADMIN.length) % SECCIONES_ADMIN.length].id
    irA(destino)
    botones.current[destino]?.focus()
  }

  return (
    <div className="mx-auto grid w-full max-w-screen-2xl gap-5 px-4 py-5 sm:px-6 md:py-8 lg:px-8">
      <header className="min-w-0">
        <p className="text-xs font-semibold uppercase tracking-wider text-primario">Administración</p>
        <h1 className="mt-1 flex items-center gap-3 text-2xl font-bold tracking-tight md:text-3xl">
          <seccion.Icono className="size-7 text-primario" />
          {seccion.texto}
        </h1>
        <p className="mt-1 max-w-3xl text-texto-suave">{seccion.descripcion}</p>
      </header>

      {/* En escritorio las secciones están en la barra lateral; en celular, aquí como pestañas */}
      <div role="tablist" aria-label="Secciones de administración" className="-mx-1 flex gap-1 overflow-x-auto border-b border-borde px-1 md:hidden">
        {SECCIONES_ADMIN.map((s, i) => (
          <button
            key={s.id}
            ref={(el) => {
              botones.current[s.id] = el
            }}
            type="button"
            role="tab"
            aria-selected={seccion.id === s.id}
            aria-controls="panel-administracion"
            tabIndex={seccion.id === s.id ? 0 : -1}
            onClick={() => irA(s.id)}
            onKeyDown={(e) => moverConTeclado(e, i)}
            className={`min-h-11 shrink-0 border-b-2 px-3 text-sm font-semibold transition ${
              seccion.id === s.id ? 'border-primario text-primario' : 'border-transparent text-texto-suave hover:text-texto'
            }`}
          >
            {s.texto}
          </button>
        ))}
      </div>

      <div id="panel-administracion" role="region" aria-label={seccion.texto}>
        <Contenido key={seccion.id} />
      </div>
    </div>
  )
}
