import { useState } from 'react'
import { Cargando, MensajeError } from '../../../compartido/componentes/Avisos.tsx'
import { IconoAgregar, IconoBorrar, IconoEditar } from '../../../compartido/componentes/Iconos.tsx'
import Mapa, { type LineaMapa, type MarcadorMapa } from '../../../compartido/componentes/Mapa.tsx'
import { aLeaflet } from '../../../compartido/utils/geo.ts'
import * as api from '../api.ts'
import { confirmar } from '../formato.ts'
import useAccion from '../hooks/useAccion.ts'
import useCarga from '../hooks/useCarga.ts'
import type { RutaAdmin } from '../tipos.ts'
import { BotonIcono, Insignia, Vacio } from './Comun.tsx'
import EditorRuta from './EditorRuta.tsx'

const nombreDe = (r: RutaAdmin) => r.nombre || `Ruta ${r.id}`

export default function PanelRutas() {
  const { datos: rutas, cargando, error, recargar } = useCarga(api.obtenerRutas)
  const [editando, setEditando] = useState<RutaAdmin | 'nueva' | null>(null)
  const [elegida, setElegida] = useState<number | null>(null)
  const accion = useAccion()

  if (editando) {
    return (
      <EditorRuta
        ruta={editando === 'nueva' ? null : editando}
        otras={rutas ?? []}
        onCerrar={(guardada) => {
          setEditando(null)
          if (guardada) recargar()
        }}
      />
    )
  }

  async function borrar(r: RutaAdmin) {
    if (!confirmar(`¿Borrar «${nombreDe(r)}»? La app dejará de sugerirla. El historial que la usa se conserva.`)) return
    if ((await accion.ejecutar(() => api.borrarRuta(r.id))) !== undefined) {
      if (elegida === r.id) setElegida(null)
      recargar()
    }
  }

  const lista = rutas ?? []
  const actual = lista.find((r) => r.id === elegida)
  const lineas: LineaMapa[] = lista.filter((r) => r.id !== elegida).map((r) => ({ id: `r${r.id}`, puntos: r.trazo.map(aLeaflet), estilo: 'trazo-tenue' }))
  const marcadores: MarcadorMapa[] = (actual?.paradas ?? []).map((p, i) => ({
    id: `p${i}`,
    lat: p.ubicacion.coordinates[1],
    lng: p.ubicacion.coordinates[0],
    tipo: 'parada',
    texto: String(i + 1),
    titulo: p.nombre,
  }))

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,24rem)_minmax(0,1fr)] [&>*]:min-w-0">
      <section className="tarjeta grid content-start gap-3" aria-labelledby="titulo-rutas">
        <div className="flex items-center justify-between gap-2">
          <h2 id="titulo-rutas" className="text-lg font-bold">
            Rutas {rutas && <span className="text-texto-suave">({lista.length})</span>}
          </h2>
          <button type="button" className="boton-primario px-3 text-sm" onClick={() => setEditando('nueva')}>
            <IconoAgregar className="size-4" />
            Nueva ruta
          </button>
        </div>
        <MensajeError>{error || accion.error}</MensajeError>
        {cargando && !rutas ? (
          <Cargando texto="Cargando rutas…" />
        ) : lista.length === 0 ? (
          <Vacio>Todavía no hay rutas. Con “Nueva ruta” dibujas la primera en el mapa.</Vacio>
        ) : (
          <ul className="grid gap-1">
            {lista.map((r) => (
              <li key={r.id} className={`flex items-center gap-2 rounded-xl px-2 py-1.5 ${elegida === r.id ? 'bg-primario-claro' : 'hover:bg-fondo'}`}>
                <button type="button" className="min-w-0 flex-1 text-left" aria-pressed={elegida === r.id} onClick={() => setElegida(elegida === r.id ? null : r.id)}>
                  <span className="block truncate font-semibold">{nombreDe(r)}</span>
                  <span className="flex flex-wrap items-center gap-1.5 text-xs text-texto-suave">
                    {r.trazo.length} puntos
                    {r.paradas?.length ? <Insignia tono="ok">{r.paradas.length} paradas</Insignia> : <Insignia tono="aviso">sin paradas reales</Insignia>}
                  </span>
                </button>
                <BotonIcono Icono={IconoEditar} etiqueta={`Editar ${nombreDe(r)}`} onClick={() => setEditando(r)} />
                <BotonIcono Icono={IconoBorrar} etiqueta={`Borrar ${nombreDe(r)}`} peligro disabled={accion.ocupado} onClick={() => borrar(r)} />
              </li>
            ))}
          </ul>
        )}
      </section>

      <div className="grid content-start gap-2">
        <Mapa className="h-[60vh] min-h-96" trazo={actual?.trazo.map(aLeaflet)} lineas={lineas} marcadores={marcadores} />
        <p className="text-xs text-texto-suave">{actual ? `Resaltada: ${nombreDe(actual)}.` : 'Elige una ruta de la lista para resaltarla en el mapa.'}</p>
      </div>
    </div>
  )
}
