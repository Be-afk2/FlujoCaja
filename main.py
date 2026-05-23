import threading
import subprocess
import os
import argparse
import sys

# Importar la función de comprobación de BD
from bd.bd import comprobar_y_crear_bd

# Importar la función principal de la web view
from web.webView import main as web_main

# Importar la app de FastAPI
from api.mainApi import app

def iniciar_api():
    # Iniciar uvicorn en un subprocess para reload
    proceso_api = subprocess.Popen([
        "uvicorn", "api.mainApi:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload"
    ])
    return proceso_api

def iniciar_aplicacion():
    """
    Función que inicia la aplicación completa:
    - Comprueba y crea la base de datos si es necesario
    - Inicia el servidor API con uvicorn
    - Inicia la vista web con PyQt6
    """
    print("Iniciando aplicación...")

    # 1. Comprobar y crear BD si no existe
    comprobar_y_crear_bd()

    # 2. Iniciar el servidor API en un subprocess
    proceso_api = iniciar_api()

    # 3. Iniciar la vista web en el hilo principal (para evitar warning de PyQt6)
    try:
        web_main()
    except KeyboardInterrupt:
        print("Aplicación detenida por el usuario.")
    finally:
        proceso_api.terminate()
        proceso_api.wait()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='FlujoCaja - Gestor de Flujo de Caja')
    parser.add_argument('--api', action='store_true', help='Iniciar solo la API')
    
    args = parser.parse_args()
    
    if args.api:
        print("Iniciando solo la API...")
        comprobar_y_crear_bd()
        
        subprocess.run([
            sys.executable, "-m", "uvicorn", "api.mainApi:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--reload"
        ])
    else:
        iniciar_aplicacion()