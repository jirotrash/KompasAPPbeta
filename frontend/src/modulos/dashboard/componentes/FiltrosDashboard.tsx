import { useState } from 'react'
import Chip from '../../../compartido/componentes/Chip.tsx'
import type { Rango, Seleccion } from '../filtros.ts'
import type { Agrupar } from '../tipos.ts'

const RANGOS: { id: Rango; texto: string }[] = [
  { id: '7', texto: '7 días' },
  { id: '30', texto: '30 días' },
  { id: '90', texto: '90 días' },
  { id: 'todo', texto: 'Todo' },
  { id: 'personalizado', texto: 'Personalizado' },
]

/** Filtros en una sola fila arriba de las gráficas. Se aplican al pulsar Actualizar. */
type Props = { inicial: Seleccion; onAplicar: (s: Seleccion) => void; cargando: boolean }

export default function FiltrosDashboard({ inicial, onAplicar, cargando }: Props) {
  const [seleccion, setSeleccion] = useState(inicial)
  const cambiar = (cambios: Partial<Seleccion>) => setSeleccion((s) => ({ ...s, ...cambios }))
  const invalido = seleccion.rango === 'personalizado' && (!seleccion.desde || !seleccion.hasta || seleccion.desde > seleccion.hasta)

  return (
    <form
      className="tarjeta flex flex-wrap items-end gap-3"
      onSubmit={(e) => {
        e.preventDefault()
        if (!invalido) onAplicar(seleccion)
      }}
    >
      <fieldset className="min-w-0">
        <legend className="etiqueta">Periodo</legend>
        <div className="flex flex-wrap gap-2">
          {RANGOS.map((r) => (
            <Chip
              key={r.id}
              activo={seleccion.rango === r.id}
              onClick={() => cambiar({ rango: r.id, ...(r.id === 'todo' ? { agrupar: 'mes' } : {}) })}
            >
              {r.texto}
            </Chip>
          ))}
        </div>
      </fieldset>

      {seleccion.rango === 'personalizado' && (
        <>
          <label className="w-40">
            <span className="etiqueta">Desde</span>
            <input type="date" className="campo" value={seleccion.desde} max={seleccion.hasta} onChange={(e) => cambiar({ desde: e.target.value })} />
          </label>
          <label className="w-40">
            <span className="etiqueta">Hasta</span>
            <input type="date" className="campo" value={seleccion.hasta} min={seleccion.desde} onChange={(e) => cambiar({ hasta: e.target.value })} />
          </label>
        </>
      )}

      <label className="w-36">
        <span className="etiqueta">Agrupar por</span>
        <select className="campo" value={seleccion.agrupar} onChange={(e) => cambiar({ agrupar: e.target.value as Agrupar })}>
          <option value="dia">Día</option>
          <option value="semana">Semana</option>
          <option value="mes">Mes</option>
        </select>
      </label>

      <label className="flex min-h-11 cursor-pointer items-center gap-2 text-sm font-medium">
        <input
          type="checkbox"
          className="size-5 accent-[var(--color-primario)]"
          checked={seleccion.incluirDemo}
          onChange={(e) => cambiar({ incluirDemo: e.target.checked })}
        />
        Incluir datos demo
      </label>

      <button type="submit" className="boton-primario ml-auto" disabled={cargando || invalido}>
        {cargando ? 'Cargando…' : 'Actualizar'}
      </button>
    </form>
  )
}
