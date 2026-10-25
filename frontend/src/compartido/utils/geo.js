// Utilidades geográficas. Ojo: GeoJSON (MongoDB) usa [lng, lat]; Leaflet usa [lat, lng].

export const aLeaflet = ([lng, lat]) => [lat, lng]
export const aGeoJSON = ([lat, lng]) => [lng, lat]

/** Distancia en km entre dos puntos {lat, lng} (fórmula de haversine). */
export function distanciaKm(a, b) {
  const rad = (g) => (g * Math.PI) / 180
  const dLat = rad(b.lat - a.lat)
  const dLng = rad(b.lng - a.lng)
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dLng / 2) ** 2
  return 2 * 6371 * Math.asin(Math.sqrt(h))
}

/** Pide la ubicación del dispositivo. Resuelve {lat, lng}. */
export function obtenerUbicacion() {
  return new Promise((resolve, reject) => {
    if (!('geolocation' in navigator)) {
      reject(new Error('Tu dispositivo no permite obtener la ubicación.'))
      return
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => reject(new Error('No pudimos obtener tu ubicación. Revisa los permisos del navegador.')),
      { enableHighAccuracy: true, timeout: 10000 },
    )
  })
}

export const formatoCoordenada = ({ lat, lng }) => `${lat.toFixed(5)}, ${lng.toFixed(5)}`

export function formatoMinutos(min) {
  if (min == null) return '—'
  if (min < 60) return `${Math.round(min)} min`
  const h = Math.floor(min / 60)
  const m = Math.round(min % 60)
  return m ? `${h} h ${m} min` : `${h} h`
}

export function formatoFecha(iso) {
  if (!iso) return 'fecha desconocida'
  const fecha = new Date(iso.length === 10 ? `${iso}T12:00:00` : iso)
  return fecha.toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' })
}
