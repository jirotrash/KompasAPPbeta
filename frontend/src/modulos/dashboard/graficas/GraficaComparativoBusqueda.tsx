import { useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { MensajeError } from '../../../compartido/componentes/Avisos.tsx'
import { compararBusqueda, obtenerParadasRed } from '../api.ts'
import TarjetaGrafica from '../componentes/TarjetaGrafica.tsx'
import TooltipKompas from '../componentes/TooltipKompas.tsx'
import { CATEGORICO, COLOR, decimal, EJE, numero, REJILLA } from '../estilo.ts'
import type { ComparativoBusqueda, FilaComparativo, ParadaRed } from '../tipos.ts'

// Barras agrupadas: familia de algoritmo en el eje X, una barra por heurística (color fijo por heurística)
const FAMILIAS = [
  { algoritmo: 'dfs', nombre: 'DFS' },
  { algoritmo: 'costo_uniforme', nombre: 'UCS' },
  { algoritmo: 'voraz', nombre: 'Voraz' },
  { algoritmo: 'a_estrella', nombre: 'A*' },
]
const HEURISTICAS = [
  { clave: 'sin', nombre: 'Sin heurística', color: CATEGORICO[0] },
  { clave: 'euclidiana', nombre: 'Euclidiana', color: CATEGORICO[1] },
  { clave: 'manhattan', nombre: 'Manhattan', color: CATEGORICO[3] },
] as const

const etiqueta = (f: FilaComparativo) =>
  `${FAMILIAS.find((x) => x.algoritmo === f.algoritmo)?.nombre ?? f.nombre}${f.heuristica ? ` (${f.heuristica})` : ''}`

/** Nodos explorados por algoritmo para un par de la red académica (GET /api/busqueda/comparar). */
export default function GraficaComparativoBusqueda() {
  const [paradas, setParadas] = useState<ParadaRed[]>([])
  const [par, setPar] = useState({ origen: 'TerminalToluca', destino: 'PlazaSendero' })
  const [resultado, setResultado] = useState<{ para: string; datos: ComparativoBusqueda | null; error: string } | null>(null)
  const clave = `${par.origen}|${par.destino}`

  useEffect(() => {
    obtenerParadasRed()
      .then(setParadas)
      .catch(() => setParadas([]))
  }, [])

  useEffect(() => {
    let vigente = true
    compararBusqueda(par.origen, par.destino)
      .then((datos) => vigente && setResultado({ para: clave, datos, error: '' }))
      .catch((e: unknown) => vigente && setResultado({ para: clave, datos: null, error: e instanceof Error ? e.message : String(e) }))
    return () => {
      vigente = false
    }
  }, [par, clave])

  const datos = resultado?.para === clave ? resultado.datos : null
  const filas = (datos?.filas ?? []).map((f) => ({ ...f, etiqueta: etiqueta(f), optimoTexto: f.optimo ? 'Sí' : 'No' }))
  const grupos = FAMILIAS.map((familia) => {
    const fila: Record<string, string | number | null> = { familia: familia.nombre }
    for (const h of HEURISTICAS) {
      const f = filas.find((x) => x.algoritmo === familia.algoritmo && (x.heuristica ?? 'sin') === h.clave)
      fila[h.clave] = f ? f.nodos_explorados : null
    }
    return fila
  })

  return (
    <TarjetaGrafica
      titulo="Nodos explorados por algoritmo"
      descripcion={
        <>
          Red académica del DFS (sin verificación operativa). Óptimo = mismo costo que UCS
          {datos?.costo_optimo_km != null && ` (${decimal(datos.costo_optimo_km)} km)`}. A* con Manhattan puede no ser óptimo porque la
          heurística no es admisible.
        </>
      }
      archivo="comparativo-busqueda"
      columnas={[
        { clave: 'etiqueta', titulo: 'Algoritmo' },
        { clave: 'costo_km', titulo: 'Costo (km)', formato: decimal },
        { clave: 'nodos_explorados', titulo: 'Nodos explorados', formato: numero },
        { clave: 'longitud_camino', titulo: 'Aristas del camino', formato: numero },
        { clave: 'optimoTexto', titulo: '¿Óptimo?' },
        { clave: 'ms', titulo: 'ms', formato: decimal },
      ]}
      filas={filas}
      vacio={!filas.length}
      alto="h-80"
    >
      <div className="flex h-full flex-col gap-2">
        <div className="flex flex-wrap gap-2">
          {(['origen', 'destino'] as const).map((campo) => (
            <label key={campo} className="min-w-40 flex-1">
              <span className="sr-only">{campo === 'origen' ? 'Origen' : 'Destino'}</span>
              <select className="campo py-1 text-sm" value={par[campo]} onChange={(e) => setPar({ ...par, [campo]: e.target.value })}>
                {paradas.map((p) => (
                  <option key={p.id} value={p.id}>
                    {campo === 'origen' ? 'Desde' : 'Hasta'}: {p.nombre}
                  </option>
                ))}
              </select>
            </label>
          ))}
        </div>
        {resultado?.error && <MensajeError>{resultado.error}</MensajeError>}
        <div className="min-h-0 flex-1">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={grupos} margin={{ top: 8, right: 8, left: -12, bottom: 0 }} barGap={2}>
              <CartesianGrid {...REJILLA} />
              <XAxis dataKey="familia" {...EJE} />
              <YAxis allowDecimals={false} {...EJE} />
              <Tooltip content={<TooltipKompas formato={numero} />} cursor={{ fill: 'var(--color-fondo)' }} />
              <Legend wrapperStyle={{ fontSize: 12, color: COLOR.textoSuave }} />
              {HEURISTICAS.map((h) => (
                <Bar key={h.clave} dataKey={h.clave} name={h.nombre} fill={h.color} radius={[4, 4, 0, 0]} maxBarSize={36} stroke={COLOR.superficie} strokeWidth={2} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </TarjetaGrafica>
  )
}
