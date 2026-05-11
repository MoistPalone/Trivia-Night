from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from ui.utils.transitions import paint_bg_gradient
from PyQt6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from game.state import GameState

BG = "#0d1b2a"
GOLD = "#c9a84c"
TEXT_COLOR = "#e8e8e8"
DIM = "#7788aa"
PANEL_BG = "#0f2236"


class GameOverScreen(QWidget):
    play_again = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(80, 60, 80, 60)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        trophy = QLabel("🏆")
        trophy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        trophy.setFont(QFont("Sans", 72))
        trophy.setStyleSheet("background: transparent;")
        layout.addWidget(trophy)

        self._winner_label = QLabel("")
        self._winner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._winner_label.setFont(QFont("Sans", 36, QFont.Weight.Bold))
        self._winner_label.setStyleSheet(f"color: {GOLD}; background: transparent;")
        layout.addWidget(self._winner_label)

        self._winner_score = QLabel("")
        self._winner_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._winner_score.setFont(QFont("Sans", 24))
        self._winner_score.setStyleSheet(f"color: {TEXT_COLOR}; background: transparent;")
        layout.addWidget(self._winner_score)

        # Standings container — populated dynamically in show_winner
        self._standings_widget = QWidget()
        self._standings_layout = QVBoxLayout(self._standings_widget)
        self._standings_layout.setSpacing(8)
        self._standings_layout.setContentsMargins(0, 8, 0, 8)
        layout.addWidget(self._standings_widget)

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

    def paintEvent(self, event) -> None:
        paint_bg_gradient(self, event)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def show_winner(self, state: GameState) -> None:
        winner = state.players[state.winner_index]
        self._winner_label.setText(f"{winner.name} Wins!")
        self._winner_score.setText(f"{winner.score:,} points")

        # Rebuild standings
        while self._standings_layout.count():
            item = self._standings_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        ranked = sorted(enumerate(state.players), key=lambda t: t[1].score, reverse=True)
        for rank, (idx, player) in enumerate(ranked, start=1):
            row = self._standings_row(rank, player.name, player.score, idx == state.winner_index)
            fx = QGraphicsOpacityEffect(row)
            fx.setOpacity(0.0)
            row.setGraphicsEffect(fx)
            self._standings_layout.addWidget(row)
            QTimer.singleShot(80 * rank, lambda r=row: self._reveal_row(r))

    def _reveal_row(self, row: QWidget) -> None:
        fx = row.graphicsEffect()
        if fx is None:
            return
        anim = QPropertyAnimation(fx, b"opacity", row)
        anim.setDuration(350)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        anim.finished.connect(lambda: row.setGraphicsEffect(None))
        anim.start()

    def _standings_row(self, rank: int, name: str, score: int, is_winner: bool) -> QWidget:
        w = QWidget()
        w.setStyleSheet(
            f"background-color: {PANEL_BG if is_winner else 'transparent'};"
            f"border: {'1px solid ' + GOLD if is_winner else 'none'};"
            f"border-radius: 6px;"
        )
        row = QHBoxLayout(w)
        row.setContentsMargins(20, 6, 20, 6)
        row.setSpacing(16)

        rank_lbl = QLabel(f"#{rank}")
        rank_lbl.setFont(QFont("Sans", 14, QFont.Weight.Bold))
        rank_lbl.setStyleSheet(f"color: {GOLD if is_winner else DIM}; border: none;")
        row.addWidget(rank_lbl)

        name_lbl = QLabel(name)
        name_lbl.setFont(QFont("Sans", 14, QFont.Weight.Bold if is_winner else QFont.Weight.Normal))
        name_lbl.setStyleSheet(f"color: {GOLD if is_winner else TEXT_COLOR}; border: none;")
        row.addWidget(name_lbl)

        row.addStretch()

        score_lbl = QLabel(f"{score:,} pts")
        score_lbl.setFont(QFont("Sans", 14))
        score_lbl.setStyleSheet(f"color: {TEXT_COLOR}; border: none;")
        row.addWidget(score_lbl)

        if is_winner:
            crown = QLabel("👑")
            crown.setFont(QFont("Sans", 16))
            crown.setStyleSheet("border: none;")
            row.addWidget(crown)

        return w
