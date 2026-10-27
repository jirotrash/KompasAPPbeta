import { useMemo, useRef, useState, type KeyboardEvent, type ReactNode } from 'react'
import { useSearchParams } from 'react-router-dom'
import { MensajeError } from '../../../compartido/componentes/Avisos.tsx'
import {
  IconoItinerario,
  IconoReloj,
  IconoReporte,
  IconoRuta,
  IconoUbicacion,
  IconoChat,
  IconoBus,
  IconoMatraz,
  IconoUsuarios,
} from '../../../compartido/componentes/Iconos.tsx'
import FiltrosDashboard from '../componentes/FiltrosDashboard.tsx'
import TarjetaKpi, { EsqueletoKpi } from '../componentes/TarjetaKpi.tsx'
import { decimal, minutos, numero, porcentaje } from '../estilo.ts'
import { filtrosDesde, SELECCION_INICIAL } from '../filtros.ts'
import GraficaActividad from '../graficas/GraficaActividad.tsx'
import GraficaAhorroGenetico from '../graficas/GraficaAhorroGenetico.tsx'
import GraficaComparativoBusqueda from '../graficas/GraficaComparativoBusqueda.tsx'
import GraficaConvergencia from '../graficas/GraficaConvergencia.tsx'
import GraficaCostoOptimo from '../graficas/GraficaCostoOptimo.tsx'
import { GraficaHerramientas, GraficaOrigenPlanes, GraficaUsoAsistente } from '../graficas/GraficasAsistente.tsx'
import PanelRutasParadas from '../graficas/PanelRutasParadas.tsx'
import GraficaContexto from '../graficas/GraficaContexto.tsx'
import GraficaDfs from '../graficas/GraficaDfs.tsx'
import GraficaDiaHora from '../graficas/GraficaDiaHora.tsx'
import GraficaDistancias from '../graficas/GraficaDistancias.tsx'
import GraficaEstados from '../graficas/GraficaEstados.tsx'
import GraficaInteresesTiempo from '../graficas/GraficaInteresesTiempo.tsx'
import GraficaLugaresCategoria from '../graficas/GraficaLugaresCategoria.tsx'
import GraficaMovilidadElegida from '../graficas/GraficaMovilidadElegida.tsx'
import GraficaParesDfs from '../graficas/GraficaParesDfs.tsx'
import GraficaPerfilContexto from '../graficas/GraficaPerfilContexto.tsx'
import GraficaPlanesInteres from '../graficas/GraficaPlanesInteres.tsx'
import GraficaPresupuesto from '../graficas/GraficaPresupuesto.tsx'
import GraficaPuntuacion from '../graficas/GraficaPuntuacion.tsx'
import GraficaRecomendacion from '../graficas/GraficaRecomendacion.tsx'
import GraficaReglas from '../graficas/GraficaReglas.tsx'
import GraficaReportesTipo from '../graficas/GraficaReportesTipo.tsx'
import GraficaRutasTop from '../graficas/GraficaRutasTop.tsx'
import GraficaTiempoDisponible from '../graficas/GraficaTiempoDisponible.tsx'
import GraficaTransporte from '../graficas/GraficaTransporte.tsx'
import MapaLugaresReportes from '../graficas/MapaLugaresReportes.tsx'
import useDashboard from '../hooks/useDashboard.ts'
import { SECCIONES, seccionDe, type IdSeccion } from '../secciones.ts'
import type { DatosDashboard } from '../tipos.ts'

function Resumen({ d }: { d: DatosDashboard }) {
  const k = d.kpis
  return (
    <div className="grid gap-4 [&>*]:min-w-0">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-3 xl:grid-cols-6">
        <TarjetaKpi Icono={IconoUsuarios} tono="primario" titulo="Usuarios" valor={numero(k.usuarios_totales)} detalle={`${numero(k.usuarios_nuevos)} nuevos en el periodo`} />
        <TarjetaKpi Icono={IconoItinerario} tono="detalle" titulo="Planes creados" valor={numero(k.planes)} detalle={`${numero(k.planes_evaluados)} evaluados por la IA`} />
        <TarjetaKpi Icono={IconoRuta} tono="ok" titulo="Recorridos" valor={numero(k.recorridos)} detalle="guardados en el historial" />
        <TarjetaKpi Icono={IconoReloj} tono="primario" titulo="Tiempo promedio" valor={minutos(k.tiempo_promedio_recorrido_min)} detalle="por recorrido (estimado)" />
        <TarjetaKpi Icono={IconoReporte} tono="peligro" titulo="Reportes vigentes" valor={numero(k.reportes_vigentes)} detalle="en este momento" />
        <TarjetaKpi Icono={IconoUbicacion} tono="aviso" titulo="Lugares" valor={numero(k.lugares)} detalle="registrados en la base" />
      </div>
      <div className="grid gap-4 lg:grid-cols-3 [&>*]:min-w-0">
        <GraficaRecomendacion kpis={k} />
        <div className="lg:col-span-2">
          <GraficaActividad series={d.series} />
        </div>
      </div>
      <GraficaInteresesTiempo series={d.series} />
    </div>
  )
}

const CONTENIDO: Record<IdSeccion, (d: DatosDashboard) => ReactNode> = {
  resumen: (d) => <Resumen d={d} />,
  planes: (d) => (
    <div className="grid gap-4 lg:grid-cols-2 [&>*]:min-w-0">
      <GraficaPlanesInteres planes={d.planes} />
      <GraficaContexto planes={d.planes} />
      <GraficaMovilidadElegida planes={d.planes} />
      <GraficaPerfilContexto planes={d.planes} />
      <GraficaPresupuesto planes={d.planes} />
      <GraficaTiempoDisponible planes={d.planes} />
      <div className="lg:col-span-2">
        <GraficaDiaHora planes={d.planes} />
      </div>
    </div>
  ),
  sistema: (d) => (
    <div className="grid gap-4 lg:grid-cols-2 [&>*]:min-w-0">
      <GraficaEstados sistema={d.sistema} />
      <GraficaPuntuacion sistema={d.sistema} />
      <div className="lg:col-span-2">
        <GraficaReglas sistema={d.sistema} />
      </div>
      <p className="text-sm text-texto-suave lg:col-span-2">
        Planes en los que el motor no tuvo datos suficientes para recomendar: <strong className="text-texto">{numero(d.sistema.sin_datos_suficientes)}</strong>
        {d.sistema.por_version.length > 0 && ` · Versión de reglas: ${d.sistema.por_version.map((v) => `${v.version} (${numero(v.total)})`).join(', ')}`}
      </p>
    </div>
  ),
  movilidad: (d) => (
    <div className="grid gap-4 lg:grid-cols-2 [&>*]:min-w-0">
      <GraficaTransporte movilidad={d.movilidad} />
      <GraficaRutasTop movilidad={d.movilidad} />
      <div className="lg:col-span-2">
        <PanelRutasParadas movilidad={d.movilidad} />
      </div>
    </div>
  ),
  reportes: (d) => (
    <div className="grid gap-4 lg:grid-cols-2 [&>*]:min-w-0">
      <GraficaReportesTipo reportes={d.reportes} />
      <GraficaLugaresCategoria lugares={d.lugares} />
      <div className="lg:col-span-2">
        <MapaLugaresReportes lugares={d.lugares} reportes={d.reportes} />
      </div>
    </div>
  ),
  laboratorio: (d) => (
    <div className="grid gap-4 lg:grid-cols-2 [&>*]:min-w-0">
      <GraficaComparativoBusqueda />
      <GraficaCostoOptimo laboratorio={d.laboratorio} />
      <GraficaConvergencia laboratorio={d.laboratorio} />
      <GraficaAhorroGenetico laboratorio={d.laboratorio} />
      <div className="grid grid-cols-2 gap-3 lg:col-span-2 xl:grid-cols-4">
        <TarjetaKpi Icono={IconoBus} titulo="Transbordos calculados con A*" valor={numero(d.laboratorio.transbordos?.consultas ?? 0)} detalle="búsquedas de una combinación de rutas" />
        <TarjetaKpi
          Icono={IconoRuta}
          tono="ok"
          titulo="Combinaciones encontradas"
          valor={numero(d.laboratorio.transbordos?.encontrados ?? 0)}
          detalle={d.laboratorio.transbordos?.consultas ? porcentaje((100 * d.laboratorio.transbordos.encontrados) / d.laboratorio.transbordos.consultas) + ' de las búsquedas' : 'sin búsquedas en el periodo'}
        />
        <TarjetaKpi
          Icono={IconoMatraz}
          tono="detalle"
          titulo="Nodos explorados (promedio)"
          valor={decimal(d.laboratorio.transbordos?.nodos_explorados_promedio)}
          detalle={`de ${decimal(d.laboratorio.transbordos?.nodos_grafo_promedio)} nodos del grafo`}
        />
        <TarjetaKpi Icono={IconoReloj} titulo="Tiempo de A*" valor={`${decimal(d.laboratorio.transbordos?.ms_promedio)} ms`} detalle="promedio por búsqueda" />
      </div>
      <GraficaDfs laboratorio={d.laboratorio} />
      <GraficaDistancias laboratorio={d.laboratorio} />
      <div className="lg:col-span-2">
        <GraficaParesDfs laboratorio={d.laboratorio} />
      </div>
    </div>
  ),
  asistente: (d) => (
    <div className="grid gap-4 lg:grid-cols-2 [&>*]:min-w-0">
      <div className="grid grid-cols-2 gap-3 lg:col-span-2 xl:grid-cols-4">
        <TarjetaKpi Icono={IconoChat} titulo="Respuestas del modelo" valor={numero(d.asistente.tiempo_respuesta.respuestas)} detalle="en el periodo" />
        <TarjetaKpi Icono={IconoReloj} tono="primario" titulo="Tiempo de respuesta" valor={`${decimal((d.asistente.tiempo_respuesta.promedio_ms ?? 0) / 1000)} s`} detalle={`promedio · p90: ${decimal((d.asistente.tiempo_respuesta.p90_ms ?? 0) / 1000)} s`} />
        <TarjetaKpi Icono={IconoReporte} tono="peligro" titulo="Sin respuesta" valor={porcentaje(d.asistente.errores.porcentaje_error)} detalle={`${numero(d.asistente.errores.errores)} veces el asistente no estuvo disponible`} />
        <TarjetaKpi Icono={IconoItinerario} tono="detalle" titulo="Planes desde el asistente" valor={numero(d.asistente.planes_por_origen.find((o) => o.origen === 'asistente')?.total ?? 0)} detalle="guardados en Mis planes" />
      </div>
      <div className="lg:col-span-2">
        <GraficaUsoAsistente asistente={d.asistente} />
      </div>
      <GraficaHerramientas asistente={d.asistente} />
      <GraficaOrigenPlanes asistente={d.asistente} />
    </div>
  ),
}

function Esqueleto() {
  return (
    <div className="grid gap-4" aria-busy="true" aria-label="Cargando estadísticas">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-3 xl:grid-cols-6">
        {Array.from({ length: 6 }, (_, i) => (
          <EsqueletoKpi key={i} />
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-2 [&>*]:min-w-0">
        {[0, 1].map((i) => (
          <div key={i} className="tarjeta h-80 animate-pulse bg-borde/40" />
        ))}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [seleccion, setSeleccion] = useState(SELECCION_INICIAL)
  const filtros = useMemo(() => filtrosDesde(seleccion), [seleccion])
  const [params, setParams] = useSearchParams()
  const seccion = seccionDe(params.get('seccion'))
  const { datos, cargando, error, recargar } = useDashboard(filtros)
  const botones = useRef<Partial<Record<IdSeccion, HTMLButtonElement | null>>>({})

  const incluyeDemo = datos && Object.values(datos).some((d) => d?.incluye_demo)
  const irA = (id: IdSeccion) => setParams(id === 'resumen' ? {} : { seccion: id })

  function moverConTeclado(e: KeyboardEvent<HTMLButtonElement>, indice: number) {
    const teclas: Record<string, number> = { ArrowRight: indice + 1, ArrowLeft: indice - 1, Home: 0, End: SECCIONES.length - 1 }
    const siguiente = teclas[e.key]
    if (siguiente === undefined) return
    e.preventDefault()
    const destino = SECCIONES[(siguiente + SECCIONES.length) % SECCIONES.length].id
    irA(destino)
    botones.current[destino]?.focus()
  }

  return (
    <div className="mx-auto grid w-full max-w-screen-2xl gap-5 px-4 py-5 sm:px-6 md:py-8 lg:px-8">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wider text-primario">Dashboard</p>
          <h1 className="mt-1 flex items-center gap-3 text-2xl font-bold tracking-tight md:text-3xl">
            <seccion.Icono className="size-7 text-primario" />
            {seccion.texto}
          </h1>
          <p className="mt-1 text-texto-suave">{seccion.descripcion}</p>
        </div>
        {incluyeDemo && seleccion.incluirDemo && (
          <span
            role="status"
            title="Incluye documentos marcados con demo: true. Desactiva “Incluir datos demo” para ver solo la actividad real."
            className="inline-flex items-center gap-2 rounded-full border border-aviso/40 bg-aviso-fondo px-3 py-1 text-xs font-semibold text-texto"
          >
            <span aria-hidden="true" className="size-2 rounded-full bg-aviso" />
            Incluye datos de demostración
          </span>
        )}
      </header>

      <FiltrosDashboard inicial={seleccion} onAplicar={setSeleccion} cargando={cargando} />

      {/* En escritorio las secciones están en la barra lateral; en celular, aquí como pestañas */}
      <div role="tablist" aria-label="Secciones del dashboard" className="-mx-1 flex gap-1 overflow-x-auto border-b border-borde px-1 md:hidden">
        {SECCIONES.map((p, i) => (
          <button
            key={p.id}
            ref={(el) => {
              botones.current[p.id] = el
            }}
            id={`pestana-${p.id}`}
            type="button"
            role="tab"
            aria-selected={seccion.id === p.id}
            aria-controls="panel-dashboard"
            tabIndex={seccion.id === p.id ? 0 : -1}
            onClick={() => irA(p.id)}
            onKeyDown={(e) => moverConTeclado(e, i)}
            className={`min-h-11 shrink-0 border-b-2 px-3 text-sm font-semibold transition ${
              seccion.id === p.id ? 'border-primario text-primario' : 'border-transparent text-texto-suave hover:text-texto'
            }`}
          >
            {p.texto}
          </button>
        ))}
      </div>

      <div id="panel-dashboard" role="region" aria-label={seccion.texto}>
        {error ? (
          <div className="grid justify-items-start gap-3">
            <MensajeError>{error}</MensajeError>
            <button type="button" className="boton-secundario" onClick={recargar}>
              Reintentar
            </button>
          </div>
        ) : cargando || !datos ? (
          <Esqueleto />
        ) : (
          CONTENIDO[seccion.id](datos)
        )}
      </div>
    </div>
  )
}
