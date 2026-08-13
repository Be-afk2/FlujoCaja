from pathlib import Path
import os
import sys

APP_NAME = "FlujoCaja"

# Ruta raíz del proyecto (directorio donde está este archivo)
PROJECT_ROOT = Path(__file__).resolve().parent

# True cuando la app corre dentro de un exe generado con PyInstaller.
IS_FROZEN = getattr(sys, "frozen", False)

# Directorio de recursos: en el exe apunta a _MEIPASS (extracción temporal de
# PyInstaller); en desarrollo, a la raíz del proyecto.
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))

# Directorio donde vive el frontend estático (empaquetado en prod, local en dev).
WEB_DIR = RESOURCE_DIR / "web"

# Directorio donde el usuario descomprime el exe (solo aplica en producción).
EXE_DIR = Path(sys.executable).resolve().parent if IS_FROZEN else PROJECT_ROOT

# Nombre del archivo SQLite
DATABASE_FILENAME = "database.db"
# Ruta al directorio de datos de la aplicación (%APPDATA% en Windows, data/ como fallback)
DATA_DIR = Path(os.environ.get("APPDATA", PROJECT_ROOT / "data")) / APP_NAME
# Ruta completa al archivo de base de datos
DATABASE_PATH = DATA_DIR / DATABASE_FILENAME
# URL de conexión SQLAlchemy/SQLModel — usado en bd/database.py (crear engine),
# bd/migrations.py (Alembic), alembic/env.py
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

# Host y puerto donde escucha el API local
API_HOST = "127.0.0.1"
API_PORT = 8000
# Variable de entorno que activa el modo debug (ej: $env:DEBUG=1)
DEBUG_ENV_VAR = "DEBUG"


def is_debug_enabled() -> bool:
    """Retorna True si la variable DEBUG_ENV_VAR está en "1".
    Usado en main.py y api/mainApi.py para decidir si la API corre en modo debug."""
    return os.environ.get(DEBUG_ENV_VAR, "0") == "1"
