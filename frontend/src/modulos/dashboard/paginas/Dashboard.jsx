import { useMemo, useRef, useState } from 'react'
import { MensajeError } from '../../../compartido/componentes/Avisos.jsx'
import Pagina from '../../../compartido/componentes/Pagina.jsx'
import FiltrosDashboard from '../componentes/FiltrosDashboard.jsx'
import TarjetaKpi, { EsqueletoKpi } from '../componentes/TarjetaKpi.jsx'
import { minutos, numero } from '../estilo.js'
import { filtrosDesde, SELECCION_INICIAL } from '../filtros.js'
import GraficaActividad from '../graficas/GraficaActividad.jsx'
import GraficaContexto from '../graficas/GraficaContexto.jsx'
import GraficaDfs from '../graficas/GraficaDfs.jsx'
import GraficaDiaHora from '../graficas/GraficaDiaHora.jsx'
import GraficaDistancias from '../graficas/GraficaDistancias.jsx'
import GraficaEstados from '../graficas/GraficaEstados.jsx'
import GraficaInteresesTiempo from '../graficas/GraficaInteresesTiempo.jsx'
import GraficaLugaresCategoria from '../graficas/GraficaLugaresCategoria.jsx'
import GraficaMovilidadElegida from '../graficas/GraficaMovilidadElegida.jsx'
import GraficaParesDfs from '../graficas/GraficaParesDfs.jsx'
import GraficaPerfilContexto from '../graficas/GraficaPerfilContexto.jsx'
import GraficaPlanesInteres from '../graficas/GraficaPlanesInteres.jsx'
import GraficaPresupuesto from '../graficas/GraficaPresupuesto.jsx'
import GraficaPuntuacion from '../graficas/GraficaPuntuacion.jsx'
import GraficaRecomendacion from '../graficas/GraficaRecomendacion.jsx'
import GraficaReglas from '../graficas/GraficaReglas.jsx'
import GraficaReportesTipo from '../graficas/GraficaReportesTipo.jsx'
import GraficaRutasTop from '../graficas/GraficaRutasTop.jsx'
import GraficaTiempoDisponible from '../graficas/GraficaTiempoDisponible.jsx'
import GraficaTransporte from '../graficas/GraficaTransporte.jsx'
import MapaLugaresReportes from '../graficas/MapaLugaresReportes.jsx'
import useDashboard from '../hooks/useDashboard.js'

const PESTANAS = [
  { id: 'resumen', texto: 'Resumen' },
  { id: 'planes', texto: 'Planes' },
  { id: 'sistema', texto: 'Sistema experto' },
  { id: 'movilidad', texto: 'Movilidad' },
  { id: 'reportes', texto: 'Reportes y lugares' },
  { id: 'laboratorio', texto: 'Laboratorio IA' },
]

function Resumen({ d }) {
  const k = d.kpis
  return (
    <div className="grid gap-4 [&>*]:min-w-0">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-3 xl:grid-cols-6">
        <TarjetaKpi titulo="Usuarios" valor={numero(k.usuarios_totales)} detalle={`${numero(k.usuarios_nuevos)} nuevos en el periodo`} />
        <TarjetaKpi titulo="Planes creados" valor={numero(k.planes)} detalle={`${numero(k.planes_evaluados)} evaluados por la IA`} />
        <TarjetaKpi titulo="Recorridos" valor={numero(k.recorridos)} detalle="guardados en el historial" />
        <TarjetaKpi titulo="Tiempo promedio" valor={minutos(k.tiempo_promedio_recorrido_min)} detalle="por recorrido (estimado)" />
        <TarjetaKpi titulo="Reportes vigentes" valor={numero(k.reportes_vigentes)} detalle="en este momento" />
        <TarjetaKpi titulo="Lugares" valor={numero(k.lugares)} detalle="registrados en la base" />
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

const CONTENIDO = {
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
      <GraficaDfs laboratorio={d.laboratorio} />
      <GraficaDistancias laboratorio={d.laboratorio} />
      <div className="lg:col-span-2">
        <GraficaParesDfs laboratorio={d.laboratorio} />
      </div>
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
  const [pestana, setPestana] = useState('resumen')
  const { datos, cargando, error, recargar } = useDashboard(filtros)
  const botones = useRef({})

  const incluyeDemo = datos && Object.values(datos).some((d) => d?.incluye_demo)

  function moverConTeclado(e, indice) {
    const siguiente = { ArrowRight: indice + 1, ArrowLeft: indice - 1, Home: 0, End: PESTANAS.length - 1 }[e.key]
    if (siguiente === undefined) return
    e.preventDefault()
    const destino = PESTANAS[(siguiente + PESTANAS.length) % PESTANAS.length].id
    setPestana(destino)
    botones.current[destino]?.focus()
  }

  return (
    <Pagina titulo="Dashboard" descripcion="Cómo se usa Kompás y cómo decide la IA. Todas las cifras vienen agregadas desde la API." ancho="max-w-screen-2xl">
      <div className="grid gap-4">
        <FiltrosDashboard inicial={seleccion} onAplicar={setSeleccion} cargando={cargando} />

        {incluyeDemo && seleccion.incluirDemo && (
          <p role="status" className="rounded-xl bg-aviso-fondo px-3 py-2 text-sm font-medium text-texto">
            Incluye datos de demostración (marcados con demo: true). Desactiva “Incluir datos demo” para ver solo la actividad real.
          </p>
        )}

        <div role="tablist" aria-label="Secciones del dashboard" className="-mx-1 flex gap-1 overflow-x-auto border-b border-borde px-1">
          {PESTANAS.map((p, i) => (
            <button
              key={p.id}
              ref={(el) => (botones.current[p.id] = el)}
              id={`pestana-${p.id}`}
              type="button"
              role="tab"
              aria-selected={pestana === p.id}
              aria-controls={`panel-${p.id}`}
              tabIndex={pestana === p.id ? 0 : -1}
              onClick={() => setPestana(p.id)}
              onKeyDown={(e) => moverConTeclado(e, i)}
              className={`min-h-11 shrink-0 border-b-2 px-3 text-sm font-semibold transition ${
                pestana === p.id ? 'border-primario text-primario' : 'border-transparent text-texto-suave hover:text-texto'
              }`}
            >
              {p.texto}
            </button>
          ))}
        </div>

        <div role="tabpanel" id={`panel-${pestana}`} aria-labelledby={`pestana-${pestana}`}>
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
            CONTENIDO[pestana](datos)
          )}
        </div>
      </div>
    </Pagina>
  )
}
