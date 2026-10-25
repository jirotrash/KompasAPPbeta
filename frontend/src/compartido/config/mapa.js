// Capas base de los mapas (Mapa.jsx y el mapa del dashboard).

// Mosaicos de Esri (gratuitos, sin llave): estilo de calles parecido a Google Maps y versión oscura.
// En oscuro se pone una capa base sin nombres y encima otra solo con los nombres de calles y colonias.
const ESRI = 'https://server.arcgisonline.com/ArcGIS/rest/services'
export const MOSAICOS = {
  claro: [{ url: `${ESRI}/World_Street_Map/MapServer/tile/{z}/{y}/{x}`, maxNativeZoom: 19 }],
  oscuro: [
    { url: `${ESRI}/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}`, maxNativeZoom: 16 },
    { url: `${ESRI}/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}`, maxNativeZoom: 16 },
  ],
}
export const ATRIBUCION = 'Mapa &copy; <a href="https://www.esri.com">Esri</a>, datos &copy; OpenStreetMap y colaboradores'
