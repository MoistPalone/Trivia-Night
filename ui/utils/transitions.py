from PyQt6.QtCore import QEasingCurve, QPropertyAnimation
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QStackedWidget, QWidget


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
