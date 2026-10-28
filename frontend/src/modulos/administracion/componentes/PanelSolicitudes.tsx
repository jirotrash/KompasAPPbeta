import { useCallback, useState } from 'react'
import { Cargando, MensajeError } from '../../../compartido/componentes/Avisos.tsx'
import Chip from '../../../compartido/componentes/Chip.tsx'
import { IconoBorrar } from '../../../compartido/componentes/Iconos.tsx'
import Mapa, { type MarcadorMapa } from '../../../compartido/componentes/Mapa.tsx'
import { aLeaflet } from '../../../compartido/utils/geo.ts'
import * as api from '../api.ts'
import { confirmar, coordenadas, fechaHora } from '../formato.ts'
import useAccion from '../hooks/useAccion.ts'
import useCarga from '../hooks/useCarga.ts'
import type { EstadoSolicitud, Solicitud } from '../tipos.ts'
import { BotonIcono, Insignia, Vacio } from './Comun.tsx'

const ESTADOS: { valor: EstadoSolicitud; texto: string; accion: string; tono: 'aviso' | 'ok' | 'neutro' }[] = [
  { valor: 'pendiente', texto: 'Pendiente', accion: 'Regresar a pendiente', tono: 'aviso' },
  { valor: 'atendida', texto: 'Atendida', accion: 'Marcar atendida', tono: 'ok' },
  { valor: 'descartada', texto: 'Descartada', accion: 'Descartar', tono: 'neutro' },
]

function TarjetaSolicitud({ s, elegida, onElegir, onCambio }: { s: Solicitud; elegida: boolean; onElegir: () => void; onCambio: () => void }) {
  const [nota, setNota] = useState(s.nota_admin ?? '')
  const accion = useAccion()
  const info = ESTADOS.find((e) => e.valor === s.estado)!

  async function cambiar(estado: EstadoSolicitud) {
    if (await accion.ejecutar(() => api.atenderSolicitud(s.id, estado, nota.trim() || null))) onCambio()
  }

  async function borrar() {
    if (!confirmar('¿Borrar esta solicitud? La persona ya no la verá en la app.')) return
    if ((await accion.ejecutar(() => api.borrarSolicitud(s.id))) !== undefined) onCambio()
  }

  return (
    <li className={`grid gap-2 rounded-xl border p-3 ${elegida ? 'border-primario bg-primario-claro/50' : 'border-borde'}`}>
      <button type="button" className="text-left" aria-pressed={elegida} onClick={onElegir}>
        <span className="flex flex-wrap items-center gap-1.5">
          <strong>Usuario #{s.id_usuario}</strong>
          <Insignia tono={info.tono}>{info.texto}</Insignia>
          <span className="text-xs text-texto-suave">{fechaHora(s.creado_en)}</span>
        </span>
        <span className="block text-xs text-texto-suave">
          {coordenadas(s.origen)} → {coordenadas(s.destino)}
        </span>
        {s.comentario && <span className="mt-1 block text-sm">“{s.comentario}”</span>}
      </button>
      <label>
        <span className="sr-only">Nota para la solicitud</span>
        <input className="campo min-h-9 py-1 text-sm" placeholder="Nota (opcional): qué ruta se agregó o por qué no procede" value={nota} maxLength={500} onChange={(e) => setNota(e.target.value)} />
      </label>
      <MensajeError>{accion.error}</MensajeError>
      <div className="flex flex-wrap items-center gap-1.5">
        {ESTADOS.filter((e) => e.valor !== s.estado || nota.trim() !== (s.nota_admin ?? '')).map((e) => (
          <button key={e.valor} type="button" className={`${e.valor === 'atendida' ? 'boton-primario' : 'boton-secundario'} min-h-9 px-3 text-sm`} disabled={accion.ocupado} onClick={() => cambiar(e.valor)}>
            {e.valor === s.estado ? 'Guardar nota' : e.accion}
          </button>
        ))}
        <BotonIcono Icono={IconoBorrar} etiqueta="Borrar solicitud" peligro disabled={accion.ocupado} onClick={borrar} className="ml-auto" />
      </div>
    </li>
  )
}

export default function PanelSolicitudes() {
  const [estado, setEstado] = useState<EstadoSolicitud | undefined>('pendiente')
  const cargar = useCallback(() => api.obtenerSolicitudes(estado), [estado])
  const { datos: solicitudes, cargando, error, recargar } = useCarga(cargar)
  const [elegida, setElegida] = useState<string | null>(null)

  const lista = solicitudes ?? []
  const actual = lista.find((s) => s.id === elegida)
  const marcadores: MarcadorMapa[] = lista.flatMap((s) => {
    const [lngO, latO] = s.origen.coordinates
    const [lngD, latD] = s.destino.coordinates
    const resaltada = s.id === elegida
    return [
      { id: `${s.id}-o`, lat: latO, lng: lngO, tipo: resaltada ? 'origen' : 'intermedia', titulo: `Origen · usuario #${s.id_usuario}`, onClic: () => setElegida(s.id) },
      { id: `${s.id}-d`, lat: latD, lng: lngD, tipo: resaltada ? 'destino' : 'intermedia', titulo: `Destino · usuario #${s.id_usuario}`, onClic: () => setElegida(s.id) },
    ]
  })

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,28rem)] [&>*]:min-w-0">
      <section className="tarjeta grid content-start gap-3" aria-labelledby="titulo-solicitudes">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 id="titulo-solicitudes" className="text-lg font-bold">
            Solicitudes {solicitudes && <span className="text-texto-suave">({lista.length})</span>}
          </h2>
          <div className="flex flex-wrap gap-2" role="group" aria-label="Filtrar por estado">
            {ESTADOS.map((e) => (
              <Chip key={e.valor} activo={estado === e.valor} onClick={() => setEstado(e.valor)}>
                {e.texto}
              </Chip>
            ))}
            <Chip activo={!estado} onClick={() => setEstado(undefined)}>
              Todas
            </Chip>
          </div>
        </div>
        <p className="text-sm text-texto-suave">
          Cuando la app no encuentra camión, la persona puede pedir la ruta. Dala de alta en <strong className="text-texto">Rutas</strong> y márcala como atendida; la persona ve el estado y tu nota.
        </p>
        <MensajeError>{error}</MensajeError>
        {cargando && !solicitudes ? (
          <Cargando texto="Cargando solicitudes…" />
        ) : lista.length === 0 ? (
          <Vacio>No hay solicitudes {estado ? `con estado «${estado}»` : ''}.</Vacio>
        ) : (
          <ul className="grid gap-2">
            {lista.map((s) => (
              <TarjetaSolicitud key={`${s.id}-${s.actualizado_en}`} s={s} elegida={s.id === elegida} onElegir={() => setElegida(s.id)} onCambio={recargar} />
            ))}
          </ul>
        )}
      </section>
      <div className="grid content-start gap-2 xl:sticky xl:top-4">
        <Mapa className="h-[50vh] min-h-80" marcadores={marcadores} trazo={actual ? [aLeaflet(actual.origen.coordinates), aLeaflet(actual.destino.coordinates)] : undefined} estiloTrazo="trazo-a-pie" />
        <p className="text-xs text-texto-suave">Elige una solicitud para ver su origen (A) y destino.</p>
      </div>
    </div>
  )
}
