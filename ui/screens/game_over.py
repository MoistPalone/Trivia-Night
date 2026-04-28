from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from game.state import GameState

BG = "#0d1b2a"
GOLD = "#c9a84c"
TEXT_COLOR = "#e8e8e8"
DIM = "#7788aa"


class GameOverScreen(QWidget):
    play_again = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {BG};")
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(80, 80, 80, 80)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        trophy = QLabel("🏆")
        trophy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        trophy.setFont(QFont("Sans", 72))
        layout.addWidget(trophy)

        self._winner_label = QLabel("")
        self._winner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._winner_label.setFont(QFont("Sans", 36, QFont.Weight.Bold))
        self._winner_label.setStyleSheet(f"color: {GOLD};")
        layout.addWidget(self._winner_label)

        self._winner_score = QLabel("")
        self._winner_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._winner_score.setFont(QFont("Sans", 24))
        self._winner_score.setStyleSheet(f"color: {TEXT_COLOR};")
        layout.addWidget(self._winner_score)

        self._loser_label = QLabel("")
        self._loser_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loser_label.setFont(QFont("Sans", 16))
        self._loser_label.setStyleSheet(f"color: {DIM};")
        layout.addWidget(self._loser_label)

        btn = QPushButton("Play Again")
        btn.setFont(QFont("Sans", 16, QFont.Weight.Bold))
        btn.setFixedHeight(52)
        btn.setFixedWidth(200)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {GOLD};
                color: #0d1b2a;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{ background-color: #dbb85c; }}
            QPushButton:pressed {{ background-color: #b8922a; }}
        """)
        btn.clicked.connect(self.play_again.emit)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def show_winner(self, state: GameState) -> None:
        winner = state.players[state.winner_index]
        loser = state.players[1 - state.winner_index]

        self._winner_label.setText(f"{winner.name} Wins!")
        self._winner_score.setText(f"{winner.score:,} points")
        self._loser_label.setText(f"{loser.name}  —  {loser.score:,} points")
