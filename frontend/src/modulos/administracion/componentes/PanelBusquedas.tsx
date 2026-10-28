import { useCallback, useState } from 'react'
import { Cargando, MensajeError } from '../../../compartido/componentes/Avisos.tsx'
import Chip from '../../../compartido/componentes/Chip.tsx'
import Mapa, { type LineaMapa, type MarcadorMapa } from '../../../compartido/componentes/Mapa.tsx'
import { aLeaflet } from '../../../compartido/utils/geo.ts'
import * as api from '../api.ts'
import { coordenadas, fechaHora } from '../formato.ts'
import useCarga from '../hooks/useCarga.ts'
import { Insignia, Vacio } from './Comun.tsx'

export default function PanelBusquedas() {
  const [sinAutobus, setSinAutobus] = useState(false)
  const cargar = useCallback(() => api.obtenerBusquedas(sinAutobus), [sinAutobus])
  const { datos: busquedas, cargando, error } = useCarga(cargar)
  const [elegida, setElegida] = useState<string | null>(null)

  const lista = busquedas ?? []
  const sinCamion = lista.filter((b) => !b.datos_suficientes).length
  const actual = lista.find((b) => b.id === elegida)

  // Cada búsqueda es una línea recta origen → destino; las que no encontraron camión van resaltadas
  const lineas: LineaMapa[] = lista
    .filter((b) => b.id !== elegida)
    .map((b) => ({ id: b.id, puntos: [aLeaflet(b.origen.coordinates), aLeaflet(b.destino.coordinates)], estilo: b.datos_suficientes ? 'trazo-tenue' : 'trazo-a-pie' }))
  const marcadores: MarcadorMapa[] = actual
    ? [
        { id: 'o', lat: actual.origen.coordinates[1], lng: actual.origen.coordinates[0], tipo: 'origen', titulo: 'Origen' },
        { id: 'd', lat: actual.destino.coordinates[1], lng: actual.destino.coordinates[0], tipo: 'destino', titulo: 'Destino' },
      ]
    : []

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,28rem)] [&>*]:min-w-0">
      <section className="tarjeta grid content-start gap-3" aria-labelledby="titulo-busquedas">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 id="titulo-busquedas" className="text-lg font-bold">
            Búsquedas de “¿Cómo llego?”
          </h2>
          <div className="flex gap-2" role="group" aria-label="Filtrar búsquedas">
            <Chip activo={!sinAutobus} onClick={() => setSinAutobus(false)}>
              Todas
            </Chip>
            <Chip activo={sinAutobus} onClick={() => setSinAutobus(true)}>
              Solo sin camión
            </Chip>
          </div>
        </div>
        {busquedas && (
          <p className="text-sm text-texto-suave">
            Últimas <strong className="text-texto">{lista.length}</strong> búsquedas
            {!sinAutobus && (
              <>
                {' '}
                · <strong className="text-texto">{sinCamion}</strong> sin camión ({lista.length ? Math.round((100 * sinCamion) / lista.length) : 0}%)
              </>
            )}
            . Las que no encontraron camión son las rutas que conviene dar de alta.
          </p>
        )}
        <MensajeError>{error}</MensajeError>
        {cargando && !busquedas ? (
          <Cargando texto="Cargando búsquedas…" />
        ) : lista.length === 0 ? (
          <Vacio>Todavía nadie ha buscado cómo llegar{sinAutobus ? ' sin encontrar camión' : ''}.</Vacio>
        ) : (
          <div className="max-h-[60vh] overflow-auto">
            <table className="w-full text-left text-sm">
              <thead className="sticky top-0 bg-superficie text-xs uppercase tracking-wide text-texto-suave">
                <tr>
                  <th className="py-2 pr-3 font-semibold">Cuándo</th>
                  <th className="py-2 pr-3 font-semibold">Quién</th>
                  <th className="py-2 pr-3 font-semibold">Origen → destino</th>
                  <th className="py-2 pr-3 font-semibold">Distancia</th>
                  <th className="py-2 font-semibold">Resultado</th>
                </tr>
              </thead>
              <tbody>
                {lista.map((b) => (
                  <tr
                    key={b.id}
                    onClick={() => setElegida(b.id === elegida ? null : b.id)}
                    className={`cursor-pointer border-t border-borde ${b.id === elegida ? 'bg-primario-claro/60' : 'hover:bg-fondo'}`}
                  >
                    <td className="whitespace-nowrap py-2 pr-3">{fechaHora(b.creado_en)}</td>
                    <td className="whitespace-nowrap py-2 pr-3">{b.id_usuario ? `#${b.id_usuario}` : <span className="text-texto-suave">sin sesión</span>}</td>
                    <td className="py-2 pr-3 text-xs">
                      {/* El clic sube a la fila; el botón deja elegirla con teclado */}
                      <button type="button" className="text-left" aria-pressed={b.id === elegida}>
                        {coordenadas(b.origen)} → {coordenadas(b.destino)}
                      </button>
                    </td>
                    <td className="whitespace-nowrap py-2 pr-3">{b.distancia_km != null ? `${b.distancia_km.toFixed(1)} km` : '—'}</td>
                    <td className="py-2">
                      {b.datos_suficientes ? <Insignia tono="ok">{b.rutas.length > 1 ? `rutas ${b.rutas.join(' + ')}` : `ruta ${b.rutas[0] ?? ''}`}</Insignia> : <Insignia tono="peligro">sin camión</Insignia>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
      <div className="grid content-start gap-2 xl:sticky xl:top-4">
        <Mapa className="h-[50vh] min-h-80" lineas={lineas} trazo={actual ? [aLeaflet(actual.origen.coordinates), aLeaflet(actual.destino.coordinates)] : undefined} marcadores={marcadores} />
        <p className="text-xs text-texto-suave">Línea punteada: búsqueda sin camión. Línea tenue: sí hubo camión. Elige una fila para resaltarla.</p>
      </div>
    </div>
  )
}
