import logging
import os
import sys

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QColor
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication, QFileDialog

from config import APP_NAME, DATA_DIR

logger = logging.getLogger(__name__)


def main():
    app = QApplication(sys.argv)
    QApplication.setOrganizationName(APP_NAME)
    QApplication.setApplicationName(APP_NAME)

    # 💾 Perfil persistente: permite que localStorage (token/sesión recordada)
    # sobreviva entre ejecuciones de la aplicación.
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    profile = QWebEngineProfile(APP_NAME)
    profile.setPersistentStoragePath(str(DATA_DIR / "QtWebEngine"))
    profile.setCachePath(str(DATA_DIR / "QtWebEngine" / "Cache"))
    profile.settings().setAttribute(
        QWebEngineSettings.WebAttribute.LocalStorageEnabled,
        True
    )
    # ⬇️ Manejar descargas (backup BD, exportar CSV) para que el usuario
    # elija dónde guardarlas; sin esto WebEngine cancela las descargas.
    profile.downloadRequested.connect(_guardar_descarga)

    view = QWebEngineView()
    view.setPage(QWebEnginePage(profile, view))

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


def _guardar_descarga(download):
    """Pide al usuario dónde guardar el archivo descargado desde la web."""
    try:
        nombre = download.suggestedFileName() or "descarga"
        ruta, _ = QFileDialog.getSaveFileName(None, "Guardar archivo", nombre)
        if not ruta:
            download.cancel()
            return
        download.setDownloadDirectory(os.path.dirname(ruta))
        download.setDownloadFileName(os.path.basename(ruta))
        download.accept()
    except Exception as e:
        logger.error("Error al configurar descarga: %s", e)
        download.cancel()


if __name__ == "__main__":
    main()
