import { useEffect, useState } from 'react';
import { XStack, YStack } from 'tamagui';

import { AvisoSinInformacion, Cargando, MensajeError } from '@/components/Avisos';
import { BotonPrimario } from '@/components/Botones';
import Icono from '@/components/Icono';
import Pantalla from '@/components/Pantalla';
import { Pildora, Recuadro, Tarjeta, Texto, Titulo } from '@/components/ui';
import { useTema } from '@/context/Tema';
import { buscarRutasDfs, listarParadasDfs } from '@/services/api';
import type { ParadaDFS, PasoDFS, RespuestaDFS, RutaDFS } from '@/types/dominio';

const PROFUNDIDADES = [3, 5, 7];

function SelectorParada({ etiqueta, paradas, valor, onChange }: { etiqueta: string; paradas: ParadaDFS[]; valor: string; onChange: (id: string) => void }) {
  return (
    <YStack gap={8}>
      <Texto peso="semi">{etiqueta}</Texto>
      <YStack overflow="hidden" rounded={14} borderWidth={1} borderColor="$borde" bg="$tarjeta">
        {paradas.map((parada, indice) => {
          const activa = parada.id === valor;
          return (
            <XStack
              key={parada.id}
              role="radio"
              aria-checked={activa}
              aria-label={parada.nombre}
              onPress={() => onChange(parada.id)}
              cursor="pointer"
              minH={48}
              px={14}
              items="center"
              gap={10}
              borderTopWidth={indice ? 1 : 0}
              borderColor="$borde"
              bg={activa ? '$suave' : '$tarjeta'}
              pressStyle={{ opacity: 0.75 }}
            >
              <YStack width={18} height={18} rounded={99} borderWidth={2} borderColor={activa ? '$primario' : '$borde'} items="center" justify="center">
                {activa && <YStack width={8} height={8} rounded={99} bg="$primario" />}
              </YStack>
              <Texto flex={1} tam="sm" peso={activa ? 'semi' : 'normal'}>
                {parada.nombre}
              </Texto>
            </XStack>
          );
        })}
      </YStack>
    </YStack>
  );
}

function TarjetaRuta({ ruta, indice }: { ruta: RutaDFS; indice: number }) {
  return (
    <Tarjeta>
      <XStack items="center" justify="space-between" gap={12}>
        <Texto peso="fuerte">Camino {indice + 1}</Texto>
        <Pildora tono="suave">
          <Texto tam="xs" peso="fuerte" acento>
            {ruta.tiempo_total_minutos} min estimados
          </Texto>
        </Pildora>
      </XStack>
      <Texto tam="sm">{ruta.paradas.join(' → ')}</Texto>
      <Texto tam="xs" suave>
        {ruta.numero_transbordos} transbordo{ruta.numero_transbordos === 1 ? '' : 's'} · Sin costo: no hay tarifas verificadas.
      </Texto>
      <Recuadro>
        {ruta.tramos.map((tramo, tramoIndice) => (
          <Texto key={`${tramo.de}-${tramo.a}-${tramoIndice}`} tam="xs">
            {tramo.de} → {tramo.a} · {tramo.linea} · {tramo.tiempo_min} min
          </Texto>
        ))}
      </Recuadro>
    </Tarjeta>
  );
}

function GraficaIndagacion({ traza, paradas }: { traza: PasoDFS[]; paradas: ParadaDFS[] }) {
  const nombres = Object.fromEntries(paradas.map((parada) => [parada.id, parada.nombre]));
  const nombre = (id?: string | null) => (id ? (nombres[id] ?? id) : '');
  const titulo = (paso: PasoDFS) => {
    const actual = nombre(paso.nodo);
    const hacia = nombre(paso.hacia);
    if (paso.tipo === 'avanza') return `Explora ${actual} → ${hacia}`;
    if (paso.tipo === 'ciclo_evitado') return `Evita ciclo ${actual} → ${hacia}`;
    if (paso.tipo === 'objetivo') return `Llega al destino: ${actual}`;
    if (paso.tipo === 'limite') return `Detiene expansión en ${actual}`;
    if (paso.tipo === 'retroceso') return `Retrocede desde ${hacia} a ${actual}`;
    return `Visita ${actual}`;
  };
  const color = (paso: PasoDFS) => {
    if (paso.tipo === 'objetivo') return '$ok';
    if (paso.tipo === 'ciclo_evitado') return '$peligro';
    if (paso.tipo === 'limite') return '$aviso';
    if (paso.tipo === 'retroceso') return '$textoSuave';
    return '$primario';
  };

  return (
    <Tarjeta gap={10}>
      <Texto peso="fuerte">Gráfica de indagación</Texto>
      <Texto tam="xs" suave>
        Cada punto representa una decisión real tomada por DFS. La sangría indica la profundidad de la rama explorada.
      </Texto>
      <YStack gap={4}>
        {traza.map((paso) => (
          <XStack key={paso.paso} ml={Math.min(paso.profundidad, 5) * 12} gap={10} items="flex-start">
            <YStack width={22} items="center" pt={3}>
              <YStack width={12} height={12} rounded={99} bg={color(paso)} />
              {paso.paso !== traza.length && <YStack width={2} minH={42} bg="$borde" />}
            </YStack>
            <YStack flex={1} pb={10} gap={2}>
              <Texto tam="sm" peso="semi">{paso.paso}. {titulo(paso)}</Texto>
              <Texto tam="xs" suave>{paso.mensaje}</Texto>
              <Texto tam="xs" color="$textoSuave">Camino: {paso.camino.map(nombre).join(' → ')}</Texto>
            </YStack>
          </XStack>
        ))}
      </YStack>
    </Tarjeta>
  );
}

/** Visualiza la ejecución del DFS; no sustituye la búsqueda de rutas operativas. */
export default function DemostracionDfs() {
  const { paleta } = useTema();
  const [paradas, setParadas] = useState<ParadaDFS[]>([]);
  const [origen, setOrigen] = useState('');
  const [destino, setDestino] = useState('');
  const [profundidad, setProfundidad] = useState(5);
  const [resultado, setResultado] = useState<RespuestaDFS | null>(null);
  const [cargandoCatalogo, setCargandoCatalogo] = useState(true);
  const [buscando, setBuscando] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    listarParadasDfs()
      .then((lista) => {
        setParadas(lista);
        setOrigen(lista[0]?.id ?? '');
        setDestino(lista.at(-1)?.id ?? '');
      })
      .catch((causa) => setError(causa instanceof Error ? causa.message : 'No se pudo cargar la red DFS.'))
      .finally(() => setCargandoCatalogo(false));
  }, []);

  const buscar = () => {
    if (!origen || !destino || origen === destino) {
      setError('Selecciona paradas de origen y destino diferentes.');
      return;
    }
    setBuscando(true);
    setError('');
    buscarRutasDfs(origen, destino, profundidad)
      .then(setResultado)
      .catch((causa) => setError(causa instanceof Error ? causa.message : 'No se pudo ejecutar la búsqueda DFS.'))
      .finally(() => setBuscando(false));
  };

  return (
    <Pantalla bordes={['left', 'right']}>
      <YStack gap={16}>
        <XStack gap={12} p={16} rounded={16} bg="$avisoFondo" borderWidth={1} borderColor="$aviso">
          <Icono nombre="aviso" color={paleta.aviso} tamano={22} />
          <YStack flex={1} gap={4}>
            <Titulo fontSize={21} lineHeight={26}>Laboratorio DFS</Titulo>
            <Texto tam="sm" color="$aviso">
              Explora todos los caminos simples de una red académica. No son rutas ni tarifas reales de transporte.
            </Texto>
          </YStack>
        </XStack>

        {cargandoCatalogo ? (
          <Cargando texto="Cargando paradas de la demostración…" />
        ) : (
          <>
            <SelectorParada etiqueta="Parada de origen" paradas={paradas} valor={origen} onChange={(id) => { setOrigen(id); setResultado(null); }} />
            <SelectorParada etiqueta="Parada de destino" paradas={paradas} valor={destino} onChange={(id) => { setDestino(id); setResultado(null); }} />
            <YStack gap={8}>
              <Texto peso="semi">Profundidad máxima</Texto>
              <XStack gap={8}>
                {PROFUNDIDADES.map((valor) => (
                  <XStack
                    key={valor}
                    flex={1}
                    minH={44}
                    rounded={12}
                    items="center"
                    justify="center"
                    role="radio"
                    aria-checked={profundidad === valor}
                    onPress={() => setProfundidad(valor)}
                    cursor="pointer"
                    bg={profundidad === valor ? '$primario' : '$tarjeta'}
                    borderWidth={1}
                    borderColor={profundidad === valor ? '$primario' : '$borde'}
                  >
                    <Texto peso="fuerte" color={profundidad === valor ? '$sobrePrimario' : '$texto'}>
                      {valor} aristas
                    </Texto>
                  </XStack>
                ))}
              </XStack>
            </YStack>
            <BotonPrimario texto="Explorar rutas DFS" icono="ruta" onPress={buscar} cargando={buscando} />
          </>
        )}

        <MensajeError>{error}</MensajeError>

        {resultado && (
          <YStack gap={12}>
            {!resultado.datos_verificados && <AvisoSinInformacion mensaje={resultado.aviso ?? undefined} />}
            <Tarjeta>
              <Texto peso="fuerte">Cómo trabajó DFS</Texto>
              <Texto tam="sm">Visitó {resultado.total_nodos_explorados} nodos y encontró {resultado.total_rutas_encontradas} caminos.</Texto>
              <Texto tam="xs" suave>
                Orden de exploración: {resultado.orden_exploracion.join(' → ')}
              </Texto>
              <Texto tam="xs" suave>
                Fuente: {resultado.fuente}
              </Texto>
            </Tarjeta>
            <GraficaIndagacion traza={resultado.traza} paradas={paradas} />
            {resultado.rutas.map((ruta, indice) => <TarjetaRuta key={ruta.nodos_id.join('-')} ruta={ruta} indice={indice} />)}
          </YStack>
        )}
      </YStack>
    </Pantalla>
  );
}
