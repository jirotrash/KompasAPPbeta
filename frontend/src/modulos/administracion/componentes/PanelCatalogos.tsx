import { useState, type FormEvent } from 'react'
import { Cargando, MensajeError } from '../../../compartido/componentes/Avisos.tsx'
import { IconoAgregar, IconoBorrar, IconoEditar } from '../../../compartido/componentes/Iconos.tsx'
import * as api from '../api.ts'
import { confirmar } from '../formato.ts'
import useAccion from '../hooks/useAccion.ts'
import useCarga from '../hooks/useCarga.ts'
import { BotonIcono, Insignia, Vacio } from './Comun.tsx'

type Item = { id: number; nombre: string; clave: string; protegida: boolean; descripcion?: string | null }
type Formulario = { id?: number; nombre: string; descripcion: string }

type Props<T extends Item> = {
  titulo: string
  singular: string
  conDescripcion?: boolean
  cargar: () => Promise<T[]>
  guardar: (datos: { nombre: string; descripcion: string | null }, id?: number) => Promise<T>
  borrar: (id: number) => Promise<unknown>
}

/** Lista editable de un catálogo. Los protegidos se pueden editar (acentos, descripción) pero no borrar. */
function Catalogo<T extends Item>({ titulo, singular, conDescripcion, cargar, guardar, borrar }: Props<T>) {
  const { datos, cargando, error, recargar } = useCarga(cargar)
  const [form, setForm] = useState<Formulario | null>(null)
  const accion = useAccion()

  async function enviar(e: FormEvent) {
    e.preventDefault()
    if (!form) return
    if (await accion.ejecutar(() => guardar({ nombre: form.nombre, descripcion: form.descripcion.trim() || null }, form.id))) {
      setForm(null)
      recargar()
    }
  }

  async function quitar(item: T) {
    if (!confirmar(`¿Borrar «${item.nombre}»?`)) return
    if ((await accion.ejecutar(() => borrar(item.id))) !== undefined) recargar()
  }

  const formulario = form && (
    <form onSubmit={enviar} className="grid gap-2 rounded-xl border border-primario/40 bg-primario-claro/40 p-3">
      <label>
        <span className="etiqueta">Nombre</span>
        <input className="campo" value={form.nombre} maxLength={60} required autoFocus onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
      </label>
      {conDescripcion && (
        <label>
          <span className="etiqueta">Descripción (opcional)</span>
          <textarea className="campo" rows={2} maxLength={300} value={form.descripcion} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} />
        </label>
      )}
      <MensajeError>{accion.error}</MensajeError>
      <div className="flex gap-2">
        <button type="submit" className="boton-primario flex-1 text-sm" disabled={accion.ocupado}>
          {accion.ocupado ? 'Guardando…' : 'Guardar'}
        </button>
        <button type="button" className="boton-secundario text-sm" onClick={() => setForm(null)}>
          Cancelar
        </button>
      </div>
    </form>
  )

  return (
    <section className="tarjeta grid content-start gap-3" aria-label={titulo}>
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-lg font-bold">{titulo}</h2>
        <button type="button" className="boton-secundario px-3 text-sm" onClick={() => setForm({ nombre: '', descripcion: '' })}>
          <IconoAgregar className="size-4" />
          Agregar {singular}
        </button>
      </div>
      {form && !form.id && formulario}
      {!form && <MensajeError>{error || accion.error}</MensajeError>}
      {cargando && !datos ? (
        <Cargando />
      ) : !datos?.length ? (
        <Vacio>Sin registros.</Vacio>
      ) : (
        <ul className="grid gap-1">
          {datos.map((item) =>
            form?.id === item.id ? (
              <li key={item.id}>{formulario}</li>
            ) : (
              <li key={item.id} className="flex items-center gap-2 rounded-xl px-2 py-1.5 hover:bg-fondo">
                <div className="min-w-0 flex-1">
                  <p className="flex flex-wrap items-center gap-1.5 font-semibold">
                    {item.nombre}
                    {item.protegida && <Insignia tono="primario">protegida</Insignia>}
                  </p>
                  <p className="text-xs text-texto-suave">
                    Clave en la app: <code>{item.clave}</code>
                    {item.descripcion ? ` · ${item.descripcion}` : ''}
                  </p>
                </div>
                <BotonIcono Icono={IconoEditar} etiqueta={`Editar ${item.nombre}`} onClick={() => setForm({ id: item.id, nombre: item.nombre, descripcion: item.descripcion ?? '' })} />
                <BotonIcono
                  Icono={IconoBorrar}
                  etiqueta={item.protegida ? `${item.nombre} está protegida: la usa el sistema experto` : `Borrar ${item.nombre}`}
                  peligro
                  disabled={item.protegida || accion.ocupado}
                  onClick={() => quitar(item)}
                />
              </li>
            ),
          )}
        </ul>
      )}
    </section>
  )
}

export default function PanelCatalogos() {
  return (
    <div className="grid gap-4 lg:grid-cols-2 [&>*]:min-w-0">
      <Catalogo
        titulo="Categorías de lugares"
        singular="categoría"
        conDescripcion
        cargar={api.obtenerCategorias}
        guardar={api.guardarCategoria}
        borrar={api.borrarCategoria}
      />
      <Catalogo
        titulo="Medios de transporte"
        singular="transporte"
        cargar={api.obtenerTransportes}
        guardar={({ nombre }, id) => api.guardarTransporte({ nombre }, id)}
        borrar={api.borrarTransporte}
      />
      <p className="text-sm text-texto-suave lg:col-span-2">
        La <strong className="text-texto">clave</strong> es el valor que mandan la app y el planificador (por ejemplo <code>cafe</code> o <code>taxi_app</code>). Las protegidas son
        las que conocen el formulario de la app y las reglas R01–R20; las nuevas se pueden usar para clasificar lugares, pero la app no las ofrece como interés.
      </p>
    </div>
  )
}
