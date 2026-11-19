"""Modulo de Motor Inteligente de Recomendaciones Multimodelo de Movilidad (Practica 14).

Este modulo integra tres modelos complementarios de Inteligencia Artificial para
generar recomendaciones personalizadas de transporte en KompasAPPbeta:
1. Modelo Supervisado (Random Forest): Prediccion del medio de transporte optimo o riesgo de demora.
2. Modelo No Supervisado (K-Means): Clasificacion del usuario en 4 perfiles de viajeros.
3. Reduccion de Dimensionalidad (PCA): Mapeo bidimensional cartesiano (PC1, PC2).

A partir de los tres resultados, aplica un motor de reglas de inferencia para emitir
recomendaciones operativas para la ruta y el presupuesto del usuario.
"""

from pathlib import Path
from typing import Any
import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from app.modulos.ia_kompas.p07_segmentacion_viajeros import COLUMNAS_CLUSTERING
from app.modulos.ia_kompas.pipeline_datos import RUTA_LIMPIO_DEFECTO

# Definicion semantica de los perfiles de movilidad
PERFILES_VIAJEROS = {
    0: {
        "nombre": "Viajero Economico / Rutinario",
        "descripcion": "Prioriza tarifas bajas y trayectos habituales en transporte masivo (Metro/Autobus).",
        "sensibilidad_precio": "Alta",
        "flexibilidad_horaria": "Baja",
    },
    1: {
        "nombre": "Viajero Expres / Ejecutivo",
        "descripcion": "Prioriza el menor tiempo de traslado y confort directo, tolerando mayores presupuestos.",
        "sensibilidad_precio": "Baja",
        "flexibilidad_horaria": "Media",
    },
    2: {
        "nombre": "Viajero Interurbano / Larga Distancia",
        "descripcion": "Realiza trayectos extensos conectando distintas zonas del area metropolitana.",
        "sensibilidad_precio": "Media",
        "flexibilidad_horaria": "Baja",
    },
    3: {
        "nombre": "Viajero Multimodal / Flexible",
        "descripcion": "Combina trayectos cortos a pie, bicicleta compartida y transporte colectivo.",
        "sensibilidad_precio": "Media",
        "flexibilidad_horaria": "Alta",
    },
}


class MotorRecomendacionesKompas:
    """Motor inteligente que orquesta Random Forest, K-Means y PCA para movilidad urbana."""

    def __init__(self, ruta_csv_limpio: Path | str = RUTA_LIMPIO_DEFECTO, semilla: int = 42):
        """Inicializa el motor de recomendaciones con datos y configuracion base.
        
        Que hace:
            Configura el origen de datos y prepara las estructuras para almacenar los modelos.
        Como lo hace:
            Establece la ruta al CSV de traslados limpios y fija la semilla aleatoria.
        Conexiones:
            Se alimenta de kompas_traslados_limpio.csv.
        """
        self.ruta_csv_limpio = Path(ruta_csv_limpio)
        self.semilla = semilla
        self.escalador_kmeans = StandardScaler()
        self.escalador_pca = StandardScaler()
        self.modelo_supervisado: RandomForestClassifier | None = None
        self.modelo_kmeans: KMeans | None = None
        self.modelo_pca: PCA | None = None
        self.caracteristicas_supervisadas: list[str] = []
        self._ajustar_o_cargar_modelos()

    def _ajustar_o_cargar_modelos(self) -> None:
        """Entrena y calibra los tres modelos necesarios para el motor si no estan precargados.
        
        Que hace:
            Garantiza la disponibilidad inmediata de Random Forest, K-Means y PCA en memoria,
            cargando artefactos .joblib si existen o entrenandolos al vuelo.
        Como lo hace:
            1. Comprueba si existen los archivos serializados en backend/data/modelos.
            2. Si existen, los carga con joblib.load() (Practica 14).
            3. Si no existen, los entrena sobre kompas_traslados_limpio.csv y los serializa.
        """
        dir_modelos = self.ruta_csv_limpio.parent / "modelos"
        arch_rf = dir_modelos / "modelo_random_forest_kompas.joblib"
        arch_km = dir_modelos / "modelo_kmeans_kompas.joblib"
        arch_pca = dir_modelos / "modelo_pca_kompas.joblib"

        if arch_rf.exists() and arch_km.exists() and arch_pca.exists():
            pkg_rf = joblib.load(arch_rf)
            pkg_km = joblib.load(arch_km)
            pkg_pca = joblib.load(arch_pca)

            self.modelo_supervisado = pkg_rf["modelo"]
            self.caracteristicas_supervisadas = pkg_rf["caracteristicas"]
            self.modelo_kmeans = pkg_km["modelo"]
            self.escalador_kmeans = pkg_km["escalador"]
            self.modelo_pca = pkg_pca["modelo_pca"]
            self.escalador_pca = pkg_pca["escalador"]
            return

        if not self.ruta_csv_limpio.exists():
            raise FileNotFoundError(f"No existe el archivo de traslados: {self.ruta_csv_limpio}")

        df = pd.read_csv(self.ruta_csv_limpio)

        # 1. Ajuste del Modelo Supervisado (Random Forest)
        columnas_features = ["distancia_km", "hora_dia", "presupuesto_mxn", "es_hora_pico", "clima_lluvia"]
        self.caracteristicas_supervisadas = [c for c in columnas_features if c in df.columns]
        
        if "medio_transporte" in df.columns:
            etiqueta_objetivo = "medio_transporte"
        elif "resultado" in df.columns:
            etiqueta_objetivo = "resultado"
        else:
            etiqueta_objetivo = df.columns[-1]

        X_sup = df[self.caracteristicas_supervisadas].values
        y_sup = df[etiqueta_objetivo].values

        self.modelo_supervisado = RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            random_state=self.semilla,
        )
        self.modelo_supervisado.fit(X_sup, y_sup)

        # 2. Ajuste del Modelo No Supervisado (K-Means k=4)
        X_k = df[COLUMNAS_CLUSTERING].values
        X_k_esc = self.escalador_kmeans.fit_transform(X_k)

        self.modelo_kmeans = KMeans(
            n_clusters=4,
            init="k-means++",
            n_init=10,
            random_state=self.semilla,
        )
        self.modelo_kmeans.fit(X_k_esc)

        # 3. Ajuste de PCA (2 Componentes)
        X_pca_esc = self.escalador_pca.fit_transform(X_k)
        self.modelo_pca = PCA(n_components=2, random_state=self.semilla)
        self.modelo_pca.fit(X_pca_esc)

    def evaluar_traslado_integral(self, datos_traslado: dict[str, Any]) -> dict[str, Any]:
        """Ejecuta la inferencia conjunta (Supervisado + K-Means + PCA + Recomendaciones).
        
        Que hace:
            Procesa una solicitud de viaje individual generando clasificacion, cluster,
            posicionamiento cartesiano y recomendaciones contextuales.
        Como lo hace:
            1. Vectoriza los datos de entrada segun los esquemas esperados por cada modelo.
            2. Infiere la prediccion y probabilidades con Random Forest.
            3. Asigna el cluster de perfil de viajero con K-Means y escala adecuada.
            4. Proyecta las coordenadas (PC1, PC2) con PCA.
            5. Invoca el generador de directivas de recomendacion.
        Conexiones:
            Alimenta el endpoint POST /api/ia/motor-recomendacion-integral y a ServicioIAKompas.
        """
        distancia = float(datos_traslado.get("distancia_km", 10.0))
        hora = int(datos_traslado.get("hora_dia", 8))
        duracion = float(datos_traslado.get("duracion_min", 35.0))
        presupuesto = float(datos_traslado.get("presupuesto_mxn", 25.0))
        es_pico = int(datos_traslado.get("es_hora_pico", 1 if (7 <= hora <= 9 or 18 <= hora <= 20) else 0))
        lluvia = int(datos_traslado.get("clima_lluvia", 0))

        # Vector supervisado
        dict_sup = {
            "distancia_km": distancia,
            "hora_dia": hora,
            "presupuesto_mxn": presupuesto,
            "es_hora_pico": es_pico,
            "clima_lluvia": lluvia,
        }
        x_sup_vec = np.array([[dict_sup[c] for c in self.caracteristicas_supervisadas]])
        pred_transporte = str(self.modelo_supervisado.predict(x_sup_vec)[0])
        probabilidades = self.modelo_supervisado.predict_proba(x_sup_vec)[0]
        clases = [str(c) for c in self.modelo_supervisado.classes_]
        dict_probs = {clases[i]: round(float(probabilidades[i]), 4) for i in range(len(clases))}
        confianza_prediccion = round(float(np.max(probabilidades)), 4)

        # Vector clustering
        vec_clustering = np.array([[distancia, hora, duracion, presupuesto, es_pico]])
        vec_k_esc = self.escalador_kmeans.transform(vec_clustering)
        cluster_id = int(self.modelo_kmeans.predict(vec_k_esc)[0])
        perfil_info = PERFILES_VIAJEROS.get(cluster_id, PERFILES_VIAJEROS[0])

        # Vector PCA
        vec_pca_esc = self.escalador_pca.transform(vec_clustering)
        coords_pca = self.modelo_pca.transform(vec_pca_esc)[0]
        pc1 = round(float(coords_pca[0]), 4)
        pc2 = round(float(coords_pca[1]), 4)

        # Generacion de directivas de recomendacion
        recomendaciones = self._construir_recomendaciones(
            cluster_id=cluster_id,
            transporte_sugerido=pred_transporte,
            confianza=confianza_prediccion,
            distancia=distancia,
            es_pico=es_pico,
            lluvia=lluvia,
            presupuesto=presupuesto,
        )

        return {
            "prediccion_supervisada": {
                "transporte_optimo": pred_transporte,
                "confianza": confianza_prediccion,
                "distribucion_probabilidades": dict_probs,
            },
            "segmentacion_no_supervisada": {
                "cluster_asignado": cluster_id,
                "nombre_perfil": perfil_info["nombre"],
                "descripcion_perfil": perfil_info["descripcion"],
                "sensibilidad_precio": perfil_info["sensibilidad_precio"],
            },
            "reduccion_dimensionalidad_pca": {
                "coordenada_pc1": pc1,
                "coordenada_pc2": pc2,
                "varianza_explicada_acumulada_pct": round(float(np.sum(self.modelo_pca.explained_variance_ratio_) * 100), 2),
            },
            "recomendaciones_operativas": recomendaciones,
        }

    def _construir_recomendaciones(
        self,
        cluster_id: int,
        transporte_sugerido: str,
        confianza: float,
        distancia: float,
        es_pico: int,
        lluvia: int,
        presupuesto: float,
    ) -> list[str]:
        """Genera directivas de asistencia personalizadas basadas en el perfil y las condiciones.
        
        Que hace:
            Transforma los resultados matematicos de los tres modelos en consejos claros de movilidad.
        Como lo hace:
            Aplica un conjunto de condiciones sobre el cluster, clima, horario y presupuesto.
        """
        recs = []

        # Recomendacion por modelo supervisado
        recs.append(f"Modo recomendado por el modelo: {transporte_sugerido} (confianza del {round(confianza * 100, 1)}%).")

        # Reglas por cluster
        if cluster_id == 0:
            recs.append("Perfil Economico: Se priorizan lineas masivas (Metro/Tren Interurbano) con tarifa integrada.")
            if presupuesto < 15.0:
                recs.append("Aviso de presupuesto ajustado: Considera recargar tu tarjeta multimodal con anticipacion.")
        elif cluster_id == 1:
            recs.append("Perfil Expres: Se recomiendan rutas directas con menor tiempo de espera en plataforma.")
            if es_pico:
                recs.append("Alerta de congestion: El transito vehicular supera el promedio; considera lineas en carril confinado.")
        elif cluster_id == 2:
            recs.append("Perfil Larga Distancia: Sugerido planificar transbordos en nodos troncales para reducir demoras.")
        elif cluster_id == 3:
            recs.append("Perfil Multimodal: Ruta ideal combinando tramo en bicicleta o caminata hacia la estacion mas cercana.")

        # Reglas por condiciones ambientales
        if lluvia:
            recs.append("Condicion climatica adversa (lluvia): Anticipa tu salida 10 a 15 minutos debido a marcha lenta preventiva.")

        if es_pico and distancia > 8.0:
            recs.append("Horario de maxima demanda detectado: Verifica alternativas de ruta con menos transbordos intermedios.")

        return recs
