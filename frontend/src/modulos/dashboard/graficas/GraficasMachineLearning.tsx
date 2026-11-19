// Gráficas de la sección Machine Learning (prácticas P04, P05 y P06).
// El color sigue al algoritmo en TODAS las gráficas: Árbol = azul, Random Forest = rojo, KNN = verde
// (orden categórico validado de estilo.ts). Los conjuntos de datos usan otros tonos para no confundirse.

import { Bar, BarChart, CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import LeyendaKompas from '../componentes/LeyendaKompas.tsx'
import TarjetaGrafica from '../componentes/TarjetaGrafica.tsx'
import TooltipKompas from '../componentes/TooltipKompas.tsx'
import { ALGORITMOS, nombreClase, ORDEN_ALGORITMOS, pct, REGIMENES } from '../catalogoML.ts'
import { COLOR, decimal, EJE, porcentaje, REJILLA } from '../estilo.ts'
import type { ClaveAlgoritmo, ClaveRegimen, ComparacionAlgoritmos, DiagnosticoAjuste, OptimizacionHiperparametros } from '../tiposML.ts'

const CONJUNTOS = {
  entrenamiento: { nombre: 'Entrenamiento (60 %)', color: COLOR.aviso },
  validacion: { nombre: 'Validación (20 %)', color: COLOR.detalle },
  prueba: { nombre: 'Prueba ciega (20 %)', color: COLOR.textoSuave },
}

const formatoPct = (v: number) => porcentaje(v)
const formatoMs = (v: number) => `${decimal(v)} ms`
const etiquetaProfundidad = (d: number | null) => (d === null ? 'Libre' : String(d))

const LEYENDA_ALGORITMOS = ORDEN_ALGORITMOS.map((c) => ({ nombre: ALGORITMOS[c].nombre, color: ALGORITMOS[c].color }))
const LEYENDA_CONJUNTOS = Object.values(CONJUNTOS)

// ───────────── P05: métricas de clasificación ─────────────

type FilaMetrica = { metrica: string } & Record<ClaveAlgoritmo, number>

/** Exactitud (validación y prueba), precisión, recall y F1 de los tres algoritmos lado a lado. */
export function GraficaMetricasAlgoritmos({ comparacion }: { comparacion: ComparacionAlgoritmos }) {
  const por = Object.fromEntries(comparacion.tabla_comparativa.map((f) => [f.clave, f])) as Record<ClaveAlgoritmo, ComparacionAlgoritmos['tabla_comparativa'][number]>
  const metricas: [string, (f: (typeof por)[ClaveAlgoritmo]) => number][] = [
    ['Exactitud val.', (f) => f.exactitud_validacion],
    ['Exactitud prueba', (f) => f.exactitud_prueba],
    ['Precisión', (f) => f.precision_prueba],
    ['Recall', (f) => f.recall_prueba],
    ['F1-score', (f) => f.f1_score_prueba],
  ]
  const filas: FilaMetrica[] = metricas.map(([metrica, valor]) => ({
    metrica,
    ...(Object.fromEntries(ORDEN_ALGORITMOS.map((c) => [c, por[c] ? pct(valor(por[c])) : 0])) as Record<ClaveAlgoritmo, number>),
  }))

  return (
    <TarjetaGrafica
      titulo="Árbol vs. Random Forest vs. KNN"
      descripcion="Exactitud en validación y en prueba ciega, y precisión, recall y F1 ponderados en prueba. Más alto es mejor."
      archivo="comparacion-algoritmos-ml"
      columnas={[
        { clave: 'metrica', titulo: 'Métrica' },
        ...ORDEN_ALGORITMOS.map((c) => ({ clave: c, titulo: ALGORITMOS[c].nombre, formato: formatoPct })),
      ]}
      filas={filas}
      alto="h-80"
    >
      <div className="flex h-full flex-col">
        <div className="min-h-0 flex-1">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={filas} margin={{ top: 8, right: 8, left: -12, bottom: 0 }} barGap={2} barCategoryGap="22%">
              <CartesianGrid {...REJILLA} />
              <XAxis dataKey="metrica" {...EJE} interval={0} tick={{ ...EJE.tick, fontSize: 11 }} />
              <YAxis domain={[0, 100]} unit="%" {...EJE} />
              <Tooltip content={<TooltipKompas formato={formatoPct} />} cursor={{ fill: COLOR.borde, fillOpacity: 0.35 }} />
              {ORDEN_ALGORITMOS.map((c) => (
                <Bar key={c} dataKey={c} name={ALGORITMOS[c].nombre} fill={ALGORITMOS[c].color} radius={[4, 4, 0, 0]} maxBarSize={28} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
        <LeyendaKompas items={LEYENDA_ALGORITMOS} />
      </div>
    </TarjetaGrafica>
  )
}

/** Costo de cómputo medido con time.perf_counter() en el backend. */
export function GraficaTiemposAlgoritmos({ comparacion }: { comparacion: ComparacionAlgoritmos }) {
  const por = Object.fromEntries(comparacion.tabla_comparativa.map((f) => [f.clave, f]))
  const filas = [
    { fase: 'Entrenamiento (96 traslados)', ...Object.fromEntries(ORDEN_ALGORITMOS.map((c) => [c, por[c]?.tiempo_entrenamiento_ms ?? 0])) },
    { fase: 'Predicción (32 traslados)', ...Object.fromEntries(ORDEN_ALGORITMOS.map((c) => [c, por[c]?.tiempo_inferencia_ms ?? 0])) },
  ] as ({ fase: string } & Record<ClaveAlgoritmo, number>)[]

  return (
    <TarjetaGrafica
      titulo="Tiempo de entrenamiento y de predicción"
      descripcion="Milisegundos en el servidor (cambian un poco en cada ejecución). Más bajo es mejor."
      archivo="tiempos-algoritmos-ml"
      columnas={[
        { clave: 'fase', titulo: 'Fase' },
        ...ORDEN_ALGORITMOS.map((c) => ({ clave: c, titulo: `${ALGORITMOS[c].nombre} (ms)`, formato: formatoMs })),
      ]}
      filas={filas}
      alto="h-80"
    >
      <div className="flex h-full flex-col">
        <div className="min-h-0 flex-1">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={filas} layout="vertical" margin={{ top: 8, right: 16, left: 8, bottom: 0 }} barGap={2} barCategoryGap="20%">
              <CartesianGrid {...REJILLA} vertical horizontal={false} />
              <XAxis type="number" unit=" ms" {...EJE} />
              <YAxis type="category" dataKey="fase" width={110} {...EJE} tick={{ ...EJE.tick, fontSize: 11 }} />
              <Tooltip content={<TooltipKompas formato={formatoMs} />} cursor={{ fill: COLOR.borde, fillOpacity: 0.35 }} />
              {ORDEN_ALGORITMOS.map((c) => (
                <Bar key={c} dataKey={c} name={ALGORITMOS[c].nombre} fill={ALGORITMOS[c].color} radius={[0, 4, 4, 0]} maxBarSize={22} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
        <LeyendaKompas items={LEYENDA_ALGORITMOS} />
      </div>
    </TarjetaGrafica>
  )
}

// ───────────── P04: overfitting vs. underfitting ─────────────

/**
 * Curva de complejidad: exactitud en entrenamiento, validación y prueba según la profundidad del árbol.
 * A la izquierda el árbol es demasiado simple; a la derecha memoriza el entrenamiento.
 */
export function GraficaCurvaComplejidad({ ajuste }: { ajuste: DiagnosticoAjuste }) {
  const filas = ajuste.curva_complejidad.map((p) => ({
    profundidad: etiquetaProfundidad(p.max_depth),
    profundidad_real: p.profundidad_real,
    entrenamiento: pct(p.exactitud_entrenamiento),
    validacion: pct(p.exactitud_validacion),
    prueba: pct(p.exactitud_prueba),
    brecha: Math.round((p.exactitud_entrenamiento - p.exactitud_prueba) * 1000) / 10,
  }))
  const minimo = Math.max(0, Math.floor((Math.min(...filas.flatMap((f) => [f.entrenamiento, f.validacion, f.prueba])) - 5) / 10) * 10)
  const tope = Math.max(...ajuste.curva_complejidad.map((p) => p.profundidad_real))
  const equilibrado = etiquetaProfundidad(ajuste.comparacion_modelos.ajuste_adecuado.max_depth)

  return (
    <TarjetaGrafica
      titulo="Overfitting vs. underfitting: curva de complejidad del árbol"
      descripcion={
        <>
          Exactitud según la profundidad máxima (<code>max_depth</code>). Izquierda: muy simple, no aprende ni el entrenamiento (subajuste). Derecha: el entrenamiento llega a 100 % pero la prueba deja de
          mejorar (sobreajuste). Con estos datos el árbol deja de crecer en profundidad {tope}.
        </>
      }
      archivo="curva-complejidad-arbol"
      columnas={[
        { clave: 'profundidad', titulo: 'max_depth' },
        { clave: 'profundidad_real', titulo: 'Profundidad real' },
        { clave: 'entrenamiento', titulo: 'Entrenamiento', formato: formatoPct },
        { clave: 'validacion', titulo: 'Validación', formato: formatoPct },
        { clave: 'prueba', titulo: 'Prueba', formato: formatoPct },
        { clave: 'brecha', titulo: 'Brecha entrenamiento − prueba (pts)', formato: (v: number) => decimal(v) },
      ]}
      filas={filas}
      alto="h-96"
    >
      <div className="flex h-full flex-col">
        <div className="flex justify-between px-10 text-xs font-medium text-texto-suave">
          <span>← más simple · riesgo de subajuste</span>
          <span>más complejo · riesgo de sobreajuste →</span>
        </div>
        <div className="min-h-0 flex-1">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={filas} margin={{ top: 16, right: 16, left: -12, bottom: 8 }}>
              <CartesianGrid {...REJILLA} />
              <XAxis
                dataKey="profundidad"
                {...EJE}
                label={{ value: 'Profundidad máxima del árbol', position: 'insideBottom', offset: -4, fill: COLOR.textoSuave, fontSize: 12 }}
              />
              <YAxis domain={[minimo, 100]} unit="%" {...EJE} />
              <ReferenceLine
                x={equilibrado}
                stroke={COLOR.textoSuave}
                strokeDasharray="4 4"
                label={{ value: `Árbol equilibrado (P04)`, position: 'insideBottomRight', fill: COLOR.textoSuave, fontSize: 11 }}
              />
              <Tooltip
                content={
                  <TooltipKompas
                    formato={formatoPct}
                    titulo={(t: string) => `max_depth = ${t}`}
                    extra={(f: (typeof filas)[number]) => `Profundidad real ${f.profundidad_real} · brecha entrenamiento − prueba: ${decimal(f.brecha)} pts`}
                  />
                }
                cursor={{ stroke: COLOR.borde }}
              />
              <Line type="linear" dataKey="entrenamiento" name={CONJUNTOS.entrenamiento.nombre} stroke={CONJUNTOS.entrenamiento.color} strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              <Line type="linear" dataKey="validacion" name={CONJUNTOS.validacion.nombre} stroke={CONJUNTOS.validacion.color} strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              <Line
                type="linear"
                dataKey="prueba"
                name={CONJUNTOS.prueba.nombre}
                stroke={CONJUNTOS.prueba.color}
                strokeWidth={2}
                strokeDasharray="6 3"
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <LeyendaKompas items={LEYENDA_CONJUNTOS} />
      </div>
    </TarjetaGrafica>
  )
}

/** Los tres árboles de P04 (profundidad 1, 4 y libre) en entrenamiento, validación y prueba. */
export function GraficaRegimenesAjuste({ ajuste }: { ajuste: DiagnosticoAjuste }) {
  const filas = (Object.keys(REGIMENES) as ClaveRegimen[]).map((clave) => {
    const m = ajuste.comparacion_modelos[clave]
    return {
      modelo: REGIMENES[clave].nombre,
      entrenamiento: pct(m.exactitud_entrenamiento),
      validacion: pct(m.exactitud_validacion),
      prueba: pct(m.exactitud_prueba),
      diagnostico: m.diagnostico.split(':')[0],
    }
  })

  return (
    <TarjetaGrafica
      titulo="Los tres árboles de la práctica 04"
      descripcion="Mismo algoritmo, distinta profundidad. Si entrenamiento es mucho mayor que validación/prueba hay sobreajuste; si los tres son bajos, subajuste."
      archivo="regimenes-ajuste-p04"
      columnas={[
        { clave: 'modelo', titulo: 'Árbol' },
        { clave: 'entrenamiento', titulo: 'Entrenamiento', formato: formatoPct },
        { clave: 'validacion', titulo: 'Validación', formato: formatoPct },
        { clave: 'prueba', titulo: 'Prueba', formato: formatoPct },
        { clave: 'diagnostico', titulo: 'Diagnóstico del backend' },
      ]}
      filas={filas}
      alto="h-80"
    >
      <div className="flex h-full flex-col">
        <div className="min-h-0 flex-1">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={filas} margin={{ top: 8, right: 8, left: -12, bottom: 0 }} barGap={2} barCategoryGap="24%">
              <CartesianGrid {...REJILLA} />
              <XAxis dataKey="modelo" {...EJE} />
              <YAxis domain={[0, 100]} unit="%" {...EJE} />
              <Tooltip
                content={<TooltipKompas formato={formatoPct} extra={(f: (typeof filas)[number]) => `Diagnóstico: ${f.diagnostico}`} />}
                cursor={{ fill: COLOR.borde, fillOpacity: 0.35 }}
              />
              {(['entrenamiento', 'validacion', 'prueba'] as const).map((k) => (
                <Bar key={k} dataKey={k} name={CONJUNTOS[k].nombre} fill={CONJUNTOS[k].color} radius={[4, 4, 0, 0]} maxBarSize={32} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
        <LeyendaKompas items={LEYENDA_CONJUNTOS} />
      </div>
    </TarjetaGrafica>
  )
}

// ───────────── Matrices de confusión ─────────────

/**
 * Filas = clase real, columnas = clase predicha. La intensidad es el % de la fila (recall por clase),
 * así la clase pequeña (caminando) se ve igual que las grandes. Un solo tono por matriz.
 */
export function MatrizConfusion({ titulo, color, etiquetas, matriz }: { titulo: string; color: string; etiquetas: string[]; matriz: number[][] }) {
  const total = matriz.flat().reduce((a, b) => a + b, 0)
  const aciertos = matriz.reduce((a, fila, i) => a + (fila[i] ?? 0), 0)
  return (
    <figure className="min-w-0">
      <figcaption className="mb-2 flex items-center justify-between gap-2 text-sm">
        <span className="flex items-center gap-2 font-semibold">
          <span aria-hidden="true" className="size-2.5 rounded-sm" style={{ background: color }} />
          {titulo}
        </span>
        <span className="tabular-nums text-texto-suave">
          {aciertos}/{total} aciertos
        </span>
      </figcaption>
      <div className="overflow-x-auto">
        <table className="w-full border-separate border-spacing-0.5 text-xs">
          <caption className="sr-only">Matriz de confusión de {titulo}: filas clase real, columnas clase predicha</caption>
          <thead>
            <tr>
              <th scope="col" className="p-1 text-left font-normal text-texto-suave">
                Real ↓ / Predicho →
              </th>
              {etiquetas.map((e) => (
                <th key={e} scope="col" className="p-1 font-medium text-texto-suave">
                  {nombreClase(e)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matriz.map((fila, i) => {
              const totalFila = fila.reduce((a, b) => a + b, 0) || 1
              return (
                <tr key={etiquetas[i]}>
                  <th scope="row" className="p-1 text-left font-medium text-texto-suave">
                    {nombreClase(etiquetas[i])}
                  </th>
                  {fila.map((v, j) => {
                    const mezcla = v === 0 ? 0 : Math.round(12 + (v / totalFila) * 58)
                    return (
                      <td
                        key={j}
                        title={`Real ${nombreClase(etiquetas[i])}, predicho ${nombreClase(etiquetas[j])}: ${v} (${Math.round((100 * v) / totalFila)} % de la fila)`}
                        className={`h-10 rounded-md text-center tabular-nums ${i === j ? 'outline outline-1 outline-texto/30' : ''}`}
                        style={{ background: v === 0 ? 'var(--color-fondo)' : `color-mix(in srgb, ${color} ${mezcla}%, var(--color-superficie))` }}
                      >
                        <span className="rounded bg-superficie/85 px-1.5 py-0.5 font-semibold text-texto">{v}</span>
                      </td>
                    )
                  })}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </figure>
  )
}

// ───────────── P06: validación cruzada ─────────────

/** Exactitud de los mejores hiperparámetros en cada uno de los 5 pliegues (StratifiedKFold). */
export function GraficaPliegues({ optimizacion }: { optimizacion: OptimizacionHiperparametros }) {
  const { arbol_decision: arbol, bosque_aleatorio: bosque } = optimizacion.resultados_por_algoritmo
  const filas = arbol.puntajes_por_pliegue.map((v, i) => ({
    pliegue: `Pliegue ${i + 1}`,
    decision_tree: pct(v),
    random_forest: pct(bosque.puntajes_por_pliegue[i] ?? 0),
  }))
  const minimo = Math.max(0, Math.floor((Math.min(...filas.flatMap((f) => [f.decision_tree, f.random_forest])) - 5) / 5) * 5)
  const series = [
    { clave: 'decision_tree' as const, media: pct(arbol.exactitud_media_cv) },
    { clave: 'random_forest' as const, media: pct(bosque.exactitud_media_cv) },
  ]

  return (
    <TarjetaGrafica
      titulo="Validación cruzada con 5 pliegues (P06)"
      descripcion="Exactitud de la mejor configuración de cada algoritmo en cada pliegue. Las líneas punteadas son la media; menos variación entre pliegues = modelo más estable."
      archivo="validacion-cruzada-p06"
      columnas={[
        { clave: 'pliegue', titulo: 'Pliegue' },
        { clave: 'decision_tree', titulo: ALGORITMOS.decision_tree.nombre, formato: formatoPct },
        { clave: 'random_forest', titulo: ALGORITMOS.random_forest.nombre, formato: formatoPct },
      ]}
      filas={filas}
      alto="h-80"
    >
      <div className="flex h-full flex-col">
        <div className="min-h-0 flex-1">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={filas} margin={{ top: 12, right: 16, left: -12, bottom: 0 }}>
              <CartesianGrid {...REJILLA} />
              <XAxis dataKey="pliegue" {...EJE} />
              <YAxis domain={[minimo, 100]} unit="%" {...EJE} />
              {series.map((s) => (
                <ReferenceLine key={s.clave} y={s.media} stroke={ALGORITMOS[s.clave].color} strokeDasharray="4 4" strokeOpacity={0.7} />
              ))}
              <Tooltip content={<TooltipKompas formato={formatoPct} />} cursor={{ stroke: COLOR.borde }} />
              {series.map((s) => (
                <Line
                  key={s.clave}
                  type="linear"
                  dataKey={s.clave}
                  name={ALGORITMOS[s.clave].nombre}
                  stroke={ALGORITMOS[s.clave].color}
                  strokeWidth={2}
                  dot={{ r: 4, stroke: COLOR.superficie, strokeWidth: 2, fill: ALGORITMOS[s.clave].color }}
                  activeDot={{ r: 6 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
        <LeyendaKompas items={series.map((s) => ({ nombre: ALGORITMOS[s.clave].nombre, color: ALGORITMOS[s.clave].color }))} />
      </div>
    </TarjetaGrafica>
  )
}
