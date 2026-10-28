import { useState, type FormEvent } from 'react'
import { MensajeError } from '../../../compartido/componentes/Avisos.tsx'
import Chip from '../../../compartido/componentes/Chip.tsx'
import { IconoAtras, IconoBorrar, IconoIntercambiar } from '../../../compartido/componentes/Iconos.tsx'
import Mapa, { type LineaMapa, type MarcadorMapa } from '../../../compartido/componentes/Mapa.tsx'
import { estaDentroDeZona, ZONA } from '../../../compartido/config/zona.ts'
import type { Coordenada, Parada, ParGeoJSON } from '../../../compartido/tipos/dominio.ts'
import { aLeaflet, distanciaKm } from '../../../compartido/utils/geo.ts'
import * as api from '../api.ts'
import useAccion from '../hooks/useAccion.ts'
import type { RutaAdmin } from '../tipos.ts'
import { BotonIcono } from './Comun.tsx'

type Modo = 'trazo' | 'paradas'

const longitudKm = (trazo: ParGeoJSON[]) =>
  trazo.slice(1).reduce((km, [lng, lat], i) => km + distanciaKm({ lat: trazo[i][1], lng: trazo[i][0] }, { lat, lng }), 0)

type Props = {
  /** null = ruta nueva */
  ruta: RutaAdmin | null
  /** Las demás rutas se dibujan tenues como referencia */
  otras: RutaAdmin[]
  onCerrar: (guardada: boolean) => void
}

/** Alta y edición de una ruta: el trazo se dibuja haciendo clic en el mapa en el sentido en que circula. */
export default function EditorRuta({ ruta, otras, onCerrar }: Props) {
  const [nombre, setNombre] = useState(ruta?.nombre ?? '')
  const [trazo, setTrazo] = useState<ParGeoJSON[]>(ruta?.trazo ?? [])
  const [paradas, setParadas] = useState<Parada[]>(ruta?.paradas ?? [])
  const [modo, setModo] = useState<Modo>('trazo')
  // Se encuadra solo al abrir: si siguiera al trazo, el mapa saltaría con cada clic
  const [enfocar] = useState(() => (ruta?.trazo ?? []).map(aLeaflet))
  const { ocupado, error, setError, ejecutar } = useAccion()

  function alHacerClic({ lat, lng }: Coordenada) {
    if (!estaDentroDeZona(lat, lng)) {
      setError(`Ese punto está fuera de la zona piloto (${ZONA.nombre}).`)
      return
    }
    setError('')
    if (modo === 'trazo') setTrazo((t) => [...t, [lng, lat]])
    else setParadas((p) => [...p, { nombre: `Parada ${p.length + 1}`, ubicacion: { type: 'Point', coordinates: [lng, lat] } }])
  }

  async function guardar(e: FormEvent) {
    e.preventDefault()
    if (!nombre.trim()) return setError('Escribe el nombre de la ruta.')
    if (trazo.length < 2) return setError('Dibuja el trazo: haz clic en el mapa al menos en dos puntos.')
    if (paradas.some((p) => !p.nombre.trim())) return setError('Cada parada necesita un nombre.')
    const guardada = await ejecutar(() => api.guardarRuta({ nombre: nombre.trim(), trazo, paradas }, ruta?.id))
    if (guardada) onCerrar(true)
  }

  const renombrar = (i: number, texto: string) => setParadas((p) => p.map((x, j) => (j === i ? { ...x, nombre: texto } : x)))

  const marcadores: MarcadorMapa[] = [
    ...trazo.map(([lng, lat], i): MarcadorMapa => {
      const extremo = i === 0 ? 'origen' : i === trazo.length - 1 ? 'destino' : null
      return { id: `v${i}`, lat, lng, tipo: extremo ?? 'intermedia', titulo: extremo === 'origen' ? 'Inicio del trazo' : extremo ? 'Fin del trazo' : `Punto ${i + 1}` }
    }),
    ...paradas.map(({ nombre: n, ubicacion: { coordinates: [lng, lat] } }, i): MarcadorMapa => ({ id: `p${i}`, lat, lng, tipo: 'parada', texto: String(i + 1), titulo: n })),
  ]
  const lineas: LineaMapa[] = otras.filter((o) => o.id !== ruta?.id).map((o) => ({ id: `otra-${o.id}`, puntos: o.trazo.map(aLeaflet), estilo: 'trazo-tenue' }))

  return (
    <form onSubmit={guardar} className="grid gap-4 lg:grid-cols-[minmax(0,22rem)_minmax(0,1fr)] [&>*]:min-w-0">
      <div className="tarjeta grid content-start gap-4">
        <div className="flex items-center gap-2">
          <BotonIcono Icono={IconoAtras} etiqueta="Volver a la lista de rutas" onClick={() => onCerrar(false)} />
          <h2 className="text-lg font-bold">{ruta ? 'Editar ruta' : 'Nueva ruta'}</h2>
        </div>

        <label>
          <span className="etiqueta">Nombre de la línea</span>
          <input className="campo" value={nombre} onChange={(e) => setNombre(e.target.value)} maxLength={120} placeholder="Ej. Lerma – Toluca por Tollocan" required />
        </label>

        <fieldset className="grid gap-2">
          <legend className="etiqueta">Al hacer clic en el mapa…</legend>
          <div className="flex flex-wrap gap-2">
            <Chip activo={modo === 'trazo'} onClick={() => setModo('trazo')}>
              Dibujo el trazo
            </Chip>
            <Chip activo={modo === 'paradas'} onClick={() => setModo('paradas')}>
              Agrego paradas
            </Chip>
          </div>
          <p className="text-xs text-texto-suave">
            {modo === 'trazo'
              ? 'Marca las calles por donde pasa la ruta, en el sentido en que circula. La app solo sugiere subir antes de bajar en ese sentido.'
              : 'Marca dónde se sube y se baja la gente. Si no agregas paradas, la app usa los puntos del trazo y avisa que no son paradas reales.'}
          </p>
        </fieldset>

        <div className="grid gap-2">
          <p className="text-sm">
            <strong>{trazo.length}</strong> puntos en el trazo · <strong>{longitudKm(trazo).toFixed(1)} km</strong> en línea recta entre puntos
          </p>
          <div className="flex flex-wrap gap-2">
            <button type="button" className="boton-secundario px-3 text-sm" disabled={!trazo.length} onClick={() => setTrazo((t) => t.slice(0, -1))}>
              Deshacer último punto
            </button>
            <button type="button" className="boton-secundario px-3 text-sm" disabled={trazo.length < 2} onClick={() => setTrazo((t) => [...t].reverse())}>
              <IconoIntercambiar className="size-4" />
              Invertir sentido
            </button>
            <button type="button" className="boton-secundario px-3 text-sm text-peligro" disabled={!trazo.length} onClick={() => setTrazo([])}>
              Borrar trazo
            </button>
          </div>
        </div>

        <div className="grid gap-2">
          <p className="etiqueta mb-0">Paradas ({paradas.length})</p>
          {paradas.length === 0 ? (
            <p className="text-sm text-texto-suave">Sin paradas. Elige “Agrego paradas” y haz clic en el mapa.</p>
          ) : (
            <ol className="grid max-h-64 gap-2 overflow-y-auto pr-1">
              {paradas.map((p, i) => (
                <li key={i} className="flex items-center gap-2">
                  <span aria-hidden="true" className="grid size-6 shrink-0 place-items-center rounded-full bg-primario text-xs font-bold text-sobre-primario">
                    {i + 1}
                  </span>
                  <input className="campo min-h-9 py-1 text-sm" value={p.nombre} onChange={(e) => renombrar(i, e.target.value)} maxLength={120} aria-label={`Nombre de la parada ${i + 1}`} />
                  <BotonIcono Icono={IconoBorrar} etiqueta={`Quitar ${p.nombre}`} peligro onClick={() => setParadas((ps) => ps.filter((_, j) => j !== i))} />
                </li>
              ))}
            </ol>
          )}
        </div>

        <MensajeError>{error}</MensajeError>
        <div className="flex flex-wrap gap-2">
          <button type="submit" className="boton-primario flex-1" disabled={ocupado}>
            {ocupado ? 'Guardando…' : ruta ? 'Guardar cambios' : 'Crear ruta'}
          </button>
          <button type="button" className="boton-secundario" onClick={() => onCerrar(false)}>
            Cancelar
          </button>
        </div>
      </div>

      <div className="grid content-start gap-2">
        <Mapa className="h-[60vh] min-h-96" trazo={trazo.map(aLeaflet)} lineas={lineas} marcadores={marcadores} onSeleccionar={alHacerClic} enfocar={enfocar} />
        <p className="text-xs text-texto-suave">
          {modo === 'trazo' ? 'Clic: agrega un punto al final del trazo.' : 'Clic: agrega una parada.'} Las otras rutas se ven tenues como referencia.
        </p>
      </div>
    </form>
  )
}
