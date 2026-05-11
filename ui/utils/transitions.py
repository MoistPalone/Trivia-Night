from PyQt6.QtCore import QEasingCurve, QPropertyAnimation
from PyQt6.QtGui import QColor, QPainter, QRadialGradient
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QStackedWidget, QWidget


def paint_bg_gradient(widget: QWidget, event) -> None:
    """Shared radial gradient background used across all main game screens.
    Call from paintEvent; do NOT set a background-color stylesheet on the same widget."""
    painter = QPainter(widget)
    cx = widget.width() // 2
    cy = widget.height() * 2 // 5
    radius = max(widget.width(), widget.height()) * 0.85
    grad = QRadialGradient(cx, cy, radius)
    grad.setColorAt(0.0, QColor(22, 52, 82))
    grad.setColorAt(0.6, QColor(13, 27, 42))
    grad.setColorAt(1.0, QColor(4, 9, 18))
    painter.fillRect(widget.rect(), grad)


def fade_to(stack: QStackedWidget, widget: QWidget, duration_ms: int = 250) -> None:
    """Swap to widget on stack with a fade-in. No-op if widget is already current."""
    if stack.currentWidget() is widget:
        return
    stack.setCurrentWidget(widget)
    widget.setGraphicsEffect(None)          # clear any leftover effect
    fx = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(fx)
    anim = QPropertyAnimation(fx, b"opacity", widget)   # widget owns anim
    anim.setDuration(duration_ms)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutQuad)
    anim.finished.connect(lambda: widget.setGraphicsEffect(None))
    anim.start()
