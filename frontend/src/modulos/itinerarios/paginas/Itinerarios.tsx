import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { AvisoSinInformacion, Cargando, MensajeError } from '../../../compartido/componentes/Avisos.tsx'
import Chip from '../../../compartido/componentes/Chip.tsx'
import ExplicacionReglas from '../componentes/ExplicacionReglas.tsx'
import type { PuntoElegido } from '../../../compartido/componentes/BuscadorLugar.tsx'
import Mapa, { type MarcadorMapa } from '../../../compartido/componentes/Mapa.tsx'
import type { RespuestaItinerarios } from '../../../compartido/tipos/dominio.ts'
import Pagina from '../../../compartido/componentes/Pagina.tsx'
import SelectorPunto from '../../../compartido/componentes/SelectorPunto.tsx'
import TarjetaLugar from '../../../compartido/componentes/TarjetaLugar.tsx'
import { PUNTOS_REFERENCIA } from '../../../compartido/config/zona.ts'
import { USA_MOCK } from '../../../compartido/api/cliente.ts'
import { generarItinerarios } from '../api.ts'
import { CATEGORIAS, CONTEXTOS, diaDeHoy, horaActual } from '../../../compartido/utils/dominio.ts'
import { aLeaflet, formatoMinutos } from '../../../compartido/utils/geo.ts'

const TIEMPOS: [number, string][] = [
  [60, '1 h'],
  [120, '2 h'],
  [180, '3 h'],
  [240, '4 h'],
  [360, '6 h'],
]

export default function Itinerarios() {
  const [contexto, setContexto] = useState('amigos')
  const [presupuesto, setPresupuesto] = useState<number | ''>(300)
  const [tiempo, setTiempo] = useState(180)
  const [gustos, setGustos] = useState<string[]>([])
  const [hora, setHora] = useState(horaActual)
  const [origen, setOrigen] = useState<PuntoElegido | null>(() => ({ ...PUNTOS_REFERENCIA[0] }))

  const [estado, setEstado] = useState<{ cargando: boolean; error: string; resultado: RespuestaItinerarios | null }>({ cargando: false, error: '', resultado: null })
  const [elegido, setElegido] = useState<string | null>(null)
  const resultadosRef = useRef<HTMLDivElement>(null)
  const dia = diaDeHoy()

  const alternarGusto = (g: string) => setGustos((lista) => (lista.includes(g) ? lista.filter((x) => x !== g) : [...lista, g]))

  async function generar(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!origen) return setEstado({ cargando: false, error: 'Elige desde dónde sales.', resultado: null })
    if (presupuesto === '' || !(presupuesto >= 0)) return setEstado({ cargando: false, error: 'Escribe un presupuesto válido.', resultado: null })
    setEstado({ cargando: true, error: '', resultado: null })
    try {
      const resultado = await generarItinerarios({
        contexto,
        presupuesto: Number(presupuesto),
        tiempo_min: tiempo,
        gustos,
        hora,
        dia,
        origen: { lat: origen.lat, lng: origen.lng },
      })
      setEstado({ cargando: false, error: '', resultado })
      setElegido(resultado.itinerarios?.[0]?.id ?? null)
    } catch (err) {
      setEstado({ cargando: false, error: err instanceof Error ? err.message : String(err), resultado: null })
    }
  }

  useEffect(() => {
    if (estado.resultado) resultadosRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [estado.resultado])

  const { resultado } = estado
  const itinerario = resultado?.itinerarios?.find((i) => i.id === elegido)
  const marcadores = useMemo(() => {
    const lista: MarcadorMapa[] = origen ? [{ id: 'origen', tipo: 'origen', lat: origen.lat, lng: origen.lng, titulo: origen.nombre }] : []
    itinerario?.lugares.forEach((l, i) => {
      const [lat, lng] = aLeaflet(l.ubicacion.coordinates)
      lista.push({ id: l._id, tipo: 'lugar', lat, lng, texto: String(i + 1), titulo: l.nombre })
    })
    return lista
  }, [origen, itinerario])

  return (
    <Pagina
      titulo="Armar una salida"
      descripcion="El sistema experto combina lugares según tu tiempo, presupuesto y gustos, y te explica por qué."
      ancho="max-w-6xl"
    >
      <form onSubmit={generar} className="tarjeta grid gap-5 md:grid-cols-2 md:p-6">
        <fieldset className="md:col-span-2">
          <legend className="etiqueta">¿Con quién sales?</legend>
          <div className="flex flex-wrap gap-2">
            {Object.entries(CONTEXTOS).map(([valor, texto]) => (
              <Chip key={valor} activo={contexto === valor} onClick={() => setContexto(valor)}>
                {texto}
              </Chip>
            ))}
          </div>
        </fieldset>

        <div>
          <label htmlFor="presupuesto" className="etiqueta">
            Presupuesto por persona (MXN)
          </label>
          <input
            id="presupuesto"
            type="number"
            inputMode="numeric"
            min="0"
            step="10"
            className="campo"
            value={presupuesto}
            onChange={(e) => setPresupuesto(e.target.value === '' ? '' : Number(e.target.value))}
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="tiempo" className="etiqueta">
              Tiempo disponible
            </label>
            <select id="tiempo" className="campo" value={tiempo} onChange={(e) => setTiempo(Number(e.target.value))}>
              {TIEMPOS.map(([min, texto]) => (
                <option key={min} value={min}>
                  {texto}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="hora-salida" className="etiqueta">
              Hora de salida
            </label>
            <input id="hora-salida" type="time" className="campo" value={hora} onChange={(e) => setHora(e.target.value)} />
          </div>
        </div>

        <fieldset className="md:col-span-2">
          <legend className="etiqueta">Gustos (opcional)</legend>
          <div className="flex flex-wrap gap-2">
            {Object.entries(CATEGORIAS).map(([valor, texto]) => (
              <Chip key={valor} activo={gustos.includes(valor)} onClick={() => alternarGusto(valor)}>
                {texto}
              </Chip>
            ))}
          </div>
        </fieldset>

        <div className="md:col-span-2">
          <SelectorPunto etiqueta="Sales desde" valor={origen} onCambiar={setOrigen} tipoMarcador="origen" />
        </div>

        <div className="md:col-span-2">
          <MensajeError>{estado.error}</MensajeError>
          <button type="submit" className="boton-primario mt-2 w-full sm:w-auto" disabled={estado.cargando}>
            {estado.cargando ? 'Evaluando lugares…' : 'Generar itinerarios'}
          </button>
        </div>
      </form>

      <div ref={resultadosRef} className="scroll-mt-20">
        {estado.cargando && <Cargando texto="El sistema experto está evaluando los lugares…" />}

        {resultado && (
          <div className="mt-8 space-y-8">
            {!resultado.datos_suficientes && <AvisoSinInformacion mensaje={resultado.mensaje} />}

            {resultado.itinerarios?.length > 0 && (
              <section>
                <h2 className="mb-3 text-xl font-bold">
                  {resultado.itinerarios.length === 1 ? '1 itinerario' : `${resultado.itinerarios.length} itinerarios`} para ti
                </h2>
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {resultado.itinerarios.map((it, n) => (
                    <article
                      key={it.id}
                      className={`tarjeta flex flex-col gap-4 ${it.id === elegido ? 'border-primario ring-2 ring-primario/30' : ''}`}
                    >
                      <header>
                        <p className="text-xs font-semibold uppercase tracking-wide text-primario">Opción {n + 1}</p>
                        <h3 className="text-lg font-semibold leading-snug">{it.titulo}</h3>
                      </header>
                      <dl className="grid grid-cols-2 gap-2 text-center">
                        <div className="rounded-lg bg-fondo p-2">
                          <dt className="text-[11px] uppercase text-texto-suave">Costo aprox.</dt>
                          <dd className="font-bold">${it.costo_total}</dd>
                        </div>
                        <div className="rounded-lg bg-fondo p-2">
                          <dt className="text-[11px] uppercase text-texto-suave">Tiempo estimado</dt>
                          <dd className="font-bold">{formatoMinutos(it.tiempo_total_min)}</dd>
                        </div>
                      </dl>
                      <ol className="space-y-3">
                        {it.lugares.map((l, i) => (
                          <li key={l._id}>
                            <TarjetaLugar lugar={l} indice={i + 1} dia={dia} />
                          </li>
                        ))}
                      </ol>
                      <p className="text-sm text-texto-suave">{it.explicacion}</p>
                      <ExplicacionReglas reglas={it.reglas_cumplidas} titulo="Reglas que se cumplieron" />
                      <button
                        type="button"
                        className={`mt-auto ${it.id === elegido ? 'boton-primario' : 'boton-secundario'}`}
                        onClick={() => setElegido(it.id)}
                      >
                        {it.id === elegido ? 'Viendo en el mapa' : 'Ver en el mapa'}
                      </button>
                    </article>
                  ))}
                </div>
                <Mapa className="mt-4 h-72 md:h-96" marcadores={marcadores} />
              </section>
            )}

            {resultado.descartados?.length > 0 && (
              <section>
                <h2 className="mb-1 text-xl font-bold">Lugares descartados</h2>
                <p className="mb-3 text-sm text-texto-suave">Estos lugares no cumplieron las reglas para tu salida.</p>
                <ul className="grid gap-3 md:grid-cols-2">
                  {resultado.descartados.map(({ lugar, reglas }) => (
                    <li key={lugar._id} className="tarjeta space-y-3">
                      <TarjetaLugar lugar={lugar} dia={dia} compacta />
                      <ExplicacionReglas reglas={reglas} titulo="Por qué se descartó" tono="peligro" />
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {USA_MOCK && (
              <p className="text-xs text-texto-suave">
                En modo demostración el motor de reglas se simula en el navegador; el definitivo corre en la API (Python).
              </p>
            )}
          </div>
        )}
      </div>
    </Pagina>
  )
}
