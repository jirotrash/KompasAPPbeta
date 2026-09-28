import { useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { MensajeError } from '../components/Avisos.jsx'
import BuscadorLugar from '../components/BuscadorLugar.jsx'
import { IconoIntercambiar } from '../components/Iconos.jsx'
import Mapa from '../components/Mapa.jsx'
import { estaDentroDeZona, ZONA } from '../config/zona.js'
import useEsMovil from '../hooks/useEsMovil.js'
import useLugares from '../hooks/useLugares.js'
import { horaActual } from '../utils/dominio.js'
import { aLeaflet, formatoCoordenada } from '../utils/geo.js'

function Letra({ children, oscura }) {
  return (
    <span
      className={`grid size-5 place-items-center rounded-full text-[11px] font-bold ${
        oscura ? 'bg-texto text-fondo' : 'bg-primario text-sobre-primario'
      }`}
    >
      {children}
    </span>
  )
}

export default function BuscarDestino() {
  const navigate = useNavigate()
  const location = useLocation()
  const lugares = useLugares()
  const esMovil = useEsMovil()
  const [origen, setOrigen] = useState(location.state?.origen ?? null)
  const [destino, setDestino] = useState(location.state?.destino ?? null)
  const [hora, setHora] = useState(horaActual)
  const [campo, setCampo] = useState(location.state?.destino ? 'origen' : 'destino')
  const [error, setError] = useState('')

  function asignar(punto) {
    setError('')
    if (campo === 'origen') {
      setOrigen(punto)
      if (!destino) setCampo('destino')
    } else {
      setDestino(punto)
      if (!origen) setCampo('origen')
    }
  }

  function tocarMapa(p) {
    if (!estaDentroDeZona(p.lat, p.lng)) return setError(`Ese punto está fuera de la zona piloto (${ZONA.nombre}).`)
    asignar({ ...p, id: '__personalizado', nombre: `Punto en el mapa (${formatoCoordenada(p)})` })
  }

  function buscar(e) {
    e.preventDefault()
    if (!origen || !destino) return setError('Elige un origen y un destino.')
    if (origen.lat === destino.lat && origen.lng === destino.lng) return setError('El origen y el destino son el mismo punto.')
    const params = new URLSearchParams({
      origen: `${origen.lat},${origen.lng}`,
      origen_nombre: origen.nombre,
      destino: `${destino.lat},${destino.lng}`,
      destino_nombre: destino.nombre,
      hora,
    })
    navigate(`/resultados?${params}`)
  }

  const marcadores = useMemo(() => {
    const lista = lugares.map((l) => {
      const [lat, lng] = aLeaflet(l.ubicacion.coordinates)
      return {
        id: l._id,
        tipo: 'lugar',
        lat,
        lng,
        titulo: l.nombre,
        onClic: () => asignar({ id: l._id, nombre: l.nombre, lat, lng }),
      }
    })
    if (origen) lista.push({ id: 'origen', tipo: 'origen', lat: origen.lat, lng: origen.lng, titulo: origen.nombre })
    if (destino) lista.push({ id: 'destino', tipo: 'destino', lat: destino.lat, lng: destino.lng, titulo: destino.nombre })
    return lista
    // asignar cambia en cada render; basta con recalcular cuando cambian los datos
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lugares, origen, destino, campo])

  const enfocar = useMemo(() => {
    const elegidos = [origen, destino].filter(Boolean).map((p) => [p.lat, p.lng])
    return elegidos.length ? elegidos : undefined
  }, [origen, destino])

  return (
    <div className="relative flex min-h-[520px] flex-1 flex-col md:grid md:grid-cols-[minmax(340px,420px)_1fr] lg:grid-cols-[minmax(380px,460px)_1fr]">
      {/* En celular el panel flota sobre el mapa (como Google Maps); en tablet/escritorio va a la izquierda */}
      <section className="pointer-events-none absolute inset-x-0 top-0 z-[600] space-y-2 p-3 md:pointer-events-auto md:static md:z-auto md:space-y-4 md:p-4 md:py-6">
        <h1 className="sr-only text-2xl font-bold tracking-tight md:not-sr-only md:text-3xl">¿A dónde vas?</h1>

        <form onSubmit={buscar} className="tarjeta pointer-events-auto space-y-3 p-3 shadow-lg md:p-4 md:shadow-sm">
          <div className="flex items-center gap-2">
            <div className="min-w-0 flex-1 space-y-2">
              <BuscadorLugar
                etiqueta="Origen"
                ocultarEtiqueta
                placeholder="Punto de partida"
                icono={<Letra>A</Letra>}
                valor={origen}
                onElegir={setOrigen}
                onFocus={() => setCampo('origen')}
                lugares={lugares}
              />
              <BuscadorLugar
                etiqueta="Destino"
                ocultarEtiqueta
                placeholder="Busca tu destino"
                icono={<Letra oscura>B</Letra>}
                valor={destino}
                onElegir={setDestino}
                onFocus={() => setCampo('destino')}
                lugares={lugares}
                incluirMiUbicacion={false}
              />
            </div>
            <button
              type="button"
              onClick={() => {
                setOrigen(destino)
                setDestino(origen)
              }}
              className="grid size-11 shrink-0 place-items-center rounded-full text-texto-suave hover:bg-fondo"
              aria-label="Intercambiar origen y destino"
              title="Intercambiar"
            >
              <IconoIntercambiar className="size-5" />
            </button>
          </div>

          <div className="flex flex-wrap items-end gap-2">
            <div className="min-w-32 flex-1">
              <label htmlFor="hora" className="etiqueta">
                Hora de salida
              </label>
              <input id="hora" type="time" className="campo" value={hora} onChange={(e) => setHora(e.target.value)} required />
            </div>
            <button type="submit" className="boton-primario flex-1">
              Ver rutas
            </button>
          </div>
          <MensajeError>{error}</MensajeError>
        </form>

        <p className="pointer-events-auto mx-auto w-fit rounded-full bg-superficie/95 px-3 py-1.5 text-xs text-texto-suave shadow-md md:mx-0 md:w-auto md:rounded-none md:bg-transparent md:p-0 md:text-sm md:shadow-none">
          Toca el mapa o un lugar para elegir el{' '}
          <strong className="text-texto">{campo === 'origen' ? 'origen (A)' : 'destino (B)'}</strong>
        </p>
      </section>

      <div className="absolute inset-0 md:sticky md:inset-auto md:top-0 md:order-last md:h-dvh md:p-4 md:pl-0">
        <Mapa
          className="h-full md:rounded-2xl md:border md:border-borde"
          redondeado={false}
          rellenoArriba={esMovil ? 230 : 0}
          marcadores={marcadores}
          enfocar={enfocar}
          onSeleccionar={tocarMapa}
        />
      </div>
    </div>
  )
}
