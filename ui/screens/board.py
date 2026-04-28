from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QGridLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from data.queries import get_genres
from game.state import GameState
from ui.widgets.scoreboard import Scoreboard

BG = "#0d1b2a"
GOLD = "#c9a84c"
TILE_BG = "#1a3a6b"
TILE_CLEARED_BG = "#131320"
TILE_BORDER = "#2a5a9b"
TILE_CLEARED_BORDER = "#222233"

DIFFICULTIES = [1, 2, 3, 4, 5]
POINTS = [100, 200, 300, 400, 500]


def _tile_style(cleared: bool) -> str:
    bg = TILE_CLEARED_BG if cleared else TILE_BG
    fg = "#444460" if cleared else GOLD
    border = TILE_CLEARED_BORDER if cleared else TILE_BORDER
    hover = "" if cleared else f"QPushButton:hover {{ background-color: #22508b; border-color: {GOLD}; }}"
    return f"""
        QPushButton {{
            background-color: {bg};
            color: {fg};
            border: 2px solid {border};
            border-radius: 4px;
        }}
        {hover}
        QPushButton:pressed {{ background-color: #0f2a5b; }}
    """


class BoardScreen(QWidget):
    tile_selected = pyqtSignal(int, int)  # (genre_id, difficulty)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {BG};")
        self._genres: list[tuple[int, str]] = get_genres()
        self._tiles: dict[tuple[int, int], QPushButton] = {}
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(12)

        self.scoreboard = Scoreboard(genres=self._genres)
        outer.addWidget(self.scoreboard)

        grid = QGridLayout()
        grid.setSpacing(6)
        grid.setContentsMargins(0, 0, 0, 0)

        # Genre header row
        for col, (_, name) in enumerate(self._genres):
            lbl = QLabel(name.upper())
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFont(QFont("Sans", 12, QFont.Weight.Bold))
            lbl.setStyleSheet(f"color: {GOLD}; padding: 6px 2px;")
            lbl.setWordWrap(True)
            grid.addWidget(lbl, 0, col)

        # Tile rows
        for row, (diff, pts) in enumerate(zip(DIFFICULTIES, POINTS), start=1):
            for col, (gid, _) in enumerate(self._genres):
                btn = QPushButton(f"${pts}")
                btn.setFont(QFont("Sans", 22, QFont.Weight.Bold))
                btn.setMinimumSize(110, 80)
                btn.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Expanding,
                )
                btn.setStyleSheet(_tile_style(cleared=False))
                btn.clicked.connect(
                    lambda _, g=gid, d=diff: self.tile_selected.emit(g, d)
                )
                grid.addWidget(btn, row, col)
                self._tiles[(gid, diff)] = btn

        outer.addLayout(grid)

    def refresh(self, state: GameState) -> None:
        for (gid, diff), btn in self._tiles.items():
            cleared = (gid, diff) in state.board_cleared
            btn.setEnabled(not cleared)
            btn.setStyleSheet(_tile_style(cleared=cleared))
        self.scoreboard.refresh(state)
