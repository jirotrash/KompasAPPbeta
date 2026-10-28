import { useMemo, useState, type FormEvent } from 'react'
import { Cargando, MensajeError } from '../../../compartido/componentes/Avisos.tsx'
import type { PuntoElegido } from '../../../compartido/componentes/BuscadorLugar.tsx'
import { IconoAgregar, IconoBorrar, IconoEditar } from '../../../compartido/componentes/Iconos.tsx'
import Mapa, { type MarcadorMapa } from '../../../compartido/componentes/Mapa.tsx'
import SelectorPunto from '../../../compartido/componentes/SelectorPunto.tsx'
import { normalizarTexto } from '../../../compartido/utils/dominio.ts'
import * as api from '../api.ts'
import { confirmar } from '../formato.ts'
import useAccion from '../hooks/useAccion.ts'
import useCarga from '../hooks/useCarga.ts'
import type { LugarAdmin } from '../tipos.ts'
import { BotonIcono, Insignia, Vacio } from './Comun.tsx'

type Formulario = { id?: number; nombre: string; idCategoria: string; punto: PuntoElegido | null }

const VACIO: Formulario = { nombre: '', idCategoria: '', punto: null }

const aFormulario = (l: LugarAdmin): Formulario => ({
  id: l.id,
  nombre: l.nombre,
  idCategoria: l.id_categoria ? String(l.id_categoria) : '',
  punto: { id: l._id, nombre: l.nombre, lat: l.lat, lng: l.lng },
})

export default function PanelLugares() {
  const { datos: lugares, cargando, error, recargar } = useCarga(api.obtenerLugares)
  const { datos: categorias } = useCarga(api.obtenerCategorias)
  const [form, setForm] = useState<Formulario | null>(null)
  const [filtro, setFiltro] = useState('')
  const accion = useAccion()

  const visibles = useMemo(() => {
    const buscado = normalizarTexto(filtro)
    return (lugares ?? []).filter((l) => !buscado || normalizarTexto(`${l.nombre} ${l.categoria ?? ''}`).includes(buscado))
  }, [lugares, filtro])

  async function guardar(e: FormEvent) {
    e.preventDefault()
    if (!form) return
    if (!form.nombre.trim()) return accion.setError('Escribe el nombre del lugar.')
    if (!form.idCategoria) return accion.setError('Elige la categoría.')
    if (!form.punto) return accion.setError('Marca dónde está: búscalo o elígelo en el mapa.')
    const { lat, lng } = form.punto
    const datos = { nombre: form.nombre.trim(), id_categoria: Number(form.idCategoria), ubicacion: { type: 'Point' as const, coordinates: [lng, lat] as [number, number] } }
    if (await accion.ejecutar(() => api.guardarLugar(datos, form.id))) {
      setForm(null)
      recargar()
    }
  }

  async function borrar(l: LugarAdmin) {
    if (!confirmar(`¿Borrar «${l.nombre}»? Deja de aparecer en la app y en el dashboard.`)) return
    if ((await accion.ejecutar(() => api.borrarLugar(l.id))) !== undefined) {
      if (form?.id === l.id) setForm(null)
      recargar()
    }
  }

  const marcadores: MarcadorMapa[] = visibles
    .filter((l) => l.id !== form?.id)
    .map((l) => ({ id: `l${l.id}`, lat: l.lat, lng: l.lng, tipo: 'lugar', titulo: `${l.nombre} · editar`, onClic: () => setForm(aFormulario(l)) }))
  if (form?.punto) marcadores.push({ id: 'form', lat: form.punto.lat, lng: form.punto.lng, tipo: 'seleccion', titulo: form.nombre || 'Lugar nuevo' })

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,26rem)_minmax(0,1fr)] [&>*]:min-w-0">
      <div className="grid content-start gap-4">
        {form ? (
          <form onSubmit={guardar} className="tarjeta grid gap-3" aria-labelledby="titulo-form-lugar">
            <h2 id="titulo-form-lugar" className="text-lg font-bold">
              {form.id ? 'Editar lugar' : 'Nuevo lugar'}
            </h2>
            <label>
              <span className="etiqueta">Nombre</span>
              <input className="campo" value={form.nombre} maxLength={120} required onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
            </label>
            <label>
              <span className="etiqueta">Categoría</span>
              <select className="campo" value={form.idCategoria} required onChange={(e) => setForm({ ...form, idCategoria: e.target.value })}>
                <option value="">Elige una categoría</option>
                {(categorias ?? []).map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nombre}
                  </option>
                ))}
              </select>
            </label>
            <SelectorPunto etiqueta="Ubicación" valor={form.punto} onCambiar={(punto) => setForm({ ...form, punto })} />
            <MensajeError>{accion.error}</MensajeError>
            <div className="flex flex-wrap gap-2">
              <button type="submit" className="boton-primario flex-1" disabled={accion.ocupado}>
                {accion.ocupado ? 'Guardando…' : form.id ? 'Guardar cambios' : 'Crear lugar'}
              </button>
              <button type="button" className="boton-secundario" onClick={() => setForm(null)}>
                Cancelar
              </button>
            </div>
          </form>
        ) : (
          <button type="button" className="boton-primario justify-self-start" onClick={() => setForm(VACIO)}>
            <IconoAgregar className="size-4" />
            Nuevo lugar
          </button>
        )}

        <section className="tarjeta grid gap-3" aria-labelledby="titulo-lugares">
          <h2 id="titulo-lugares" className="text-lg font-bold">
            Lugares {lugares && <span className="text-texto-suave">({lugares.length})</span>}
          </h2>
          <input className="campo" type="search" placeholder="Buscar por nombre o categoría" value={filtro} onChange={(e) => setFiltro(e.target.value)} aria-label="Buscar lugares" />
          {!form && <MensajeError>{error || accion.error}</MensajeError>}
          {cargando && !lugares ? (
            <Cargando texto="Cargando lugares…" />
          ) : visibles.length === 0 ? (
            <Vacio>{filtro ? 'Ningún lugar coincide con la búsqueda.' : 'Todavía no hay lugares.'}</Vacio>
          ) : (
            <ul className="grid max-h-[50vh] gap-1 overflow-y-auto pr-1">
              {visibles.map((l) => (
                <li key={l.id} className={`flex items-center gap-2 rounded-xl px-2 py-1.5 ${form?.id === l.id ? 'bg-primario-claro' : 'hover:bg-fondo'}`}>
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-semibold">{l.nombre}</p>
                    <p className="flex items-center gap-1.5 text-xs text-texto-suave">
                      {l.categoria ?? 'Sin categoría'}
                      {!l.interes && <Insignia tono="aviso">no es interés de la app</Insignia>}
                    </p>
                  </div>
                  <BotonIcono Icono={IconoEditar} etiqueta={`Editar ${l.nombre}`} onClick={() => setForm(aFormulario(l))} />
                  <BotonIcono Icono={IconoBorrar} etiqueta={`Borrar ${l.nombre}`} peligro disabled={accion.ocupado} onClick={() => borrar(l)} />
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <div className="grid content-start gap-2">
        <Mapa className="h-[60vh] min-h-96" marcadores={marcadores} />
        <p className="text-xs text-texto-suave">Toca un lugar del mapa para editarlo.</p>
      </div>
    </div>
  )
}
