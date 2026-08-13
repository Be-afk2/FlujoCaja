import io
import logging
from logging.handlers import RotatingFileHandler

from rich.console import Console

from config import DATA_DIR, IS_FROZEN

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILENAME = "flujocaja.log"
LOG_MAX_BYTES = 1_000_000
LOG_BACKUP_COUNT = 3


def setup_logging(debug: bool = False) -> None:
    """Configura el logging de la aplicación.

    - Siempre escribe a %APPDATA%/FlujoCaja/logs/flujocaja.log (RotatingFileHandler).
    - En desarrollo (no frozen) además muestra los logs en la consola.
    - Es idempotente: llamarlo varias veces no duplica handlers.
    """
    root = logging.getLogger()
    handler = getattr(root, "_flujocaja_handler", None)

    if handler is None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logs_dir = DATA_DIR / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        handler = RotatingFileHandler(
            logs_dir / LOG_FILENAME,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root.addHandler(handler)
        root._flujocaja_handler = handler

        if not IS_FROZEN:
            stream = logging.StreamHandler()
            stream.setFormatter(logging.Formatter(LOG_FORMAT))
            root.addHandler(stream)

    root.setLevel(logging.DEBUG if debug else logging.INFO)


def get_console() -> Console:
    """Devuelve una Console de rich segura para el entorno.

    En un exe congelado (console=False) `sys.stdout` es None y rich puede fallar
    al imprimir; en ese caso los mensajes se descartan silenciosamente.
    """
    if IS_FROZEN:
        return Console(file=io.StringIO())
    return Console()
