import { useEffect, useMemo, useState } from 'react'
import { CircleMarker, MapContainer, Polyline, Popup, TileLayer, Tooltip as TooltipMapa } from 'react-leaflet'
import { MensajeError } from '../../../compartido/componentes/Avisos.tsx'
import { ATRIBUCION, MOSAICOS } from '../../../compartido/config/mapa.ts'
import { ZONA } from '../../../compartido/config/zona.ts'
import type { ArbolRuta, ParLeaflet, Ruta } from '../../../compartido/tipos/dominio.ts'
import { aLeaflet } from '../../../compartido/utils/geo.ts'
import { useTema } from '../../../compartido/utils/tema.ts'
import { obtenerArbolRuta, obtenerRutas } from '../api.ts'
import TarjetaGrafica from '../componentes/TarjetaGrafica.tsx'
import { COLOR, decimal, numero } from '../estilo.ts'
import type { MovilidadDashboard } from '../tipos.ts'

const PASOS = [25, 45, 65, 85, 100] // % de azul (un solo tono, claro → oscuro) según cuántas subidas y bajadas

/**
 * Panel "Rutas y paradas": trazo de la ruta elegida con sus paradas numeradas en orden (recorrido inorden del
 * árbol binario de la API) y un mapa de calor de las paradas donde más se sube y se baja. No se dibuja el árbol.
 */
export default function PanelRutasParadas({ movilidad }: { movilidad: MovilidadDashboard }) {
  const { tema } = useTema()
  const [rutas, setRutas] = useState<Ruta[]>([])
  const [idRuta, setIdRuta] = useState<number | null>(null)
  const [arbol, setArbol] = useState<{ para: number; datos: ArbolRuta | null; error: string } | null>(null)
  const uso = useMemo(() => movilidad.paradas_uso ?? [], [movilidad.paradas_uso])

  useEffect(() => {
    obtenerRutas()
      .then((lista) => {
        setRutas(lista)
        setIdRuta((actual) => actual ?? lista[0]?.id ?? null)
      })
      .catch(() => setRutas([]))
  }, [])

  useEffect(() => {
    if (idRuta === null) return
    let vigente = true
    obtenerArbolRuta(idRuta)
      .then((datos) => vigente && setArbol({ para: idRuta, datos, error: '' }))
      .catch((e: unknown) => vigente && setArbol({ para: idRuta, datos: null, error: e instanceof Error ? e.message : String(e) }))
    return () => {
      vigente = false
    }
  }, [idRuta])

  const ruta = rutas.find((r) => r.id === idRuta)
  const paradas = arbol?.para === idRuta ? (arbol.datos?.inorden ?? []) : []
  const trazo: ParLeaflet[] = ruta ? ruta.trazo.map(aLeaflet) : []
  const usoRuta = uso.filter((p) => p.id_ruta === idRuta || idRuta === null)
  const maximo = Math.max(1, ...uso.map((p) => p.total))
  const tono = (total: number) => PASOS[Math.min(PASOS.length - 1, Math.floor(((total - 1) / maximo) * PASOS.length))]
  // Con muchos puntos del trazo solo se numeran algunos para que se lean
  const cada = Math.max(1, Math.ceil(paradas.length / 25))

  const filas = paradas.map((p, i) => {
    const u = uso.find((x) => x.id_ruta === idRuta && x.nombre === p.nombre)
    return { orden: i + 1, nombre: p.nombre, km: p.km, subidas: u?.subidas ?? 0, bajadas: u?.bajadas ?? 0 }
  })

  return (
    <TarjetaGrafica
      titulo="Rutas y paradas"
      descripcion={
        arbol?.datos && !arbol.datos.paradas_reales
          ? 'Esta ruta todavía no tiene paradas capturadas: se muestran los puntos de su trazo ("Punto N"). Círculos azules: paradas donde más se sube y se baja.'
          : 'Paradas de la ruta en orden y, en azul, las paradas donde más se sube y se baja según "¿Cómo llego?".'
      }
      archivo="rutas-y-paradas"
      columnas={[
        { clave: 'orden', titulo: '#' },
        { clave: 'nombre', titulo: 'Parada' },
        { clave: 'km', titulo: 'Km desde el inicio', formato: decimal },
        { clave: 'subidas', titulo: 'Subidas', formato: numero },
        { clave: 'bajadas', titulo: 'Bajadas', formato: numero },
      ]}
      filas={filas}
      vacio={!rutas.length}
      alto="h-[30rem]"
    >
      <div className="flex h-full flex-col gap-2">
        <label className="max-w-sm">
          <span className="sr-only">Ruta</span>
          <select className="campo py-1 text-sm" value={idRuta ?? ''} onChange={(e) => setIdRuta(Number(e.target.value))}>
            {rutas.map((r) => (
              <option key={r.id} value={r.id}>
                {r.nombre ?? `Ruta ${r.id}`}
              </option>
            ))}
          </select>
        </label>
        {arbol?.error && <MensajeError>{arbol.error}</MensajeError>}
        <MapContainer
          key={idRuta ?? 'sin-ruta'}
          bounds={trazo.length > 1 ? trazo : ZONA.limites}
          minZoom={ZONA.zoomMinimo}
          className="min-h-0 flex-1 rounded-xl"
          scrollWheelZoom={false}
        >
          {MOSAICOS[tema].map((capa, i) => (
            <TileLayer key={`${tema}-${i}`} url={capa.url} maxNativeZoom={capa.maxNativeZoom} maxZoom={19} attribution={i === 0 ? ATRIBUCION : undefined} />
          ))}
          {trazo.length > 1 && (
            <>
              <Polyline positions={trazo} pathOptions={{ className: 'trazo-borde', weight: 9, opacity: 1 }} />
              <Polyline positions={trazo} pathOptions={{ className: 'trazo-ruta', weight: 5, opacity: 1 }} />
            </>
          )}
          {usoRuta.map((p) => (
            <CircleMarker
              key={`uso-${p.id_ruta}-${p.nombre}-${p.lat}`}
              center={[p.lat, p.lng]}
              radius={8 + (14 * p.total) / maximo}
              pathOptions={{
                color: COLOR.superficie,
                weight: 2,
                fillColor: `color-mix(in srgb, var(--color-primario) ${tono(p.total)}%, var(--color-superficie))`,
                fillOpacity: 0.85,
              }}
            >
              <Popup>
                <strong>{p.nombre}</strong>
                <br />
                {numero(p.subidas)} subidas · {numero(p.bajadas)} bajadas
              </Popup>
            </CircleMarker>
          ))}
          {paradas.map((p, i) => (
            <CircleMarker
              key={p.id}
              center={[p.lat, p.lng]}
              radius={i % cada === 0 || i === paradas.length - 1 ? 9 : 4}
              pathOptions={{ color: COLOR.superficie, weight: 2, fillColor: COLOR.texto, fillOpacity: 1 }}
            >
              {(i % cada === 0 || i === paradas.length - 1) && (
                <TooltipMapa permanent direction="center" className="numero-parada">
                  {i + 1}
                </TooltipMapa>
              )}
              <Popup>
                <strong>
                  {i + 1}. {p.nombre}
                </strong>
                <br />
                km {decimal(p.km)}
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
    </TarjetaGrafica>
  )
}
