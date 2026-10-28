import { useCallback, useState } from 'react'
import { Cargando, MensajeError } from '../../../compartido/componentes/Avisos.tsx'
import Chip from '../../../compartido/componentes/Chip.tsx'
import { IconoBorrar } from '../../../compartido/componentes/Iconos.tsx'
import Mapa, { type MarcadorMapa } from '../../../compartido/componentes/Mapa.tsx'
import { TIPOS_REPORTE } from '../../../compartido/utils/dominio.ts'
import * as api from '../api.ts'
import { confirmar, coordenadas, fechaHora } from '../formato.ts'
import useAccion from '../hooks/useAccion.ts'
import useCarga from '../hooks/useCarga.ts'
import type { EstadoReporte, ReporteAdmin } from '../tipos.ts'
import { BotonIcono, Insignia, Vacio } from './Comun.tsx'

const ESTADOS: { valor: EstadoReporte; texto: string; tono: 'aviso' | 'ok' | 'neutro' }[] = [
  { valor: 'pendiente', texto: 'Pendiente', tono: 'aviso' },
  { valor: 'verificado', texto: 'Verificado', tono: 'ok' },
  { valor: 'descartado', texto: 'Descartado', tono: 'neutro' },
]

export default function PanelReportes() {
  const [estado, setEstado] = useState<EstadoReporte | undefined>(undefined)
  const cargar = useCallback(() => api.obtenerReportes(estado), [estado])
  const { datos: reportes, cargando, error, recargar } = useCarga(cargar)
  const [elegido, setElegido] = useState<string | null>(null)
  const accion = useAccion()

  async function moderar(r: ReporteAdmin, nuevo: EstadoReporte) {
    if (await accion.ejecutar(() => api.moderarReporte(r._id, nuevo))) recargar()
  }

  async function borrar(r: ReporteAdmin) {
    if (!confirmar('¿Borrar este reporte? También deja de contarse en el dashboard. Para conservarlo, márcalo como descartado.')) return
    if ((await accion.ejecutar(() => api.borrarReporte(r._id))) !== undefined) recargar()
  }

  const lista = reportes ?? []
  const marcadores: MarcadorMapa[] = lista.map((r) => ({
    id: r._id,
    lat: r.ubicacion.coordinates[1],
    lng: r.ubicacion.coordinates[0],
    tipo: r._id === elegido ? 'seleccion' : 'reporte',
    titulo: TIPOS_REPORTE[r.tipo],
    onClic: () => setElegido(r._id),
  }))

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,26rem)] [&>*]:min-w-0">
      <section className="tarjeta grid content-start gap-3" aria-labelledby="titulo-reportes">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 id="titulo-reportes" className="text-lg font-bold">
            Reportes {reportes && <span className="text-texto-suave">({lista.length})</span>}
          </h2>
          <div className="flex flex-wrap gap-2" role="group" aria-label="Filtrar por estado">
            <Chip activo={!estado} onClick={() => setEstado(undefined)}>
              Todos
            </Chip>
            {ESTADOS.map((e) => (
              <Chip key={e.valor} activo={estado === e.valor} onClick={() => setEstado(e.valor)}>
                {e.texto}
              </Chip>
            ))}
          </div>
        </div>
        <MensajeError>{error || accion.error}</MensajeError>
        {cargando && !reportes ? (
          <Cargando texto="Cargando reportes…" />
        ) : lista.length === 0 ? (
          <Vacio>No hay reportes {estado ? `con estado «${estado}»` : ''}.</Vacio>
        ) : (
          <ul className="grid gap-2">
            {lista.map((r) => {
              const info = ESTADOS.find((e) => e.valor === r.estado)!
              return (
                <li
                  key={r._id}
                  className={`grid gap-2 rounded-xl border p-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center ${r._id === elegido ? 'border-primario bg-primario-claro/50' : 'border-borde'}`}
                >
                  <button type="button" className="min-w-0 text-left" onClick={() => setElegido(r._id)}>
                    <span className="flex flex-wrap items-center gap-1.5">
                      <strong>{TIPOS_REPORTE[r.tipo]}</strong>
                      {r.nivel_afluencia && <span className="text-sm text-texto-suave">({r.nivel_afluencia})</span>}
                      <Insignia tono={info.tono}>{info.texto}</Insignia>
                      <Insignia tono={r.vigente ? 'peligro' : 'neutro'}>{r.vigente ? 'vigente' : 'vencido'}</Insignia>
                    </span>
                    <span className="block text-xs text-texto-suave">
                      {fechaHora(r.observado_en)} · {coordenadas(r.ubicacion)} · {r.confirmaciones} confirmaciones
                      {r.id_usuario ? ` · usuario #${r.id_usuario}` : ''}
                      {r.ruta_id ? ` · ruta ${r.ruta_id}` : ''}
                    </span>
                    {r.comentario && <span className="mt-1 block text-sm">“{r.comentario}”</span>}
                  </button>
                  <div className="flex flex-wrap items-center gap-1.5">
                    {ESTADOS.filter((e) => e.valor !== r.estado).map((e) => (
                      <button key={e.valor} type="button" className="boton-secundario min-h-9 px-3 text-sm" disabled={accion.ocupado} onClick={() => moderar(r, e.valor)}>
                        {e.valor === 'pendiente' ? 'Regresar a pendiente' : e.valor === 'verificado' ? 'Verificar' : 'Descartar'}
                      </button>
                    ))}
                    <BotonIcono Icono={IconoBorrar} etiqueta="Borrar reporte" peligro disabled={accion.ocupado} onClick={() => borrar(r)} />
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </section>
      <div className="grid content-start gap-2 xl:sticky xl:top-4">
        <Mapa className="h-[50vh] min-h-80" marcadores={marcadores} />
        <p className="text-xs text-texto-suave">Toca un reporte del mapa para ubicarlo en la lista.</p>
      </div>
    </div>
  )
}
