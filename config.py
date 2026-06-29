from pathlib import Path
import os

APP_NAME = "FlujoCaja"
PROJECT_ROOT = Path(__file__).resolve().parent
DATABASE_FILENAME = "database.db"
DATABASE_PATH = PROJECT_ROOT / DATABASE_FILENAME
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

API_HOST = "127.0.0.1"
API_PORT = 8000
API_IMPORT_PATH = "api.mainApi:app"
API_RELOAD_IN_DEBUG = True
API_STARTUP_DELAY_SECONDS = 1
FRONTEND_LOAD_TIMEOUT_SECONDS = 30
DEBUG_ENV_VAR = "DEBUG"


def is_debug_enabled() -> bool:
    return os.environ.get(DEBUG_ENV_VAR, "0") == "1"


def build_api_command(python_executable: str, debug: bool = False) -> list[str]:
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
