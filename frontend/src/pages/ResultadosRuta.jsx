import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { AvisoSinInformacion, Cargando, MensajeError } from '../components/Avisos.jsx'
import { IconoAtras } from '../components/Iconos.jsx'
import Mapa from '../components/Mapa.jsx'
import TarjetaRuta from '../components/TarjetaRuta.jsx'
import { buscarRutas, obtenerReportes } from '../services/api.js'
import { TIPOS_REPORTE } from '../utils/dominio.js'
import { aLeaflet } from '../utils/geo.js'

function leerPunto(texto) {
  const [lat, lng] = (texto ?? '').split(',').map(Number)
  return Number.isFinite(lat) && Number.isFinite(lng) ? { lat, lng } : null
}

const marcadorDe = (id, tipo, parada) => {
  const [lat, lng] = aLeaflet(parada.ubicacion.coordinates)
  return { id, tipo, lat, lng, titulo: parada.nombre }
}

export default function ResultadosRuta() {
  const [params] = useSearchParams()
  const origen = useMemo(() => leerPunto(params.get('origen')), [params])
  const destino = useMemo(() => leerPunto(params.get('destino')), [params])
  const hora = params.get('hora') ?? '12:00'

  const [estado, setEstado] = useState({ cargando: true, error: '', resultado: null })
  const [seleccion, setSeleccion] = useState(null)
  const [reportes, setReportes] = useState([])

  useEffect(() => {
    if (!origen || !destino) return
    let activo = true
    buscarRutas({ origen, destino, hora })
      .then((resultado) => {
        if (!activo) return
        setEstado({ cargando: false, error: '', resultado })
        setSeleccion(resultado.alternativas?.[0]?.id ?? null)
      })
      .catch((e) => activo && setEstado({ cargando: false, error: e.message, resultado: null }))
    return () => {
      activo = false
    }
  }, [origen, destino, hora])

  const alternativas = estado.resultado?.alternativas ?? []
  const elegida = alternativas.find((a) => a.id === seleccion)

  // Reportes vigentes de la ruta de autobús elegida
  const rutaId = elegida?.ruta_id
  useEffect(() => {
    let activo = true
    const peticion = rutaId ? obtenerReportes(rutaId) : Promise.resolve([])
    peticion.then((lista) => activo && setReportes(lista ?? [])).catch(() => activo && setReportes([]))
    return () => {
      activo = false
    }
  }, [rutaId])

  const marcadores = useMemo(() => {
    const lista = []
    if (origen) lista.push({ id: 'origen', tipo: 'origen', ...origen, titulo: params.get('origen_nombre') ?? 'Origen' })
    if (destino) lista.push({ id: 'destino', tipo: 'destino', ...destino, titulo: params.get('destino_nombre') ?? 'Destino' })
    if (elegida?.abordaje) lista.push(marcadorDe('abordaje', 'abordaje', elegida.abordaje))
    if (elegida?.descenso) lista.push(marcadorDe('descenso', 'descenso', elegida.descenso))
    elegida?.transbordos?.forEach((t, i) => lista.push(marcadorDe(`transbordo_${i}`, 'transbordo', t)))
    reportes.forEach((r) => {
      const [lat, lng] = aLeaflet(r.ubicacion.coordinates)
      lista.push({ id: r._id, tipo: 'reporte', lat, lng, titulo: `Reporte: ${TIPOS_REPORTE[r.tipo]} (${r.estado})` })
    })
    return lista
  }, [origen, destino, elegida, reportes, params])

  const trazo = useMemo(() => elegida?.trazo?.coordinates.map(aLeaflet), [elegida])

  if (!origen || !destino) {
    return (
      <div className="p-4">
        <MensajeError>Faltan el origen o el destino.</MensajeError>
        <Link to="/buscar" className="boton-primario mt-4">
          Nueva búsqueda
        </Link>
      </div>
    )
  }

  return (
    <div className="flex flex-col md:grid md:grid-cols-[minmax(340px,420px)_1fr] lg:grid-cols-[minmax(380px,460px)_1fr]">
      {/* Mapa: arriba en celular, a la derecha y fijo en tablet/escritorio */}
      <div className="md:sticky md:top-0 md:order-last md:h-dvh md:p-4 md:pl-0">
        <Mapa
          redondeado={false}
          className="h-[45vh] min-h-64 md:h-full md:rounded-2xl md:border md:border-borde"
          marcadores={marcadores}
          trazo={trazo}
          estiloTrazo={elegida?.modo === 'pie' ? 'trazo-a-pie' : 'trazo-ruta'}
        />
        <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 px-4 text-xs text-texto-suave md:hidden">
          <li>A: origen</li>
          <li className="text-[#ea4335]">📍 destino</li>
          <li className="text-ok">↑ subir</li>
          <li className="text-aviso">↓ bajar</li>
          <li className="text-peligro">! reporte</li>
        </ul>
      </div>

      <section className="space-y-4 p-4 md:py-6">
        <div>
          <Link to="/buscar" className="mb-2 inline-flex items-center gap-1 text-sm font-semibold text-primario">
            <IconoAtras className="size-4" /> Cambiar búsqueda
          </Link>
          <h1 className="text-xl font-bold leading-snug">
            {params.get('origen_nombre') ?? 'Origen'} → {params.get('destino_nombre') ?? 'Destino'}
          </h1>
          <p className="text-sm text-texto-suave">Salida a las {hora} · tiempos estimados</p>
        </div>

        {estado.cargando && <Cargando texto="Buscando alternativas…" />}
        <MensajeError>{estado.error}</MensajeError>

        {estado.resultado && !estado.resultado.datos_suficientes && (
          <AvisoSinInformacion mensaje={estado.resultado.mensaje} />
        )}

        <div className="space-y-3">
          {alternativas.map((a) => (
            <TarjetaRuta key={a.id} alternativa={a} seleccionada={a.id === seleccion} onSeleccionar={() => setSeleccion(a.id)} />
          ))}
        </div>

        {reportes.length > 0 && (
          <p className="rounded-xl bg-peligro-fondo p-3 text-sm text-peligro">
            Hay {reportes.length} reporte(s) comunitario(s) vigente(s) en esta ruta. Los reportes no sustituyen a los servicios
            de emergencia.
          </p>
        )}
      </section>
    </div>
  )
}
