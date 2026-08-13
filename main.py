import argparse
import atexit
import logging
import os
import signal
import sys
import time

from config import API_HOST, API_PORT, DEBUG_ENV_VAR
from bd.bd import comprobar_y_crear_bd
from bd.logging import get_console, setup_logging
from web.webView import main as web_main

logger = logging.getLogger(__name__)
console = get_console()


# ==================== CONFIGURACIÓN GLOBAL ====================
servidor_api = None  # Instancia de api.server.ServidorAPI
DEBUG_MODE: bool = False


# ==================== LIMPIEZA Y SEÑALES ====================
def registrar_limpieza():
    """Registra la limpieza al finalizar la aplicación."""
    atexit.register(detener_api)


def manejar_signal_interrupt(signum, frame):
    """Maneja Ctrl+C para detener el servidor correctamente."""
    console.print("\n[yellow]-> Recibido Ctrl+C, deteniendo servicios...[/yellow]")
    detener_api()
    console.print("[green]OK - Todos los servicios han sido terminados.[/green]")
    sys.exit(0)


def detener_api():
    """Detiene el servidor API in-process de manera ordenada."""
    global servidor_api
    if servidor_api is not None:
        try:
            servidor_api.detener()
            logger.info("API detenida.")
        except Exception as e:
            logger.error("Error al detener la API: %s", e)
        finally:
            servidor_api = None


# ==================== INICIALIZACIÓN DE SERVICIOS ====================
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
        logger.exception("Error al inicializar la base de datos")
        return False


def iniciar_api() -> bool:
    """
    Inicia el servidor API en un hilo dentro del proceso actual.

    Returns:
        bool: True si la API arrancó correctamente, False en caso contrario.
    """
    global servidor_api
    # Import lazy: api.server importa api.mainApi, que lee DEBUG_ENV_VAR al
    # importarse. Hay que asegurarse de que el flag --debug ya fue aplicado.
    from api.server import ServidorAPI

    try:
        console.print(f"[cyan]-> Iniciando API ({API_HOST}:{API_PORT})...[/cyan]")
        servidor = ServidorAPI(host=API_HOST, port=API_PORT, debug=DEBUG_MODE)
        servidor.iniciar()
        servidor_api = servidor
        console.print("[green]OK - API iniciada correctamente.[/green]")
        return True
    except RuntimeError as e:
        logger.error("%s", e)
        console.print(f"[red]ERROR - {e}[/red]")
        _aviso_puerto_ocupado(API_PORT)
        return False
    except Exception as e:
        console.print(f"[red]ERROR - Error al iniciar la API: {e}[/red]")
        logger.exception("Error al iniciar la API")
        return False


def _aviso_puerto_ocupado(port: int) -> None:
    """Muestra un diálogo claro cuando el puerto del API está ocupado."""
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox

        app = QApplication.instance() or QApplication([])
        QMessageBox.critical(
            None,
            "FlujoCaja",
            f"El puerto {port} está ocupado.\n\n"
            "Otra aplicación está usando el puerto que FlujoCaja necesita.\n"
            "Cerrala y volvé a abrir FlujoCaja.",
        )
    except Exception:
        logger.error("Puerto %s ocupado", port)


def iniciar_web() -> bool:
    """
    Inicia la interfaz web (PyQt6). Bloquea hasta que se cierre la ventana.

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
        logger.exception("Error en la interfaz web")
        return False


# ==================== MODOS OPERACIONALES ====================
def modo_solo_api() -> None:
    """Inicia solo el servidor API."""
    console.print("[bold cyan]--- Modo: Solo API ---[/bold cyan]")

    if not iniciar_base_datos():
        console.print("[red]Fallando aplicacion: No se pudo inicializar la BD.[/red]")
        sys.exit(1)

    if not iniciar_api():
        console.print("[red]Fallando aplicacion: No se pudo iniciar la API.[/red]")
        sys.exit(1)

    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        console.print("[yellow]-> Deteniendo API...[/yellow]")
        detener_api()
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
    """Inicia BD + API + la interfaz web (la UI se sirve desde el API)."""
    console.print("[bold cyan]--- Modo: Solo Web ---[/bold cyan]")

    if not iniciar_base_datos():
        console.print("[red]Fallando aplicacion: No se pudo inicializar la BD.[/red]")
        sys.exit(1)

    if not iniciar_api():
        console.print("[red]Fallando aplicacion: No se pudo iniciar la API.[/red]")
        sys.exit(1)

    try:
        if not iniciar_web():
            console.print("[red]Fallando aplicacion: No se pudo iniciar la interfaz web.[/red]")
            sys.exit(1)
    finally:
        detener_api()


def modo_completo() -> None:
    """Inicia todos los servicios (API, BD y Web)."""
    console.print("[bold cyan]--- Modo: Aplicacion Completa ---[/bold cyan]")

    # 1. Inicializar Base de Datos
    if not iniciar_base_datos():
        console.print("[red]Fallando aplicacion: No se pudo inicializar la BD.[/red]")
        sys.exit(1)

    # 2. Iniciar API
    if not iniciar_api():
        console.print("[red]Fallando aplicacion: No se pudo iniciar la API.[/red]")
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
        detener_api()
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
    parser.add_argument('--api', action='store_true', help='Iniciar solo el servidor API')
    parser.add_argument('--bd', action='store_true', help='Iniciar solo la base de datos')
    parser.add_argument('--web', action='store_true', help='Iniciar solo la interfaz web')
    parser.add_argument('--debug', action='store_true', help='Activar modo debug (logs detallados)')

    args = parser.parse_args()

    # Configurar modo debug global
    global DEBUG_MODE
    DEBUG_MODE = args.debug

    if DEBUG_MODE:
        os.environ[DEBUG_ENV_VAR] = "1"
        console.print("[yellow]*** Modo DEBUG activado [/yellow]")

    setup_logging(debug=DEBUG_MODE)

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
        modo_completo()


if __name__ == "__main__":
    main()