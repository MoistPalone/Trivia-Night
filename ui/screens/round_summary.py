from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from game.state import GameState

BG = "#0d1b2a"
GOLD = "#c9a84c"
GREEN = "#2ecc71"
TEXT_COLOR = "#e8e8e8"
DIM = "#7788aa"
PANEL_BG = "#0f2236"


def _score_panel(name: str, score: int, leading: bool) -> QWidget:
    w = QWidget()
    border_color = GOLD if leading else "#2a4a6a"
    w.setStyleSheet(
        f"background-color: {PANEL_BG}; border: 2px solid {border_color}; border-radius: 8px;"
    )
    layout = QVBoxLayout(w)
    layout.setContentsMargins(24, 20, 24, 20)
    layout.setSpacing(8)

    name_lbl = QLabel(name)
    name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    name_lbl.setFont(QFont("Sans", 16, QFont.Weight.Bold))
    name_lbl.setStyleSheet(f"color: {GOLD if leading else TEXT_COLOR}; border: none;")
    layout.addWidget(name_lbl)

    score_lbl = QLabel(f"{score:,}")
    score_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    score_lbl.setFont(QFont("Sans", 28, QFont.Weight.Bold))
    score_lbl.setStyleSheet(f"color: {TEXT_COLOR}; border: none;")
    layout.addWidget(score_lbl)

    if leading:
        tag = QLabel("Leading")
        tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag.setFont(QFont("Sans", 11))
        tag.setStyleSheet(f"color: {GOLD}; border: none;")
        layout.addWidget(tag)

    return w


class RoundSummaryScreen(QWidget):
    finished = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {BG};")
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(80, 60, 80, 60)
        outer.setSpacing(32)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._title = QLabel("")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setFont(QFont("Sans", 32, QFont.Weight.Bold))
        self._title.setStyleSheet(f"color: {GOLD};")
        outer.addWidget(self._title)

        self._panels_row = QHBoxLayout()
        self._panels_row.setSpacing(40)
        outer.addLayout(self._panels_row)

        self._status = QLabel("")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setFont(QFont("Sans", 14))
        self._status.setStyleSheet(f"color: {DIM};")
        outer.addWidget(self._status)

        self._next_hint = QLabel("")
        self._next_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._next_hint.setFont(QFont("Sans", 13, QFont.Weight.Bold))
        self._next_hint.setStyleSheet(f"color: {GREEN};")
        outer.addWidget(self._next_hint)

        btn = QPushButton("Continue")
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
        btn.clicked.connect(self.finished.emit)
        outer.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def show_summary(self, state: GameState) -> None:
        self._title.setText(f"Round {state.round_number} Complete")

        # Clear old panels
        while self._panels_row.count():
            item = self._panels_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        max_score = max(p.score for p in state.players)
        leaders = [p for p in state.players if p.score == max_score]

        for p in state.players:
            self._panels_row.addWidget(_score_panel(p.name, p.score, p.score == max_score))

        if len(leaders) == len(state.players):
            self._status.setText("All players are tied!")
        elif len(leaders) > 1:
            names = " and ".join(p.name for p in leaders)
            self._status.setText(f"{names} are tied for the lead")
        else:
            self._status.setText(f"{leaders[0].name} is in the lead")

        next_round = state.round_number + 1
        if next_round == 3:
            self._next_hint.setText("Round 3 — all points doubled  ★ 2×")
        else:
            self._next_hint.setText(f"Up next: Round {next_round}")
