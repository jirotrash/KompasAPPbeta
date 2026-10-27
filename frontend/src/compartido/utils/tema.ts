// Tema claro/oscuro. La preferencia se guarda en el navegador y puede ser
// 'claro', 'oscuro' o 'sistema' (sigue la configuración del dispositivo).
// El script en línea de index.html aplica el tema antes de pintar para evitar parpadeos;
// si cambias CLAVE aquí, cámbiala también allá.

import { useSyncExternalStore } from 'react'

export type Tema = 'claro' | 'oscuro'
export type PreferenciaTema = Tema | 'sistema'

const CLAVE = 'bu_tema'
// Barra del navegador con los colores de COLORIMETRIA.md (primario en claro, fondo base en oscuro)
const COLOR_BARRA: Record<Tema, string> = { claro: '#1A62A5', oscuro: '#0E1420' }
const medio = window.matchMedia('(prefers-color-scheme: dark)')
const oyentes = new Set<() => void>()

const esPreferencia = (valor: string | null): valor is PreferenciaTema => valor === 'claro' || valor === 'oscuro' || valor === 'sistema'

function leerPreferencia(): PreferenciaTema {
  try {
    const valor = localStorage.getItem(CLAVE)
    return esPreferencia(valor) ? valor : 'sistema'
  } catch {
    return 'sistema'
  }
}

let preferencia = leerPreferencia()

const temaResuelto = (): Tema => (preferencia === 'sistema' ? (medio.matches ? 'oscuro' : 'claro') : preferencia)

function aplicar() {
  const tema = temaResuelto()
  document.documentElement.dataset.tema = tema
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', COLOR_BARRA[tema])
  oyentes.forEach((avisar) => avisar())
}

medio.addEventListener('change', () => preferencia === 'sistema' && aplicar())
aplicar()

export function cambiarTema(nueva: PreferenciaTema) {
  preferencia = nueva
  try {
    localStorage.setItem(CLAVE, nueva)
  } catch {
    // Sin almacenamiento: el tema dura solo mientras la pestaña esté abierta
  }
  aplicar()
}

function suscribir(avisar: () => void) {
  oyentes.add(avisar)
  return () => {
    oyentes.delete(avisar)
  }
}

export function useTema(): { preferencia: PreferenciaTema; tema: Tema } {
  const estado = useSyncExternalStore(suscribir, () => `${preferencia}|${temaResuelto()}`)
  const [pref, tema] = estado.split('|') as [PreferenciaTema, Tema]
  return { preferencia: pref, tema }
}
