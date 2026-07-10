from pathlib import Path
import os

APP_NAME = "FlujoCaja"

# Ruta raíz del proyecto (directorio donde está este archivo)
PROJECT_ROOT = Path(__file__).resolve().parent

# Nombre del archivo SQLite
DATABASE_FILENAME = "database.db"
# Ruta al directorio de datos de la aplicación (%APPDATA% en Windows, data/ como fallback)
DATA_DIR = Path(os.environ.get("APPDATA", PROJECT_ROOT / "data")) / APP_NAME
# Ruta completa al archivo de base de datos
DATABASE_PATH = DATA_DIR / DATABASE_FILENAME
# URL de conexión SQLAlchemy/SQLModel — usado en bd/database.py (crear engine),
# bd/migrations.py (Alembic), alembic/env.py
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

# Host donde escucha FastAPI — usado en main.py y build_api_command()
API_HOST = "127.0.0.1"
# Puerto del servidor — usado en main.py y build_api_command()
API_PORT = 8000
# Ruta ASGI para uvicorn ("api.mainApi:app") — usado en build_api_command()
API_IMPORT_PATH = "api.mainApi:app"
# Habilita --reload en modo debug — usado en build_api_command()
API_RELOAD_IN_DEBUG = True
# Segundos de espera antes de abrir la ventana web — usado en main.py
API_STARTUP_DELAY_SECONDS = 1
# Tiempo máximo para que cargue el frontend — usado en main.py
FRONTEND_LOAD_TIMEOUT_SECONDS = 30
# Variable de entorno que activa el modo debug (ej: $env:DEBUG=1) — usado en is_debug_enabled()
DEBUG_ENV_VAR = "DEBUG"


def is_debug_enabled() -> bool:
    """Retorna True si la variable DEBUG_ENV_VAR está en "1".
    Usado en main.py para decidir si lanza la API en modo debug."""
    return os.environ.get(DEBUG_ENV_VAR, "0") == "1"


def build_api_command(python_executable: str, debug: bool = False) -> list[str]:
    """Construye la lista de argumentos para lanzar Uvicorn como subproceso.
    Usado en main.py al arrancar el servidor API."""
    command = [
        python_executable,
        "-m",
        "uvicorn",
        API_IMPORT_PATH,
        "--host",
        API_HOST,
        "--port",
        str(API_PORT),
    ]

    if debug and API_RELOAD_IN_DEBUG:
        command.append("--reload")

    if debug:
        command.extend(["--log-level", "debug"])

    return command
