import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineCore import QWebEngineSettings

app = QApplication(sys.argv)

view = QWebEngineView()

view.settings().setAttribute(
    QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
)

ruta = os.path.abspath("index.html")
view.load(QUrl.fromLocalFile(ruta))

view.show()
app.exec()