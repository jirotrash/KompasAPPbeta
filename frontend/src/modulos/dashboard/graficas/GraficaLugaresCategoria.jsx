import { ResponsiveContainer, Tooltip, Treemap } from 'recharts'
import TarjetaGrafica from '../componentes/TarjetaGrafica.jsx'
import TooltipKompas from '../componentes/TooltipKompas.jsx'
import { CATEGORIAS_LUGAR, COLOR, numero } from '../estilo.js'

function Celda({ x, y, width, height, name, value, fill }) {
  if (!width || !height) return null
  return (
    <g>
      <rect x={x} y={y} width={width} height={height} rx={4} fill={fill} stroke={COLOR.superficie} strokeWidth={2} />
      {width > 36 && height > 36 && (
        // Texto blanco con contorno oscuro: legible sobre cualquier color del logo
        <text x={x + 8} y={y + 20} fill="#fff" stroke="rgb(0 0 0 / .35)" strokeWidth={3} paintOrder="stroke" fontSize={13} fontWeight={600}>
          {width > 130 ? `${name} · ${numero(value)}` : numero(value)}
        </text>
      )}
    </g>
  )
}

/** #18 Lugares por categoría (treemap: el área es proporcional al número de lugares). */
export default function GraficaLugaresCategoria({ lugares }) {
  const filas = lugares.por_categoria.map((f) => ({ name: f.categoria, size: f.total, fill: CATEGORIAS_LUGAR[f.categoria] ?? COLOR.textoSuave, ...f }))
  return (
    <TarjetaGrafica
      titulo="Lugares por categoría"
      descripcion="Lugares registrados en la base; el tamaño de cada bloque es proporcional a cuántos hay."
      archivo="lugares-por-categoria"
      columnas={[
        { clave: 'categoria', titulo: 'Categoría' },
        { clave: 'total', titulo: 'Lugares', formato: numero },
      ]}
      filas={filas}
      vacio={!filas.length}
    >
      <ResponsiveContainer width="100%" height="100%">
        <Treemap data={filas} dataKey="size" nameKey="name" content={<Celda />} isAnimationActive={false}>
          <Tooltip content={<TooltipKompas formato={numero} titulo={() => 'Lugares'} />} />
        </Treemap>
      </ResponsiveContainer>
    </TarjetaGrafica>
  )
}
