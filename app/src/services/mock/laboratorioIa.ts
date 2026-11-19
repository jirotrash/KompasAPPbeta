// Datos y motor determinista de respaldo (fallback offline / modo demostración)
// para el Laboratorio de Inteligencia Artificial de Kompás (GET /api/ia/metricas y POST /api/ia/simular).

export type ResumenLimpiezaIA = {
  registros_iniciales: number;
  nulos_imputados: number;
  detalle_nulos_imputados: Record<string, number>;
  duplicados_eliminados: number;
  outliers_eliminados: number;
  registros_limpios: number;
  mediana_rating_imputada: number;
  mediana_presupuesto_imputada: number;
  nulos_restantes: number;
  distribucion_plan_viable: {
    viable_1: number;
    no_viable_0: number;
  };
};

export type ParticionComparativaIA = {
  codigo: string;
  proporcion: string;
  muestras_train: number;
  muestras_val: number;
  muestras_test: number;
  train_acc: number;
  val_acc: number;
  test_acc: number;
  precision: number;
  recall: number;
  f1_score: number;
  cv_score: number;
  brecha: number;
  exactitud_reglas: number;
  f1_reglas: number;
  es_baseline: boolean;
  es_optima: boolean;
};

export type PuntoCurvaComplejidadIA = {
  max_depth: number;
  train_acc: number;
  val_acc: number;
  test_acc: number;
  cv_score: number;
  brecha_generalizacion: number;
  num_hojas: number;
  estado: 'Underfitting (Subajuste)' | 'Buen ajuste' | 'Overfitting (Sobreajuste)' | string;
};

export type ComparativaSistemasIA = {
  exactitud_reglas: number;
  f1_reglas: number;
  exactitud_ml: number;
  precision_ml: number;
  recall_ml: number;
  f1_ml: number;
  mejora_exactitud_ml_vs_reglas: number;
  particion_optima: string;
  codigo_particion_optima: string;
  max_depth_optimo: number;
  mejora_vs_70_30_acc: number;
  mejora_vs_70_30_f1: number;
  matriz_confusion: {
    etiquetas: string[];
    matriz: number[][];
    verdaderos_negativos: number;
    falsos_positivos: number;
    falsos_negativos: number;
    verdaderos_positivos: number;
  };
  importancia_variables: Record<string, number>;
};

export type MetricasLaboratorioIA = {
  resumen_limpieza: ResumenLimpiezaIA;
  particion_optima: string;
  max_depth_optimo: number;
  comparativa_particiones: ParticionComparativaIA[];
  curva_complejidad: PuntoCurvaComplejidadIA[];
  comparativa_sistemas: ComparativaSistemasIA;
};

export type PeticionSimulacionIA = {
  distancia_km: number;
  presupuesto_mxn: number;
  rating_lugar: number;
  num_paradas: number;
  trafico_nivel: number;
  origen?: string;
  destino?: string;
};

export type RespuestaSimulacionIA = {
  entrada: Required<PeticionSimulacionIA>;
  prediccion_reglas: {
    plan_viable: number;
    etiqueta_viabilidad: 'viable' | 'no_viable';
    modo_recomendado: string;
    regla_activada: string;
    explicacion: string;
  };
  prediccion_arbol_ml: {
    plan_viable: number;
    etiqueta_viabilidad: 'viable' | 'no_viable';
    modo_recomendado: string;
    confianza: number;
    max_depth_usado: number;
    particion_usada: string;
    explicacion: string;
  };
  coinciden_sistemas: boolean;
  ruta_bfs: {
    origen: string;
    destino: string;
    ruta_paradas: string[];
    num_escalas: number;
    saltos_totales: number;
    algoritmo: string;
    encontrado: boolean;
  };
};

export const ZONAS_BFS_KOMPAS = [
  'Terminal Toluca',
  'Cosmovitral',
  'Los Portales',
  'Alameda Central Toluca',
  'Estadio Nemesio Diez',
  'Parque Metropolitano Bicentenario',
  'Centro Metepec',
  'Galerias Metepec',
  'Parque Ambiental Bicentenario',
  'San Mateo Atenco',
  'Lerma Centro',
  'Plazas Outlet Lerma',
] as const;

const GRAFO_BASE_KOMPAS: Record<string, string[]> = {
  'Terminal Toluca': ['Cosmovitral', 'Centro Metepec', 'Los Portales'],
  Cosmovitral: ['Los Portales', 'Alameda Central Toluca', 'Terminal Toluca'],
  'Los Portales': ['Cosmovitral', 'Alameda Central Toluca', 'Parque Metropolitano Bicentenario'],
  'Alameda Central Toluca': ['Cosmovitral', 'Los Portales', 'Estadio Nemesio Diez'],
  'Estadio Nemesio Diez': ['Alameda Central Toluca', 'Parque Metropolitano Bicentenario'],
  'Parque Metropolitano Bicentenario': ['Los Portales', 'Estadio Nemesio Diez', 'Centro Metepec', 'Galerias Metepec'],
  'Centro Metepec': ['Terminal Toluca', 'Parque Metropolitano Bicentenario', 'Galerias Metepec', 'Parque Ambiental Bicentenario'],
  'Galerias Metepec': ['Centro Metepec', 'Parque Ambiental Bicentenario', 'San Mateo Atenco'],
  'Parque Ambiental Bicentenario': ['Centro Metepec', 'Galerias Metepec', 'Lerma Centro'],
  'San Mateo Atenco': ['Galerias Metepec', 'Lerma Centro'],
  'Lerma Centro': ['San Mateo Atenco', 'Parque Ambiental Bicentenario', 'Plazas Outlet Lerma'],
  'Plazas Outlet Lerma': ['Lerma Centro'],
};

const METRICAS_MOCK_KOMPAS: MetricasLaboratorioIA = {
  resumen_limpieza: {
    registros_iniciales: 519,
    nulos_imputados: 26,
    detalle_nulos_imputados: {
      presupuesto_mxn: 11,
      rating_lugar: 15,
    },
    duplicados_eliminados: 15,
    outliers_eliminados: 4,
    registros_limpios: 500,
    mediana_rating_imputada: 4.0,
    mediana_presupuesto_imputada: 256.13,
    nulos_restantes: 0,
    distribucion_plan_viable: {
      viable_1: 234,
      no_viable_0: 266,
    },
  },
  particion_optima: '60% Train / 20% Validation / 20% Test',
  max_depth_optimo: 5,
  comparativa_particiones: [
    {
      codigo: '60_40',
      proporcion: '60% Train / 40% Test',
      muestras_train: 300,
      muestras_val: 0,
      muestras_test: 200,
      train_acc: 0.9467,
      val_acc: 0.8567,
      test_acc: 0.83,
      precision: 0.8329,
      recall: 0.83,
      f1_score: 0.8301,
      cv_score: 0.8567,
      brecha: 0.1167,
      exactitud_reglas: 0.78,
      f1_reglas: 0.7796,
      es_baseline: false,
      es_optima: false,
    },
    {
      codigo: '70_30',
      proporcion: '70% Train / 30% Test (Baseline de clase)',
      muestras_train: 350,
      muestras_val: 0,
      muestras_test: 150,
      train_acc: 0.94,
      val_acc: 0.8114,
      test_acc: 0.8267,
      precision: 0.834,
      recall: 0.8267,
      f1_score: 0.8267,
      cv_score: 0.8114,
      brecha: 0.1133,
      exactitud_reglas: 0.7867,
      f1_reglas: 0.7867,
      es_baseline: true,
      es_optima: false,
    },
    {
      codigo: '75_25',
      proporcion: '75% Train / 25% Test',
      muestras_train: 375,
      muestras_val: 0,
      muestras_test: 125,
      train_acc: 0.9413,
      val_acc: 0.856,
      test_acc: 0.832,
      precision: 0.8351,
      recall: 0.832,
      f1_score: 0.8322,
      cv_score: 0.856,
      brecha: 0.1093,
      exactitud_reglas: 0.752,
      f1_reglas: 0.752,
      es_baseline: false,
      es_optima: false,
    },
    {
      codigo: '80_20',
      proporcion: '80% Train / 20% Test',
      muestras_train: 400,
      muestras_val: 0,
      muestras_test: 100,
      train_acc: 0.925,
      val_acc: 0.85,
      test_acc: 0.84,
      precision: 0.8429,
      recall: 0.84,
      f1_score: 0.8401,
      cv_score: 0.85,
      brecha: 0.085,
      exactitud_reglas: 0.83,
      f1_reglas: 0.8302,
      es_baseline: false,
      es_optima: false,
    },
    {
      codigo: '60_20_20',
      proporcion: '60% Train / 20% Validation / 20% Test',
      muestras_train: 300,
      muestras_val: 100,
      muestras_test: 100,
      train_acc: 0.9533,
      val_acc: 0.85,
      test_acc: 0.86,
      precision: 0.86,
      recall: 0.86,
      f1_score: 0.86,
      cv_score: 0.85,
      brecha: 0.0933,
      exactitud_reglas: 0.83,
      f1_reglas: 0.8302,
      es_baseline: false,
      es_optima: true,
    },
  ],
  curva_complejidad: [
    {
      max_depth: 1,
      train_acc: 0.79,
      val_acc: 0.84,
      test_acc: 0.83,
      cv_score: 0.7925,
      brecha_generalizacion: -0.05,
      num_hojas: 2,
      estado: 'Underfitting (Subajuste)',
    },
    {
      max_depth: 2,
      train_acc: 0.83,
      val_acc: 0.84,
      test_acc: 0.85,
      cv_score: 0.8275,
      brecha_generalizacion: -0.01,
      num_hojas: 4,
      estado: 'Underfitting (Subajuste)',
    },
    {
      max_depth: 3,
      train_acc: 0.86,
      val_acc: 0.83,
      test_acc: 0.84,
      cv_score: 0.8275,
      brecha_generalizacion: 0.03,
      num_hojas: 7,
      estado: 'Buen ajuste',
    },
    {
      max_depth: 4,
      train_acc: 0.9167,
      val_acc: 0.85,
      test_acc: 0.84,
      cv_score: 0.83,
      brecha_generalizacion: 0.0667,
      num_hojas: 13,
      estado: 'Buen ajuste',
    },
    {
      max_depth: 5,
      train_acc: 0.9533,
      val_acc: 0.85,
      test_acc: 0.86,
      cv_score: 0.85,
      brecha_generalizacion: 0.1033,
      num_hojas: 22,
      estado: 'Buen ajuste',
    },
    {
      max_depth: 8,
      train_acc: 0.9933,
      val_acc: 0.78,
      test_acc: 0.88,
      cv_score: 0.83,
      brecha_generalizacion: 0.2133,
      num_hojas: 38,
      estado: 'Overfitting (Sobreajuste)',
    },
    {
      max_depth: 12,
      train_acc: 1.0,
      val_acc: 0.79,
      test_acc: 0.88,
      cv_score: 0.825,
      brecha_generalizacion: 0.21,
      num_hojas: 40,
      estado: 'Overfitting (Sobreajuste)',
    },
    {
      max_depth: 15,
      train_acc: 1.0,
      val_acc: 0.79,
      test_acc: 0.88,
      cv_score: 0.825,
      brecha_generalizacion: 0.21,
      num_hojas: 40,
      estado: 'Overfitting (Sobreajuste)',
    },
  ],
  comparativa_sistemas: {
    exactitud_reglas: 0.83,
    f1_reglas: 0.8302,
    exactitud_ml: 0.86,
    precision_ml: 0.86,
    recall_ml: 0.86,
    f1_ml: 0.86,
    mejora_exactitud_ml_vs_reglas: 0.03,
    particion_optima: '60% Train / 20% Validation / 20% Test',
    codigo_particion_optima: '60_20_20',
    max_depth_optimo: 5,
    mejora_vs_70_30_acc: 0.0333,
    mejora_vs_70_30_f1: 0.0333,
    matriz_confusion: {
      etiquetas: ['no_viable (0)', 'viable (1)'],
      matriz: [
        [46, 7],
        [7, 40],
      ],
      verdaderos_negativos: 46,
      falsos_positivos: 7,
      falsos_negativos: 7,
      verdaderos_positivos: 40,
    },
    importancia_variables: {
      presupuesto_mxn: 0.5278,
      rating_lugar: 0.2402,
      trafico_nivel: 0.1103,
      num_paradas: 0.1021,
      distancia_km: 0.0196,
    },
  },
};

function buscarRutaBfsLocal(origen: string, destino: string) {
  if (!GRAFO_BASE_KOMPAS[origen] || !GRAFO_BASE_KOMPAS[destino]) {
    return {
      origen,
      destino,
      ruta_paradas: [],
      num_escalas: 0,
      saltos_totales: 0,
      algoritmo: 'BFS (Búsqueda en Anchura)',
      encontrado: false,
    };
  }
  if (origen === destino) {
    return {
      origen,
      destino,
      ruta_paradas: [origen],
      num_escalas: 0,
      saltos_totales: 0,
      algoritmo: 'BFS (Búsqueda en Anchura)',
      encontrado: true,
    };
  }
  const cola: string[][] = [[origen]];
  const visitados = new Set<string>([origen]);
  while (cola.length > 0) {
    const ruta = cola.shift()!;
    const actual = ruta[ruta.length - 1];
    if (actual === destino) {
      return {
        origen,
        destino,
        ruta_paradas: ruta,
        num_escalas: Math.max(0, ruta.length - 2),
        saltos_totales: Math.max(0, ruta.length - 1),
        algoritmo: 'BFS (Búsqueda en Anchura)',
        encontrado: true,
      };
    }
    for (const vecino of GRAFO_BASE_KOMPAS[actual] ?? []) {
      if (!visitados.has(vecino)) {
        visitados.add(vecino);
        cola.push([...ruta, vecino]);
      }
    }
  }
  return {
    origen,
    destino,
    ruta_paradas: [],
    num_escalas: 0,
    saltos_totales: 0,
    algoritmo: 'BFS (Búsqueda en Anchura)',
    encontrado: false,
  };
}

export async function obtenerMetricasIAMock(): Promise<MetricasLaboratorioIA> {
  return METRICAS_MOCK_KOMPAS;
}

export async function simularPrediccionIAMock(payload: PeticionSimulacionIA): Promise<RespuestaSimulacionIA> {
  const distancia_km = Number(payload.distancia_km ?? 5.0);
  const presupuesto_mxn = Number(payload.presupuesto_mxn ?? 180.0);
  const rating_lugar = Number(payload.rating_lugar ?? 4.5);
  const num_paradas = Number(payload.num_paradas ?? 3);
  const trafico_nivel = Number(payload.trafico_nivel ?? 5);
  const origen = payload.origen || 'Terminal Toluca';
  const destino = payload.destino || 'Galerias Metepec';

  // 1. Modo de transporte
  const modo =
    distancia_km <= 3.2 && num_paradas <= 3 && trafico_nivel <= 7
      ? 'caminando'
      : presupuesto_mxn >= 220 && (trafico_nivel >= 6 || distancia_km > 10 || num_paradas >= 5)
        ? 'auto_privado'
        : 'transporte_publico';

  // 2. Evaluación con Regla Fija (P01)
  let viableRegla = 0;
  let reglaActivada = 'R6_DEFECTO_PRESUPUESTO_AJUSTADO_DISTANCIA_MEDIA';
  let explicacionRegla = `Presupuesto moderado ($${presupuesto_mxn.toFixed(0)} MXN) frente a ${distancia_km.toFixed(1)} km y ${num_paradas} paradas.`;

  if (presupuesto_mxn < 80 && num_paradas >= 3) {
    viableRegla = 0;
    reglaActivada = 'R1_PRESUPUESTO_INSUFICIENTE_MULTIPLES_PARADAS';
    explicacionRegla = `Presupuesto bajo ($${presupuesto_mxn.toFixed(0)} MXN) para cubrir ${num_paradas} paradas turísticas.`;
  } else if (distancia_km > 16 && trafico_nivel >= 8) {
    viableRegla = 0;
    reglaActivada = 'R2_DISTANCIA_LARGA_TRAFICO_SEVERO';
    explicacionRegla = `Distancia extensa (${distancia_km.toFixed(1)} km) combinada con tráfico alto (nivel ${trafico_nivel}/10).`;
  } else if (rating_lugar < 3.4) {
    viableRegla = 0;
    reglaActivada = 'R3_CALIFICACION_BAJA_DESTINO';
    explicacionRegla = `Calificación promedio del lugar (${rating_lugar.toFixed(1)}★) por debajo del umbral recomendado.`;
  } else if (presupuesto_mxn >= 180) {
    viableRegla = 1;
    reglaActivada = 'R4_PRESUPUESTO_HOLGADO';
    explicacionRegla = `Presupuesto amplio ($${presupuesto_mxn.toFixed(0)} MXN) para recorrer ${num_paradas} paradas en ${modo}.`;
  } else if (distancia_km <= 10 && num_paradas <= 4) {
    viableRegla = 1;
    reglaActivada = 'R5_RECORRIDO_COMPACTO_EQUILIBRADO';
    explicacionRegla = `Recorrido compacto (${distancia_km.toFixed(1)} km y ${num_paradas} paradas) viable en ${modo}.`;
  }

  // 3. Evaluación con el Árbol de Decisión Óptimo (P03)
  const costoEstimado =
    num_paradas * 38.0 + (trafico_nivel >= 7 ? 45.0 : 0.0) + distancia_km * (trafico_nivel >= 6 ? 5.5 : 3.2);
  const holgura = presupuesto_mxn - costoEstimado;
  const viableML =
    holgura >= -15 &&
    rating_lugar >= 3.5 &&
    !(distancia_km > 18 && trafico_nivel >= 8 && num_paradas >= 6) &&
    !(presupuesto_mxn < 95 && num_paradas >= 4)
      ? 1
      : 0;
  const confianza = Math.min(0.98, Math.max(0.74, Number((0.82 + Math.min(0.14, Math.abs(holgura) / 600)).toFixed(2))));

  const ruta_bfs = buscarRutaBfsLocal(origen, destino);

  return {
    entrada: {
      distancia_km,
      presupuesto_mxn,
      rating_lugar,
      num_paradas,
      trafico_nivel,
      origen,
      destino,
    },
    prediccion_reglas: {
      plan_viable: viableRegla,
      etiqueta_viabilidad: viableRegla === 1 ? 'viable' : 'no_viable',
      modo_recomendado: modo,
      regla_activada: reglaActivada,
      explicacion: explicacionRegla,
    },
    prediccion_arbol_ml: {
      plan_viable: viableML,
      etiqueta_viabilidad: viableML === 1 ? 'viable' : 'no_viable',
      modo_recomendado: modo,
      confianza,
      max_depth_usado: 5,
      particion_usada: '60% Train / 20% Validation / 20% Test',
      explicacion: `Árbol de Decisión (max_depth=5, 60% Train / 20% Validation / 20% Test) clasifica el plan como ${viableML === 1 ? 'VIABLE' : 'NO VIABLE'} con ${Math.round(confianza * 100)}% de confianza y sugiere '${modo}'.`,
    },
    coinciden_sistemas: viableML === viableRegla,
    ruta_bfs,
  };
}
