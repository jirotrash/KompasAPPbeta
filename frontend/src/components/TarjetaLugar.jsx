import { USA_MOCK } from '../services/api.js'
import { nombreCategoria } from '../utils/dominio.js'
import { EtiquetaEjemplo } from './Avisos.jsx'
import FuenteDato from './FuenteDato.jsx'

const AFLUENCIA = {
  baja: 'bg-ok-fondo text-ok',
  media: 'bg-aviso-fondo text-aviso',
  alta: 'bg-peligro-fondo text-peligro',
}

export default function TarjetaLugar({ lugar, indice, dia, compacta }) {
  const horarioHoy = lugar.horario?.[dia]

  return (
    <div className="flex gap-3">
      {indice != null && (
        <span className="grid size-7 shrink-0 place-items-center rounded-full bg-acento text-sm font-bold text-sobre-acento">
          {indice}
        </span>
      )}
      <div className="min-w-0 flex-1 space-y-1">
        <p className="font-semibold leading-snug">{lugar.nombre}</p>
        <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-texto-suave">
          <span>{nombreCategoria(lugar.categoria)}</span>
          {lugar.municipio && <span>· {lugar.municipio}</span>}
          {lugar.costo_promedio != null && <span>· ~${lugar.costo_promedio}</span>}
          {lugar.calificacion && <span>· ★ {lugar.calificacion.valor}</span>}
        </p>
        {!compacta && (
          <>
            <p className="text-sm">
              Horario hoy:{' '}
              {lugar.horario ? (horarioHoy ? `${horarioHoy[0]} – ${horarioHoy[1]}` : 'cerrado') : 'sin información'}
            </p>
            {lugar.afluencia && (
              <p className="text-sm">
                Afluencia:{' '}
                <span className={`rounded-md px-1.5 py-0.5 text-xs font-semibold ${AFLUENCIA[lugar.afluencia.nivel]}`}>
                  {lugar.afluencia.nivel}
                </span>{' '}
                <span className="text-xs text-texto-suave">({lugar.afluencia.fuente})</span>
              </p>
            )}
            {USA_MOCK && <EtiquetaEjemplo />}
            <FuenteDato fuente={lugar.calificacion?.fuente} fecha={lugar.calificacion?.fecha} />
          </>
        )}
      </div>
    </div>
  )
}
