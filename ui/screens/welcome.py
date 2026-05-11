import math
import re

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QRadialGradient
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

BG = "#0d1b2a"
GOLD = "#c9a84c"
TILE = "#1a3a6b"
TEXT = "#ffffff"

# Title shimmer: muted amber → bright gold
_SHIMMER_R = (0xa8, 0xff)
_SHIMMER_G = (0x7c, 0xe0)
_SHIMMER_B = (0x28, 0x60)

_NAME_RE = re.compile(r"^[\x20-\x7E]{2,20}$")

_SUBTITLES = {
    2: "Two players. Six genres. One winner.",
    3: "Three players. Six genres. One winner.",
    4: "Four players. Six genres. One winner.",
}


class WelcomeScreen(QWidget):
    game_started = pyqtSignal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._player_count = 2
        self._name_inputs: list[QLineEdit] = []
        self._count_buttons: list[QPushButton] = []
        self._shimmer_t: float = 0.0
        self._shimmer_timer = QTimer(self)
        self._shimmer_timer.setInterval(50)
        self._shimmer_timer.timeout.connect(self._tick_shimmer)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        self._title = QLabel("TRIVIA NIGHT")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setFont(QFont("Sans", 52, QFont.Weight.Bold))
        self._title.setStyleSheet(f"color: {GOLD};")
        layout.addWidget(self._title)

        self._subtitle = QLabel(_SUBTITLES[self._player_count])
        self._subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitle.setFont(QFont("Sans", 16))
        self._subtitle.setStyleSheet(f"color: {TEXT};")
        layout.addWidget(self._subtitle)

        layout.addSpacing(24)

        # Player count selector
        count_row = QHBoxLayout()
        count_row.setSpacing(12)
        count_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        count_lbl = QLabel("Players:")
        count_lbl.setFont(QFont("Sans", 13, QFont.Weight.Bold))
        count_lbl.setStyleSheet(f"color: {GOLD};")
        count_row.addWidget(count_lbl)

        for n in (2, 3, 4):
            btn = QPushButton(str(n))
            btn.setFixedSize(52, 44)
            btn.setFont(QFont("Sans", 15, QFont.Weight.Bold))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, c=n: self._set_player_count(c))
            self._count_buttons.append(btn)
            count_row.addWidget(btn)

        layout.addLayout(count_row)
        layout.addSpacing(8)

        # Dynamic name fields container
        self._fields_widget = QWidget()
        self._fields_layout = QVBoxLayout(self._fields_widget)
        self._fields_layout.setSpacing(8)
        self._fields_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._fields_widget)

        layout.addSpacing(24)

        start_btn = QPushButton("START GAME")
        start_btn.setFont(QFont("Sans", 18, QFont.Weight.Bold))
        start_btn.setMinimumSize(280, 64)
        start_btn.setMaximumWidth(360)
        start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {GOLD};
                color: {BG};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover  {{ background-color: #e0be6a; }}
            QPushButton:pressed {{ background-color: #b8962e; }}
        """)
        start_btn.clicked.connect(self._on_start)
        layout.addWidget(start_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self._refresh_count_buttons()
        self._rebuild_name_fields()

    def _set_player_count(self, count: int) -> None:
        self._player_count = count
        self._subtitle.setText(_SUBTITLES[count])
        self._refresh_count_buttons()
        self._rebuild_name_fields()

    def _refresh_count_buttons(self) -> None:
        for i, btn in enumerate(self._count_buttons):
            n = i + 2
            active = (n == self._player_count)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {"#1a3a6b" if not active else GOLD};
                    color: {GOLD if not active else BG};
                    border: 2px solid {GOLD if active else "#2a5a9b"};
                    border-radius: 4px;
                }}
                QPushButton:hover {{ border-color: {GOLD}; }}
            """)

    def _rebuild_name_fields(self) -> None:
        while self._fields_layout.count():
            item = self._fields_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        self._name_inputs = []
        for i in range(self._player_count):
            label_text = f"Player {i + 1}"
            lbl = QLabel(label_text)
            lbl.setFont(QFont("Sans", 13, QFont.Weight.Bold))
            lbl.setStyleSheet(f"color: {GOLD};")
            self._fields_layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)

            field = QLineEdit()
            field.setPlaceholderText(f"Enter {label_text} name")
            field.setMaxLength(20)
            field.setMinimumSize(320, 48)
            field.setMaximumWidth(400)
            field.setFont(QFont("Sans", 15))
            field.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {TILE};
                    color: {TEXT};
                    border: 2px solid #2a5a9b;
                    border-radius: 4px;
                    padding: 6px 14px;
                }}
                QLineEdit:focus {{ border-color: {GOLD}; }}
            """)
            self._fields_layout.addWidget(field, alignment=Qt.AlignmentFlag.AlignCenter)

            self._name_inputs.append(field)

    def _on_start(self) -> None:
        names = []
        for i, field in enumerate(self._name_inputs):
            name = field.text().strip()
            if not _NAME_RE.match(name):
                self._err(f"Player {i + 1} name must be 2–20 printable characters.")
                return
            names.append(name)

        self.game_started.emit(names)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        cx = self.width() // 2
        cy = self.height() * 2 // 5
        radius = max(self.width(), self.height()) * 0.80
        grad = QRadialGradient(cx, cy, radius)
        grad.setColorAt(0.0, QColor(22, 52, 82))   # lighter blue-navy center
        grad.setColorAt(0.6, QColor(13, 27, 42))   # mid BG
        grad.setColorAt(1.0, QColor(4, 9, 18))     # very dark vignette edges
        painter.fillRect(self.rect(), grad)

    def _tick_shimmer(self) -> None:
        self._shimmer_t += 0.09
        v = 0.5 + 0.5 * math.sin(self._shimmer_t)
        r = int(_SHIMMER_R[0] + (_SHIMMER_R[1] - _SHIMMER_R[0]) * v)
        g = int(_SHIMMER_G[0] + (_SHIMMER_G[1] - _SHIMMER_G[0]) * v)
        b = int(_SHIMMER_B[0] + (_SHIMMER_B[1] - _SHIMMER_B[0]) * v)
        self._title.setStyleSheet(f"color: #{r:02x}{g:02x}{b:02x};")

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._shimmer_t = 0.0
        self._shimmer_timer.start()

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        self._shimmer_timer.stop()

    def _err(self, msg: str) -> None:
        box = QMessageBox(self)
        box.setWindowTitle("Invalid Input")
        box.setText(msg)
        box.setStyleSheet(f"background-color: {BG}; color: {TEXT};")
        box.exec()
