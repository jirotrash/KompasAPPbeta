// Tema claro/oscuro. La preferencia se guarda en el navegador y puede ser
// 'claro', 'oscuro' o 'sistema' (sigue la configuración del dispositivo).
// El script en línea de index.html aplica el tema antes de pintar para evitar parpadeos;
// si cambias CLAVE aquí, cámbiala también allá.

import { useSyncExternalStore } from 'react'

const CLAVE = 'bu_tema'
const COLOR_BARRA = { claro: '#0f766e', oscuro: '#0b1120' }
const medio = window.matchMedia('(prefers-color-scheme: dark)')
const oyentes = new Set()

function leerPreferencia() {
  try {
    const valor = localStorage.getItem(CLAVE)
    return ['claro', 'oscuro', 'sistema'].includes(valor) ? valor : 'sistema'
  } catch {
    return 'sistema'
  }
}

let preferencia = leerPreferencia()

const temaResuelto = () => (preferencia === 'sistema' ? (medio.matches ? 'oscuro' : 'claro') : preferencia)

function aplicar() {
  const tema = temaResuelto()
  document.documentElement.dataset.tema = tema
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', COLOR_BARRA[tema])
  oyentes.forEach((avisar) => avisar())
}

medio.addEventListener('change', () => preferencia === 'sistema' && aplicar())
aplicar()

export function cambiarTema(nueva) {
  preferencia = nueva
  try {
    localStorage.setItem(CLAVE, nueva)
  } catch {
    // Sin almacenamiento: el tema dura solo mientras la pestaña esté abierta
  }
  aplicar()
}

function suscribir(avisar) {
  oyentes.add(avisar)
  return () => oyentes.delete(avisar)
}

/** @returns {{preferencia: 'claro'|'oscuro'|'sistema', tema: 'claro'|'oscuro'}} */
export function useTema() {
  const estado = useSyncExternalStore(suscribir, () => `${preferencia}|${temaResuelto()}`)
  const [pref, tema] = estado.split('|')
  return { preferencia: pref, tema }
}
