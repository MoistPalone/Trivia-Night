import math
from pathlib import Path

from PyQt6.QtCore import (
    QEasingCurve, QPropertyAnimation, Qt, QTimer, pyqtSignal,
)
from PyQt6.QtGui import QBrush, QColor, QPainter, QPixmap, QRadialGradient
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QPushButton, QWidget

# Pill centre as fraction of image dimensions (1717 × 916).
# "LET'S PLAY" banner sits at roughly 50% across, 67.5% down.
_PILL_CX = 0.500
_PILL_CY = 0.690
_PILL_W  = 0.145   # fraction of image width
_PILL_H  = 0.065   # fraction of image height

_ASSETS = Path(__file__).parent.parent.parent / "assets" / "images" / "splash.png"


class SplashScreen(QWidget):
    finished = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._pixmap = QPixmap(str(_ASSETS))
        self._glow_t: float = 0.0
        self._glow_alpha: int = 0

        # Invisible clickable overlay anchored over the pill
        self._btn = QPushButton("", self)
        self._btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn.setStyleSheet("background: transparent; border: none;")
        self._btn.clicked.connect(self._on_click)

        # Glow pulse timer (60 fps-ish)
        self._glow_timer = QTimer(self)
        self._glow_timer.setInterval(16)
        self._glow_timer.timeout.connect(self._tick_glow)

        self._fade_in_anim: QPropertyAnimation | None = None

    # ------------------------------------------------------------------ #
    # Show / hide lifecycle                                                #
    # ------------------------------------------------------------------ #

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._glow_timer.start()

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        self._glow_timer.stop()

    # ------------------------------------------------------------------ #
    # Layout                                                               #
    # ------------------------------------------------------------------ #

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._reposition_btn()

    def _reposition_btn(self) -> None:
        w, h = self.width(), self.height()
        # Map pill fractions to the displayed image rect (letterboxed)
        img_rect = self._image_rect()
        iw, ih = img_rect.width(), img_rect.height()
        ox, oy = img_rect.x(), img_rect.y()

        bw = int(iw * _PILL_W)
        bh = int(ih * _PILL_H)
        bx = ox + int(iw * _PILL_CX) - bw // 2
        by = oy + int(ih * _PILL_CY) - bh // 2
        self._btn.setGeometry(bx, by, bw, bh)

    def _image_rect(self):
        """Return the QRect of the image as drawn (letterboxed, aspect-preserved)."""
        from PyQt6.QtCore import QRect
        if self._pixmap.isNull():
            return self.rect()
        pw, ph = self._pixmap.width(), self._pixmap.height()
        ww, wh = self.width(), self.height()
        scale = min(ww / pw, wh / ph)
        iw = int(pw * scale)
        ih = int(ph * scale)
        ox = (ww - iw) // 2
        oy = (wh - ih) // 2
        return QRect(ox, oy, iw, ih)

    # ------------------------------------------------------------------ #
    # Paint                                                                #
    # ------------------------------------------------------------------ #

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0))

        if not self._pixmap.isNull():
            painter.drawPixmap(self._image_rect(), self._pixmap)

        # Diffuse bloom over the pill — layered concentric ellipses, each
        # larger and more transparent, so there is never a visible hard edge.
        if self._glow_alpha > 0:
            btn_geo = self._btn.geometry()
            cx = float(btn_geo.center().x())
            cy = float(btn_geo.center().y())
            base_rw = btn_geo.width() / 2
            base_rh = btn_geo.height() / 2

            painter.setPen(Qt.PenStyle.NoPen)
            a = self._glow_alpha
            # (scale_w, scale_h, alpha_fraction) — outermost layer last
            layers = [
                (1.1,  0.55, 0.40),
                (1.7,  0.65, 0.22),
                (2.6,  0.75, 0.11),
                (3.8,  0.85, 0.05),
            ]
            for sw, sh, af in layers:
                rw = base_rw * sw
                rh = base_rh * sh
                color = QColor(255, 228, 110, int(a * af))
                painter.setBrush(QBrush(color))
                painter.drawEllipse(
                    int(cx - rw), int(cy - rh), int(rw * 2), int(rh * 2)
                )

    # ------------------------------------------------------------------ #
    # Glow animation                                                       #
    # ------------------------------------------------------------------ #

    def _tick_glow(self) -> None:
        self._glow_t += 0.05
        # Sine wave 0→1→0, range maps to alpha 40→180
        v = 0.5 + 0.5 * math.sin(self._glow_t)
        self._glow_alpha = int(40 + 140 * v)
        self.update()

    # ------------------------------------------------------------------ #
    # Click → fade out                                                     #
    # ------------------------------------------------------------------ #

    def _on_click(self) -> None:
        self._glow_timer.stop()
        self._btn.setEnabled(False)

        fx = QGraphicsOpacityEffect(self)
        fx.setOpacity(1.0)
        self.setGraphicsEffect(fx)

        anim = QPropertyAnimation(fx, b"opacity", self)
        anim.setDuration(350)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InQuad)
        anim.finished.connect(self.finished.emit)
        anim.start()
        self._fade_in_anim = anim   # keep reference alive

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def fade_in(self) -> None:
        """Fade the splash in from black on first show."""
        fx = QGraphicsOpacityEffect(self)
        fx.setOpacity(0.0)
        self.setGraphicsEffect(fx)

        anim = QPropertyAnimation(fx, b"opacity", self)
        anim.setDuration(500)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.finished.connect(lambda: self.setGraphicsEffect(None))
        anim.start()
        self._fade_in_anim = anim
