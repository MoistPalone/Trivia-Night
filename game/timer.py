from PyQt6.QtCore import QObject, QTimer, pyqtSignal

QUESTION_DURATION_MS = 30_000
TICK_INTERVAL_MS = 100


class GameTimer(QObject):
    expired = pyqtSignal()
    tick = pyqtSignal(int)  # milliseconds remaining

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setInterval(TICK_INTERVAL_MS)
        self._timer.timeout.connect(self._on_tick)
        self._remaining_ms: int = 0
        self._running: bool = False

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def start(self, duration_ms: int = QUESTION_DURATION_MS) -> None:
        self._remaining_ms = duration_ms
        self._running = True
        self._timer.start()

    def pause(self) -> None:
        if self._running:
            self._timer.stop()
            self._running = False

    def resume(self) -> None:
        if not self._running and self._remaining_ms > 0:
            self._running = True
            self._timer.start()

    def stop(self) -> None:
        self._timer.stop()
        self._running = False
        self._remaining_ms = 0

    @property
    def remaining_ms(self) -> int:
        return self._remaining_ms

    @property
    def is_running(self) -> bool:
        return self._running

    # ------------------------------------------------------------------ #
    # Internal                                                             #
    # ------------------------------------------------------------------ #

    def _on_tick(self) -> None:
        self._remaining_ms = max(0, self._remaining_ms - TICK_INTERVAL_MS)
        self.tick.emit(self._remaining_ms)
        if self._remaining_ms == 0:
            self._timer.stop()
            self._running = False
            self.expired.emit()
