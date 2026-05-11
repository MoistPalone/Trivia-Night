from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

BG = "#1a0505"
RED = "#e74c3c"
GOLD = "#c9a84c"
TEXT_COLOR = "#e8e8e8"
DIM = "#aa8888"


class SuddenDeathScreen(QWidget):
    finished = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {BG};")
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(80, 80, 80, 80)
        layout.setSpacing(28)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bolt = QLabel("⚡")
        bolt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bolt.setFont(QFont("Sans", 72))
        bolt.setStyleSheet(f"color: {RED};")
        layout.addWidget(bolt)

        title = QLabel("SUDDEN DEATH")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Sans", 40, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {RED};")
        layout.addWidget(title)

        self._tied_label = QLabel("")
        self._tied_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._tied_label.setFont(QFont("Sans", 18))
        self._tied_label.setStyleSheet(f"color: {DIM};")
        layout.addWidget(self._tied_label)

        rule = QLabel("First to answer correctly wins!")
        rule.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rule.setFont(QFont("Sans", 16, QFont.Weight.Bold))
        rule.setStyleSheet(f"color: {TEXT_COLOR};")
        layout.addWidget(rule)

        btn = QPushButton("Begin!")
        btn.setFont(QFont("Sans", 18, QFont.Weight.Bold))
        btn.setFixedHeight(56)
        btn.setFixedWidth(200)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {RED};
                color: white;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{ background-color: #ff6655; }}
            QPushButton:pressed {{ background-color: #c0392b; }}
        """)
        btn.clicked.connect(self.finished.emit)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def show_sudden_death(self, tied_names: list[str], score: int) -> None:
        if len(tied_names) == 2:
            names_str = f"{tied_names[0]} and {tied_names[1]}"
        else:
            names_str = ", ".join(tied_names[:-1]) + f", and {tied_names[-1]}"
        self._tied_label.setText(f"{names_str} are tied at {score:,} points")
