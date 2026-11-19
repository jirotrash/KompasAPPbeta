// Sección "Machine Learning" del dashboard: prácticas P04 (partición 60/20/20 y diagnóstico de ajuste),
// P05 (Árbol de decisión vs. Random Forest vs. KNN) y P06 (GridSearchCV con 5 pliegues).
// No usa los filtros de fecha: los modelos se entrenan en el backend sobre el CSV limpio del pipeline.

import type { ReactNode } from 'react'
import { USA_MOCK } from '../../../compartido/api/cliente.ts'
import { EtiquetaEjemplo, MensajeError } from '../../../compartido/componentes/Avisos.tsx'
import { IconoCerebro, IconoMatraz, IconoReloj, IconoTabla } from '../../../compartido/componentes/Iconos.tsx'
import TarjetaKpi, { EsqueletoKpi } from '../componentes/TarjetaKpi.tsx'
import { decimal, numero, porcentaje } from '../estilo.ts'
import useMachineLearning from '../hooks/useMachineLearning.ts'
import type { ClaveRegimen, ComparacionAlgoritmos, DiagnosticoAjuste, OptimizacionHiperparametros } from '../tiposML.ts'
import { ALGORITMOS, nombreClase, ORDEN_ALGORITMOS, pct, REGIMENES } from '../catalogoML.ts'
import {
  GraficaCurvaComplejidad,
  GraficaMetricasAlgoritmos,
  GraficaPliegues,
  GraficaRegimenesAjuste,
  GraficaTiemposAlgoritmos,
  MatrizConfusion,
} from './GraficasMachineLearning.tsx'

const NOMBRE_SKLEARN: Record<string, string> = {
  DecisionTreeClassifier: ALGORITMOS.decision_tree.nombre,
  RandomForestClassifier: ALGORITMOS.random_forest.nombre,
}

const hiperparametros = (h: Record<string, string | number | null>) =>
  Object.entries(h)
    .map(([k, v]) => `${k}=${v === null ? 'None' : v}`)
    .join(', ')

function Tarjeta({ titulo, descripcion, children, className = '' }: { titulo: string; descripcion?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`tarjeta flex min-w-0 flex-col gap-3 ${className}`}>
      <header>
        <h3 className="font-semibold leading-tight tracking-tight">{titulo}</h3>
        {descripcion && <p className="mt-0.5 text-sm text-texto-suave">{descripcion}</p>}
      </header>
      {children}
    </section>
  )
}

// ───────────── Bloques ─────────────

/** Qué se predice y cómo se reparten los datos (P04). */
function Planteamiento({ ajuste, comparacion }: { ajuste: DiagnosticoAjuste; comparacion: ComparacionAlgoritmos }) {
  const d = ajuste.distribucion_datos
  const partes = [
    { nombre: 'Entrenamiento', n: d.entrenamiento_60, clase: 'bg-aviso', uso: 'El modelo aprende aquí.' },
    { nombre: 'Validación', n: d.validacion_20, clase: 'bg-detalle', uso: 'Se elige el mejor modelo / profundidad.' },
    { nombre: 'Prueba ciega', n: d.prueba_20, clase: 'bg-texto-suave', uso: 'Solo se usa al final, para la nota honesta.' },
  ]
  return (
    <Tarjeta
      titulo="¿Qué se está comparando?"
      descripcion={
        <>
          Los tres algoritmos predicen el <strong className="text-texto">modo de transporte</strong> de un traslado (
          {comparacion.etiquetas_clases.map(nombreClase).join(', ')}) a partir de distancia, hora, hora pico, presupuesto, lluvia y calificación del destino. Todos usan la misma partición
          estratificada (<code>train_test_split</code> en dos pasos: 20 % para prueba y luego 25 % del resto para validación).
        </>
      }
    >
      <div className="flex h-9 w-full overflow-hidden rounded-lg" role="img" aria-label={`Partición: ${partes.map((p) => `${p.nombre} ${p.n}`).join(', ')} de ${d.total_registros} traslados`}>
        {partes.map((p) => (
          <div key={p.nombre} className={`${p.clase} flex items-center justify-center border-r-2 border-superficie last:border-r-0`} style={{ width: `${(100 * p.n) / d.total_registros}%` }}>
            <span className="rounded bg-superficie/85 px-1.5 text-xs font-semibold tabular-nums text-texto">{p.n}</span>
          </div>
        ))}
      </div>
      <ul className="grid gap-2 text-sm sm:grid-cols-3">
        {partes.map((p) => (
          <li key={p.nombre} className="flex gap-2">
            <span aria-hidden="true" className={`mt-1 size-2.5 shrink-0 rounded-sm ${p.clase}`} />
            <span>
              <strong>
                {p.nombre}: {numero(p.n)} ({Math.round((100 * p.n) / d.total_registros)} %)
              </strong>
              <span className="block text-texto-suave">{p.uso}</span>
            </span>
          </li>
        ))}
      </ul>
    </Tarjeta>
  )
}

/** Una tarjeta por algoritmo: cómo funciona (docstrings de P05), configuración y sus números. */
function TarjetasAlgoritmos({ comparacion }: { comparacion: ComparacionAlgoritmos }) {
  const ganador = comparacion.algoritmo_ganador.clave
  return (
    <div className="grid gap-4 lg:grid-cols-3 [&>*]:min-w-0">
      {ORDEN_ALGORITMOS.map((clave) => {
        const meta = ALGORITMOS[clave]
        const fila = comparacion.tabla_comparativa.find((f) => f.clave === clave)
        if (!fila) return null
        return (
          <article key={clave} className="tarjeta flex flex-col gap-3 border-t-4" style={{ borderTopColor: meta.color }}>
            <header className="flex items-start justify-between gap-2">
              <div>
                <h3 className="font-semibold">{meta.nombre}</h3>
                <code className="mt-0.5 block break-all text-xs text-texto-suave">{meta.configuracion}</code>
              </div>
              {clave === ganador && <span className="shrink-0 rounded-full bg-ok-fondo px-2 py-0.5 text-xs font-semibold text-ok">Ganador P05</span>}
            </header>
            <p className="text-sm">{meta.comoFunciona}</p>
            <dl className="grid grid-cols-2 gap-2 text-sm">
              {[
                ['Validación', porcentaje(pct(fila.exactitud_validacion))],
                ['Prueba', porcentaje(pct(fila.exactitud_prueba))],
                ['F1 ponderado', porcentaje(pct(fila.f1_score_prueba))],
                ['Predicción', `${decimal(fila.tiempo_inferencia_ms)} ms`],
              ].map(([t, v]) => (
                <div key={t} className="rounded-lg bg-fondo px-2.5 py-1.5">
                  <dt className="text-xs text-texto-suave">{t}</dt>
                  <dd className="font-semibold tabular-nums">{v}</dd>
                </div>
              ))}
            </dl>
            <ul className="mt-auto space-y-1 text-xs text-texto-suave">
              <li>
                <strong className="text-ok">+</strong> {meta.ventaja}
              </li>
              <li>
                <strong className="text-peligro">−</strong> {meta.riesgo}
              </li>
            </ul>
          </article>
        )
      })}
    </div>
  )
}

/** Diagnóstico que calcula el backend para cada árbol de P04, más la brecha entrenamiento − prueba. */
function DiagnosticoArboles({ ajuste }: { ajuste: DiagnosticoAjuste }) {
  const seleccionado = ajuste.modelo_seleccionado.clave
  return (
    <Tarjeta
      titulo="Diagnóstico de cada árbol"
      descripcion="Regla del backend: subajuste si entrenamiento y validación < 70 %; sobreajuste si entrenamiento > 95 % y la brecha con validación > 8 puntos."
    >
      <ul className="grid gap-2">
        {(Object.keys(REGIMENES) as ClaveRegimen[]).map((clave) => {
          const m = ajuste.comparacion_modelos[clave]
          const [titulo, explicacion] = m.diagnostico.split(':')
          const brechaPrueba = (m.exactitud_entrenamiento - m.exactitud_prueba) * 100
          return (
            <li key={clave} className="rounded-xl border border-borde p-3 text-sm">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <strong>
                  {REGIMENES[clave].nombre} <span className="font-normal text-texto-suave">· {REGIMENES[clave].escenario.toLowerCase()}</span>
                </strong>
                {clave === seleccionado && <span className="rounded-full bg-primario-claro px-2 py-0.5 text-xs font-semibold text-primario">Elegido por validación</span>}
              </div>
              <p className="mt-1">
                <strong>{titulo}</strong>
                {explicacion && <span className="text-texto-suave">:{explicacion}</span>}
              </p>
              <p className="mt-1 text-xs tabular-nums text-texto-suave">
                Brecha entrenamiento − validación: {decimal(m.brecha_train_val * 100)} pts · entrenamiento − prueba: {decimal(brechaPrueba)} pts
              </p>
            </li>
          )
        })}
      </ul>
    </Tarjeta>
  )
}

function Matrices({ comparacion }: { comparacion: ComparacionAlgoritmos }) {
  return (
    <Tarjeta
      titulo="Matrices de confusión en la prueba ciega"
      descripcion="Filas: modo real; columnas: modo que predijo el modelo. La diagonal (recuadrada) son los aciertos; todo lo demás son confusiones. La intensidad es el % de cada fila."
    >
      <div className="grid gap-5 lg:grid-cols-3 [&>*]:min-w-0">
        {ORDEN_ALGORITMOS.map((clave) => {
          const fila = comparacion.tabla_comparativa.find((f) => f.clave === clave)
          return fila?.matriz_confusion_prueba ? (
            <MatrizConfusion key={clave} titulo={ALGORITMOS[clave].nombre} color={ALGORITMOS[clave].color} etiquetas={comparacion.etiquetas_clases} matriz={fila.matriz_confusion_prueba} />
          ) : null
        })}
      </div>
    </Tarjeta>
  )
}

function Hiperparametros({ optimizacion }: { optimizacion: OptimizacionHiperparametros }) {
  const r = optimizacion.recomendacion_para_produccion
  const resultados = [optimizacion.resultados_por_algoritmo.arbol_decision, optimizacion.resultados_por_algoritmo.bosque_aleatorio]
  return (
    <Tarjeta
      titulo="Búsqueda de hiperparámetros (GridSearchCV)"
      descripcion="En vez de fijar max_depth o n_estimators a mano, se prueban todas las combinaciones de una rejilla y cada una se califica con validación cruzada estratificada de 5 pliegues."
    >
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-borde text-texto-suave">
              <th scope="col" className="py-1.5 pr-3 font-medium">Algoritmo</th>
              <th scope="col" className="py-1.5 pr-3 font-medium">Combinaciones</th>
              <th scope="col" className="py-1.5 pr-3 font-medium">Mejores hiperparámetros</th>
              <th scope="col" className="py-1.5 font-medium">Exactitud CV</th>
            </tr>
          </thead>
          <tbody>
            {resultados.map((res) => (
              <tr key={res.algoritmo} className="border-b border-borde last:border-0 align-top">
                <th scope="row" className="py-2 pr-3 font-semibold">{NOMBRE_SKLEARN[res.algoritmo] ?? res.algoritmo}</th>
                <td className="py-2 pr-3 tabular-nums">{numero(res.total_combinaciones_probadas)}</td>
                <td className="py-2 pr-3">
                  <code className="text-xs">{hiperparametros(res.mejores_hiperparametros)}</code>
                </td>
                <td className="py-2 tabular-nums">
                  {porcentaje(pct(res.exactitud_media_cv))} <span className="text-texto-suave">± {decimal(pct(res.desviacion_estandar_cv))}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="rounded-xl bg-fondo p-3 text-sm">
        <strong>Recomendación para producción:</strong> {NOMBRE_SKLEARN[r.algoritmo] ?? r.algoritmo} con <code className="text-xs">{hiperparametros(r.hiperparametros_optimos)}</code>: exactitud esperada{' '}
        {porcentaje(pct(r.exactitud_esperada))} ± {decimal(pct(r.estabilidad_desviacion))} pts. Ante un empate en la media, el backend prefiere el bosque (su desviación entre pliegues suele ser menor).
      </p>
      <p className="text-xs text-texto-suave">KNN no entra en P06: la práctica solo afina los dos modelos basados en árboles.</p>
    </Tarjeta>
  )
}

/** Conclusiones calculadas con los números de esta corrida (no son textos fijos). */
function Conclusiones({ ajuste, comparacion }: { ajuste: DiagnosticoAjuste; comparacion: ComparacionAlgoritmos }) {
  const por = Object.fromEntries(comparacion.tabla_comparativa.map((f) => [f.clave, f]))
  const ganador = por[comparacion.algoritmo_ganador.clave]
  const empatados = comparacion.tabla_comparativa.filter((f) => f.clave !== ganador.clave && f.exactitud_validacion === ganador.exactitud_validacion)
  const arbol = por.decision_tree
  const bosque = por.random_forest
  const knn = por.k_nearest_neighbors
  const curva = ajuste.curva_complejidad
  const equilibrado = curva.find((p) => p.max_depth === ajuste.comparacion_modelos.ajuste_adecuado.max_depth)
  const libre = curva[curva.length - 1]
  const puntoPorRegistro = 100 / ajuste.distribucion_datos.validacion_20

  const puntos: ReactNode[] = [
    <>
      <strong>{ALGORITMOS[ganador.clave].nombre}</strong> gana P05 con {porcentaje(pct(ganador.exactitud_validacion))} en validación
      {empatados.length > 0 && <> (empata con {empatados.map((e) => ALGORITMOS[e.clave].nombre).join(' y ')}; el backend se queda con el primero que alcanzó ese valor)</>} y{' '}
      {porcentaje(pct(ganador.exactitud_prueba))} en la prueba ciega.
    </>,
  ]
  if (arbol && bosque) {
    puntos.push(
      <>
        Random Forest tarda <strong>{decimal(bosque.tiempo_entrenamiento_ms / Math.max(arbol.tiempo_entrenamiento_ms, 0.001))}×</strong> más en entrenar y{' '}
        {decimal(bosque.tiempo_inferencia_ms / Math.max(arbol.tiempo_inferencia_ms, 0.001))}× más en predecir que un solo árbol
        {bosque.exactitud_prueba <= arbol.exactitud_prueba ? ', sin mejorar la exactitud en prueba con este volumen de datos.' : `, a cambio de ${decimal(pct(bosque.exactitud_prueba - arbol.exactitud_prueba))} pts más en prueba.`}
      </>,
    )
  }
  if (knn) {
    puntos.push(
      <>
        KNN queda en {porcentaje(pct(knn.exactitud_prueba))}: compara traslados por distancia euclidiana con las variables <strong>sin escalar</strong>, así que el presupuesto (cientos de pesos) pesa
        mucho más que lluvia u hora pico (0 o 1). Escalar con <code>StandardScaler</code> antes de KNN es la mejora natural.
      </>,
    )
  }
  if (equilibrado && libre) {
    puntos.push(
      <>
        Sobreajuste: sin límite de profundidad el árbol llega a {porcentaje(pct(libre.exactitud_entrenamiento))} en entrenamiento, pero en prueba baja de{' '}
        {porcentaje(pct(equilibrado.exactitud_prueba))} (profundidad {equilibrado.max_depth}) a {porcentaje(pct(libre.exactitud_prueba))}. Subajuste: con profundidad 1 no pasa de{' '}
        {porcentaje(pct(curva[0].exactitud_entrenamiento))} ni en entrenamiento.
      </>,
    )
  }
  puntos.push(
    <>
      Con {ajuste.distribucion_datos.validacion_20} traslados en validación, cada traslado vale {decimal(puntoPorRegistro)} puntos de exactitud: diferencias de 1–2 traslados entre modelos no son
      concluyentes. Por eso P06 confirma con validación cruzada de 5 pliegues.
    </>,
  )

  return (
    <Tarjeta titulo="Conclusiones de esta corrida" descripcion="Se calculan con los resultados que regresó el backend.">
      <ul className="list-disc space-y-2 pl-5 text-sm">
        {puntos.map((p, i) => (
          <li key={i}>{p}</li>
        ))}
      </ul>
    </Tarjeta>
  )
}

// ───────────── Sección ─────────────

function Esqueleto({ alto = 'h-80', columnas = 2 }: { alto?: string; columnas?: number }) {
  return (
    <div className={`grid gap-4 ${columnas === 2 ? 'lg:grid-cols-2' : ''}`} aria-hidden="true">
      {Array.from({ length: columnas }, (_, i) => (
        <div key={i} className={`tarjeta animate-pulse bg-borde/40 ${alto}`} />
      ))}
    </div>
  )
}

function AvisoError({ mensaje, recargar }: { mensaje: string; recargar: () => void }) {
  return (
    <div className="grid justify-items-start gap-3">
      <MensajeError>
        {mensaje} Revisa que el backend esté encendido (<code>iniciar_backend.bat</code>) y que exista el CSV limpio del pipeline.
      </MensajeError>
      <button type="button" className="boton-secundario" onClick={recargar}>
        Reintentar
      </button>
    </div>
  )
}

export default function SeccionMachineLearning() {
  const { ajuste, comparacion, optimizacion, recargar } = useMachineLearning()

  if (ajuste.error || comparacion.error) return <AvisoError mensaje={ajuste.error || comparacion.error} recargar={recargar} />

  if (!ajuste.datos || !comparacion.datos) {
    return (
      <div className="grid gap-4" aria-busy="true" aria-label="Entrenando modelos">
        <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
          {Array.from({ length: 4 }, (_, i) => (
            <EsqueletoKpi key={i} />
          ))}
        </div>
        <Esqueleto />
      </div>
    )
  }

  const a = ajuste.datos
  const c = comparacion.datos
  const ganador = c.tabla_comparativa.find((f) => f.clave === c.algoritmo_ganador.clave)
  const rapido = [...c.tabla_comparativa].sort((x, y) => x.tiempo_inferencia_ms - y.tiempo_inferencia_ms)[0]
  const o = optimizacion.datos

  return (
    <div className="grid gap-4 [&>*]:min-w-0">
      {USA_MOCK && (
        <p className="flex items-center gap-2 text-sm text-texto-suave">
          <EtiquetaEjemplo /> Resultados guardados de una corrida real; con <code>VITE_USE_MOCK=false</code> se entrenan en el backend.
        </p>
      )}

      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <TarjetaKpi
          Icono={IconoCerebro}
          tono="primario"
          titulo="Mejor algoritmo (P05)"
          valor={ALGORITMOS[c.algoritmo_ganador.clave].nombre}
          detalle={ganador ? `${porcentaje(pct(ganador.exactitud_validacion))} en validación · ${porcentaje(pct(ganador.exactitud_prueba))} en prueba` : undefined}
        />
        <TarjetaKpi Icono={IconoReloj} tono="ok" titulo="Predicción más rápida" valor={`${decimal(rapido.tiempo_inferencia_ms)} ms`} detalle={`${ALGORITMOS[rapido.clave].nombre}, ${a.distribucion_datos.validacion_20} traslados`} />
        <TarjetaKpi
          Icono={IconoMatraz}
          tono="detalle"
          titulo="Partición de datos (P04)"
          valor="60 / 20 / 20"
          detalle={`${numero(a.distribucion_datos.total_registros)} traslados: ${a.distribucion_datos.entrenamiento_60} / ${a.distribucion_datos.validacion_20} / ${a.distribucion_datos.prueba_20}`}
        />
        <TarjetaKpi
          Icono={IconoTabla}
          tono="aviso"
          titulo="Validación cruzada (P06)"
          valor={o ? porcentaje(pct(o.recomendacion_para_produccion.exactitud_esperada)) : optimizacion.error ? '—' : '…'}
          detalle={
            o
              ? `${NOMBRE_SKLEARN[o.recomendacion_para_produccion.algoritmo] ?? o.recomendacion_para_produccion.algoritmo} ± ${decimal(pct(o.recomendacion_para_produccion.estabilidad_desviacion))} pts`
              : optimizacion.error
                ? 'No se pudo calcular'
                : 'Buscando hiperparámetros…'
          }
        />
      </div>

      <Planteamiento ajuste={a} comparacion={c} />

      <h2 className="mt-2 text-lg font-bold tracking-tight">Árbol de decisión vs. Random Forest vs. KNN</h2>
      <TarjetasAlgoritmos comparacion={c} />
      <div className="grid gap-4 lg:grid-cols-2 [&>*]:min-w-0">
        <GraficaMetricasAlgoritmos comparacion={c} />
        <GraficaTiemposAlgoritmos comparacion={c} />
      </div>
      <Matrices comparacion={c} />

      <h2 className="mt-2 text-lg font-bold tracking-tight">Overfitting vs. underfitting</h2>
      <GraficaCurvaComplejidad ajuste={a} />
      <div className="grid gap-4 lg:grid-cols-2 [&>*]:min-w-0">
        <GraficaRegimenesAjuste ajuste={a} />
        <DiagnosticoArboles ajuste={a} />
      </div>

      <h2 className="mt-2 text-lg font-bold tracking-tight">Optimización con validación cruzada</h2>
      {optimizacion.error ? (
        <AvisoError mensaje={optimizacion.error} recargar={recargar} />
      ) : o ? (
        <div className="grid gap-4 lg:grid-cols-2 [&>*]:min-w-0">
          <GraficaPliegues optimizacion={o} />
          <Hiperparametros optimizacion={o} />
        </div>
      ) : (
        <div aria-busy="true" aria-label="Buscando hiperparámetros">
          <p className="mb-2 text-sm text-texto-suave">GridSearchCV está probando todas las combinaciones (tarda unos segundos)…</p>
          <Esqueleto />
        </div>
      )}

      <Conclusiones ajuste={a} comparacion={c} />
    </div>
  )
}
