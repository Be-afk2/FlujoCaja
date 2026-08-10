import logging
import os
import sys

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QColor
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


def main():
    app = QApplication(sys.argv)

    view = QWebEngineView()

    # ⚙️ Configuración
    settings = view.settings()
    settings.setAttribute(
        QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
        True
    )

    # 🎨 Fondo oscuro por defecto para evitar flash blanco/negro entre páginas
    view.page().setBackgroundColor(QColor("#0f172a"))

    # ❌ Desactivar click derecho
    view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

    # 📄 Ruta absoluta del HTML
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ruta = os.path.join(base_dir, "index.html")

    if not os.path.exists(ruta):
        logger.error("Archivo no encontrado: %s", ruta)
        sys.exit(1)

    # 🌐 Cargar archivo local
    view.load(QUrl.fromLocalFile(ruta))

    # 🔍 Zoom
    view.setZoomFactor(0.9)

    # 🖥️ Mostrar ventana
    view.showMaximized()

    # ▶️ Ejecutar app
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
