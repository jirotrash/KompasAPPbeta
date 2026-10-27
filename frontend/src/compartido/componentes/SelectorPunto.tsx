import { useState } from 'react'
import { estaDentroDeZona, ZONA } from '../config/zona.ts'
import type { Coordenada, Lugar } from '../tipos/dominio.ts'
import { formatoCoordenada } from '../utils/geo.ts'
import { MensajeError } from './Avisos.tsx'
import BuscadorLugar, { type PuntoElegido } from './BuscadorLugar.tsx'
import { IconoItinerario } from './Iconos.tsx'
import Mapa, { type TipoMarcador } from './Mapa.tsx'

type Props = {
  etiqueta: string
  valor: PuntoElegido | null
  onCambiar: (p: PuntoElegido | null) => void
  lugares?: Lugar[]
  tipoMarcador?: TipoMarcador
}

/** Elige un punto dentro de la zona piloto: buscando (lugares, direcciones, GPS) o tocando el mapa. */
export default function SelectorPunto({ etiqueta, valor, onCambiar, lugares = [], tipoMarcador = 'seleccion' }: Props) {
  const [mapaAbierto, setMapaAbierto] = useState(false)
  const [error, setError] = useState('')

  function elegirEnMapa(p: Coordenada) {
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
