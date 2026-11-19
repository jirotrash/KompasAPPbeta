// Datos de ejemplo de la sección Machine Learning (solo con VITE_USE_MOCK=true).
// Son una corrida real de P04, P05 y P06 sobre el CSV limpio de 160 traslados (semilla 42),
// copiada aquí para poder ver la sección sin backend. La pantalla los marca como "Dato de ejemplo".

import type { ComparacionAlgoritmos, DiagnosticoAjuste, OptimizacionHiperparametros } from './tiposML.ts'

const esperar = (ms = 350) => new Promise((r) => setTimeout(r, ms))

const curva = (
  [
    [1, 1, 0.6875, 0.75, 0.7188],
    [2, 2, 0.7604, 0.8125, 0.7812],
    [3, 3, 0.8542, 0.875, 0.7812],
    [4, 4, 0.9479, 0.9688, 0.9688],
    [5, 5, 1, 1, 0.9375],
    [6, 5, 1, 1, 0.9375],
    [7, 5, 1, 1, 0.9375],
    [8, 5, 1, 1, 0.9375],
    [10, 5, 1, 1, 0.9375],
    [12, 5, 1, 1, 0.9375],
    [null, 5, 1, 1, 0.9375],
  ] as const
).map(([max_depth, profundidad_real, tr, va, pr]) => ({
  max_depth,
  profundidad_real,
  exactitud_entrenamiento: tr,
  exactitud_validacion: va,
  exactitud_prueba: pr,
  brecha_train_val: Math.round(Math.abs(tr - va) * 10000) / 10000,
}))

const ADECUADO = 'Ajuste Adecuado: Buena capacidad de generalizacion con desempeno consistente en datos nuevos.'

const AJUSTE: DiagnosticoAjuste = {
  distribucion_datos: { total_registros: 160, entrenamiento_60: 96, validacion_20: 32, prueba_20: 32 },
  comparacion_modelos: {
    subajuste_underfitting: { nombre_legible: 'Arbol muy simple (Profundidad 1)', max_depth: 1, exactitud_entrenamiento: 0.6875, exactitud_validacion: 0.75, exactitud_prueba: 0.7188, brecha_train_val: 0.0625, diagnostico: ADECUADO },
    ajuste_adecuado: { nombre_legible: 'Arbol equilibrado (Profundidad 4)', max_depth: 4, exactitud_entrenamiento: 0.9479, exactitud_validacion: 0.9688, exactitud_prueba: 0.9688, brecha_train_val: 0.0208, diagnostico: ADECUADO },
    sobreajuste_overfitting: { nombre_legible: 'Arbol sin limite (Profundidad libre)', max_depth: null, exactitud_entrenamiento: 1, exactitud_validacion: 1, exactitud_prueba: 0.9375, brecha_train_val: 0, diagnostico: ADECUADO },
  },
  curva_complejidad: curva,
  modelo_seleccionado: { clave: 'sobreajuste_overfitting', nombre: 'Arbol sin limite (Profundidad libre)', max_depth: null, exactitud_validacion: 1, exactitud_prueba_final: 0.9375 },
  metricas_prueba_final: {
    matriz_confusion: [
      [14, 0, 1],
      [0, 2, 0],
      [1, 0, 14],
    ],
    etiquetas_clases: ['auto_privado', 'caminando', 'transporte_publico'],
  },
}

const COMPARACION: ComparacionAlgoritmos = {
  total_muestras_evaluadas: 160,
  algoritmos_comparados: 3,
  etiquetas_clases: ['auto_privado', 'caminando', 'transporte_publico'],
  tabla_comparativa: [
    {
      clave: 'decision_tree',
      nombre: 'Arbol de Decision (Decision Tree)',
      descripcion: 'Genera reglas logicas jerarquicas a partir de las caracteristicas de los traslados.',
      tiempo_entrenamiento_ms: 3.177,
      tiempo_inferencia_ms: 1.543,
      exactitud_validacion: 0.9688,
      exactitud_prueba: 0.9688,
      precision_prueba: 0.9707,
      recall_prueba: 0.9688,
      f1_score_prueba: 0.9687,
      matriz_confusion_prueba: [
        [14, 0, 1],
        [0, 2, 0],
        [0, 0, 15],
      ],
    },
    {
      clave: 'random_forest',
      nombre: 'Bosque Aleatorio (Random Forest)',
      descripcion: 'Combina multiples arboles de decision aleatorios para mejorar la estabilidad de la prediccion.',
      tiempo_entrenamiento_ms: 119.728,
      tiempo_inferencia_ms: 7.148,
      exactitud_validacion: 0.9688,
      exactitud_prueba: 0.9375,
      precision_prueba: 0.9449,
      recall_prueba: 0.9375,
      f1_score_prueba: 0.9337,
      matriz_confusion_prueba: [
        [14, 0, 1],
        [0, 1, 1],
        [0, 0, 15],
      ],
    },
    {
      clave: 'k_nearest_neighbors',
      nombre: 'Vecinos mas Cercanos (K-NN)',
      descripcion: 'Clasifica segun la distancia euclidiana hacia los traslados historicos mas similares.',
      tiempo_entrenamiento_ms: 4.124,
      tiempo_inferencia_ms: 3.756,
      exactitud_validacion: 0.625,
      exactitud_prueba: 0.6562,
      precision_prueba: 0.6138,
      recall_prueba: 0.6562,
      f1_score_prueba: 0.6319,
      matriz_confusion_prueba: [
        [9, 0, 6],
        [2, 0, 0],
        [3, 0, 12],
      ],
    },
  ],
  algoritmo_ganador: {
    clave: 'decision_tree',
    nombre: 'Arbol de Decision (Decision Tree)',
    criterio_seleccion: 'Mayor exactitud en el conjunto de validacion y mejor balance de latencia en milisegundos.',
  },
}

const OPTIMIZACION: OptimizacionHiperparametros = {
  total_registros_utilizados: 160,
  esquema_validacion: 'Validacion cruzada estratificada (StratifiedKFold con 5 pliegues)',
  resultados_por_algoritmo: {
    arbol_decision: {
      algoritmo: 'DecisionTreeClassifier',
      mejores_hiperparametros: { criterion: 'entropy', max_depth: 5, min_samples_split: 2 },
      exactitud_media_cv: 0.9625,
      desviacion_estandar_cv: 0.0364,
      puntajes_por_pliegue: [0.9688, 1, 1, 0.9375, 0.9062],
      total_combinaciones_probadas: 56,
    },
    bosque_aleatorio: {
      algoritmo: 'RandomForestClassifier',
      mejores_hiperparametros: { max_depth: 7, min_samples_split: 2, n_estimators: 100 },
      exactitud_media_cv: 0.9625,
      desviacion_estandar_cv: 0.0306,
      puntajes_por_pliegue: [1, 0.9688, 0.9688, 0.9688, 0.9062],
      total_combinaciones_probadas: 36,
    },
  },
  recomendacion_para_produccion: {
    algoritmo: 'RandomForestClassifier',
    hiperparametros_optimos: { max_depth: 7, min_samples_split: 2, n_estimators: 100 },
    exactitud_esperada: 0.9625,
    estabilidad_desviacion: 0.0306,
  },
}

export const diagnosticoAjuste = async () => (await esperar(), AJUSTE)
export const compararAlgoritmos = async () => (await esperar(), COMPARACION)
export const optimizarHiperparametros = async () => (await esperar(), OPTIMIZACION)
