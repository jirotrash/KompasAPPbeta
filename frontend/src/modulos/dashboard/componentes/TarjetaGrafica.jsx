import { useId, useState } from 'react'
import { IconoDescargar, IconoTabla } from '../../../compartido/componentes/Iconos.jsx'

/** CSV con los mismos datos de la gráfica (se arma en el navegador; no calcula nada nuevo). */
function descargarCsv(nombre, columnas, filas) {
  const celda = (v) => {
    const texto = v === null || v === undefined ? '' : String(v)
    return /[",\n;]/.test(texto) ? `"${texto.replace(/"/g, '""')}"` : texto
  }
  const lineas = [columnas.map((c) => celda(c.titulo)).join(','), ...filas.map((f) => columnas.map((c) => celda(f[c.clave])).join(','))]
  // BOM para que Excel abra bien los acentos
  const blob = new Blob(['﻿' + lineas.join('\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = `${nombre}.csv`
  enlace.click()
  URL.revokeObjectURL(url)
}

/**
 * Marco común de cada gráfica: título, qué se ve, estado vacío, "Ver como tabla" (alternativa accesible)
 * y "Descargar CSV".
 * @param {{
 *   titulo: string, descripcion: string, archivo: string,
 *   columnas: Array<{clave: string, titulo: string, formato?: (v) => string}>,
 *   filas: Array<object>, vacio?: boolean, alto?: string, className?: string, children: React.ReactNode
 * }} props
 */
export default function TarjetaGrafica({ titulo, descripcion, archivo, columnas, filas, vacio, alto = 'h-72', className = '', children }) {
  const [verTabla, setVerTabla] = useState(false)
  const idTitulo = useId()

  return (
    <section aria-labelledby={idTitulo} className={`tarjeta flex min-w-0 flex-col gap-3 ${className}`}>
      <header className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 id={idTitulo} className="font-semibold leading-tight tracking-tight">
            {titulo}
          </h3>
          <p className="mt-0.5 text-sm text-texto-suave">{descripcion}</p>
        </div>
        {!vacio && (
          <div className="flex shrink-0 gap-1">
            <button
              type="button"
              onClick={() => setVerTabla((v) => !v)}
              aria-pressed={verTabla}
              aria-label={verTabla ? `Ver gráfica: ${titulo}` : `Ver como tabla: ${titulo}`}
              title={verTabla ? 'Ver gráfica' : 'Ver como tabla'}
              className={`grid size-9 place-items-center rounded-lg border transition ${
                verTabla ? 'border-primario bg-primario-claro text-primario-oscuro' : 'border-borde text-texto-suave hover:bg-fondo hover:text-texto'
              }`}
            >
              <IconoTabla className="size-4" />
            </button>
            <button
              type="button"
              onClick={() => descargarCsv(archivo, columnas, filas)}
              aria-label={`Descargar CSV: ${titulo}`}
              title="Descargar CSV"
              className="grid size-9 place-items-center rounded-lg border border-borde text-texto-suave transition hover:bg-fondo hover:text-texto"
            >
              <IconoDescargar className="size-4" />
            </button>
          </div>
        )}
      </header>

      {vacio ? (
        <div className={`grid place-items-center rounded-xl border border-dashed border-borde text-sm text-texto-suave ${alto}`}>
          Sin datos en este periodo
        </div>
      ) : verTabla ? (
        <div className={`overflow-auto rounded-xl border border-borde ${alto}`}>
          <table className="w-full text-left text-sm">
            <caption className="sr-only">{titulo}</caption>
            <thead className="sticky top-0 bg-superficie">
              <tr>
                {columnas.map((c) => (
                  <th key={c.clave} scope="col" className="border-b border-borde px-3 py-2 font-semibold">
                    {c.titulo}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filas.map((f, i) => (
                <tr key={i} className="border-b border-borde last:border-0">
                  {columnas.map((c) => (
                    <td key={c.clave} className="px-3 py-1.5 tabular-nums">
                      {c.formato ? c.formato(f[c.clave], f) : f[c.clave]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className={`min-w-0 ${alto}`}>{children}</div>
      )}
    </section>
  )
}
