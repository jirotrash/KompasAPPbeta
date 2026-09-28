import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, TextInput } from 'react-native';
import { XStack, YStack } from 'tamagui';

import { AvisoSinInformacion, Cargando, EtiquetaEjemplo, MensajeError } from '@/components/Avisos';
import ExplicacionReglas from '@/components/ExplicacionReglas';
import Icono from '@/components/Icono';
import Pantalla from '@/components/Pantalla';
import { Tarjeta, Texto } from '@/components/ui';
import { CATEGORIAS, iconoDeInteres, MODOS } from '@/constants/catalogos';
import { PUNTOS_REFERENCIA, type Coordenada } from '@/constants/zona';
import { useTema } from '@/context/Tema';
import { useUbicacion } from '@/context/Ubicacion';
import { useViaje } from '@/context/Viaje';
import { buscarLugares, buscarRutas } from '@/services/api';
import { buscarDirecciones, type Direccion } from '@/services/mapas';
import type { Alternativa, Lugar, RespuestaRutas } from '@/types/dominio';
import { desdeGeoJSON, formatoKm, formatoMinutos, horaActual, normalizarTexto } from '@/utils/geo';
import { recorridoDesdeAlternativa } from '@/utils/recorrido';

type Destino = Coordenada & { id: string; nombre: string; detalle?: string };

const MIN_LETRAS = 3;
const total = (a: Alternativa) => (a.tiempos.caminata ?? 0) + (a.tiempos.espera ?? 0) + (a.tiempos.trayecto ?? 0);

function TarjetaAlternativa({ a, onPress }: { a: Alternativa; onPress: () => void }) {
  const { paleta } = useTema();
  const modo = MODOS[a.modo];
  return (
    <Tarjeta>
      <YStack
        gap={8}
        role="button"
        aria-label={`${a.linea ?? modo.texto}. Ver en el mapa`}
        onPress={onPress}
        cursor="pointer"
        pressStyle={{ opacity: 0.75 }}
      >
        <XStack items="center" gap={12}>
          <YStack width={44} height={44} rounded={14} bg="$suave" items="center" justify="center">
            <Icono nombre={modo.icono} color={paleta.primario} tamano={22} />
          </YStack>
          <YStack flex={1}>
            <Texto peso="fuerte">{a.linea ?? modo.texto}</Texto>
            {a.sentido && (
              <Texto tam="xs" suave>
                Sentido {a.sentido}
              </Texto>
            )}
            {a.distancia_km != null && (
              <Texto tam="xs" suave>
                ~{formatoKm(a.distancia_km)}
              </Texto>
            )}
          </YStack>
          <YStack items="flex-end">
            <Texto tam="lg" peso="fuerte" acento>
              {formatoMinutos(total(a))}
            </Texto>
            <Texto tam="xs" suave>
              estimado
            </Texto>
          </YStack>
        </XStack>
        {a.ejemplo && <EtiquetaEjemplo />}
        {a.modo === 'autobus' && (
          <YStack gap={2}>
            <Texto tam="sm">
              <Texto tam="sm" peso="fuerte" color="$ok">
                ↑ Sube en:{' '}
              </Texto>
              {a.abordaje?.nombre}
            </Texto>
            <Texto tam="sm">
              <Texto tam="sm" peso="fuerte" color="$aviso">
                ↓ Baja en:{' '}
              </Texto>
              {a.descenso?.nombre}
            </Texto>
            <Texto tam="xs" suave>
              Caminata {formatoMinutos(a.tiempos.caminata)} · espera {formatoMinutos(a.tiempos.espera)} · trayecto{' '}
              {formatoMinutos(a.tiempos.trayecto)} · tarifa {a.tarifa != null ? `$${a.tarifa}` : 'por confirmar'}
            </Texto>
          </YStack>
        )}
        {a.avisos?.map((t) => (
          <Texto key={t} tam="xs" color="$aviso">
            ⚠ {t}
          </Texto>
        ))}
      </YStack>
      <ExplicacionReglas reglas={a.reglas_cumplidas} />
      <Texto tam="xs" suave>
        Fuente: {a.fuente}
      </Texto>
    </Tarjeta>
  );
}

/** Buscar a dónde ir (lugares propios + direcciones de OpenStreetMap) y ver cómo llegar. */
export default function Buscar() {
  const { paleta } = useTema();
  const { posicion } = useUbicacion();
  const { setRecorrido } = useViaje();
  const params = useLocalSearchParams<{ lugar?: string }>();

  const [lugares, setLugares] = useState<Lugar[]>([]);
  const [texto, setTexto] = useState('');
  const [remoto, setRemoto] = useState<{ consulta: string; lista: Direccion[]; error: boolean }>({ consulta: '', lista: [], error: false });
  const [destino, setDestino] = useState<Destino | null>(null);
  const [rutas, setRutas] = useState<{ para: Destino; respuesta: RespuestaRutas } | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    buscarLugares({ cerca: posicion })
      .then(setLugares)
      .catch(() => setLugares([]));
  }, [posicion]);

  // Si se llegó desde una tarjeta de lugar, ese lugar es el destino (solo la primera vez)
  const lugarInicial = useRef(params.lugar);
  useEffect(() => {
    const l = lugares.find((x) => x._id === lugarInicial.current);
    if (!l) return;
    lugarInicial.current = undefined;
    setDestino({ id: l._id, nombre: l.nombre, ...desdeGeoJSON(l.ubicacion.coordinates) });
  }, [lugares]);

  // Direcciones de OpenStreetMap con espera entre teclas
  const consulta = texto.trim();
  useEffect(() => {
    if (consulta.length < MIN_LETRAS) return;
    const control = new AbortController();
    const t = setTimeout(() => {
      buscarDirecciones(consulta, control.signal)
        .then((lista) => setRemoto({ consulta, lista, error: false }))
        .catch((e) => e?.name !== 'AbortError' && setRemoto({ consulta, lista: [], error: true }));
    }, 350);
    return () => {
      clearTimeout(t);
      control.abort();
    };
  }, [consulta]);

  // Alternativas de traslado hacia el destino elegido
  useEffect(() => {
    if (!destino) return;
    let activo = true;
    buscarRutas({ origen: posicion, destino, hora: horaActual() })
      .then((respuesta) => activo && setRutas({ para: destino, respuesta }))
      .catch((e) => activo && setError(e instanceof Error ? e.message : 'No se pudieron buscar rutas.'));
    return () => {
      activo = false;
    };
  }, [destino, posicion]);

  const n = normalizarTexto(consulta);
  const propios: Destino[] = [
    ...PUNTOS_REFERENCIA.map((p) => ({ ...p, detalle: 'Punto de referencia' })),
    ...lugares.map((l) => ({
      id: l._id,
      nombre: l.nombre,
      detalle: `${CATEGORIAS[l.categoria] ?? l.categoria} · ${l.municipio ?? ''}`,
      ...desdeGeoJSON(l.ubicacion.coordinates),
    })),
  ].filter((o) => !n || normalizarTexto(o.nombre).includes(n));
  const remotos = remoto.consulta === consulta && consulta.length >= MIN_LETRAS ? remoto.lista : [];
  const buscandoRemoto = consulta.length >= MIN_LETRAS && remoto.consulta !== consulta;
  const sugerencias = [
    ...propios.slice(0, n ? 6 : 8),
    ...remotos.filter((r) => !propios.some((p) => normalizarTexto(p.nombre) === normalizarTexto(r.nombre))),
  ];

  const elegir = (d: Destino) => {
    setError('');
    setDestino(d);
  };

  const verEnMapa = (a: Alternativa) => {
    if (!destino) return;
    setRecorrido(recorridoDesdeAlternativa(a, posicion, destino, horaActual()));
    router.navigate('/mapa');
  };

  const cargandoRutas = destino && rutas?.para !== destino && !error;

  return (
    <Pantalla bordes={['left', 'right']}>
      <XStack items="center" gap={10} rounded={14} borderWidth={1} borderColor="$borde" bg="$tarjeta" px={14} minH={48}>
        <YStack width={10} height={10} rounded={999} bg="$primario" />
        <Texto flex={1} numberOfLines={1} tam="sm" suave>
          Desde:{' '}
          <Texto tam="sm" peso="semi">
            {posicion.nombre}
          </Texto>
        </Texto>
      </XStack>

      {destino ? (
        <XStack mt={12} minH={56} items="center" gap={12} rounded={14} borderWidth={2} borderColor="$primario" bg="$tarjeta" px={16}>
          <Icono nombre="ubicacion" color="#EA4335" tamano={20} />
          <YStack flex={1} py={8}>
            <Texto numberOfLines={1} peso="semi">
              {destino.nombre}
            </Texto>
            {destino.detalle && (
              <Texto tam="xs" suave>
                {destino.detalle}
              </Texto>
            )}
          </YStack>
          <XStack
            role="button"
            aria-label="Cambiar destino"
            p={6}
            cursor="pointer"
            onPress={() => {
              setDestino(null);
              setRutas(null);
            }}
          >
            <Icono nombre="cerrar" color={paleta.textoSuave} tamano={20} />
          </XStack>
        </XStack>
      ) : (
        <XStack mt={12} minH={56} items="center" gap={12} rounded={14} borderWidth={2} borderColor="$primario" bg="$tarjeta" px={16}>
          <Icono nombre="buscar" color={paleta.textoSuave} tamano={20} />
          <TextInput
            autoFocus
            value={texto}
            onChangeText={setTexto}
            placeholder="Busca un lugar o dirección"
            placeholderTextColor={paleta.textoSuave}
            returnKeyType="search"
            aria-label="Buscar destino"
            style={{ flex: 1, paddingVertical: 12, fontSize: 16, color: paleta.texto, outlineStyle: 'none' } as object}
          />
          {buscandoRemoto && <ActivityIndicator color={paleta.primario} />}
        </XStack>
      )}

      <YStack mt={16} gap={12}>
        <MensajeError>{error}</MensajeError>

        {!destino && (
          <YStack overflow="hidden" rounded={16} borderWidth={1} borderColor="$borde" bg="$tarjeta">
            {sugerencias.map((s, i) => {
              const lugar = lugares.find((l) => l._id === s.id);
              return (
                <XStack
                  key={s.id}
                  minH={56}
                  items="center"
                  gap={12}
                  px={16}
                  py={8}
                  borderTopWidth={i > 0 ? 1 : 0}
                  borderColor="$borde"
                  role="button"
                  aria-label={s.nombre}
                  onPress={() => elegir(s)}
                  cursor="pointer"
                  pressStyle={{ bg: '$suave' }}
                >
                  <YStack width={36} height={36} rounded={999} bg="$fondo" items="center" justify="center">
                    <Icono nombre={lugar ? iconoDeInteres(lugar.interes) : 'ubicacion'} color={paleta.textoSuave} tamano={18} />
                  </YStack>
                  <YStack flex={1}>
                    <Texto numberOfLines={1} peso="medio">
                      {s.nombre}
                    </Texto>
                    {!!s.detalle && (
                      <Texto numberOfLines={1} tam="xs" suave>
                        {s.detalle}
                      </Texto>
                    )}
                  </YStack>
                </XStack>
              );
            })}
            {consulta.length >= MIN_LETRAS && !buscandoRemoto && sugerencias.length === 0 && (
              <Texto p={16} tam="sm" suave>
                {remoto.error ? 'No se pudo buscar direcciones; revisa tu conexión.' : 'Sin resultados en Toluca, Lerma o San Mateo Atenco.'}
              </Texto>
            )}
            {remotos.length > 0 && (
              <Texto px={16} pb={8} tam="xs" suave text="right">
                Direcciones: © OpenStreetMap
              </Texto>
            )}
          </YStack>
        )}

        {cargandoRutas && <Cargando texto="Buscando cómo llegar…" />}

        {rutas?.para === destino && (
          <>
            <Texto tam="lg" peso="fuerte">
              Cómo llegar
            </Texto>
            {!rutas.respuesta.datos_suficientes && <AvisoSinInformacion mensaje={rutas.respuesta.mensaje} />}
            {rutas.respuesta.alternativas.map((a) => (
              <TarjetaAlternativa key={a.id} a={a} onPress={() => verEnMapa(a)} />
            ))}
            <Texto tam="xs" suave>
              Toca una opción para verla en el mapa. Salida: ahora ({horaActual()}).
            </Texto>
          </>
        )}
      </YStack>
    </Pantalla>
  );
}
