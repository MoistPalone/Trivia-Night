import re

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
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

_NAME_RE = re.compile(r"^[\x20-\x7E]{2,20}$")


class WelcomeScreen(QWidget):
    game_started = pyqtSignal(str, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {BG};")
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        title = QLabel("TRIVIA NIGHT")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Sans", 52, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {GOLD};")
        layout.addWidget(title)

        sub = QLabel("Two players. Six genres. One winner.")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setFont(QFont("Sans", 16))
        sub.setStyleSheet(f"color: {TEXT};")
        layout.addWidget(sub)

        layout.addSpacing(40)

        for label_text, attr in [("Player 1", "p1_input"), ("Player 2", "p2_input")]:
            lbl = QLabel(label_text)
            lbl.setFont(QFont("Sans", 13, QFont.Weight.Bold))
            lbl.setStyleSheet(f"color: {GOLD};")
            layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)

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
            setattr(self, attr, field)
            layout.addWidget(field, alignment=Qt.AlignmentFlag.AlignCenter)
            layout.addSpacing(8)

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

    def _on_start(self) -> None:
        p1 = self.p1_input.text().strip()
        p2 = self.p2_input.text().strip()

        if not _NAME_RE.match(p1):
            self._err("Player 1 name must be 2–20 printable characters.")
            return
        if not _NAME_RE.match(p2):
            self._err("Player 2 name must be 2–20 printable characters.")
            return

        self.game_started.emit(p1, p2)

    def _err(self, msg: str) -> None:
        box = QMessageBox(self)
        box.setWindowTitle("Invalid Input")
        box.setText(msg)
        box.setStyleSheet(f"background-color: {BG}; color: {TEXT};")
        box.exec()
