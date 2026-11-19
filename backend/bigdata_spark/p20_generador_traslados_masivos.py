"""Modulo de Generacion de Datos Masivos de Movilidad Urbana (Practica 20).

Este modulo genera grandes volumenes de telemetria sintetica de viajes (50,000+ registros)
para pruebas de estres, entrenamiento distribuido y pipelines de Big Data:
- Paradas, coordenadas lat/lon, horarios, velocidades, costos y modos de transporte.
- Simula patrones realistas: picos de demanda matutinos y vespertinos, variaciones de lluvia y trafico.
"""

from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd

RUTA_DEFECTO_EXPORTACION = Path(__file__).resolve().parent / "traslados_masivos_50k.csv"


class GeneradorTrasladosMasivosKompas:
    """Generador sintetico a gran escala para telemetria y analitica distribuida."""

    def __init__(self, registros: int = 50000, semilla: int = 42):
        """Inicializa los parametros de volumen y semilla."""
        self.registros = registros
        self.semilla = semilla

    def generar_dataset_completo(self, ruta_destino: Path | str = RUTA_DEFECTO_EXPORTACION) -> Path:
        """Crea la matriz masiva de eventos de viaje y la exporta a CSV (Practica 20).
        
        Que hace:
            Genera 50,000 registros tabulares con correlaciones urbanas realistas.
        Como lo hace:
            Utiliza distribuciones normales, uniformes y binomiales de NumPy y exporta con Pandas.
        """
        np.random.seed(self.semilla)
        ruta_salida = Path(ruta_destino)
        ruta_salida.parent.mkdir(parents=True, exist_ok=True)

        # Generacion de identificadores
        viaje_ids = [f"VI-TR-{i:06d}" for i in range(1, self.registros + 1)]
        usuario_ids = [f"USR-{np.random.randint(1000, 9999)}" for _ in range(self.registros)]

        # Horas del dia con distribucion bimodal (picos a las 8:00 y 18:30)
        pico1 = np.random.normal(8.0, 1.2, int(self.registros * 0.40))
        pico2 = np.random.normal(18.5, 1.5, int(self.registros * 0.40))
        valle = np.random.uniform(5.0, 23.0, int(self.registros * 0.20))
        horas = np.concatenate([pico1, pico2, valle])
        np.random.shuffle(horas)
        horas = np.clip(horas, 5.0, 23.9).round(2)
        horas_int = horas.astype(int)

        # Distancias en kilometros
        distancias = np.random.gamma(shape=2.5, scale=4.0, size=self.registros)
        distancias = np.clip(distancias, 0.8, 45.0).round(2)

        # Modos de transporte probables
        modos = ["Metro", "Metrobus", "Autobus", "Bicicleta", "Caminata", "Auto_App"]
        prob_modos = [0.35, 0.25, 0.20, 0.08, 0.05, 0.07]
        medios_elegidos = np.random.choice(modos, size=self.registros, p=prob_modos)

        # Costos y duraciones segun medio y distancia
        tarifas_base = {"Metro": 5.0, "Metrobus": 6.0, "Autobus": 12.0, "Bicicleta": 0.0, "Caminata": 0.0, "Auto_App": 45.0}
        velocidades_base = {"Metro": 32.0, "Metrobus": 22.0, "Autobus": 16.0, "Bicicleta": 14.0, "Caminata": 4.5, "Auto_App": 25.0}

        costos = []
        duraciones = []
        retrasos = []

        for d, h, m in zip(distancias, horas_int, medios_elegidos):
            es_pico = 1 if (7 <= h <= 9 or 18 <= h <= 20) else 0
            factor_trafico = 1.35 if es_pico else 1.0

            vel = velocidades_base[m] / factor_trafico
            dur = (d / vel) * 60.0 + np.random.normal(2.0, 1.0)
            dur = max(3.0, round(dur, 1))

            costo = tarifas_base[m] + (d * 1.5 if m == "Auto_App" else 0.0)
            costo = round(costo, 2)

            demora = 1 if dur > (d / velocidades_base[m] * 60.0 * 1.25) else 0

            costos.append(costo)
            duraciones.append(dur)
            retrasos.append(demora)

        df = pd.DataFrame({
            "id_viaje": viaje_ids,
            "id_usuario": usuario_ids,
            "hora_dia": horas,
            "hora_entera": horas_int,
            "distancia_km": distancias,
            "medio_transporte": medios_elegidos,
            "costo_mxn": costos,
            "duracion_min": duraciones,
            "retraso_demora": retrasos,
        })

        df.to_csv(ruta_salida, index=False)
        return ruta_salida


if __name__ == "__main__":
    gen = GeneradorTrasladosMasivosKompas(registros=50000)
    archivo = gen.generar_dataset_completo()
    print(f"Dataset de 50,000 registros generado en: {archivo}")
