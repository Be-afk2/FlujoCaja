"""Genera assets/icon.ico y assets/icon.png para FlujoCaja.

Uso:
    python scripts/generar_icono.py
"""
import pathlib

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import QApplication

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"


def draw_icon(size: int = 256) -> QPixmap:
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    margin = int(size * 0.04)
    radius = int(size * 0.24)

    # Fondo: cuadrado redondeado con gradiente esmeralda
    grad = QLinearGradient(QPointF(0, 0), QPointF(size, size))
    grad.setColorAt(0.0, QColor("#34d399"))
    grad.setColorAt(1.0, QColor("#059669"))

    path = QPainterPath()
    path.addRoundedRect(QRectF(margin, margin, size - 2 * margin, size - 2 * margin), radius, radius)
    p.fillPath(path, grad)

    # Moneda: círculo blanco con letra "C"
    cx, cy = size / 2, size / 2
    coin_r = size * 0.32
    p.setBrush(QColor("#ffffff"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(cx, cy), coin_r, coin_r)

    pen = p.pen()
    pen.setColor(QColor("#059669"))
    pen.setWidth(int(size * 0.09))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    arc = QRectF(cx - coin_r * 0.62, cy - coin_r * 0.62, coin_r * 1.24, coin_r * 1.24)
    p.drawArc(arc, 60 * 16, 240 * 16)

    p.end()
    return pix


def main() -> None:
    _app = QApplication.instance() or QApplication([])
    ASSETS.mkdir(parents=True, exist_ok=True)
    pix = draw_icon(256)
    png = ASSETS / "icon.png"
    ico = ASSETS / "icon.ico"
    pix.save(str(png), "PNG")
    pix.save(str(ico), "ICO")
    pix_small = draw_icon(64)
    pix_small.save(str(ASSETS / "icon-small.png"), "PNG")
    print(f"Generado: {png}, {ico}")


if __name__ == "__main__":
    main()