// Catálogos de la sección Machine Learning (prácticas P04–P06): nombre, color y explicación de cada
// algoritmo, escenarios de P04 y nombres de las clases. El color sigue al algoritmo en todas las gráficas.

import { CATEGORICO } from './estilo.ts'
import type { ClaveAlgoritmo, ClaveRegimen } from './tiposML.ts'

export type MetaAlgoritmo = {
  nombre: string
  color: string
  configuracion: string
  comoFunciona: string
  ventaja: string
  riesgo: string
}

/** Textos tomados de los docstrings de p05_comparacion_modelos.py y de la configuración real de cada modelo. */
export const ALGORITMOS: Record<ClaveAlgoritmo, MetaAlgoritmo> = {
  decision_tree: {
    nombre: 'Árbol de decisión',
    color: CATEGORICO[0],
    configuracion: 'DecisionTreeClassifier(max_depth=4)',
    comoFunciona:
      'Aprende preguntas de sí/no sobre las variables del traslado (¿distancia mayor a x km?, ¿hora pico?, ¿presupuesto?) y las encadena en un árbol. Cada hoja es un modo de transporte.',
    ventaja: 'Rápido e interpretable: sus reglas se pueden leer y explicar.',
    riesgo: 'Si se deja crecer sin límite memoriza el entrenamiento (sobreajuste).',
  },
  random_forest: {
    nombre: 'Random Forest',
    color: CATEGORICO[1],
    configuracion: 'RandomForestClassifier(n_estimators=50, max_depth=5)',
    comoFunciona:
      'Entrena 50 árboles, cada uno con una muestra aleatoria de traslados y de variables, y decide por votación de mayoría.',
    ventaja: 'Más estable: promediar muchos árboles reduce la varianza de uno solo.',
    riesgo: 'Entrenar y predecir cuesta más (50 árboles en lugar de 1).',
  },
  k_nearest_neighbors: {
    nombre: 'KNN',
    color: CATEGORICO[2],
    configuracion: 'KNeighborsClassifier(n_neighbors=5, weights="distance")',
    comoFunciona:
      'No construye reglas: guarda los traslados de entrenamiento y, para uno nuevo, busca los 5 más parecidos por distancia euclidiana. Los más cercanos pesan más en el voto.',
    ventaja: 'Sencillo y sin fase de entrenamiento real (solo almacena los datos).',
    riesgo: 'Depende de la escala: aquí las variables entran sin escalar y el presupuesto en pesos domina la distancia sobre variables 0/1 como lluvia u hora pico.',
  },
}

export const ORDEN_ALGORITMOS: ClaveAlgoritmo[] = ['decision_tree', 'random_forest', 'k_nearest_neighbors']

export const REGIMENES: Record<ClaveRegimen, { nombre: string; escenario: string }> = {
  subajuste_underfitting: { nombre: 'Profundidad 1', escenario: 'Escenario de subajuste' },
  ajuste_adecuado: { nombre: 'Profundidad 4', escenario: 'Escenario de ajuste adecuado' },
  sobreajuste_overfitting: { nombre: 'Profundidad libre', escenario: 'Escenario de sobreajuste' },
}

export const CLASES: Record<string, string> = {
  auto_privado: 'Auto privado',
  caminando: 'Caminando',
  transporte_publico: 'Transporte público',
}
export const nombreClase = (c: string) => CLASES[c] ?? c.replace(/_/g, ' ')

/** 0.9688 → 96.9 (los ejes y tooltips trabajan en 0–100). */
export const pct = (v: number) => Math.round(v * 1000) / 10
