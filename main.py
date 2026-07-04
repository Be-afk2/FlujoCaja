import subprocess
import sys
import argparse
import atexit
import signal
import os
import time
from typing import List, Optional
from rich.console import Console
from config import API_HOST, API_PORT, API_STARTUP_DELAY_SECONDS, DEBUG_ENV_VAR, build_api_command

# Importar funciones de módulos
from bd.bd import comprobar_y_crear_bd
from web.webView import main as web_main

console = Console()


# ==================== CONFIGURACIÓN GLOBAL ====================
PROCESOS_ACTIVOS: List[subprocess.Popen] = []
DEBUG_MODE: bool = False


# ==================== FUNCIONES DE GESTIÓN DE PROCESOS ====================
def registrar_limpieza():
    """Registra la función de limpieza para ejecutar al finalizar."""
    atexit.register(limpiar_procesos)


def manejar_signal_interrupt(signum, frame):
    """Maneja Ctrl+C para limpiar procesos correctamente."""
    console.print("\n[yellow]-> Recibido Ctrl+C, deteniendo servicios...[/yellow]")
    limpiar_procesos()
    console.print("[green]OK - Todos los servicios han sido terminados.[/green]")
    sys.exit(0)


def limpiar_procesos():
    """Termina todos los procesos activos de manera ordenada."""
    for proceso in PROCESOS_ACTIVOS:
        if proceso.poll() is None:  # Si el proceso aún está corriendo
            try:
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(proceso.pid)],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                else:
                    proceso.terminate()
                proceso.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proceso.kill()
                proceso.wait()
            except Exception:
                try:
                    proceso.kill()
                    proceso.wait()
                except Exception:
                    pass
    PROCESOS_ACTIVOS.clear()


def iniciar_base_datos() -> bool:
    """
    Inicia la base de datos verificando y creando si es necesario.
    
    Returns:
        bool: True si la BD se inició correctamente, False en caso contrario.
    """
    try:
        console.print("[cyan]-> Inicializando base de datos...[/cyan]")
        comprobar_y_crear_bd()
        console.print("[green]OK - Base de datos lista.[/green]")
        return True
    except Exception as e:
        console.print(f"[red]ERROR - Error al inicializar la base de datos: {e}[/red]")
        return False


def iniciar_api() -> Optional[subprocess.Popen]:
    """
    Inicia el servidor API en un subprocess.
    
    Returns:
        subprocess.Popen: Objeto del proceso si se inicia correctamente, None en caso contrario.
    """
    try:
        # Actualizar configuración según modo debug
        comando = build_api_command(sys.executable, DEBUG_MODE)
        
        if DEBUG_MODE:
            console.print(f"[cyan]-> Iniciando API ({API_HOST}:{API_PORT}) en modo DEBUG...[/cyan]")
        else:
            console.print(f"[cyan]-> Iniciando API ({API_HOST}:{API_PORT})...[/cyan]")
        
        # Preparar variables de entorno
        env = None
        if DEBUG_MODE:
            env = os.environ.copy()
            env[DEBUG_ENV_VAR] = "1"
        
        popen_kwargs = {
            "stdout": None if DEBUG_MODE else subprocess.PIPE,
            "stderr": None if DEBUG_MODE else subprocess.PIPE,
            "text": True,
            "env": env,
        }
        if os.name == "nt":
            popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        proceso = subprocess.Popen(comando, **popen_kwargs)
        # Verificar que el proceso se inició correctamente
        time.sleep(API_STARTUP_DELAY_SECONDS)
        if proceso.poll() is not None:
            stdout, stderr = proceso.communicate()
            console.print(f"[red]ERROR - Error al iniciar la API: {stderr}[/red]")
            return None
        PROCESOS_ACTIVOS.append(proceso)
        console.print("[green]OK - API iniciada correctamente.[/green]")
        return proceso
    except Exception as e:
        console.print(f"[red]ERROR - Error al iniciar la API: {e}[/red]")
        return None


def iniciar_web() -> bool:
    """
    Inicia la interfaz web (PyQt6).
    
    Returns:
        bool: True si se completó la ejecución, False si hubo error.
    """
    try:
        console.print("[cyan]-> Iniciando interfaz web...[/cyan]")
        web_main()
        return True
    except KeyboardInterrupt:
        console.print("[yellow]! Aplicacion detenida por el usuario.[/yellow]")
        return True
    except Exception as e:
        console.print(f"[red]ERROR - Error en la interfaz web: {e}[/red]")
        return False


# ==================== FUNCIONES DE MODO OPERACIONAL ====================
def modo_solo_api() -> None:
    """Inicia solo el servidor API."""
    console.print("[bold cyan]--- Modo: Solo API ---[/bold cyan]")
    
    if not iniciar_base_datos():
        console.print("[red]Fallando aplicacion: No se pudo inicializar la BD.[/red]")
        sys.exit(1)
    
    proceso_api = iniciar_api()
    if not proceso_api:
        console.print("[red]Fallando aplicacion: No se pudo iniciar la API.[/red]")
        sys.exit(1)
    
    try:
        # Usar un loop para permitir que Ctrl+C se capture correctamente
        while proceso_api.poll() is None:
            time.sleep(0.1)
    except KeyboardInterrupt:
        console.print("[yellow]-> Deteniendo API...[/yellow]")
        limpiar_procesos()
        console.print("[green]OK - API terminada.[/green]")


def modo_solo_bd() -> None:
    """Inicia solo la base de datos (útil para verificar)."""
    console.print("[bold cyan]--- Modo: Solo Base de Datos ---[/bold cyan]")
    
    if not iniciar_base_datos():
        console.print("[red]Fallando aplicacion: No se pudo inicializar la BD.[/red]")
        sys.exit(1)
    
    console.print("[green]Base de datos lista. Presione Ctrl+C para salir.[/green]")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("[yellow]Deteniendo BD...[/yellow]")


def modo_solo_web() -> None:
    """Inicia solo la interfaz web."""
    console.print("[bold cyan]--- Modo: Solo Web ---[/bold cyan]")
    
    if not iniciar_base_datos():
        console.print("[red]Fallando aplicacion: No se pudo inicializar la BD.[/red]")
        sys.exit(1)
    
    if not iniciar_web():
        console.print("[red]Fallando aplicacion: No se pudo iniciar la interfaz web.[/red]")
        sys.exit(1)


def modo_completo() -> None:
    """Inicia todos los servicios (API, BD y Web)."""
    console.print("[bold cyan]--- Modo: Aplicacion Completa ---[/bold cyan]")
    
    # 1. Inicializar Base de Datos
    if not iniciar_base_datos():
        console.print("[red]Fallando aplicacion: No se pudo inicializar la BD.[/red]")
        sys.exit(1)
    
    # 2. Iniciar API
    proceso_api = iniciar_api()
    if not proceso_api:
        console.print("[red]Fallando aplicación: No se pudo iniciar la API.[/red]")
        sys.exit(1)
    
    # 3. Iniciar Web (bloquea hasta que se cierre)
    try:
        iniciar_web()
    except KeyboardInterrupt:
        console.print("[yellow]-> Deteniendo servicios...[/yellow]")
    except Exception as e:
        console.print(f"[red]Error en la aplicacion: {e}[/red]")
    finally:
        console.print("[yellow]-> Cerrando servicios...[/yellow]")
        limpiar_procesos()
        console.print("[green]OK - Todos los servicios han sido terminados.[/green]")


# ==================== FUNCIÓN PRINCIPAL ====================
def main():
    """Punto de entrada de la aplicación."""
    parser = argparse.ArgumentParser(
        description='FlujoCaja - Gestor de Flujo de Caja',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python main.py               # Inicia API, BD y Web
  python main.py --api         # Inicia solo la API
  python main.py --api --debug # Inicia API en modo debug
  python main.py --bd          # Inicia solo la BD
  python main.py --web         # Inicia solo la Web
        """
    )
    parser.add_argument(
        '--api',
        action='store_true',
        help='Iniciar solo el servidor API'
    )
    parser.add_argument(
        '--bd',
        action='store_true',
        help='Iniciar solo la base de datos'
    )
    parser.add_argument(
        '--web',
        action='store_true',
        help='Iniciar solo la interfaz web'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Activar modo debug (muestra logs detallados del API)'
    )
    
    args = parser.parse_args()
    
    # Configurar modo debug global
    global DEBUG_MODE
    DEBUG_MODE = args.debug
    
    if DEBUG_MODE:
        console.print("[yellow]*** Modo DEBUG activado [/yellow]")
    
    # Registrar limpieza al finalizar
    registrar_limpieza()
    
    # Registrar manejador de Ctrl+C
    signal.signal(signal.SIGINT, manejar_signal_interrupt)
    
    # Determinar qué modo ejecutar
    if args.api:
        modo_solo_api()
    elif args.bd:
        modo_solo_bd()
    elif args.web:
        modo_solo_web()
    else:
        # Si no hay parámetros, iniciar todo
        modo_completo()


if __name__ == "__main__":
    main()
