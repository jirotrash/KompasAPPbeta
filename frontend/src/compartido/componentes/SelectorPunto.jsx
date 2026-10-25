import { useState } from 'react'
import { estaDentroDeZona, ZONA } from '../config/zona.js'
import { formatoCoordenada } from '../utils/geo.js'
import { MensajeError } from './Avisos.jsx'
import BuscadorLugar from './BuscadorLugar.jsx'
import { IconoItinerario } from './Iconos.jsx'
import Mapa from './Mapa.jsx'

/**
 * Elige un punto dentro de la zona piloto: buscando (lugares, direcciones, GPS) o tocando el mapa.
 * @param {{etiqueta: string, valor: {lat, lng, nombre}|null, onCambiar: Function, lugares?: Array}} props
 */
export default function SelectorPunto({ etiqueta, valor, onCambiar, lugares = [], tipoMarcador = 'seleccion' }) {
  const [mapaAbierto, setMapaAbierto] = useState(false)
  const [error, setError] = useState('')

  function elegirEnMapa(p) {
    if (!estaDentroDeZona(p.lat, p.lng)) {
      setError(`Ese punto está fuera de la zona piloto (${ZONA.nombre}).`)
      return
    }
    setError('')
    onCambiar({ ...p, id: '__personalizado', nombre: `Punto en el mapa (${formatoCoordenada(p)})` })
  }

  return (
    <div className="space-y-2">
      <BuscadorLugar etiqueta={etiqueta} valor={valor} onElegir={onCambiar} lugares={lugares} />

      <button
        type="button"
        className="boton-secundario whitespace-nowrap px-3 text-sm"
        aria-expanded={mapaAbierto}
        onClick={() => setMapaAbierto((v) => !v)}
      >
        <IconoItinerario className="size-5" />
        {mapaAbierto ? 'Cerrar mapa' : 'Elegir en el mapa'}
      </button>

      {mapaAbierto && (
        <>
          <p className="text-xs text-texto-suave">Toca el mapa para marcar el punto.</p>
          <Mapa
            className="h-64"
            marcadores={valor ? [{ id: 'sel', lat: valor.lat, lng: valor.lng, tipo: tipoMarcador }] : []}
            onSeleccionar={elegirEnMapa}
          />
        </>
      )}
      <MensajeError>{error}</MensajeError>
    </div>
  )
}
