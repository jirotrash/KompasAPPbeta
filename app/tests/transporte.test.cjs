// node --test tests/transporte.test.cjs
// Usa el compilador TypeScript ya instalado para probar utilidades puras con node:test.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const ts = require('typescript');
const src = path.resolve(__dirname, '../src');
const cache = new Map();

function cargar(archivo) {
  const nombre = path.resolve(src, archivo.endsWith('.ts') ? archivo : `${archivo}.ts`);
  if (cache.has(nombre)) return cache.get(nombre).exports;
  const m = new Module(nombre, module);
  cache.set(nombre, m);
  m.filename = nombre;
  m.require = (id) => id.startsWith('@/') ? cargar(id.slice(2))
    : id.startsWith('.') ? cargar(path.resolve(path.dirname(nombre), id)) : require(id);
  m._compile(ts.transpileModule(readFileSync(nombre, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }, fileName: nombre,
  }).outputText, nombre);
  return m.exports;
}

const { resumenTiempo, ordenarAlternativas, numeroTransbordos, enlaceCaminata } = cargar('utils/transporte');
const { recorridoDesdeAlternativa, duracionTotal } = cargar('utils/recorrido');
const { trazarPorCalles } = cargar('services/mapas');
const origen = { nombre: 'Origen', lat: 19.29, lng: -99.65 };
const destino = { nombre: 'Destino', lat: 19.30, lng: -99.60 };
const p = (nombre, lat, lng, km) => ({ nombre, lat, lng, km });
const subida = p('Subida', 19.291, -99.649, 0);
const bajada = p('Bajada', 19.299, -99.601, 5);
const bus = (espera = null) => ({
  id: 'bus_1', modo: 'autobus', fuente: 'Prueba', tipo: 'directo', numero_transbordos: 0,
  tiempos: { caminata: 3, trayecto: 20, espera },
  tramos: [
    { modo: 'pie', duracion_min: 1, distancia_km: 0.1 },
    { modo: 'autobus', duracion_min: 20, distancia_km: 5, parada_subida: subida, parada_bajada: bajada },
    { modo: 'pie', duracion_min: 2, distancia_km: 0.2 },
  ],
});

test('espera desconocida produce suma parcial, no un total inventado', () => {
  const r = resumenTiempo(bus());
  assert.equal(r.minutos, 23);
  assert.equal(r.completo, false);
  assert.equal(r.texto, '23 min + espera');
  assert.match(r.nota, /no se pueden calcular/);
});

test('cero explícito es conocido y a pie no requiere espera', () => {
  assert.equal(resumenTiempo(bus(0)).completo, true);
  assert.equal(resumenTiempo({ modo: 'pie', tiempos: { caminata: 8, espera: null, trayecto: null } }).texto, '8 min');
});

test('si faltan todos los tiempos no muestra cero minutos', () => {
  const r = resumenTiempo({ modo: 'autobus', tiempos: { caminata: null, espera: null, trayecto: null } });
  assert.equal(r.minutos, null);
  assert.equal(r.texto, 'Sin tiempo disponible');
});

test('filtra sin mutar la respuesta y ordena los datos desconocidos al final', () => {
  const a = bus(8), b = { id: 'taxi', modo: 'taxi', tiempos: { caminata: null, espera: 5, trayecto: 10 } };
  const opciones = [b, a];
  assert.deepEqual(ordenarAlternativas(opciones, 'todos', 'caminata').map((x) => x.id), ['bus_1', 'taxi']);
  assert.deepEqual(opciones.map((x) => x.id), ['taxi', 'bus_1']);
  assert.deepEqual(ordenarAlternativas(opciones, 'auto', 'tiempo').map((x) => x.id), ['taxi']);
  assert.deepEqual(ordenarAlternativas(opciones, 'pie', 'tiempo'), []);
});

test('cuenta transbordos desde los tramos cuando falta el resumen', () => {
  const a = bus();
  delete a.numero_transbordos;
  a.tramos.push({ ...a.tramos[1] });
  assert.equal(numeroTransbordos(a), 1);
});

test('el mapa suma la espera una sola vez y maneja cruce de medianoche', () => {
  const a = bus(8);
  const r = recorridoDesdeAlternativa(a, origen, destino, '23:50');
  assert.equal(duracionTotal(r), 31);
  assert.equal(duracionTotal(r), resumenTiempo(a).minutos);
  assert.equal(r.puntos.at(-1).hora, '00:21');
  assert.equal(r.puntos[2].hora, '00:19');
  assert.equal(r.tiempo_incompleto, false);
});

test('el mapa conserva geometría pero no inventa llegada sin espera conocida', () => {
  const r = recorridoDesdeAlternativa(bus(), origen, destino, '12:00');
  assert.equal(r.tiempo_incompleto, true);
  assert.equal(r.puntos[1].hora, '12:01');
  assert.equal(r.puntos[2].hora, undefined);
  assert.equal(r.puntos.at(-1).hora, undefined);
  assert.equal(duracionTotal(r), 23);
  assert.equal(r.tramos.length + 1, r.puntos.length);
});

test('una espera agregada no se inventa para cada transbordo', () => {
  const a = bus(10);
  a.tramos.splice(2, 0, { modo: 'pie', duracion_min: 2, distancia_km: 0.2 }, { ...a.tramos[1], duracion_min: 15 });
  a.tiempos = { caminata: 5, trayecto: 35, espera: 10 };
  const r = recorridoDesdeAlternativa(a, origen, destino, '12:00');
  assert.equal(duracionTotal(r), 50);
  assert.equal(r.puntos[2].hora, undefined);
  assert.equal(r.puntos.at(-1).hora, '12:50');
});

test('el enlace de abordaje usa coordenadas y modo caminata', () => {
  const u = new URL(enlaceCaminata(origen, destino));
  assert.equal(u.hostname, 'www.google.com');
  assert.equal(u.searchParams.get('api'), '1');
  assert.equal(u.searchParams.get('travelmode'), 'walking');
  assert.equal(u.searchParams.get('destination'), '19.3,-99.6');
});

test('un error del proveedor de trazos permite usar la estimación', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => ({ ok: false }));
  assert.equal(await trazarPorCalles(origen, destino, 'pie'), null);
});

test('rechaza geometrías o duraciones inválidas', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => ({ ok: true, json: async () => ({ code: 'Ok', routes: [{ distance: 1200, duration: -10, geometry: { type: 'LineString', coordinates: [[-99, 19], [-99, 20]] } }] }) }));
  assert.equal(await trazarPorCalles(origen, destino, 'auto'), null);
});

test('acepta un trazo válido y conserva sus unidades', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => ({ ok: true, json: async () => ({ code: 'Ok', routes: [{ distance: 1200, duration: 600, geometry: { type: 'LineString', coordinates: [[-99, 19], [-99, 20]] } }] }) }));
  const r = await trazarPorCalles(origen, destino, 'pie');
  assert.equal(r.distancia_km, 1.2);
  assert.equal(r.duracion_min, 10);
});

test('una consulta de trazado lenta termina y permite continuar', async (t) => {
  t.mock.method(globalThis, 'setTimeout', (fn) => { queueMicrotask(fn); return 0; });
  t.mock.method(globalThis, 'fetch', (_, { signal }) => new Promise((_, reject) => signal.addEventListener('abort', () => reject(new Error('timeout')), { once: true })));
  assert.equal(await trazarPorCalles(origen, destino, 'pie'), null);
});
