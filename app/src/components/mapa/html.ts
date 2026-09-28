// Página HTML con Leaflet que dibuja el mapa. La usan el WebView (celular) y un iframe (web).
//
// Por qué no react-native-maps: en Expo Go SDK 57 para Android el mapa de Google sale en blanco
// (bug abierto: https://github.com/expo/expo/issues/49323). Leaflet con mosaicos de Esri/OpenStreetMap
// funciona en Expo Go, en iPhone y en web, y no necesita llave de Google.
//
// Mensajes: la app llama window.recibir(datos) (o postMessage en web) y la página responde con
// { tipo: 'listo' | 'toque' | 'marcador', ... }.

import { ZONA } from '@/constants/zona';

const { sur, oeste, norte, este } = ZONA.limites;

export const HTML_MAPA = `<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  html, body, #mapa { margin: 0; height: 100%; width: 100%; }
  body { background: #eef1f2; font-family: system-ui, -apple-system, Roboto, sans-serif; }
  .marcador { background: transparent; border: 0; }
  .leaflet-control-attribution { font-size: 9px; }
  .leaflet-bar { border: 0 !important; box-shadow: 0 1px 5px rgba(0,0,0,.3); border-radius: 10px; overflow: hidden; }
  .leaflet-bar a { width: 40px !important; height: 40px !important; line-height: 40px !important; font-size: 20px !important; }
  .oscuro .leaflet-bar a { background: #16252d; color: #e6eef1; border-color: #263943; }
  .oscuro .leaflet-control-attribution { background: rgba(22,37,45,.8); color: #93a6af; }
  .oscuro .leaflet-control-attribution a { color: #2bc4bc; }
</style>
</head>
<body>
<div id="mapa"></div>
<script>
  var ESRI = 'https://server.arcgisonline.com/ArcGIS/rest/services/';
  var ATRIB = 'Mapa &copy; Esri · datos &copy; OpenStreetMap';
  var MOSAICOS = {
    claro: [['World_Street_Map', 19]],
    oscuro: [['Canvas/World_Dark_Gray_Base', 16], ['Canvas/World_Dark_Gray_Reference', 16]]
  };

  function enviar(msg) {
    if (window.ReactNativeWebView) window.ReactNativeWebView.postMessage(JSON.stringify(msg));
    else if (window.parent !== window) { msg.fuente = 'brujula-mapa'; window.parent.postMessage(msg, '*'); }
  }

  var mapa = L.map('mapa', {
    zoomControl: false,
    minZoom: 11,
    maxZoom: 19,
    maxBounds: [[${sur}, ${oeste}], [${norte}, ${este}]],
    maxBoundsViscosity: 1
  }).setView([${ZONA.centro.lat}, ${ZONA.centro.lng}], 12);
  L.control.zoom({ position: 'bottomright' }).addTo(mapa);
  mapa.on('click', function (e) { enviar({ tipo: 'toque', lat: e.latlng.lat, lng: e.latlng.lng }); });

  var capasBase = [];
  var esquemaActual = null;
  var dibujos = L.layerGroup().addTo(mapa);
  var ultimaClave = null;

  function ponerMosaicos(esquema) {
    if (esquema === esquemaActual) return;
    esquemaActual = esquema;
    capasBase.forEach(function (c) { mapa.removeLayer(c); });
    capasBase = MOSAICOS[esquema].map(function (m, i) {
      return L.tileLayer(ESRI + m[0] + '/MapServer/tile/{z}/{y}/{x}', {
        maxNativeZoom: m[1], maxZoom: 19, attribution: i === 0 ? ATRIB : ''
      }).addTo(mapa);
    });
    document.body.className = esquema;
  }

  function icono(m, c) {
    var grande = m.tipo !== 'parada';
    var fondo = { destino: '#EA4335', seleccion: '#EA4335', reporte: c.peligro, parada: c.tarjeta, origen: c.primario, lugar: c.oscuro }[m.tipo] || c.primario;
    var color = m.tipo === 'lugar' ? c.sobreOscuro : m.tipo === 'parada' ? c.primario : '#fff';
    var borde = m.tipo === 'parada' ? c.primario : '#fff';
    var tam = grande ? 30 : 20;
    var texto = m.etiqueta != null ? m.etiqueta : (m.tipo === 'reporte' ? '!' : '');
    if (m.tipo === 'destino' || m.tipo === 'seleccion') {
      return L.divIcon({
        className: 'marcador', iconSize: [30, 40], iconAnchor: [15, 40],
        html: '<svg width="30" height="40" viewBox="0 0 24 32" style="filter:drop-shadow(0 2px 2px rgba(0,0,0,.35))">' +
          '<path d="M12 0C5.4 0 0 5.2 0 11.7 0 20.4 12 32 12 32s12-11.6 12-20.3C24 5.2 18.6 0 12 0z" fill="#EA4335" stroke="#fff" stroke-width="1.5"/>' +
          '<circle cx="12" cy="11.5" r="4.2" fill="#fff"/></svg>'
      });
    }
    return L.divIcon({
      className: 'marcador', iconSize: [tam, tam], iconAnchor: [tam / 2, tam / 2],
      html: '<div style="width:' + tam + 'px;height:' + tam + 'px;border-radius:50%;background:' + fondo + ';color:' + color +
        ';border:' + (grande ? 2 : 3) + 'px solid ' + borde + ';box-sizing:border-box;display:flex;align-items:center;justify-content:center;' +
        'font:800 13px system-ui,sans-serif;box-shadow:0 1px 4px rgba(0,0,0,.35)">' + texto + '</div>'
    });
  }

  window.recibir = function (d) {
    ponerMosaicos(d.esquema);
    var c = d.colores;
    dibujos.clearLayers();

    d.lineas.forEach(function (l) {
      var puntos = l.coordenadas.map(function (p) { return [p.lat, p.lng]; });
      if (puntos.length < 2) return;
      if (l.modo === 'pie') {
        L.polyline(puntos, { color: c.ruta, weight: 6, opacity: 1, dashArray: '1 11', lineCap: 'round' }).addTo(dibujos);
      } else {
        L.polyline(puntos, { color: '#ffffff', weight: 10, opacity: .9 }).addTo(dibujos);
        L.polyline(puntos, { color: l.modo === 'autobus' ? c.oscuro : c.ruta, weight: 6, opacity: 1 }).addTo(dibujos);
      }
    });

    if (d.miUbicacion) {
      L.circle([d.miUbicacion.lat, d.miUbicacion.lng], { radius: 60, stroke: false, fillColor: '#1a73e8', fillOpacity: .15 }).addTo(dibujos);
      L.circleMarker([d.miUbicacion.lat, d.miUbicacion.lng], { radius: 8, color: '#fff', weight: 3, fillColor: '#1a73e8', fillOpacity: 1 }).addTo(dibujos);
    }

    d.marcadores.forEach(function (m) {
      var mk = L.marker([m.lat, m.lng], { icon: icono(m, c), title: m.titulo || '' }).addTo(dibujos);
      if (m.tocable) mk.on('click', function () { enviar({ tipo: 'marcador', id: m.id }); });
      else if (m.titulo) mk.bindPopup(m.titulo);
    });

    // Los controles (zoom) suben para no quedar debajo del panel inferior
    var margen = d.margen || {};
    document.querySelectorAll('.leaflet-bottom').forEach(function (el) { el.style.bottom = (margen.abajo || 0) + 'px'; });

    // Solo se vuelve a encuadrar cuando cambian los puntos (no al cambiar de tema).
    // Los reportes no cuentan para el encuadre, salvo que sean lo único en el mapa.
    if (d.clave !== ultimaClave) {
      ultimaClave = d.clave;
      var todos = [];
      d.lineas.forEach(function (l) { l.coordenadas.forEach(function (p) { todos.push([p.lat, p.lng]); }); });
      var sinReportes = d.marcadores.filter(function (m) { return m.tipo !== 'reporte'; });
      (sinReportes.length ? sinReportes : d.marcadores).forEach(function (m) { todos.push([m.lat, m.lng]); });
      var opciones = {
        paddingTopLeft: [40 + (margen.izquierda || 0), 50 + (margen.arriba || 0)],
        paddingBottomRight: [40, 50 + (margen.abajo || 0)],
        maxZoom: 16
      };
      if (todos.length) mapa.fitBounds(todos.length === 1 ? [todos[0], todos[0]] : todos, opciones);
    }
  };

  window.centrar = function (lat, lng) { mapa.flyTo([lat, lng], 16, { duration: .8 }); };

  // En web los datos llegan por postMessage desde la página que contiene el iframe
  window.addEventListener('message', function (e) {
    var d = e.data;
    if (!d || d.fuente !== 'brujula-app') return;
    if (d.tipo === 'datos') window.recibir(d);
    if (d.tipo === 'centrar') window.centrar(d.lat, d.lng);
  });

  enviar({ tipo: 'listo' });
</script>
</body>
</html>`;
