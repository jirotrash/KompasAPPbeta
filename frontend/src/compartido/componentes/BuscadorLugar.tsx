import { useEffect, useId, useRef, useState, type FocusEvent, type KeyboardEvent, type ReactNode } from 'react'
import { estaDentroDeZona, PUNTOS_REFERENCIA, ZONA } from '../config/zona.ts'
import { buscarDirecciones } from '../api/mapas.ts'
import type { Coordenada, Direccion, Lugar } from '../tipos/dominio.ts'
import { nombreCategoria, normalizarTexto } from '../utils/dominio.ts'
import { obtenerUbicacion } from '../utils/geo.ts'
import { MensajeError } from './Avisos.tsx'
import { IconoBuscar, IconoCerrar, IconoItinerario, IconoUbicacion } from './Iconos.tsx'

const MIN_LETRAS = 3
const ESPERA_MS = 350

/** Lo que entrega el buscador al elegir: un punto con nombre. */
export type PuntoElegido = Coordenada & { id: string; nombre: string }

type Opcion = Partial<Coordenada> & { id: string; nombre: string; detalle?: string; gps?: boolean; propio?: boolean }

/** Punto de referencia o lugar de la BD → opción del buscador */
const desdeLugar = (l: Lugar): Opcion & Coordenada => ({
  id: l._id,
  nombre: l.nombre,
  detalle: [nombreCategoria(l.categoria), l.municipio].filter(Boolean).join(' · '),
  lat: l.ubicacion.coordinates[1],
  lng: l.ubicacion.coordinates[0],
})

type Props = {
  etiqueta: string
  placeholder?: string
  valor: PuntoElegido | null
  onElegir: (punto: PuntoElegido | null) => void
  lugares?: Lugar[]
  incluirMiUbicacion?: boolean
  icono?: ReactNode
  ocultarEtiqueta?: boolean
  onFocus?: (e: FocusEvent<HTMLInputElement>) => void
  grande?: boolean
}

/** Caja de búsqueda con sugerencias mientras se escribe (lugares propios + direcciones de OpenStreetMap). */
export default function BuscadorLugar({
  etiqueta,
  placeholder = 'Busca un lugar o dirección',
  valor,
  onElegir,
  lugares = [],
  incluirMiUbicacion = true,
  icono,
  ocultarEtiqueta = false,
  onFocus,
  grande = false,
}: Props) {
  const id = useId()
  const inputRef = useRef<HTMLInputElement>(null)
  const [editando, setEditando] = useState(false)
  const [texto, setTexto] = useState('')
  const [activo, setActivo] = useState(-1)
  const [remoto, setRemoto] = useState<{ consulta: string; lista: Direccion[]; error: boolean }>({ consulta: '', lista: [], error: false })
  const [ubicando, setUbicando] = useState(false)
  const [error, setError] = useState('')

  const consulta = texto.trim()
  const buscaRemoto = editando && consulta.length >= MIN_LETRAS

  // Búsqueda en OpenStreetMap con espera entre teclas y cancelación de la petición anterior
  useEffect(() => {
    if (!buscaRemoto) return
    const control = new AbortController()
    const temporizador = setTimeout(() => {
      buscarDirecciones(consulta, { signal: control.signal })
        .then((lista) => setRemoto({ consulta, lista, error: false }))
        .catch((e: unknown) => !(e instanceof DOMException && e.name === 'AbortError') && setRemoto({ consulta, lista: [], error: true }))
    }, ESPERA_MS)
    return () => {
      clearTimeout(temporizador)
      control.abort()
    }
  }, [consulta, buscaRemoto])

  const n = normalizarTexto(consulta)
  const propios: Opcion[] = [...PUNTOS_REFERENCIA.map((p) => ({ ...p, detalle: 'Punto de referencia' })), ...lugares.map(desdeLugar)]
    .filter((o) => !n || normalizarTexto(o.nombre).includes(n))
    .slice(0, n ? 5 : 4)
  const remotos = remoto.consulta === consulta && buscaRemoto ? remoto.lista : []
  const cargando = buscaRemoto && remoto.consulta !== consulta

  const opciones: Opcion[] = [
    ...(incluirMiUbicacion && !n ? [{ id: '__gps', nombre: 'Mi ubicación', detalle: 'Usar el GPS del dispositivo', gps: true }] : []),
    ...propios.map((o) => ({ ...o, propio: true })),
    ...remotos.filter((r) => !propios.some((p) => normalizarTexto(p.nombre) === normalizarTexto(r.nombre))),
  ]
  const abierto = editando && (opciones.length > 0 || buscaRemoto)

  async function elegir(opcion: Opcion) {
    setError('')
    if (opcion.gps) {
      setUbicando(true)
      try {
        const p = await obtenerUbicacion()
        if (!estaDentroDeZona(p.lat, p.lng)) throw new Error(`Tu ubicación está fuera de la zona piloto (${ZONA.nombre}).`)
        onElegir({ ...p, id: '__personalizado', nombre: 'Mi ubicación' })
      } catch (e) {
        setError(e instanceof Error ? e.message : 'No pudimos obtener tu ubicación.')
      } finally {
        setUbicando(false)
      }
    } else if (opcion.lat != null && opcion.lng != null) {
      onElegir({ id: opcion.id, nombre: opcion.nombre, lat: opcion.lat, lng: opcion.lng })
    }
    setEditando(false)
    inputRef.current?.blur()
  }

  function teclado(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault()
      if (!opciones.length) return
      const paso = e.key === 'ArrowDown' ? 1 : -1
      setActivo((i) => (i + paso + opciones.length) % opciones.length)
    } else if (e.key === 'Enter' && abierto) {
      e.preventDefault()
      const opcion = opciones[activo >= 0 ? activo : 0]
      if (opcion) elegir(opcion)
    } else if (e.key === 'Escape') {
      setEditando(false)
    }
  }

  const listaId = `${id}-lista`

  return (
    <div className="relative">
      <label htmlFor={id} className={ocultarEtiqueta ? 'sr-only' : 'etiqueta'}>
        {etiqueta}
      </label>
      <div className="relative">
        <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-texto-suave">
          {icono ?? <IconoBuscar className="size-5" />}
        </span>
        <input
          ref={inputRef}
          id={id}
          type="search"
          role="combobox"
          aria-expanded={abierto}
          aria-controls={listaId}
          aria-autocomplete="list"
          aria-activedescendant={activo >= 0 ? `${id}-op-${activo}` : undefined}
          autoComplete="off"
          enterKeyHint="search"
          placeholder={ubicando ? 'Obteniendo tu ubicación…' : placeholder}
          className={`campo pl-10 pr-10 [&::-webkit-search-cancel-button]:hidden ${grande ? 'min-h-13 rounded-2xl text-lg shadow-sm' : ''}`}
          value={editando ? texto : (valor?.nombre ?? '')}
          onFocus={(e) => {
            setEditando(true)
            setTexto(valor?.nombre ?? '')
            setActivo(-1)
            onFocus?.(e)
            // Como en Google Maps: al volver a un campo lleno se selecciona el texto para reescribirlo
            if (valor?.nombre) e.target.select()
          }}
          onBlur={() => setEditando(false)}
          onChange={(e) => {
            setTexto(e.target.value)
            setActivo(-1)
          }}
          onKeyDown={teclado}
        />
        {(editando ? texto : valor) && (
          <button
            type="button"
            aria-label="Borrar"
            className="absolute right-1 top-1/2 grid size-9 -translate-y-1/2 place-items-center rounded-lg text-texto-suave hover:bg-fondo"
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => {
              if (!editando) inputRef.current?.focus()
              setTexto('')
              if (valor) onElegir(null)
            }}
          >
            <IconoCerrar className="size-4" />
          </button>
        )}
      </div>

      {abierto && (
        <ul
          id={listaId}
          role="listbox"
          aria-label={`Sugerencias para ${etiqueta}`}
          className="absolute inset-x-0 top-full z-[1200] mt-1 max-h-80 overflow-y-auto rounded-2xl border border-borde bg-superficie py-1 shadow-lg"
          // Evita que el input pierda el foco antes de registrar el clic
          onMouseDown={(e) => e.preventDefault()}
        >
          {opciones.map((o, i) => (
            <li
              key={o.id}
              id={`${id}-op-${i}`}
              role="option"
              aria-selected={i === activo}
              onClick={() => elegir(o)}
              onMouseEnter={() => setActivo(i)}
              className={`flex min-h-12 cursor-pointer items-center gap-3 px-3 py-2 ${i === activo ? 'bg-fondo' : ''}`}
            >
              <span
                className={`grid size-8 shrink-0 place-items-center rounded-full ${
                  o.gps ? 'bg-primario-claro text-primario-oscuro' : 'bg-fondo text-texto-suave'
                }`}
              >
                {o.gps ? <IconoUbicacion className="size-4" /> : <IconoItinerario className="size-4" />}
              </span>
              <span className="min-w-0">
                <span className="block truncate font-medium">{o.nombre}</span>
                {o.detalle && <span className="block truncate text-xs text-texto-suave">{o.detalle}</span>}
              </span>
            </li>
          ))}
          {cargando && <li className="px-3 py-2 text-sm text-texto-suave">Buscando direcciones…</li>}
          {!cargando && remoto.error && remoto.consulta === consulta && (
            <li className="px-3 py-2 text-sm text-aviso">No se pudo buscar direcciones; revisa tu conexión.</li>
          )}
          {!cargando && buscaRemoto && opciones.length === 0 && !remoto.error && (
            <li className="px-3 py-2 text-sm text-texto-suave">Sin resultados dentro de la zona piloto.</li>
          )}
          {remotos.length > 0 && (
            <li className="px-3 pb-1 pt-2 text-right text-[10px] text-texto-suave">Direcciones: © OpenStreetMap</li>
          )}
        </ul>
      )}
      <MensajeError>{error}</MensajeError>
    </div>
  )
}
