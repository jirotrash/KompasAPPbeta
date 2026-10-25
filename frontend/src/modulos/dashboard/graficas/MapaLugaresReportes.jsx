import { CircleMarker, LayersControl, LayerGroup, MapContainer, Popup, TileLayer } from 'react-leaflet'
import { ATRIBUCION, MOSAICOS } from '../../../compartido/config/mapa.js'
import { ZONA } from '../../../compartido/config/zona.js'
import { useTema } from '../../../compartido/utils/tema.js'
import TarjetaGrafica from '../componentes/TarjetaGrafica.jsx'
import { CATEGORIAS_LUGAR, COLOR, nombreDe, TIPOS_REPORTE } from '../estilo.js'

/** #19 Mapa con capas activables: lugares (círculo relleno) y reportes (aro, color por tipo). */
export default function MapaLugaresReportes({ lugares, reportes }) {
  const { tema } = useTema()
  const filas = [
    ...lugares.puntos.map((p) => ({ capa: 'Lugar', nombre: p.nombre, tipo: p.categoria, lat: p.lat, lng: p.lng })),
    ...reportes.puntos.map((p) => ({ capa: 'Reporte', nombre: p.vigente ? 'Vigente' : 'Vencido', tipo: nombreDe(TIPOS_REPORTE, p.tipo), lat: p.lat, lng: p.lng })),
  ]
  return (
    <TarjetaGrafica
      titulo="Mapa de lugares y reportes"
      descripcion="Activa o apaga cada capa con el control del mapa. Lugares: círculo relleno; reportes: aro (relleno si sigue vigente)."
      archivo="mapa-lugares-reportes"
      columnas={[
        { clave: 'capa', titulo: 'Capa' },
        { clave: 'nombre', titulo: 'Nombre / vigencia' },
        { clave: 'tipo', titulo: 'Categoría / tipo' },
        { clave: 'lat', titulo: 'Latitud' },
        { clave: 'lng', titulo: 'Longitud' },
      ]}
      filas={filas}
      vacio={!filas.length}
      alto="h-[28rem]"
    >
      <div className="flex h-full flex-col gap-2">
        <MapContainer bounds={ZONA.limites} minZoom={ZONA.zoomMinimo}className="min-h-0 flex-1 rounded-xl" scrollWheelZoom={false}>
          {MOSAICOS[tema].map((capa, i) => (
            <TileLayer key={`${tema}-${i}`} url={capa.url} maxNativeZoom={capa.maxNativeZoom} maxZoom={19} attribution={i === 0 ? ATRIBUCION : undefined} />
          ))}
          <LayersControl position="topright" collapsed={false}>
            <LayersControl.Overlay checked name="Lugares">
              <LayerGroup>
                {lugares.puntos.map((p) => (
                  <CircleMarker
                    key={`l-${p.id}`}
                    center={[p.lat, p.lng]}
                    radius={8}
                    pathOptions={{ color: COLOR.superficie, weight: 2, fillColor: CATEGORIAS_LUGAR[p.categoria] ?? COLOR.textoSuave, fillOpacity: 1 }}
                  >
                    <Popup>
                      <strong>{p.nombre}</strong>
                      <br />
                      {p.categoria}
                    </Popup>
                  </CircleMarker>
                ))}
              </LayerGroup>
            </LayersControl.Overlay>
            <LayersControl.Overlay checked name="Reportes">
              <LayerGroup>
                {reportes.puntos.map((p, i) => {
                  const color = TIPOS_REPORTE[p.tipo]?.color ?? COLOR.peligro
                  return (
                    <CircleMarker
                      key={`r-${i}`}
                      center={[p.lat, p.lng]}
                      radius={6}
                      pathOptions={{ color, weight: 3, fillColor: color, fillOpacity: p.vigente ? 0.9 : 0 }}
                    >
                      <Popup>
                        <strong>{nombreDe(TIPOS_REPORTE, p.tipo)}</strong>
                        <br />
                        {p.vigente ? 'Vigente' : 'Vencido'}
                      </Popup>
                    </CircleMarker>
                  )
                })}
              </LayerGroup>
            </LayersControl.Overlay>
          </LayersControl>
        </MapContainer>
        <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-texto-suave" aria-label="Leyenda del mapa">
          {Object.entries(CATEGORIAS_LUGAR).map(([nombre, color]) => (
            <li key={nombre} className="flex items-center gap-1.5">
              <span aria-hidden="true" className="size-3 rounded-full" style={{ background: color }} /> {nombre}
            </li>
          ))}
          {Object.values(TIPOS_REPORTE).map((t) => (
            <li key={t.nombre} className="flex items-center gap-1.5">
              <span aria-hidden="true" className="size-3 rounded-full border-[3px]" style={{ borderColor: t.color }} /> Reporte: {t.nombre}
            </li>
          ))}
        </ul>
      </div>
    </TarjetaGrafica>
  )
}
