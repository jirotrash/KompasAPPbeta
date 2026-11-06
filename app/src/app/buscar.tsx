import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, TextInput } from 'react-native';
import { XStack, YStack } from 'tamagui';

import { AvisoSinInformacion, Cargando, MensajeError, MensajeInfo } from '@/components/Avisos';
import { BotonSecundario } from '@/components/Botones';
import { ChipGroup } from '@/components/Chips';
import Icono from '@/components/Icono';
import Pantalla from '@/components/Pantalla';
import PedirRuta from '@/components/PedirRuta';
import TarjetaTransporte from '@/components/TarjetaTransporte';
import { Texto } from '@/components/ui';
import { CATEGORIAS, iconoDeInteres } from '@/constants/catalogos';
import { PUNTOS_REFERENCIA, type Coordenada } from '@/constants/zona';
import { useTema } from '@/context/Tema';
import { useUbicacion } from '@/context/Ubicacion';
import { useViaje } from '@/context/Viaje';
import useAlternativas from '@/hooks/useAlternativas';
import { buscarLugares, guardarRecorrido, USA_MOCK } from '@/services/api';
import { buscarDirecciones, type Direccion } from '@/services/mapas';
import type { Alternativa, Lugar } from '@/types/dominio';
import { desdeGeoJSON, normalizarTexto } from '@/utils/geo';
import { recorridoDesdeAlternativa } from '@/utils/recorrido';
import { ordenarAlternativas, type FiltroTransporte, type OrdenTransporte } from '@/utils/transporte';

type Destino = Coordenada & { id: string; nombre: string; detalle?: string };

const MIN_LETRAS = 3;
/** Buscar a dónde ir (lugares propios + direcciones de OpenStreetMap) y ver cómo llegar. */
export default function Buscar() {
  const { paleta } = useTema();
  const { posicion, estado: estadoUbicacion } = useUbicacion();
  const { setRecorrido } = useViaje();
  // lugar: id de un lugar propio; q: texto para buscar (p. ej. el destino de una tarjeta del asistente)
  const params = useLocalSearchParams<{ lugar?: string; q?: string }>();

  const [lugares, setLugares] = useState<Lugar[]>([]);
  const [texto, setTexto] = useState(params.q ?? '');
  const [remoto, setRemoto] = useState<{ consulta: string; lista: Direccion[]; error: boolean }>({ consulta: '', lista: [], error: false });
  const [destino, setDestino] = useState<Destino | null>(null);
  const [origenManual, setOrigenManual] = useState<Destino | null>(null);
  const [elegirOrigen, setElegirOrigen] = useState(false);
  const [filtro, setFiltro] = useState<FiltroTransporte>('todos');
  const [orden, setOrden] = useState<OrdenTransporte>('tiempo');
  const origen = origenManual ?? posicion;
  const { resultado: rutas, cargando: cargandoRutas, reintentar } = useAlternativas(origen, destino);
  const opciones = ordenarAlternativas(rutas?.respuesta?.alternativas ?? [], filtro, orden);

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
    setDestino(d);
    reintentar();
  };

  const verEnMapa = (a: Alternativa) => {
    if (!rutas?.respuesta) return;
    setRecorrido(recorridoDesdeAlternativa(a, rutas.origen, rutas.destino, rutas.hora));
    // El asistente aprende de este historial. Solo las opciones en autobús traen una ruta de Kompás;
    // en las combinadas cuenta la última ruta (la que lleva al destino).
    const idRuta = a.id_ruta ?? a.tramos?.filter((t) => t.modo === 'autobus').at(-1)?.id_ruta;
    if (idRuta != null && !a.ejemplo) {
      const minutos = (a.tiempos.caminata ?? 0) + (a.tiempos.espera ?? 0) + (a.tiempos.trayecto ?? 0);
      guardarRecorrido({ id_ruta: idRuta, transporte: 'Transporte público', tiempo_estimado: minutos }).catch(() => undefined);
    }
    router.navigate('/mapa');
  };

  return (
    <Pantalla bordes={['left', 'right']}>
      <Texto tam="xl" peso="fuerte" mb={12}>Compara tu transporte</Texto>
      <XStack items="center" gap={10} rounded={14} borderWidth={1} borderColor="$borde" bg="$tarjeta" px={14} minH={48}>
        <YStack width={10} height={10} rounded={999} bg="$primario" />
        <Texto flex={1} numberOfLines={1} tam="sm" suave>
          Desde:{' '}
          <Texto tam="sm" peso="semi">
            {origen.nombre}
          </Texto>
        </Texto>
      </XStack>

      <YStack gap={10} mt={10}>
        <Texto tam="xs" suave>{origenManual || estadoUbicacion !== 'gps' ? 'Origen de referencia; no es tu ubicación GPS.' : 'Origen obtenido de tu ubicación actual.'}</Texto>
        <BotonSecundario texto={elegirOrigen ? 'Cerrar selección de origen' : 'Cambiar origen'} onPress={() => setElegirOrigen((v) => !v)} />
        {elegirOrigen && <ChipGroup
          opciones={[{ valor: 'ubicacion', texto: estadoUbicacion === 'gps' ? 'Mi ubicación' : 'Ubicación de referencia' }, ...PUNTOS_REFERENCIA.map((p) => ({ valor: p.id, texto: p.nombre }))]}
          valor={origenManual?.id ?? 'ubicacion'}
          onCambiar={(id) => { setOrigenManual(PUNTOS_REFERENCIA.find((p) => p.id === id) ?? null); setElegirOrigen(false); reintentar(); }}
        />}
      </YStack>

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
        <MensajeError>{rutas?.error}</MensajeError>
        {rutas?.error && <BotonSecundario texto="Reintentar búsqueda de transporte" onPress={reintentar} />}

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

        {rutas?.respuesta && (
          <>
            <Texto tam="lg" peso="fuerte">
              Opciones de transporte
            </Texto>
            {!rutas.respuesta.datos_suficientes && <AvisoSinInformacion mensaje={rutas.respuesta.mensaje} />}
            {/* Sin camión dentro de la zona (fuera de ella no hay alternativas): se puede pedir la ruta al equipo */}
            {!rutas.respuesta.datos_suficientes && rutas.respuesta.alternativas.length > 0 && (
              <PedirRuta key={rutas.clave} origen={rutas.origen} destino={rutas.destino} />
            )}
            {USA_MOCK && <MensajeInfo>Modo demostración: las líneas de ejemplo no representan un servicio real.</MensajeInfo>}
            <Texto tam="sm" peso="semi">Medio de transporte</Texto>
            <ChipGroup opciones={[{ valor: 'todos', texto: 'Todos' }, { valor: 'autobus', texto: 'Autobús' }, { valor: 'auto', texto: 'Taxi / App' }, { valor: 'pie', texto: 'A pie' }]} valor={filtro} onCambiar={setFiltro} />
            <Texto tam="sm" peso="semi">Ordenar opciones</Texto>
            <ChipGroup opciones={[{ valor: 'tiempo', texto: 'Tiempo calculado' }, { valor: 'caminata', texto: 'Menos caminata' }, { valor: 'transbordos', texto: 'Menos transbordos' }]} valor={orden} onCambiar={setOrden} />
            <Texto tam="xs" suave>Los tiempos parciales no permiten asegurar cuál llega antes. Las tarifas sin dato se muestran por confirmar.</Texto>
            <Texto tam="sm" peso="semi">{opciones.length} opción{opciones.length === 1 ? '' : 'es'} · consulta de las {rutas.hora}</Texto>
            {opciones.length === 0 && <MensajeInfo>No hay opciones para este filtro. Prueba otro medio de transporte.</MensajeInfo>}
            {opciones.map((a) => <TarjetaTransporte key={`${rutas.clave}-${a.id}`} alternativa={a} origen={rutas.origen} onMapa={() => verEnMapa(a)} />)}
            <BotonSecundario texto="Actualizar alternativas" onPress={reintentar} />
          </>
        )}

        <YStack mt={8} gap={8}>
          <Texto tam="sm" suave>
            Laboratorios académicos: cómo explora DFS todos los caminos de una red y cómo se mide la distancia por calles.
          </Texto>
          <BotonSecundario texto="Ver demostración DFS" icono="ruta" onPress={() => router.push('/dfs')} />
          <BotonSecundario texto="Comparar distancias Euclidiana y Manhattan" icono="regla" onPress={() => router.push('/distancias')} />
        </YStack>
      </YStack>
    </Pantalla>
  );
}
