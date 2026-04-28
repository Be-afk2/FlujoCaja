import threading
import multiprocessing
import os

# Importar la función de comprobación de BD
from bd.bd import comprobar_y_crear_bd

# Importar la función principal de la web view
from web.webView import main as web_main

# Importar la app de FastAPI
from api.mainApi import app

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

    # 2. Iniciar el servidor API en un proceso separado
    def iniciar_api():
        import uvicorn
        uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)

    # 3. Iniciar la vista web en un hilo separado
    def iniciar_web():
        try:
            web_main()
        except Exception as e:
            print(f"Error al iniciar la vista web: {e}")

    # Crear proceso para la API
    proceso_api = multiprocessing.Process(target=iniciar_api)
    proceso_api.start()

    # Crear hilo para la web
    hilo_web = threading.Thread(target=iniciar_web, daemon=True)
    hilo_web.start()

    # Esperar a que terminen
    try:
        proceso_api.join()
        hilo_web.join()
    except KeyboardInterrupt:
        print("Aplicación detenida por el usuario.")
        proceso_api.terminate()
        hilo_web.join(timeout=1)

if __name__ == "__main__":
    iniciar_aplicacion()