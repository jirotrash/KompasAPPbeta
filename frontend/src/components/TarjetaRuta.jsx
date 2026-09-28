import { tiempoTotal } from '../utils/dominio.js'
import { formatoMinutos } from '../utils/geo.js'
import { EtiquetaEjemplo } from './Avisos.jsx'
import ExplicacionReglas from './ExplicacionReglas.jsx'
import FuenteDato from './FuenteDato.jsx'
import { IconoAuto, IconoBus, IconoCelular, IconoPie } from './Iconos.jsx'

const MODOS = {
  pie: { nombre: 'A pie', Icono: IconoPie },
  autobus: { nombre: 'Autobús', Icono: IconoBus },
  taxi: { nombre: 'Taxi', Icono: IconoAuto },
  app: { nombre: 'Transporte por aplicación', Icono: IconoCelular },
}

function Dato({ etiqueta, valor }) {
  if (valor == null) return null
  return (
    <div className="rounded-lg bg-fondo px-2 py-1.5 text-center">
      <dt className="text-[11px] uppercase tracking-wide text-texto-suave">{etiqueta}</dt>
      <dd className="text-sm font-semibold">{formatoMinutos(valor)}</dd>
    </div>
  )
}

export default function TarjetaRuta({ alternativa: a, seleccionada, onSeleccionar }) {
  const { nombre, Icono } = MODOS[a.modo] ?? MODOS.pie

  return (
    <article
      className={`tarjeta space-y-3 transition ${seleccionada ? 'border-primario ring-2 ring-primario/30' : ''}`}
    >
      <button type="button" onClick={onSeleccionar} className="flex w-full items-start gap-3 text-left">
        <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-primario-claro text-primario-oscuro">
          <Icono />
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center gap-2">
            <span className="font-semibold">{a.linea ?? nombre}</span>
            {a.ejemplo && <EtiquetaEjemplo />}
          </span>
          {a.sentido && <span className="block text-sm text-texto-suave">Sentido {a.sentido}</span>}
          {a.distancia_km != null && (
            <span className="block text-sm text-texto-suave">~{a.distancia_km.toFixed(1)} km</span>
          )}
        </span>
        <span className="shrink-0 text-right">
          <span className="block text-lg font-bold text-primario">{formatoMinutos(tiempoTotal(a))}</span>
          <span className="block text-[11px] text-texto-suave">estimado</span>
        </span>
      </button>

      <dl className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <Dato etiqueta="Caminata" valor={a.tiempos.caminata} />
        <Dato etiqueta="Espera" valor={a.tiempos.espera} />
        <Dato etiqueta="Trayecto" valor={a.tiempos.trayecto} />
        {a.transbordos?.length > 0 && <Dato etiqueta="Transbordos" valor={a.tiempos.transbordos} />}
      </dl>

      {a.modo === 'autobus' && (
        <ol className="space-y-2 text-sm">
          <li className="flex gap-2">
            <span className="font-bold text-ok">↑ Sube en:</span> {a.abordaje?.nombre}
          </li>
          {a.transbordos?.map((t) => (
            <li key={t.nombre} className="flex gap-2">
              <span className="font-bold text-acento">⇄ Transborda:</span> {t.nombre} ({t.linea})
            </li>
          ))}
          <li className="flex gap-2">
            <span className="font-bold text-aviso">↓ Baja en:</span> {a.descenso?.nombre}
          </li>
          <li className="text-texto-suave">Tarifa: {a.tarifa != null ? `$${a.tarifa}` : 'por confirmar'}</li>
        </ol>
      )}

      {a.avisos?.length > 0 && (
        <ul className="space-y-1 text-sm text-aviso">
          {a.avisos.map((t) => (
            <li key={t}>⚠ {t}</li>
          ))}
        </ul>
      )}

      <ExplicacionReglas reglas={a.reglas_cumplidas} />
      <FuenteDato fuente={a.fuente} fecha={a.fecha_verificacion} tipo={a.tipo_horario} />
    </article>
  )
}
