import math

from PyQt6.QtCore import QEasingCurve, Qt, QTimer, QVariantAnimation
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from game.state import GameState

GOLD = "#c9a84c"
BG = "#0d1b2a"
TEXT = "#ffffff"
DOT_ON = GOLD
DOT_OFF = "#2a3a5a"
BORDER_INACTIVE = "3px solid #2a3a5a"

# Pulse color range: dim gold (#c9a84c) → bright gold (#ffd97a)
_PULSE_R = (0xc9, 0xff)
_PULSE_G = (0xa8, 0xd9)
_PULSE_B = (0x4c, 0x7a)


class _PlayerPanel(QWidget):
    def __init__(
        self, player_number: int, genres: list[tuple[int, str]], parent=None
    ) -> None:
        super().__init__(parent)
        self._genre_ids = [gid for gid, _ in genres]
        self._genre_dots: list[QLabel] = []
        self._pulse_t = 0.0
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(40)
        self._pulse_timer.timeout.connect(self._tick_pulse)
        self._displayed_score: int = 0
        self._score_anim: QVariantAnimation | None = None
        self._build(player_number)

    def _build(self, player_number: int) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        top = QHBoxLayout()
        self.name_lbl = QLabel(f"Player {player_number}")
        self.name_lbl.setFont(QFont("Sans", 15, QFont.Weight.Bold))
        self.name_lbl.setStyleSheet(f"color: {TEXT}; border: none; background: transparent;")

        self.score_lbl = QLabel("0")
        self.score_lbl.setFont(QFont("Sans", 22, QFont.Weight.Bold))
        self.score_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.score_lbl.setStyleSheet(f"color: {GOLD}; border: none; background: transparent;")

        top.addWidget(self.name_lbl)
        top.addStretch()
        top.addWidget(self.score_lbl)
        layout.addLayout(top)

        dots_row = QHBoxLayout()
        dots_row.setSpacing(8)
        for _ in self._genre_ids:
            dot = QLabel("●")
            dot.setFont(QFont("Sans", 12))
            dot.setStyleSheet(f"color: {DOT_OFF}; border: none; background: transparent;")
            self._genre_dots.append(dot)
            dots_row.addWidget(dot)
        dots_row.addStretch()
        layout.addLayout(dots_row)

    def _tick_pulse(self) -> None:
        self._pulse_t += 0.12
        v = 0.5 + 0.5 * math.sin(self._pulse_t)
        r = int(_PULSE_R[0] + (_PULSE_R[1] - _PULSE_R[0]) * v)
        g = int(_PULSE_G[0] + (_PULSE_G[1] - _PULSE_G[0]) * v)
        b = int(_PULSE_B[0] + (_PULSE_B[1] - _PULSE_B[0]) * v)
        color = f"#{r:02x}{g:02x}{b:02x}"
        self.setStyleSheet(
            f"background-color: {BG}; border: 3px solid {color}; border-radius: 6px;"
        )

    def _update_score(self, score: int) -> None:
        if score == self._displayed_score:
            return
        if self._score_anim is not None:
            self._score_anim.stop()
        if score > self._displayed_score:
            anim = QVariantAnimation(self)
            anim.setStartValue(float(self._displayed_score))
            anim.setEndValue(float(score))
            anim.setDuration(600)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.valueChanged.connect(lambda v: self.score_lbl.setText(str(int(v))))
            anim.finished.connect(lambda: self.score_lbl.setText(str(score)))
            anim.start()
            self._score_anim = anim
        else:
            self.score_lbl.setText(str(score))
        self._displayed_score = score

    def refresh(self, name: str, score: int, genres_cleared: set, active: bool) -> None:
        self.name_lbl.setText(name)
        self._update_score(score)
        for gid, dot in zip(self._genre_ids, self._genre_dots):
            dot.setStyleSheet(
                f"color: {DOT_ON if gid in genres_cleared else DOT_OFF}; border: none; background: transparent;"
            )
        if active:
            if not self._pulse_timer.isActive():
                self._pulse_t = 0.0
                self._pulse_timer.start()
        else:
            self._pulse_timer.stop()
            self.setStyleSheet(
                f"background-color: {BG}; border: {BORDER_INACTIVE}; border-radius: 6px;"
            )


class Scoreboard(QWidget):
    def __init__(self, genres: list[tuple[int, str]], parent=None) -> None:
        super().__init__(parent)
        self._genres = genres
        self._panels: list[_PlayerPanel] = []
        self._num_players = 0

        self._layout = QHBoxLayout(self)
        self._layout.setSpacing(16)

        self.round_lbl = QLabel("Round 1")
        self.round_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.round_lbl.setFont(QFont("Sans", 14, QFont.Weight.Bold))
        self.round_lbl.setStyleSheet(f"color: {GOLD}; background: transparent;")

    def _rebuild_panels(self, num_players: int) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        self._panels = [_PlayerPanel(i + 1, self._genres) for i in range(num_players)]
        self._num_players = num_players

        for panel in self._panels:
            self._layout.addWidget(panel)
        self._layout.addWidget(self.round_lbl)

    def refresh(self, state: GameState) -> None:
        if len(state.players) != self._num_players:
            self._rebuild_panels(len(state.players))

        for i, (panel, player) in enumerate(zip(self._panels, state.players)):
            panel.refresh(
                name=player.name,
                score=player.score,
                genres_cleared=player.genres_cleared,
                active=(i == state.active_player_index),
            )
        label = f"Round {state.round_number}"
        if state.round_number == 3:
            label += "  ★ 2×"
        self.round_lbl.setText(label)
