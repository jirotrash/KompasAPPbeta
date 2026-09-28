import { useCallback, useEffect, useMemo, useState } from 'react'
import { Cargando, MensajeError } from '../components/Avisos.jsx'
import Chip from '../components/Chip.jsx'
import { IconoReporte } from '../components/Iconos.jsx'
import Mapa from '../components/Mapa.jsx'
import Pagina from '../components/Pagina.jsx'
import SelectorPunto from '../components/SelectorPunto.jsx'
import useLugares from '../hooks/useLugares.js'
import { crearReporte, obtenerReportes } from '../services/api.js'
import { TIPOS_REPORTE } from '../utils/dominio.js'
import { aGeoJSON, aLeaflet } from '../utils/geo.js'

const NIVELES = ['baja', 'media', 'alta']

const ESTADOS = {
  pendiente: 'bg-aviso-fondo text-aviso',
  verificado: 'bg-ok-fondo text-ok',
  descartado: 'bg-fondo text-texto-suave',
}

// Fecha local en formato de <input type="datetime-local">
const ahoraLocal = () => {
  const d = new Date()
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 16)
}

const formatoHora = (iso) =>
  new Date(iso).toLocaleString('es-MX', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })

export default function Reportar() {
  const lugares = useLugares()
  const [tipo, setTipo] = useState('afluencia')
  const [nivel, setNivel] = useState('media')
  const [ubicacion, setUbicacion] = useState(null)
  const [observado, setObservado] = useState(ahoraLocal)
  const [comentario, setComentario] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState('')
  const [creado, setCreado] = useState(null)

  const [vigentes, setVigentes] = useState(null)
  const cargarVigentes = useCallback(() => {
    obtenerReportes()
      .then((lista) => setVigentes(lista ?? []))
      .catch(() => setVigentes([]))
  }, [])
  useEffect(cargarVigentes, [cargarVigentes])

  async function enviar(e) {
    e.preventDefault()
    if (!ubicacion) return setError('Indica dónde ocurre.')
    setError('')
    setEnviando(true)
    try {
      const esLugar = lugares.some((l) => l._id === ubicacion.id)
      const nuevo = await crearReporte({
        tipo,
        nivel_afluencia: tipo === 'afluencia' ? nivel : undefined,
        ubicacion: { type: 'Point', coordinates: aGeoJSON([ubicacion.lat, ubicacion.lng]) },
        lugar_id: esLugar ? ubicacion.id : undefined,
        observado_en: new Date(observado).toISOString(),
        comentario: comentario.trim() || undefined,
      })
      setCreado(nuevo)
      setComentario('')
      cargarVigentes()
    } catch (err) {
      setError(err.message)
    } finally {
      setEnviando(false)
    }
  }

  const marcadores = useMemo(
    () =>
      (vigentes ?? []).map((r) => {
        const [lat, lng] = aLeaflet(r.ubicacion.coordinates)
        return { id: r._id, tipo: 'reporte', lat, lng, titulo: `${TIPOS_REPORTE[r.tipo]} · ${r.estado}` }
      }),
    [vigentes],
  )

  return (
    <Pagina titulo="Reportar" descripcion="Tu reporte ayuda a otros a decidir cómo moverse." ancho="max-w-6xl">
      <div
        role="note"
        className="mb-5 flex gap-3 rounded-2xl border border-peligro/20 bg-peligro-fondo p-4 text-sm text-peligro"
      >
        <IconoReporte className="size-5 shrink-0" />
        <p>
          <strong>Esto no es un servicio de emergencias.</strong> Si hay personas heridas o en peligro, llama al{' '}
          <a href="tel:911" className="font-bold underline">
            911
          </a>
          .
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
        <form onSubmit={enviar} className="tarjeta space-y-5 md:p-6">
          <fieldset>
            <legend className="etiqueta">¿Qué quieres reportar?</legend>
            <div className="flex flex-wrap gap-2">
              {Object.entries(TIPOS_REPORTE).map(([valor, texto]) => (
                <Chip key={valor} activo={tipo === valor} onClick={() => setTipo(valor)}>
                  {texto}
                </Chip>
              ))}
            </div>
          </fieldset>

          {tipo === 'afluencia' && (
            <fieldset>
              <legend className="etiqueta">Nivel de afluencia</legend>
              <div className="flex flex-wrap gap-2">
                {NIVELES.map((n) => (
                  <Chip key={n} activo={nivel === n} onClick={() => setNivel(n)}>
                    {n[0].toUpperCase() + n.slice(1)}
                  </Chip>
                ))}
              </div>
            </fieldset>
          )}

          <SelectorPunto etiqueta="¿Dónde?" valor={ubicacion} onCambiar={setUbicacion} lugares={lugares} tipoMarcador="reporte" />

          <div className="grid gap-5 sm:grid-cols-2">
            <div>
              <label htmlFor="observado" className="etiqueta">
                ¿Cuándo lo viste?
              </label>
              <input
                id="observado"
                type="datetime-local"
                className="campo"
                value={observado}
                max={ahoraLocal()}
                onChange={(e) => setObservado(e.target.value)}
              />
            </div>
          </div>

          <div>
            <label htmlFor="comentario" className="etiqueta">
              Comentario (opcional)
            </label>
            <textarea
              id="comentario"
              rows={3}
              maxLength={280}
              className="campo resize-y"
              value={comentario}
              onChange={(e) => setComentario(e.target.value)}
              placeholder="Ej. Cerrado un carril sobre la avenida"
            />
            <p className="mt-1 text-right text-xs text-texto-suave">{comentario.length}/280</p>
          </div>

          <MensajeError>{error}</MensajeError>
          {creado && (
            <p role="status" className="rounded-xl bg-ok-fondo p-3 text-sm text-ok">
              ¡Gracias! Tu reporte quedó <strong>{creado.estado}</strong> de verificación y estará vigente hasta las{' '}
              {formatoHora(creado.vigente_hasta)}.
            </p>
          )}
          <button type="submit" className="boton-primario w-full sm:w-auto" disabled={enviando}>
            {enviando ? 'Enviando…' : 'Enviar reporte'}
          </button>
        </form>

        <aside className="space-y-3">
          <h2 className="text-lg font-bold">Reportes vigentes</h2>
          <Mapa className="h-56" marcadores={marcadores} />
          {vigentes === null && <Cargando />}
          {vigentes?.length === 0 && <p className="text-sm text-texto-suave">No hay reportes vigentes en la zona.</p>}
          <ul className="space-y-2">
            {vigentes?.map((r) => (
              <li key={r._id} className="tarjeta p-3 text-sm">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold">
                    {TIPOS_REPORTE[r.tipo]}
                    {r.nivel_afluencia && ` · ${r.nivel_afluencia}`}
                  </span>
                  <span className={`rounded-md px-1.5 py-0.5 text-xs font-semibold ${ESTADOS[r.estado] ?? ''}`}>
                    {r.estado}
                  </span>
                </div>
                <p className="text-xs text-texto-suave">
                  Visto: {formatoHora(r.observado_en)} · vigente hasta {formatoHora(r.vigente_hasta)} ·{' '}
                  {r.confirmaciones} confirmación(es)
                </p>
                {r.comentario && <p className="mt-1">{r.comentario}</p>}
              </li>
            ))}
          </ul>
        </aside>
      </div>
    </Pagina>
  )
}
