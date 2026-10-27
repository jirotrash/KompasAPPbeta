import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import EtiquetaPie from '../componentes/EtiquetaPie.tsx'
import TarjetaGrafica from '../componentes/TarjetaGrafica.tsx'
import TooltipKompas from '../componentes/TooltipKompas.tsx'
import { CATEGORICO, COLOR, EJE, etiquetaNumero, fechaCorta, numero, REJILLA } from '../estilo.ts'
import type { Asistente } from '../tipos.ts'

const HERRAMIENTAS: Record<string, string> = {
  como_llegar: '¿Cómo llego?',
  buscar_lugares: 'Buscar lugares',
  armar_salida: 'Armar una salida',
  mis_planes: 'Mis planes',
}
const ORIGENES = {
  planificador: { nombre: 'Planificador', color: CATEGORICO[0] },
  asistente: { nombre: 'Asistente', color: CATEGORICO[1] },
}

/** Conversaciones nuevas y mensajes de los usuarios por día (ambos son conteos: un solo eje). */
export function GraficaUsoAsistente({ asistente }: { asistente: Asistente }) {
  const filas = asistente.por_dia
  return (
    <TarjetaGrafica
      titulo="Conversaciones y mensajes por día"
      descripcion="Conversaciones creadas y mensajes escritos por los usuarios. No se muestra el contenido de los mensajes."
      archivo="asistente-por-dia"
      columnas={[
        { clave: 'fecha', titulo: 'Día' },
        { clave: 'conversaciones', titulo: 'Conversaciones', formato: numero },
        { clave: 'mensajes', titulo: 'Mensajes', formato: numero },
      ]}
      filas={filas}
      vacio={filas.every((f) => !f.conversaciones && !f.mensajes)}
      alto="h-80"
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={filas} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
          <CartesianGrid {...REJILLA} />
          <XAxis dataKey="fecha" tickFormatter={fechaCorta} {...EJE} minTickGap={24} />
          <YAxis allowDecimals={false} {...EJE} />
          <Tooltip content={<TooltipKompas titulo={(l: string) => fechaCorta(l)} formato={numero} />} cursor={{ stroke: COLOR.textoSuave, strokeDasharray: '3 3' }} />
          <Legend iconType="plainline" wrapperStyle={{ fontSize: 12, color: COLOR.textoSuave }} />
          <Line type="monotone" dataKey="mensajes" name="Mensajes" stroke={CATEGORICO[0]} strokeWidth={2} dot={false} activeDot={{ r: 5, stroke: COLOR.superficie, strokeWidth: 2 }} />
          <Line type="monotone" dataKey="conversaciones" name="Conversaciones" stroke={CATEGORICO[1]} strokeWidth={2} dot={false} activeDot={{ r: 5, stroke: COLOR.superficie, strokeWidth: 2 }} />
        </LineChart>
      </ResponsiveContainer>
    </TarjetaGrafica>
  )
}

/** Herramientas que más llama el modelo. */
export function GraficaHerramientas({ asistente }: { asistente: Asistente }) {
  const filas = asistente.herramientas.map((h) => ({ ...h, nombre: HERRAMIENTAS[h.herramienta] ?? h.herramienta }))
  return (
    <TarjetaGrafica
      titulo="Herramientas más usadas"
      descripcion="Veces que el asistente consultó cada función de Kompás para responder."
      archivo="asistente-herramientas"
      columnas={[
        { clave: 'nombre', titulo: 'Herramienta' },
        { clave: 'total', titulo: 'Llamadas', formato: numero },
      ]}
      filas={filas}
      vacio={filas.every((f) => !f.total)}
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={filas} layout="vertical" margin={{ top: 4, right: 36, left: 8, bottom: 0 }}>
          <CartesianGrid {...REJILLA} horizontal={false} vertical />
          <XAxis type="number" allowDecimals={false} {...EJE} />
          <YAxis type="category" dataKey="nombre" width={120} {...EJE} />
          <Tooltip content={<TooltipKompas formato={numero} />} cursor={{ fill: 'var(--color-fondo)' }} />
          <Bar dataKey="total" name="Llamadas" fill={COLOR.primario} radius={[0, 4, 4, 0]} maxBarSize={24} label={{ position: 'right', fill: COLOR.texto, fontSize: 11, formatter: etiquetaNumero }} />
        </BarChart>
      </ResponsiveContainer>
    </TarjetaGrafica>
  )
}

/** Planes creados desde el asistente contra los del planificador (dona). */
export function GraficaOrigenPlanes({ asistente }: { asistente: Asistente }) {
  const filas = asistente.planes_por_origen.map((f) => ({ ...f, nombre: ORIGENES[f.origen].nombre }))
  return (
    <TarjetaGrafica
      titulo="¿Desde dónde se crean los planes?"
      descripcion="Planes guardados desde la pantalla Planificar o pedidos al asistente."
      archivo="planes-por-origen"
      columnas={[
        { clave: 'nombre', titulo: 'Origen' },
        { clave: 'total', titulo: 'Planes', formato: numero },
      ]}
      filas={filas}
      vacio={filas.every((f) => !f.total)}
    >
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={filas}
            dataKey="total"
            nameKey="nombre"
            innerRadius="55%"
            outerRadius="78%"
            paddingAngle={1}
            stroke={COLOR.superficie}
            strokeWidth={2}
            label={<EtiquetaPie />}
            labelLine={false}
          >
            {filas.map((f) => (
              <Cell key={f.origen} fill={ORIGENES[f.origen].color} />
            ))}
          </Pie>
          <Tooltip content={<TooltipKompas formato={numero} />} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
        </PieChart>
      </ResponsiveContainer>
    </TarjetaGrafica>
  )
}
