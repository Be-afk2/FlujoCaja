import logging
import socket
import threading
import time

import uvicorn

from api.mainApi import app
from config import API_HOST, API_PORT

logger = logging.getLogger(__name__)


def puerto_disponible(host: str, port: int) -> bool:
    """Retorna True si el puerto está libre probando un bind real."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
        return True
    except OSError:
        return False


class ServidorAPI:
    """Servidor uvicorn in-process corriendo en un hilo.

    Permite que el exe no lance una segunda copia de sí mismo con
    `sys.executable -m uvicorn` (que no funciona en un binario congelado).
    """

    def __init__(self, host: str = API_HOST, port: int = API_PORT, debug: bool = False) -> None:
        self.host = host
        self.port = port
        self.debug = debug
        self.server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None

    def iniciar(self) -> None:
        """Arranca el servidor en un hilo y espera a que esté listo.

        Lanza RuntimeError si el puerto está ocupado o si el arranque falla.
        """
        if not puerto_disponible(self.host, self.port):
            raise RuntimeError(
                f"No se pudo iniciar la API: el puerto {self.port} está ocupado. "
                f"Cerrá la aplicación que lo esté usando e intentá de nuevo."
            )

        config = uvicorn.Config(
            app,
            host=self.host,
            port=self.port,
            log_level="debug" if self.debug else "info",
            log_config=None,  # en un exe sin consola sys.stdout es None y uvicorn crashea
        )
        self.server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self.server.run, daemon=True, name="api-uvicorn")
        self._thread.start()

        deadline = time.time() + 10
        while time.time() < deadline:
            if self.server.started:
                logger.info("API iniciada en http://%s:%s", self.host, self.port)
                return
            if not self._thread.is_alive():
                raise RuntimeError("La API no pudo arrancar (el hilo terminó).")
            time.sleep(0.05)

        raise RuntimeError("Timeout esperando el arranque de la API.")

    def detener(self) -> None:
        """Solicita el cierre ordenado del servidor y espera al hilo."""
        if self.server is not None:
            self.server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=5)