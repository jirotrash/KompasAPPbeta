"""Modulo de Red Neuronal Convolucional 1D para Clasificacion de Congestion (Practicas 23 y 24).

Este modulo implementa un pipeline de Deep Learning utilizando PyTorch para
clasificar el nivel de congestion o demora de un trayecto a partir de secuencias
temporales de mediciones en tramos de ruta (velocidad, tiempo y ocupacion):
1. Preparacion de tensores tridimensionales (batch_size, canales, longitud_secuencia) [Practica 23].
2. Arquitectura CNN 1D con Conv1d, BatchNorm1d, ReLU, Dropout y Linear [Practica 24].
3. Entrenamiento con PyTorch, Early Stopping y evaluacion en prueba ciega.
"""

from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.preprocessing import StandardScaler

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_DISPONIBLE = True
except ImportError:
    TORCH_DISPONIBLE = False

# Mapeo de clases de nivel de congestion urbana
CLASES_CONGESTION = {
    0: "Transito Fluido / Despejado",
    1: "Transito Moderado / Saturacion Media",
    2: "Congestion Severa / Cuello de Botella",
}


if TORCH_DISPONIBLE:
    class ArquitecturaCNN1DClasificador(nn.Module):
        """Red Neuronal Convolucional Unidimensional para analisis de series de traslados."""

        def __init__(self, canales_entrada: int = 3, num_clases: int = 3):
            super().__init__()
            # Capa Conv 1: Analiza patrones en ventanas temporales adyacentes
            self.conv1 = nn.Conv1d(in_channels=canales_entrada, out_channels=16, kernel_size=2, padding=1)
            self.bn1 = nn.BatchNorm1d(16)
            self.relu1 = nn.ReLU()

            # Capa Conv 2: Aprende combinaciones de orden superior
            self.conv2 = nn.Conv1d(in_channels=16, out_channels=32, kernel_size=2)
            self.bn2 = nn.BatchNorm1d(32)
            self.relu2 = nn.ReLU()

            # Agrupamiento adaptativo para colapsar la dimension temporal
            self.pool = nn.AdaptiveAvgPool1d(1)
            self.dropout = nn.Dropout(p=0.25)
            self.fc = nn.Linear(in_features=32, out_features=num_clases)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            x = self.relu1(self.bn1(self.conv1(x)))
            x = self.relu2(self.bn2(self.conv2(x)))
            x = self.pool(x)
            x = x.squeeze(-1)
            x = self.dropout(x)
            x = self.fc(x)
            return x
else:
    class ArquitecturaCNN1DClasificador:
        def __init__(self, *args, **kwargs):
            pass


class ClasificadorCongestionCNN1D:
    """Orquestador de preparacion de datos, entrenamiento y evaluacion de la CNN 1D."""

    def __init__(
        self,
        canales_entrada: int = 3,
        longitud_secuencia: int = 4,
        num_clases: int = 3,
        semilla: int = 42,
    ):
        """Inicializa los parametros de la red y el preprocesamiento temporal.
        
        Que hace:
            Establece las dimensiones tensoriles y la semilla aleatoria para reproducibilidad.
        Como lo hace:
            Configura canales (velocidad, demora, costo_tramo), longitud temporal y clases.
        """
        self.canales_entrada = canales_entrada
        self.longitud_secuencia = longitud_secuencia
        self.num_clases = num_clases
        self.semilla = semilla
        self.escalador = StandardScaler()
        self.modelo: Any = None
        self.dispositivo = "cpu"
        if TORCH_DISPONIBLE and torch.cuda.is_available():
            self.dispositivo = "cuda"

    def generar_o_cargar_secuencias_sinteticas(
        self, num_muestras: int = 1200
    ) -> tuple[np.ndarray, np.ndarray]:
        """Genera tensores de secuencias temporales para el entrenamiento (Practica 23).
        
        Que hace:
            Crea observaciones temporales continuas representando los tramos sucesivos de una ruta.
        Como lo hace:
            Para cada muestra genera `longitud_secuencia` pasos con variables simuladas
            (velocidad media, tiempo por parada, ocupacion del autobus/metro).
            Calcula la etiqueta de congestion con base en el promedio de velocidad.
        """
        np.random.seed(self.semilla)
        X = np.zeros((num_muestras, self.canales_entrada, self.longitud_secuencia), dtype=np.float32)
        y = np.zeros(num_muestras, dtype=np.int64)

        for i in range(num_muestras):
            # Canal 0: Velocidad promedio en tramo (km/h)
            estado_base = np.random.choice([0, 1, 2], p=[0.40, 0.35, 0.25])
            if estado_base == 0:
                vel = np.random.normal(loc=45.0, scale=6.0, size=self.longitud_secuencia)
                tiempo = np.random.normal(loc=3.0, scale=0.8, size=self.longitud_secuencia)
                ocupacion = np.random.normal(loc=40.0, scale=10.0, size=self.longitud_secuencia)
            elif estado_base == 1:
                vel = np.random.normal(loc=25.0, scale=5.0, size=self.longitud_secuencia)
                tiempo = np.random.normal(loc=6.5, scale=1.2, size=self.longitud_secuencia)
                ocupacion = np.random.normal(loc=70.0, scale=12.0, size=self.longitud_secuencia)
            else:
                vel = np.random.normal(loc=12.0, scale=3.5, size=self.longitud_secuencia)
                tiempo = np.random.normal(loc=14.0, scale=2.5, size=self.longitud_secuencia)
                ocupacion = np.random.normal(loc=92.0, scale=5.0, size=self.longitud_secuencia)

            vel = np.clip(vel, 3.0, 90.0)
            tiempo = np.clip(tiempo, 1.0, 35.0)
            ocupacion = np.clip(ocupacion, 5.0, 100.0)

            X[i, 0, :] = vel
            X[i, 1, :] = tiempo
            X[i, 2, :] = ocupacion
            y[i] = estado_base

        return X, y

    def entrenar_modelo(
        self,
        epocas: int = 25,
        tamano_lote: int = 32,
        tasa_aprendizaje: float = 0.003,
    ) -> dict[str, Any]:
        """Ejecuta el ciclo de entrenamiento supervisado de la CNN 1D con Early Stopping (Practica 24).
        
        Que hace:
            Entrena los pesos convolucionales optimizando la funcion CrossEntropyLoss con AdamW.
        Como lo hace:
            1. Particiona los datos en 70% Train, 15% Val y 15% Test.
            2. Normaliza los canales de entrada.
            3. Entrena por epocas monitoreando la perdida de validacion.
            4. Si no mejora tras 5 epocas consecutivas, detiene tempranamente.
            5. Evalua el modelo optimo sobre el conjunto de prueba ciego.
        Conexiones:
            Alimenta a ServicioIAKompas y al comparador de modelos de la Practica 25.
        """
        if not TORCH_DISPONIBLE:
            return {
                "error": "PyTorch no esta instalado en este entorno.",
                "estado": "OMITIDO",
            }

        X, y = self.generar_o_cargar_secuencias_sinteticas()

        # Particion 70/15/15
        X_train, X_temp, y_train, y_temp = train_test_split(
            X, y, test_size=0.30, random_state=self.semilla, stratify=y
        )
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=0.50, random_state=self.semilla, stratify=y_temp
        )

        # Normalizacion canal por canal
        for c in range(self.canales_entrada):
            media = X_train[:, c, :].mean()
            std = X_train[:, c, :].std() + 1e-7
            X_train[:, c, :] = (X_train[:, c, :] - media) / std
            X_val[:, c, :] = (X_val[:, c, :] - media) / std
            X_test[:, c, :] = (X_test[:, c, :] - media) / std

        # Convertir a Tensores PyTorch
        t_X_train = torch.tensor(X_train, dtype=torch.float32)
        t_y_train = torch.tensor(y_train, dtype=torch.long)
        t_X_val = torch.tensor(X_val, dtype=torch.float32)
        t_y_val = torch.tensor(y_val, dtype=torch.long)
        t_X_test = torch.tensor(X_test, dtype=torch.float32)
        t_y_test = torch.tensor(y_test, dtype=torch.long)

        loader_train = DataLoader(TensorDataset(t_X_train, t_y_train), batch_size=tamano_lote, shuffle=True)
        loader_val = DataLoader(TensorDataset(t_X_val, t_y_val), batch_size=tamano_lote, shuffle=False)
        loader_test = DataLoader(TensorDataset(t_X_test, t_y_test), batch_size=tamano_lote, shuffle=False)

        modelo = ArquitecturaCNN1DClasificador(
            canales_entrada=self.canales_entrada, num_clases=self.num_clases
        ).to(self.dispositivo)

        criterio = nn.CrossEntropyLoss()
        optimizador = torch.optim.AdamW(modelo.parameters(), lr=tasa_aprendizaje, weight_decay=1e-4)

        mejor_perdida_val = float("inf")
        paciencia = 6
        contador_paciencia = 0
        pesos_optimos = None

        historial = []

        for epoca in range(1, epocas + 1):
            modelo.train()
            perdida_acum = 0.0
            for bx, by in loader_train:
                bx, by = bx.to(self.dispositivo), by.to(self.dispositivo)
                optimizador.zero_grad()
                salida = modelo(bx)
                perdida = criterio(salida, by)
                perdida.backward()
                optimizador.step()
                perdida_acum += perdida.item() * len(by)
            perdida_train = perdida_acum / len(t_X_train)

            # Evaluacion en validacion
            modelo.eval()
            perdida_val_acum = 0.0
            correctos_val = 0
            with torch.no_grad():
                for bx, by in loader_val:
                    bx, by = bx.to(self.dispositivo), by.to(self.dispositivo)
                    salida = modelo(bx)
                    perdida = criterio(salida, by)
                    perdida_val_acum += perdida.item() * len(by)
                    preds = salida.argmax(dim=1)
                    correctos_val += (preds == by).sum().item()

            perdida_val = perdida_val_acum / len(t_X_val)
            acc_val = correctos_val / len(t_X_val)

            historial.append({
                "epoca": epoca,
                "perdida_train": round(perdida_train, 4),
                "perdida_val": round(perdida_val, 4),
                "exactitud_val": round(acc_val, 4),
            })

            # Early stopping check
            if perdida_val < mejor_perdida_val:
                mejor_perdida_val = perdida_val
                pesos_optimos = modelo.state_dict().copy()
                contador_paciencia = 0
            else:
                contador_paciencia += 1
                if contador_paciencia >= paciencia:
                    break

        if pesos_optimos is not None:
            modelo.load_state_dict(pesos_optimos)

        self.modelo = modelo

        # Evaluacion en conjunto de prueba ciego final
        modelo.eval()
        preds_test = []
        with torch.no_grad():
            for bx, _ in loader_test:
                bx = bx.to(self.dispositivo)
                salida = modelo(bx)
                preds_test.extend(salida.argmax(dim=1).cpu().numpy().tolist())

        y_true = t_y_test.numpy()
        acc_test = accuracy_score(y_true, preds_test)
        f1_test = f1_score(y_true, preds_test, average="weighted")
        cm = confusion_matrix(y_true, preds_test).tolist()

        return {
            "arquitectura": "CNN 1D (Conv1d x 2 + BatchNorm + AdaptiveAvgPool + Dropout + FC)",
            "dispositivo": self.dispositivo,
            "epocas_ejecutadas": len(historial),
            "metricas_prueba_ciega": {
                "exactitud": round(float(acc_test), 4),
                "f1_score_ponderado": round(float(f1_test), 4),
                "matriz_confusion": cm,
            },
            "clases_interpretadas": CLASES_CONGESTION,
            "historial_reciente": historial[-5:],
        }

    def inferir_secuencia_en_caliente(self, secuencia: list[list[float]]) -> dict[str, Any]:
        """Clasifica una secuencia de tramos enviada en tiempo real.
        
        Que hace:
            Permite a la app o al router enviar las ultimas paradas y recibir la estimacion de congestion.
        """
        if not TORCH_DISPONIBLE or self.modelo is None:
            # Fallback heuristico si el modelo no fue entrenado
            prom_vel = np.mean([paso[0] for paso in secuencia]) if secuencia else 30.0
            clase = 0 if prom_vel > 35 else (1 if prom_vel > 20 else 2)
            return {
                "nivel_congestion_id": clase,
                "diagnostico": CLASES_CONGESTION[clase],
                "confianza": 0.85,
                "nota": "Inferencia calculada mediante clasificador heuristico de respaldo.",
            }

        matriz = np.array(secuencia, dtype=np.float32).T  # Forma [canales, longitud]
        tensor = torch.tensor(matriz, dtype=torch.float32).unsqueeze(0).to(self.dispositivo)

        self.modelo.eval()
        with torch.no_grad():
            logits = self.modelo(tensor)
            probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]
            pred_id = int(np.argmax(probs))

        return {
            "nivel_congestion_id": pred_id,
            "diagnostico": CLASES_CONGESTION[pred_id],
            "confianza": round(float(probs[pred_id]), 4),
            "probabilidades": {CLASES_CONGESTION[i]: round(float(probs[i]), 4) for i in range(self.num_clases)},
        }
