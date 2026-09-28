// SIMULACIÓN del sistema experto para poder probar la interfaz sin backend.
// El motor real lo programa Einar en Python (backend/app/ia). Aquí solo se imita
// la FORMA de la respuesta: hechos booleanos → reglas SI…ENTONCES → explicación.

import { distanciaKm } from '../../utils/geo.js'

export const REGLAS = {
  R1: 'abierto ∧ dentro_presupuesto ∧ cabe_en_tiempo → candidato',
  R2: 'candidato ∧ coincide_contexto → recomendable',
  R5: '¬datos_suficientes → avisar_sin_informacion',
  R6: 'afluencia_alta ∧ contexto_cita → penalizar_lugar',
  R7: 'recomendable ∧ coincide_gustos → prioridad_alta',
  R8: '¬abierto → descartar_lugar',
  R9: '¬dentro_presupuesto → descartar_lugar',
  R10: '¬cabe_en_tiempo → descartar_lugar',
  R11: 'candidato ∧ ¬coincide_contexto → descartar_lugar',
}

const regla = (id, detalle) => ({ id, descripcion: detalle ? `${REGLAS[id]} (${detalle})` : REGLAS[id] })

// Minutos que se pasan en cada tipo de lugar (supuesto del prototipo)
const ESTANCIA_MIN = { cafeteria: 60, restaurante: 90, parque: 60, museo: 90, cine: 150, plaza: 90 }
const VELOCIDAD_KMH = 18 // promedio urbano estimado para transporte

const aMinutos = (hhmm) => {
  const [h, m] = hhmm.split(':').map(Number)
  return h * 60 + m
}

const minutosTraslado = (a, b) => Math.round(((distanciaKm(a, b) * 1.3) / VELOCIDAD_KMH) * 60) + 10

const coordenadas = (lugar) => {
  const [lng, lat] = lugar.ubicacion.coordinates
  return { lat, lng }
}

function calcularHechos(lugar, { contexto, presupuesto, tiempo_min, gustos, hora, dia, origen }) {
  const datos_suficientes = Boolean(lugar.horario && lugar.costo_promedio != null)
  const estancia = ESTANCIA_MIN[lugar.categoria] ?? 60
  const traslado = minutosTraslado(origen, coordenadas(lugar))
  const horarioDia = lugar.horario?.[dia]
  const llegada = aMinutos(hora) + traslado
  const abierto = Boolean(horarioDia) && llegada >= aMinutos(horarioDia[0]) && llegada + estancia <= aMinutos(horarioDia[1])

  return {
    datos_suficientes,
    abierto,
    dentro_presupuesto: datos_suficientes && lugar.costo_promedio <= presupuesto,
    cabe_en_tiempo: traslado + estancia <= tiempo_min,
    coincide_contexto: lugar.contextos.includes(contexto),
    coincide_gustos: gustos.length === 0 || gustos.includes(lugar.categoria),
    afluencia_alta: lugar.afluencia?.nivel === 'alta',
    contexto_cita: contexto === 'cita',
    _traslado: traslado,
    _estancia: estancia,
  }
}

function evaluarLugar(lugar, peticion) {
  const h = calcularHechos(lugar, peticion)
  const cumplidas = []
  const descartes = []

  if (!h.datos_suficientes) {
    descartes.push(regla('R5', 'faltan horario o costo verificados'))
    return { lugar, h, cumplidas, descartes, puntaje: 0 }
  }
  if (!h.abierto) descartes.push(regla('R8', `cerrado o sin tiempo suficiente a las ${peticion.hora}`))
  if (!h.dentro_presupuesto) descartes.push(regla('R9', `costo promedio $${lugar.costo_promedio}`))
  if (!h.cabe_en_tiempo) descartes.push(regla('R10', `requiere ~${h._traslado + h._estancia} min`))

  const candidato = h.abierto && h.dentro_presupuesto && h.cabe_en_tiempo
  if (candidato) {
    cumplidas.push(regla('R1'))
    if (h.coincide_contexto) cumplidas.push(regla('R2'))
    else descartes.push(regla('R11', `no es un lugar típico para "${peticion.contexto}"`))
  }

  let puntaje = (lugar.calificacion?.valor ?? 0) - h._traslado / 60
  if (candidato && h.coincide_contexto && h.coincide_gustos && peticion.gustos.length) {
    cumplidas.push(regla('R7'))
    puntaje += 2
  }
  if (h.afluencia_alta && h.contexto_cita) {
    cumplidas.push(regla('R6', 'afluencia alta reportada'))
    puntaje -= 1.5
  }
  return { lugar, h, cumplidas, descartes, puntaje }
}

export function inferirItinerarios(lugares, peticion) {
  const evaluados = lugares.map((l) => evaluarLugar(l, peticion))
  const recomendables = evaluados.filter((e) => e.descartes.length === 0).sort((a, b) => b.puntaje - a.puntaje)
  const descartados = evaluados
    .filter((e) => e.descartes.length > 0)
    .map((e) => ({ lugar: e.lugar, reglas: e.descartes }))

  if (recomendables.length === 0) {
    return {
      datos_suficientes: false,
      mensaje: 'No tenemos información suficiente para armar un itinerario con esos datos. Prueba con otro horario, presupuesto o tiempo.',
      itinerarios: [],
      descartados,
    }
  }

  // Hasta 3 itinerarios: cada uno arranca con un lugar distinto y, si alcanza, suma un segundo lugar
  const itinerarios = []
  const vistos = new Set()
  for (const principal of recomendables) {
    if (itinerarios.length === 3) break
    const seleccion = [principal]
    let costo = principal.lugar.costo_promedio
    let tiempo = principal.h._traslado + principal.h._estancia

    for (const extra of recomendables) {
      if (extra === principal || extra.lugar.categoria === principal.lugar.categoria) continue
      const entre = minutosTraslado(coordenadas(principal.lugar), coordenadas(extra.lugar))
      const tiempoExtra = entre + extra.h._estancia
      if (costo + extra.lugar.costo_promedio <= peticion.presupuesto && tiempo + tiempoExtra <= peticion.tiempo_min) {
        seleccion.push(extra)
        costo += extra.lugar.costo_promedio
        tiempo += tiempoExtra
        break
      }
    }

    const clave = seleccion.map((s) => s.lugar._id).sort().join('|')
    if (vistos.has(clave)) continue
    vistos.add(clave)

    const reglas = new Map()
    seleccion.forEach((s) => s.cumplidas.forEach((r) => reglas.set(r.id, r)))
    itinerarios.push({
      id: `itinerario_${itinerarios.length + 1}`,
      titulo: seleccion.map((s) => s.lugar.nombre).join(' + '),
      lugares: seleccion.map((s) => s.lugar),
      costo_total: costo,
      tiempo_total_min: tiempo,
      reglas_cumplidas: [...reglas.values()].sort((a, b) => Number(a.id.slice(1)) - Number(b.id.slice(1))),
      explicacion:
        `Se recomienda porque ${seleccion.length > 1 ? 'los lugares están' : 'el lugar está'} abierto${seleccion.length > 1 ? 's' : ''} a tu hora de salida, ` +
        `cabe${seleccion.length > 1 ? 'n' : ''} en tu presupuesto ($${costo} de $${peticion.presupuesto}) y en tu tiempo disponible.`,
    })
  }

  return { datos_suficientes: true, itinerarios, descartados }
}
