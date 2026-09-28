import L from 'leaflet'
import { useEffect, useMemo, useState } from 'react'
import {
  Circle,
  CircleMarker,
  MapContainer,
  Marker,
  Polyline,
  Popup,
  TileLayer,
  useMap,
  useMapEvents,
  ZoomControl,
} from 'react-leaflet'
import { estaDentroDeZona, ZONA } from '../config/zona.js'
import { obtenerUbicacion } from '../utils/geo.js'
import { useTema } from '../utils/tema.js'
import { IconoUbicacion } from './Iconos.jsx'

// Mosaicos de Esri (gratuitos, sin llave): estilo de calles parecido a Google Maps y versión oscura.
// En oscuro se pone una capa base sin nombres y encima otra solo con los nombres de calles y colonias.
const ESRI = 'https://server.arcgisonline.com/ArcGIS/rest/services'
const MOSAICOS = {
  claro: [{ url: `${ESRI}/World_Street_Map/MapServer/tile/{z}/{y}/{x}`, maxNativeZoom: 19 }],
  oscuro: [
    { url: `${ESRI}/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}`, maxNativeZoom: 16 },
    { url: `${ESRI}/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}`, maxNativeZoom: 16 },
  ],
}
const ATRIBUCION = 'Mapa &copy; <a href="https://www.esri.com">Esri</a>, datos &copy; OpenStreetMap y colaboradores'

// Estilo de cada tipo de marcador: [color (token CSS), texto, forma]
const ESTILOS = {
  origen: ['var(--color-primario)', 'A', 'circulo'],
  destino: ['#ea4335', '', 'pin'],
  abordaje: ['var(--color-ok)', '↑', 'circulo'],
  descenso: ['var(--color-aviso)', '↓', 'circulo'],
  transbordo: ['var(--color-acento)', '⇄', 'circulo'],
  lugar: ['#f97316', '', 'pin-chico'],
  reporte: ['var(--color-peligro)', '!', 'circulo'],
  seleccion: ['#ea4335', '', 'pin'],
}

const pin = (color, ancho, texto) => {
  const alto = Math.round(ancho * 1.35)
  return L.divIcon({
    className: 'marcador-mapa',
    html: `<svg width="${ancho}" height="${alto}" viewBox="0 0 24 32" style="filter:drop-shadow(0 2px 2px rgb(0 0 0/.35))"><path d="M12 0C5.4 0 0 5.2 0 11.7 0 20.4 12 32 12 32s12-11.6 12-20.3C24 5.2 18.6 0 12 0z" fill="${color}" stroke="#fff" stroke-width="1.5"/>${
      texto
        ? `<text x="12" y="16" text-anchor="middle" font-size="11" font-weight="700" fill="#fff" font-family="system-ui">${texto}</text>`
        : '<circle cx="12" cy="11.5" r="4.2" fill="#fff" fill-opacity=".9"/>'
    }</svg>`,
    iconSize: [ancho, alto],
    iconAnchor: [ancho / 2, alto],
    popupAnchor: [0, -alto],
  })
}

function icono(tipo, texto) {
  const [color, simbolo, forma] = ESTILOS[tipo] ?? ESTILOS.seleccion
  if (forma === 'pin') return pin(color, 30, texto)
  if (forma === 'pin-chico') return pin(color, 22, texto)
  return L.divIcon({
    className: 'marcador-mapa',
    html: `<span style="display:grid;place-items:center;width:28px;height:28px;border-radius:9999px;background:${color};color:#fff;font-weight:700;font-size:13px;border:3px solid #fff;box-shadow:0 1px 4px rgb(0 0 0/.4)">${texto ?? simbolo}</span>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -16],
  })
}

/** Ajusta la vista al contenido y recalcula el tamaño cuando cambia el contenedor. */
function AjustarVista({ puntos, rellenoArriba }) {
  const map = useMap()
  const clave = JSON.stringify(puntos)

  useEffect(() => {
    const lista = JSON.parse(clave)
    if (!lista.length) return
    // Con un solo punto se encuadra como si fueran dos iguales para respetar el relleno de arriba
    const limites = lista.length === 1 ? [lista[0], lista[0]] : lista
    map.fitBounds(limites, {
      paddingTopLeft: [48, rellenoArriba + 48],
      paddingBottomRight: [48, 48],
      maxZoom: lista.length === 1 ? Math.max(map.getZoom(), 15) : 16,
    })
  }, [clave, map, rellenoArriba])

  useEffect(() => {
    const observador = new ResizeObserver(() => map.invalidateSize())
    observador.observe(map.getContainer())
    return () => observador.disconnect()
  }, [map])

  return null
}

function AlHacerClic({ onSeleccionar }) {
  useMapEvents({ click: (e) => onSeleccionar({ lat: e.latlng.lat, lng: e.latlng.lng }) })
  return null
}

/**
 * Mapa limitado a la zona piloto, con estilo y controles parecidos a Google Maps.
 * @param {{
 *   marcadores?: Array<{id: string, lat: number, lng: number, tipo: keyof ESTILOS, titulo?: string, texto?: string, onClic?: Function}>,
 *   trazo?: Array<[number, number]>,   // [lat, lng]
 *   estiloTrazo?: 'trazo-ruta' | 'trazo-a-pie',
 *   onSeleccionar?: (p: {lat, lng}) => void,
 *   enfocar?: Array<[number, number]>,  // puntos a encuadrar; por defecto, todo lo que hay en el mapa
 *   redondeado?: boolean,
 *   rellenoArriba?: number,             // px tapados por paneles flotantes sobre el mapa
 *   className?: string
 * }} props
 */
export default function Mapa({
  marcadores = [],
  trazo,
  estiloTrazo = 'trazo-ruta',
  onSeleccionar,
  enfocar,
  redondeado = true,
  rellenoArriba = 0,
  className = 'h-72',
}) {
  const { tema } = useTema()
  const [mapa, setMapa] = useState(null)
  const [miPosicion, setMiPosicion] = useState(null)
  const [ubicando, setUbicando] = useState(false)
  const [aviso, setAviso] = useState('')

  const puntos = useMemo(
    () => enfocar ?? [...(trazo ?? []), ...marcadores.map((m) => [m.lat, m.lng])],
    [enfocar, marcadores, trazo],
  )

  function mostrarAviso(texto) {
    setAviso(texto)
    setTimeout(() => setAviso(''), 4000)
  }

  async function irAMiUbicacion() {
    setUbicando(true)
    try {
      const p = await obtenerUbicacion()
      if (!estaDentroDeZona(p.lat, p.lng)) {
        mostrarAviso('Estás fuera de la zona piloto.')
        return
      }
      setMiPosicion(p)
      mapa?.flyTo([p.lat, p.lng], 16, { duration: 0.8 })
    } catch (e) {
      mostrarAviso(e.message)
    } finally {
      setUbicando(false)
    }
  }

  const aPie = estiloTrazo === 'trazo-a-pie'

  return (
    <div
      className={`relative overflow-hidden ${redondeado ? 'rounded-2xl border border-borde' : ''} ${className}`}
    >
      <MapContainer
        ref={setMapa}
        center={ZONA.centro}
        zoom={ZONA.zoomInicial}
        minZoom={ZONA.zoomMinimo}
        maxZoom={19}
        maxBounds={ZONA.limites}
        maxBoundsViscosity={1}
        zoomControl={false}
        scrollWheelZoom
        className={`h-full w-full ${onSeleccionar ? 'cursor-crosshair' : ''}`}
      >
        {MOSAICOS[tema].map((capa, i) => (
          <TileLayer
            key={`${tema}-${i}`}
            url={capa.url}
            maxNativeZoom={capa.maxNativeZoom}
            maxZoom={19}
            attribution={i === 0 ? ATRIBUCION : undefined}
          />
        ))}
        <ZoomControl position="bottomright" />

        {trazo?.length > 1 && (
          <>
            {/* Borde + línea, como las rutas de Google Maps */}
            {!aPie && <Polyline positions={trazo} pathOptions={{ className: 'trazo-borde', weight: 10, opacity: 1 }} />}
            <Polyline
              key={estiloTrazo}
              positions={trazo}
              pathOptions={{ className: estiloTrazo, weight: aPie ? 7 : 6, opacity: 1 }}
            />
          </>
        )}

        {marcadores.map((m) => (
          <Marker
            key={m.id}
            position={[m.lat, m.lng]}
            icon={icono(m.tipo, m.texto)}
            title={m.titulo}
            eventHandlers={m.onClic ? { click: m.onClic } : undefined}
          >
            {m.titulo && !m.onClic && <Popup>{m.titulo}</Popup>}
          </Marker>
        ))}

        {miPosicion && (
          <>
            <Circle center={miPosicion} radius={60} pathOptions={{ className: 'mi-posicion-halo', weight: 0 }} />
            <CircleMarker center={miPosicion} radius={8} pathOptions={{ className: 'mi-posicion', weight: 3, fillOpacity: 1 }} />
          </>
        )}

        <AjustarVista puntos={puntos} rellenoArriba={rellenoArriba} />
        {onSeleccionar && <AlHacerClic onSeleccionar={onSeleccionar} />}
      </MapContainer>

      {/* Botón "Mi ubicación" flotante, arriba de los controles de zoom */}
      <button
        type="button"
        onClick={irAMiUbicacion}
        disabled={ubicando}
        aria-label="Ir a mi ubicación"
        title="Mi ubicación"
        className="absolute bottom-[92px] right-[10px] z-[500] grid size-10 place-items-center rounded-lg bg-superficie text-texto-suave shadow-md transition hover:text-primario disabled:opacity-60"
      >
        <IconoUbicacion className={`size-5 ${ubicando ? 'animate-pulse text-primario' : ''}`} />
      </button>

      {aviso && (
        <p
          role="status"
          className="absolute inset-x-3 top-3 z-[500] rounded-xl bg-superficie px-3 py-2 text-center text-sm text-aviso shadow-md"
        >
          {aviso}
        </p>
      )}
    </div>
  )
}
