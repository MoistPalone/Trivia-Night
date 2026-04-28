from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QWidget

from game.timer import GameTimer, QUESTION_DURATION_MS

GREEN = "#2ecc71"
YELLOW = "#f39c12"
RED = "#e74c3c"
BG = "#0d1b2a"


def _bar_style(color: str) -> str:
    return f"""
        QProgressBar {{
            background-color: #1a2a3a;
            border: 1px solid #2a4a6a;
            border-radius: 4px;
            text-align: center;
        }}
        QProgressBar::chunk {{
            background-color: {color};
            border-radius: 3px;
        }}
    """


URGENT_THRESHOLD_S = 10


class TimerWidget(QWidget):
    expired = pyqtSignal()
    urgent_tick = pyqtSignal()  # fires once per second when ≤ URGENT_THRESHOLD_S remain

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._timer = GameTimer(self)
        self._duration_ms = QUESTION_DURATION_MS
        self._last_second: int = -1

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self._bar = QProgressBar()
        self._bar.setRange(0, QUESTION_DURATION_MS)
        self._bar.setValue(QUESTION_DURATION_MS)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(18)
        self._bar.setStyleSheet(_bar_style(GREEN))

        self._label = QLabel("30")
        self._label.setFont(QFont("Sans", 14, QFont.Weight.Bold))
        self._label.setStyleSheet(f"color: {GREEN};")
        self._label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._label.setFixedWidth(36)

        layout.addWidget(self._bar)
        layout.addWidget(self._label)

        self._timer.tick.connect(self._on_tick)
        self._timer.expired.connect(self._on_expired)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def start(self, duration_ms: int = QUESTION_DURATION_MS) -> None:
        self._duration_ms = duration_ms
        self._last_second = -1
        self._bar.setRange(0, duration_ms)
        self._bar.setValue(duration_ms)
        self._apply_color(duration_ms, duration_ms)
        self._timer.start(duration_ms)

    def pause(self) -> None:
        self._timer.pause()

    def resume(self) -> None:
        self._timer.resume()

    def stop(self) -> None:
        self._timer.stop()

    @property
    def remaining_ms(self) -> int:
        return self._timer.remaining_ms

    # ------------------------------------------------------------------ #
    # Internals                                                            #
    # ------------------------------------------------------------------ #

    def _on_tick(self, remaining_ms: int) -> None:
        self._bar.setValue(remaining_ms)
        seconds = (remaining_ms + 999) // 1000
        self._label.setText(str(seconds))
        self._apply_color(remaining_ms, self._duration_ms)
        if seconds <= URGENT_THRESHOLD_S and seconds != self._last_second:
            self._last_second = seconds
            self.urgent_tick.emit()

    def _on_expired(self) -> None:
        self._bar.setValue(0)
        self._label.setText("0")
        self._apply_color(0, self._duration_ms)
        self.expired.emit()

    def _apply_color(self, remaining_ms: int, total_ms: int) -> None:
        ratio = remaining_ms / total_ms if total_ms else 0
        if ratio > 0.5:
            color = GREEN
        elif ratio > 0.25:
            color = YELLOW
        else:
            color = RED
        self._bar.setStyleSheet(_bar_style(color))
        self._label.setStyleSheet(f"color: {color};")
