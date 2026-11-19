// Respuestas de /api/ia de las prácticas de Machine Learning supervisado (P04, P05 y P06).
// Las forman backend/app/modulos/ia_kompas/p04_ajuste_modelo.py, p05_comparacion_modelos.py y
// p06_optimizacion_hiperparametros.py. Las exactitudes van de 0 a 1.

export type ClaveRegimen = 'subajuste_underfitting' | 'ajuste_adecuado' | 'sobreajuste_overfitting'

export type ModeloAjuste = {
  nombre_legible: string
  max_depth: number | null
  exactitud_entrenamiento: number
  exactitud_validacion: number
  exactitud_prueba: number
  brecha_train_val: number
  diagnostico: string
}

export type PuntoCurva = {
  max_depth: number | null
  profundidad_real: number
  exactitud_entrenamiento: number
  exactitud_validacion: number
  exactitud_prueba: number
  brecha_train_val: number
}

/** GET /api/ia/diagnostico-ajuste (P04) */
export type DiagnosticoAjuste = {
  distribucion_datos: { total_registros: number; entrenamiento_60: number; validacion_20: number; prueba_20: number }
  comparacion_modelos: Record<ClaveRegimen, ModeloAjuste>
  curva_complejidad: PuntoCurva[]
  modelo_seleccionado: { clave: ClaveRegimen; nombre: string; max_depth: number | null; exactitud_validacion: number; exactitud_prueba_final: number }
  metricas_prueba_final: { matriz_confusion: number[][]; etiquetas_clases: string[] }
}

export type ClaveAlgoritmo = 'decision_tree' | 'random_forest' | 'k_nearest_neighbors'

export type FilaAlgoritmo = {
  clave: ClaveAlgoritmo
  nombre: string
  descripcion: string
  tiempo_entrenamiento_ms: number
  tiempo_inferencia_ms: number
  exactitud_validacion: number
  exactitud_prueba: number
  precision_prueba: number
  recall_prueba: number
  f1_score_prueba: number
  matriz_confusion_prueba: number[][]
}

/** GET /api/ia/comparar-algoritmos (P05) */
export type ComparacionAlgoritmos = {
  total_muestras_evaluadas: number
  algoritmos_comparados: number
  etiquetas_clases: string[]
  tabla_comparativa: FilaAlgoritmo[]
  algoritmo_ganador: { clave: ClaveAlgoritmo; nombre: string; criterio_seleccion: string }
}

export type ResultadoBusqueda = {
  algoritmo: string
  mejores_hiperparametros: Record<string, string | number | null>
  exactitud_media_cv: number
  desviacion_estandar_cv: number
  puntajes_por_pliegue: number[]
  total_combinaciones_probadas: number
}

/** GET /api/ia/optimizar-hiperparametros (P06) */
export type OptimizacionHiperparametros = {
  total_registros_utilizados: number
  esquema_validacion: string
  resultados_por_algoritmo: { arbol_decision: ResultadoBusqueda; bosque_aleatorio: ResultadoBusqueda }
  recomendacion_para_produccion: {
    algoritmo: string
    hiperparametros_optimos: Record<string, string | number | null>
    exactitud_esperada: number
    estabilidad_desviacion: number
  }
}

export type DatosMachineLearning = {
  ajuste: DiagnosticoAjuste
  comparacion: ComparacionAlgoritmos
  optimizacion: OptimizacionHiperparametros
}
