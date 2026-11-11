import { useEffect, useState } from 'react';
import { ActivityIndicator } from 'react-native';
import { XStack, YStack } from 'tamagui';

import { EtiquetaEjemplo, MensajeError } from '@/components/Avisos';
import { BotonPrimario, BotonSecundario } from '@/components/Botones';
import Icono from '@/components/Icono';
import Pantalla from '@/components/Pantalla';
import { Pildora, Recuadro, Subtitulo, Tarjeta, Texto, Titulo } from '@/components/ui';
import { useTema } from '@/context/Tema';
import {
  obtenerMetricasIA,
  simularPrediccionIA,
  USA_MOCK,
  ZONAS_BFS_KOMPAS,
  type MetricasLaboratorioIA,
  type PeticionSimulacionIA,
  type RespuestaSimulacionIA,
} from '@/services/api';

const ESCENARIOS_RAPIDOS: { etiqueta: string; datos: PeticionSimulacionIA }[] = [
  {
    etiqueta: 'Paseo corto Centro',
    datos: {
      distancia_km: 1.8,
      presupuesto_mxn: 120,
      rating_lugar: 4.7,
      num_paradas: 2,
      trafico_nivel: 4,
      origen: 'Cosmovitral',
      destino: 'Los Portales',
    },
  },
  {
    etiqueta: 'Tour Metepec (4 paradas)',
    datos: {
      distancia_km: 7.5,
      presupuesto_mxn: 260,
      rating_lugar: 4.6,
      num_paradas: 4,
      trafico_nivel: 6,
      origen: 'Terminal Toluca',
      destino: 'Galerias Metepec',
    },
  },
  {
    etiqueta: 'Presupuesto ajustado (6 paradas)',
    datos: {
      distancia_km: 14.0,
      presupuesto_mxn: 75,
      rating_lugar: 4.1,
      num_paradas: 6,
      trafico_nivel: 8,
      origen: 'Cosmovitral',
      destino: 'Plazas Outlet Lerma',
    },
  },
];

const pct = (valor: number) => `${(valor * 100).toFixed(1)}%`;

function BarraProgreso({
  valor,
  color,
  fondo,
}: {
  valor: number;
  color: string;
  fondo: string;
}) {
  const anchoPct = Math.max(4, Math.min(100, Math.round(valor * 100)));
  return (
    <YStack height={8} width="100%" rounded={999} overflow="hidden" style={{ backgroundColor: fondo }}>
      <YStack height="100%" rounded={999} style={{ width: `${anchoPct}%`, backgroundColor: color }} />
    </YStack>
  );
}

function ControlNumerico({
  etiqueta,
  valorTexto,
  onMenos,
  onMas,
}: {
  etiqueta: string;
  valorTexto: string;
  onMenos: () => void;
  onMas: () => void;
}) {
  return (
    <XStack items="center" justify="space-between" py={6} gap={8}>
      <YStack flex={1}>
        <Texto tam="sm" peso="medio">
          {etiqueta}
        </Texto>
      </YStack>
      <XStack items="center" gap={8}>
        <XStack
          width={34}
          height={34}
          rounded={10}
          borderWidth={1}
          borderColor="$borde"
          bg="$fondo"
          items="center"
          justify="center"
          role="button"
          aria-label={`Disminuir ${etiqueta}`}
          onPress={onMenos}
          cursor="pointer"
          pressStyle={{ bg: '$suave' }}
        >
          <Texto peso="fuerte">−</Texto>
        </XStack>
        <YStack minW={78} items="center">
          <Texto peso="fuerte" tam="sm">
            {valorTexto}
          </Texto>
        </YStack>
        <XStack
          width={34}
          height={34}
          rounded={10}
          borderWidth={1}
          borderColor="$borde"
          bg="$fondo"
          items="center"
          justify="center"
          role="button"
          aria-label={`Aumentar ${etiqueta}`}
          onPress={onMas}
          cursor="pointer"
          pressStyle={{ bg: '$suave' }}
        >
          <Texto peso="fuerte">+</Texto>
        </XStack>
      </XStack>
    </XStack>
  );
}

export default function LaboratorioIA() {
  const { paleta } = useTema();
  const [metricas, setMetricas] = useState<MetricasLaboratorioIA | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');

  const [form, setForm] = useState<Required<PeticionSimulacionIA>>({
    distancia_km: 7.5,
    presupuesto_mxn: 260,
    rating_lugar: 4.6,
    num_paradas: 4,
    trafico_nivel: 6,
    origen: 'Terminal Toluca',
    destino: 'Galerias Metepec',
  });
  const [simulacion, setSimulacion] = useState<RespuestaSimulacionIA | null>(null);
  const [simulando, setSimulando] = useState(false);

  useEffect(() => {
    let cancelado = false;
    Promise.all([obtenerMetricasIA(), simularPrediccionIA(form)])
      .then(([datosMetricas, datosSim]) => {
        if (cancelado) return;
        setMetricas(datosMetricas);
        setSimulacion(datosSim);
      })
      .catch((e) => {
        if (!cancelado) setError(e instanceof Error ? e.message : 'No se pudieron cargar las métricas de IA.');
      })
      .finally(() => {
        if (!cancelado) setCargando(false);
      });
    return () => {
      cancelado = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const ejecutarSimulacion = async (nuevoForm = form) => {
    setSimulando(true);
    try {
      const res = await simularPrediccionIA(nuevoForm);
      setSimulacion(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo ejecutar la simulación.');
    } finally {
      setSimulando(false);
    }
  };

  const cambiarZona = (campo: 'origen' | 'destino') => {
    const actual = form[campo];
    const idx = ZONAS_BFS_KOMPAS.indexOf(actual as (typeof ZONAS_BFS_KOMPAS)[number]);
    const siguiente = ZONAS_BFS_KOMPAS[(idx + 1) % ZONAS_BFS_KOMPAS.length];
    const actualizado = { ...form, [campo]: siguiente };
    setForm(actualizado);
    ejecutarSimulacion(actualizado);
  };

  return (
    <Pantalla bordes={['bottom', 'left', 'right']}>
      <YStack gap={20}>
        {/* Encabezado */}
        <YStack gap={6}>
          <XStack items="center" justify="space-between" gap={8}>
            <Titulo>Laboratorio IA</Titulo>
            {USA_MOCK && <EtiquetaEjemplo />}
          </XStack>
          <Subtitulo>
            Evaluación experimental de limpieza de datos (P02), optimización de particiones más allá del 70/30, control
            de subajuste vs. sobreajuste (P03) y comparativa frente a Reglas Fijas y BFS (P01).
          </Subtitulo>
        </YStack>

        <MensajeError>{error}</MensajeError>

        {cargando && !metricas ? (
          <YStack py={48} items="center" gap={12}>
            <ActivityIndicator color={paleta.primario} size="large" />
            <Texto tam="sm" suave>
              Evaluando particiones y entrenando Árbol de Decisión sobre 500 recorridos…
            </Texto>
          </YStack>
        ) : null}

        {metricas && (
          <>
            {/* 1. Tarjetas de Resumen: ML vs Reglas Fijas y Partición Óptima */}
            <XStack gap={12} flexWrap="wrap">
              <Tarjeta destacada flex={1} minW={260}>
                <XStack items="center" justify="space-between">
                  <Pildora tono="primario">
                    <Texto tam="xs" peso="fuerte" color="$sobrePrimario">
                      ÁRBOL DE DECISIÓN (P03)
                    </Texto>
                  </Pildora>
                  <Icono nombre="check" color={paleta.ok} tamano={20} />
                </XStack>
                <Texto tam="xl" peso="fuerte">
                  {pct(metricas.comparativa_sistemas.exactitud_ml)} Exactitud ML
                </Texto>
                <Texto tam="sm" suave>
                  Supera al sistema de Reglas Fijas ({pct(metricas.comparativa_sistemas.exactitud_reglas)}) por +
                  {(metricas.comparativa_sistemas.mejora_exactitud_ml_vs_reglas * 100).toFixed(1)} puntos en prueba.
                </Texto>
                <Recuadro>
                  <Texto tam="xs" peso="semi">
                    F1-Score ML: {pct(metricas.comparativa_sistemas.f1_ml)} · Precisión:{' '}
                    {pct(metricas.comparativa_sistemas.precision_ml)} · Recall:{' '}
                    {pct(metricas.comparativa_sistemas.recall_ml)}
                  </Texto>
                </Recuadro>
              </Tarjeta>

              <Tarjeta flex={1} minW={260}>
                <XStack items="center" justify="space-between">
                  <Pildora tono="suave">
                    <Texto tam="xs" peso="fuerte" color="$primario">
                      PARTICIÓN ÓPTIMA SELECCIONADA
                    </Texto>
                  </Pildora>
                  <Icono nombre="filtros" color={paleta.primario} tamano={20} />
                </XStack>
                <Texto tam="lg" peso="fuerte">
                  {metricas.particion_optima}
                </Texto>
                <Texto tam="sm" suave>
                  Profundidad óptima: max_depth = {metricas.max_depth_optimo}. Supera al 70/30 de clase en +
                  {(metricas.comparativa_sistemas.mejora_vs_70_30_acc * 100).toFixed(1)}% de exactitud.
                </Texto>
                <Recuadro>
                  <Texto tam="xs" suave>
                    500 recorridos limpios · Validación cruzada 5-Folds estratificada
                  </Texto>
                </Recuadro>
              </Tarjeta>
            </XStack>

            {/* 2. Comparativa Visual de Particiones (60/40, 70/30, 75/25, 80/20, 60/20/20) */}
            <Tarjeta>
              <XStack items="center" gap={10}>
                <Icono nombre="regla" color={paleta.primario} tamano={20} />
                <YStack flex={1}>
                  <Texto tam="lg" peso="fuerte">
                    Optimización de Particiones (Más allá del 70/30)
                  </Texto>
                  <Texto tam="xs" suave>
                    Comparación experimental de exactitud en prueba, validación 5-Fold CV y F1-Score
                  </Texto>
                </YStack>
              </XStack>

              <YStack gap={12} mt={4}>
                {metricas.comparativa_particiones.map((part) => {
                  const colorBarra = part.es_optima
                    ? paleta.ok
                    : part.es_baseline
                      ? paleta.aviso
                      : paleta.primario;
                  return (
                    <YStack
                      key={part.codigo}
                      gap={6}
                      p={12}
                      rounded={14}
                      borderWidth={part.es_optima ? 2 : 1}
                      borderColor={part.es_optima ? '$primario' : '$borde'}
                      bg="$fondo"
                    >
                      <XStack items="center" justify="space-between" gap={8} flexWrap="wrap">
                        <XStack items="center" gap={8} flex={1}>
                          <Texto peso="fuerte" tam="sm">
                            {part.proporcion}
                          </Texto>
                          {part.es_optima && (
                            <Pildora style={{ backgroundColor: paleta.okFondo }}>
                              <Texto tam="xs" peso="fuerte" style={{ color: paleta.ok }}>
                                ÓPTIMA
                              </Texto>
                            </Pildora>
                          )}
                          {part.es_baseline && (
                            <Pildora tono="aviso">
                              <Texto tam="xs" peso="fuerte" color="$texto">
                                BASELINE CLASE
                              </Texto>
                            </Pildora>
                          )}
                        </XStack>
                        <Texto peso="fuerte" tam="md">
                          Test: {pct(part.test_acc)}
                        </Texto>
                      </XStack>

                      <BarraProgreso valor={part.test_acc} color={colorBarra} fondo={paleta.borde} />

                      <XStack justify="space-between" flexWrap="wrap" gap={8}>
                        <Texto tam="xs" suave>
                          Train: {pct(part.train_acc)} ({part.muestras_train})
                        </Texto>
                        <Texto tam="xs" suave>
                          Val/CV: {pct(part.val_acc)}
                        </Texto>
                        <Texto tam="xs" suave>
                          F1: {pct(part.f1_score)}
                        </Texto>
                        <Texto tam="xs" suave>
                          Regla Fija: {pct(part.exactitud_reglas)}
                        </Texto>
                      </XStack>
                    </YStack>
                  );
                })}
              </YStack>
            </Tarjeta>

            {/* 3. Monitor de Overfitting vs. Underfitting (Curva de Complejidad max_depth) */}
            <Tarjeta>
              <XStack items="center" gap={10}>
                <Icono nombre="filtros" color={paleta.primario} tamano={20} />
                <YStack flex={1}>
                  <Texto tam="lg" peso="fuerte">
                    Control de Underfitting vs. Overfitting (max_depth)
                  </Texto>
                  <Texto tam="xs" suave>
                    Falta de capacidad en profundidad 1–2 vs. memorización sin poda en profundidad 8–15
                  </Texto>
                </YStack>
              </XStack>

              <YStack gap={10} mt={4}>
                {metricas.curva_complejidad.map((item) => {
                  const esSubajuste = item.estado.includes('Underfitting');
                  const esSobreajuste = item.estado.includes('Overfitting');
                  const esOptimo = item.max_depth === metricas.max_depth_optimo;

                  const bgInsignia = esSubajuste
                    ? paleta.avisoFondo
                    : esSobreajuste
                      ? paleta.peligroFondo
                      : paleta.okFondo;
                  // Respeto estricto a COLORIMETRIA.md §4 regla 3: texto oscuro sobre fondo dorado/aviso
                  const colorTextoInsignia = esSubajuste
                    ? paleta.texto
                    : esSobreajuste
                      ? paleta.peligro
                      : paleta.ok;

                  return (
                    <YStack
                      key={item.max_depth}
                      gap={6}
                      p={12}
                      rounded={14}
                      borderWidth={esOptimo ? 2 : 1}
                      borderColor={esOptimo ? '$primario' : '$borde'}
                      bg="$fondo"
                    >
                      <XStack items="center" justify="space-between" flexWrap="wrap" gap={6}>
                        <XStack items="center" gap={8}>
                          <Texto peso="fuerte" tam="sm">
                            max_depth = {item.max_depth}
                          </Texto>
                          <Texto tam="xs" suave>
                            ({item.num_hojas} hojas)
                          </Texto>
                          {esOptimo && (
                            <Pildora tono="primario">
                              <Texto tam="xs" peso="fuerte" color="$sobrePrimario">
                                SELECCIONADO
                              </Texto>
                            </Pildora>
                          )}
                        </XStack>

                        <Pildora style={{ backgroundColor: bgInsignia }}>
                          <Texto tam="xs" peso="fuerte" style={{ color: colorTextoInsignia }}>
                            {item.estado}
                          </Texto>
                        </Pildora>
                      </XStack>

                      <XStack justify="space-between" flexWrap="wrap" gap={8}>
                        <Texto tam="xs">Train: {pct(item.train_acc)}</Texto>
                        <Texto tam="xs">Validación: {pct(item.val_acc)}</Texto>
                        <Texto tam="xs">5-Fold CV: {pct(item.cv_score)}</Texto>
                        <Texto tam="xs" suave>
                          Brecha: {(item.brecha_generalizacion * 100).toFixed(1)}%
                        </Texto>
                      </XStack>
                    </YStack>
                  );
                })}
              </YStack>
            </Tarjeta>

            {/* 4. Matriz de Confusión y Limpieza de Datos (Práctica 02) */}
            <XStack gap={12} flexWrap="wrap">
              <Tarjeta flex={1} minW={260}>
                <XStack items="center" gap={8}>
                  <Icono nombre="check" color={paleta.primario} tamano={20} />
                  <Texto tam="lg" peso="fuerte">
                    Matriz de Confusión (Prueba)
                  </Texto>
                </XStack>
                <Texto tam="xs" suave>
                  Clasificación de viabilidad del plan turístico en el conjunto de prueba ciego
                </Texto>

                <YStack gap={8} mt={4}>
                  <XStack gap={8}>
                    <YStack flex={1} p={12} rounded={14} style={{ backgroundColor: paleta.okFondo }} items="center">
                      <Texto tam="xl" peso="fuerte" style={{ color: paleta.ok }}>
                        {metricas.comparativa_sistemas.matriz_confusion.verdaderos_negativos}
                      </Texto>
                      <Texto tam="xs" peso="semi">
                        Verdaderos Negativos
                      </Texto>
                      <Texto tam="xs" suave>
                        No viable acertado
                      </Texto>
                    </YStack>

                    <YStack
                      flex={1}
                      p={12}
                      rounded={14}
                      style={{ backgroundColor: paleta.peligroFondo }}
                      items="center"
                    >
                      <Texto tam="xl" peso="fuerte" style={{ color: paleta.peligro }}>
                        {metricas.comparativa_sistemas.matriz_confusion.falsos_positivos}
                      </Texto>
                      <Texto tam="xs" peso="semi">
                        Falsos Positivos
                      </Texto>
                      <Texto tam="xs" suave>
                        Error tipo I
                      </Texto>
                    </YStack>
                  </XStack>

                  <XStack gap={8}>
                    <YStack
                      flex={1}
                      p={12}
                      rounded={14}
                      style={{ backgroundColor: paleta.peligroFondo }}
                      items="center"
                    >
                      <Texto tam="xl" peso="fuerte" style={{ color: paleta.peligro }}>
                        {metricas.comparativa_sistemas.matriz_confusion.falsos_negativos}
                      </Texto>
                      <Texto tam="xs" peso="semi">
                        Falsos Negativos
                      </Texto>
                      <Texto tam="xs" suave>
                        Error tipo II
                      </Texto>
                    </YStack>

                    <YStack flex={1} p={12} rounded={14} style={{ backgroundColor: paleta.okFondo }} items="center">
                      <Texto tam="xl" peso="fuerte" style={{ color: paleta.ok }}>
                        {metricas.comparativa_sistemas.matriz_confusion.verdaderos_positivos}
                      </Texto>
                      <Texto tam="xs" peso="semi">
                        Verdaderos Positivos
                      </Texto>
                      <Texto tam="xs" suave>
                        Plan viable acertado
                      </Texto>
                    </YStack>
                  </XStack>
                </YStack>
              </Tarjeta>

              <Tarjeta flex={1} minW={260}>
                <XStack items="center" gap={8}>
                  <Icono nombre="documento" color={paleta.primario} tamano={20} />
                  <Texto tam="lg" peso="fuerte">
                    Limpieza de Datos (Práctica 02)
                  </Texto>
                </XStack>
                <Texto tam="xs" suave>
                  Auditoría antes y después de imputación por mediana y eliminación de ruido
                </Texto>

                <YStack gap={8} mt={4}>
                  <Recuadro>
                    <XStack justify="space-between">
                      <Texto tam="sm">Registros crudos iniciales</Texto>
                      <Texto tam="sm" peso="fuerte">
                        {metricas.resumen_limpieza.registros_iniciales}
                      </Texto>
                    </XStack>
                    <XStack justify="space-between">
                      <Texto tam="sm">Nulos imputados (mediana)</Texto>
                      <Texto tam="sm" peso="fuerte">
                        {metricas.resumen_limpieza.nulos_imputados}
                      </Texto>
                    </XStack>
                    <XStack justify="space-between">
                      <Texto tam="sm">Duplicados eliminados</Texto>
                      <Texto tam="sm" peso="fuerte">
                        {metricas.resumen_limpieza.duplicados_eliminados}
                      </Texto>
                    </XStack>
                    <XStack justify="space-between">
                      <Texto tam="sm">Outliers fuera de rango</Texto>
                      <Texto tam="sm" peso="fuerte">
                        {metricas.resumen_limpieza.outliers_eliminados}
                      </Texto>
                    </XStack>
                    <XStack justify="space-between">
                      <Texto tam="sm" peso="semi">
                        Dataset limpio final
                      </Texto>
                      <Texto tam="sm" peso="fuerte" acento>
                        {metricas.resumen_limpieza.registros_limpios} recorridos
                      </Texto>
                    </XStack>
                  </Recuadro>
                  <Texto tam="xs" suave>
                    Nulos restantes tras Etapa D: {metricas.resumen_limpieza.nulos_restantes} · Mediana rating:{' '}
                    {metricas.resumen_limpieza.mediana_rating_imputada}★ · Mediana presupuesto: $
                    {metricas.resumen_limpieza.mediana_presupuesto_imputada} MXN
                  </Texto>
                </YStack>
              </Tarjeta>
            </XStack>

            {/* 5. Simulador Interactivo en Vivo: Regla Fija vs Árbol de Decisión + Ruta BFS */}
            <Tarjeta destacada>
              <XStack items="center" gap={10}>
                <Icono nombre="ruta" color={paleta.primario} tamano={22} />
                <YStack flex={1}>
                  <Texto tam="lg" peso="fuerte">
                    Simulador Interactivo en Vivo (P01 + P03)
                  </Texto>
                  <Texto tam="xs" suave>
                    Ajusta los parámetros de un recorrido y compara qué decide la Regla Fija, el Árbol de Decisión y BFS
                  </Texto>
                </YStack>
              </XStack>

              {/* Botones rápidos de escenarios */}
              <XStack gap={8} flexWrap="wrap">
                {ESCENARIOS_RAPIDOS.map((esc) => (
                  <Pildora
                    key={esc.etiqueta}
                    tono="suave"
                    role="button"
                    onPress={() => {
                      const completo = {
                        origen: esc.datos.origen ?? 'Terminal Toluca',
                        destino: esc.datos.destino ?? 'Galerias Metepec',
                        ...esc.datos,
                      };
                      setForm(completo);
                      ejecutarSimulacion(completo);
                    }}
                    cursor="pointer"
                  >
                    <Texto tam="xs" peso="semi" acento>
                      {esc.etiqueta}
                    </Texto>
                  </Pildora>
                ))}
              </XStack>

              <YStack gap={4}>
                <ControlNumerico
                  etiqueta="Distancia del recorrido"
                  valorTexto={`${form.distancia_km.toFixed(1)} km`}
                  onMenos={() => setForm((f) => ({ ...f, distancia_km: Math.max(0.5, Number((f.distancia_km - 1.5).toFixed(1))) }))}
                  onMas={() => setForm((f) => ({ ...f, distancia_km: Math.min(25.0, Number((f.distancia_km + 1.5).toFixed(1))) }))}
                />
                <ControlNumerico
                  etiqueta="Presupuesto disponible"
                  valorTexto={`$${form.presupuesto_mxn} MXN`}
                  onMenos={() => setForm((f) => ({ ...f, presupuesto_mxn: Math.max(20, f.presupuesto_mxn - 30) }))}
                  onMas={() => setForm((f) => ({ ...f, presupuesto_mxn: Math.min(500, f.presupuesto_mxn + 30) }))}
                />
                <ControlNumerico
                  etiqueta="Rating promedio destino"
                  valorTexto={`${form.rating_lugar.toFixed(1)} ★`}
                  onMenos={() => setForm((f) => ({ ...f, rating_lugar: Math.max(3.0, Number((f.rating_lugar - 0.2).toFixed(1))) }))}
                  onMas={() => setForm((f) => ({ ...f, rating_lugar: Math.min(5.0, Number((f.rating_lugar + 0.2).toFixed(1))) }))}
                />
                <ControlNumerico
                  etiqueta="Número de paradas"
                  valorTexto={`${form.num_paradas} paradas`}
                  onMenos={() => setForm((f) => ({ ...f, num_paradas: Math.max(1, f.num_paradas - 1) }))}
                  onMas={() => setForm((f) => ({ ...f, num_paradas: Math.min(8, f.num_paradas + 1) }))}
                />
                <ControlNumerico
                  etiqueta="Nivel de tráfico (1-10)"
                  valorTexto={`Nivel ${form.trafico_nivel}/10`}
                  onMenos={() => setForm((f) => ({ ...f, trafico_nivel: Math.max(1, f.trafico_nivel - 1) }))}
                  onMas={() => setForm((f) => ({ ...f, trafico_nivel: Math.min(10, f.trafico_nivel + 1) }))}
                />
              </YStack>

              <XStack gap={8} flexWrap="wrap">
                <BotonSecundario
                  flex
                  icono="ubicacion"
                  texto={`Origen: ${form.origen}`}
                  onPress={() => cambiarZona('origen')}
                />
                <BotonSecundario
                  flex
                  icono="bandera"
                  texto={`Destino: ${form.destino}`}
                  onPress={() => cambiarZona('destino')}
                />
              </XStack>

              <BotonPrimario
                texto="Evaluar con Reglas Fijas, Árbol ML y BFS"
                icono="check"
                cargando={simulando}
                onPress={() => ejecutarSimulacion(form)}
              />

              {simulacion && (
                <YStack gap={10} mt={4}>
                  <XStack gap={10} flexWrap="wrap">
                    <Recuadro flex={1} minW={220}>
                      <Texto tam="xs" peso="fuerte" acento>
                        ÁRBOL DE DECISIÓN ÓPTIMO (ML)
                      </Texto>
                      <Texto tam="md" peso="fuerte">
                        {simulacion.prediccion_arbol_ml.plan_viable === 1 ? 'Plan Viable' : 'Requiere Ajuste'} ·{' '}
                        {simulacion.prediccion_arbol_ml.modo_recomendado}
                      </Texto>
                      <Texto tam="xs" suave>
                        {simulacion.prediccion_arbol_ml.explicacion}
                      </Texto>
                    </Recuadro>

                    <Recuadro flex={1} minW={220}>
                      <Texto tam="xs" peso="fuerte" suave>
                        SISTEMA DE REGLAS FIJAS (BASELINE P01)
                      </Texto>
                      <Texto tam="md" peso="fuerte">
                        {simulacion.prediccion_reglas.plan_viable === 1 ? 'Plan Viable' : 'Requiere Ajuste'} ·{' '}
                        {simulacion.prediccion_reglas.modo_recomendado}
                      </Texto>
                      <Texto tam="xs" suave>
                        [{simulacion.prediccion_reglas.regla_activada}] {simulacion.prediccion_reglas.explicacion}
                      </Texto>
                    </Recuadro>
                  </XStack>

                  <Recuadro>
                    <XStack items="center" justify="space-between" flexWrap="wrap" gap={6}>
                      <Texto tam="xs" peso="fuerte" acento>
                        RUTA CON MENOS ESCALAS — {simulacion.ruta_bfs.algoritmo}
                      </Texto>
                      <Texto tam="xs" peso="semi">
                        {simulacion.ruta_bfs.num_escalas} escalas intermedias ({simulacion.ruta_bfs.saltos_totales}{' '}
                        tramos)
                      </Texto>
                    </XStack>
                    <Texto tam="sm" peso="medio">
                      {simulacion.ruta_bfs.ruta_paradas.length > 0
                        ? simulacion.ruta_bfs.ruta_paradas.join(' → ')
                        : 'Sin ruta directa registrada en el grafo base'}
                    </Texto>
                  </Recuadro>
                </YStack>
              )}
            </Tarjeta>
          </>
        )}
      </YStack>
    </Pantalla>
  );
}
