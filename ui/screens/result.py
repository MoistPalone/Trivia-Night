from PyQt6.QtCore import QEasingCurve, Qt, QTimer, QVariantAnimation, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

BG_CORRECT = "#0d2a1a"
BG_WRONG = "#2a0d0d"
BG = "#0d1b2a"
GOLD = "#c9a84c"
GREEN = "#2ecc71"
RED = "#e74c3c"
TEXT_COLOR = "#e8e8e8"

DISPLAY_MS = 2000


class ResultScreen(QWidget):
    finished = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._icon_anim: QVariantAnimation | None = None
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(24)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._icon_label = QLabel("")
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setFont(QFont("Sans", 72, QFont.Weight.Bold))
        self._icon_label.setFixedHeight(110)
        layout.addWidget(self._icon_label)

        self._verdict_label = QLabel("")
        self._verdict_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._verdict_label.setFont(QFont("Sans", 28, QFont.Weight.Bold))
        layout.addWidget(self._verdict_label)

        self._points_label = QLabel("")
        self._points_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._points_label.setFont(QFont("Sans", 20))
        self._points_label.setStyleSheet(f"color: {GOLD}; background: transparent;")
        layout.addWidget(self._points_label)

        self._answer_label = QLabel("")
        self._answer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._answer_label.setFont(QFont("Sans", 14))
        self._answer_label.setStyleSheet(f"color: {TEXT_COLOR}; background: transparent;")
        self._answer_label.setWordWrap(True)
        layout.addWidget(self._answer_label)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def show_result(
        self,
        correct: bool,
        points_awarded: int,
        player_name: str,
        correct_answer: str,
    ) -> None:
        if correct:
            self.setStyleSheet(f"background-color: {BG_CORRECT};")
            self._icon_label.setText("✓")
            self._icon_label.setStyleSheet(f"color: {GREEN}; background: transparent;")
            self._verdict_label.setText(f"Correct!  {player_name} scores!")
            self._verdict_label.setStyleSheet(f"color: {GREEN}; background: transparent;")
            self._points_label.setText(f"+{points_awarded} points")
            self._answer_label.setText("")
        else:
            self.setStyleSheet(f"background-color: {BG_WRONG};")
            self._icon_label.setText("✗")
            self._icon_label.setStyleSheet(f"color: {RED}; background: transparent;")
            self._verdict_label.setText("Wrong!")
            self._verdict_label.setStyleSheet(f"color: {RED}; background: transparent;")
            self._points_label.setText("No points awarded")
            self._answer_label.setText(f"Answer: {correct_answer}")

        QTimer.singleShot(260, self._animate_icon)
        QTimer.singleShot(DISPLAY_MS, self.finished.emit)

    def _animate_icon(self) -> None:
        if self._icon_anim is not None:
            self._icon_anim.stop()
        anim = QVariantAnimation(self)
        anim.setStartValue(16.0)
        anim.setEndValue(72.0)
        anim.setDuration(220)
        anim.setEasingCurve(QEasingCurve.Type.OutBack)
        anim.valueChanged.connect(
            lambda v: self._icon_label.setFont(QFont("Sans", int(v), QFont.Weight.Bold))
        )
        anim.finished.connect(
            lambda: self._icon_label.setFont(QFont("Sans", 72, QFont.Weight.Bold))
        )
        anim.start()
        self._icon_anim = anim
