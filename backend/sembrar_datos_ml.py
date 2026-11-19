"""Script para sembrar datos de prueba en la colección 'historial_rutas' de MongoDB

Alimenta el modelo de Machine Learning con hábitos reales de movilidad en Toluca y Metepec.
"""

import os
from pymongo import MongoClient

# Conexión local a MongoDB Compass
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
NOMBRE_BD = "kompas"  # <--- Tu base de datos real mostrada en Compass

def sembrar_historial():
    print("Conectando a MongoDB Compass...")
    cliente = MongoClient(MONGO_URI)
    db = cliente[NOMBRE_BD]
    
    # Colección exacta visible en tu interfaz de Compass
    coleccion = db["historial_rutas"]

    # Limpiamos registros previos de prueba para evitar duplicidad
    coleccion.delete_many({"usuario_id": "kevin_eduardo"})

    # Documentos de prueba alineados con los hábitos del usuario
    datos_prueba = [
        {
            "usuario_id": "kevin_eduardo",
            "origen": "Casa",
            "destino": "Universidad Tecnológica (UTVT)",
            "hora_dia": 7,
            "dia_semana": "Lunes",
            "distancia_km": 4.5,
            "presupuesto_mxn": 30.0,
            "clima_lluvia": False,
            "temperatura": 14.0,
            "modo_utilizado": "transporte_publico"
        },
        {
            "usuario_id": "kevin_eduardo",
            "origen": "Universidad Tecnológica (UTVT)",
            "destino": "Centro Toluca",
            "hora_dia": 15,
            "dia_semana": "Lunes",
            "distancia_km": 8.2,
            "presupuesto_mxn": 50.0,
            "clima_lluvia": True,
            "temperatura": 12.0,
            "modo_utilizado": "transporte_publico"
        },
        {
            "usuario_id": "kevin_eduardo",
            "origen": "Casa",
            "destino": "Centro Comercial Metepec",
            "hora_dia": 18,
            "dia_semana": "Viernes",
            "distancia_km": 5.0,
            "presupuesto_mxn": 100.0,
            "clima_lluvia": False,
            "temperatura": 22.0,
            "modo_utilizado": "auto"
        },
        {
            "usuario_id": "kevin_eduardo",
            "origen": "Universidad Tecnológica (UTVT)",
            "destino": "Casa",
            "hora_dia": 17,
            "dia_semana": "Martes",
            "distancia_km": 4.5,
            "presupuesto_mxn": 30.0,
            "clima_lluvia": False,
            "temperatura": 24.0,
            "modo_utilizado": "transporte_publico"
        }
    ]

    # Inserción masiva
    resultado = coleccion.insert_many(datos_prueba)
    print(f"¡Éxito! Se insertaron {len(resultado.inserted_ids)} registros en la colección 'historial_rutas' de la BD 'kompas'.")
    
    cliente.close()

if __name__ == "__main__":
    sembrar_historial()