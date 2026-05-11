from PyQt6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt, QTimer, pyqtSignal
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

# One accent color per genre (keyed by genre_id 1–6)
GENRE_COLORS: dict[int, str] = {
    1: "#5b9bd5",  # History — steel blue
    2: "#4abf7f",  # Science — teal
    3: "#d5865b",  # Geography — terracotta
    4: "#bf9a4a",  # Arts — amber
    5: "#9b5bd5",  # People — violet
    6: "#5bd5c8",  # Music — cyan
}

DIFFICULTIES = [1, 2, 3, 4, 5]
POINTS = [100, 200, 300, 400, 500]

OVERLAY_BG = "#080f1a"


class RoundAnnouncementOverlay(QWidget):
    """Full-screen overlay that slides in, holds, then slides out announcing the new round."""

    finished = pyqtSignal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {OVERLAY_BG};")
        self.hide()
        self._anim: QPropertyAnimation | None = None
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        self._round_lbl = QLabel("")
        self._round_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._round_lbl.setFont(QFont("Sans", 60, QFont.Weight.Bold))
        self._round_lbl.setStyleSheet(f"color: {GOLD};")
        layout.addWidget(self._round_lbl)

        self._sub_lbl = QLabel("")
        self._sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sub_lbl.setFont(QFont("Sans", 22, QFont.Weight.Bold))
        self._sub_lbl.setStyleSheet(f"color: #e8e8e8;")
        layout.addWidget(self._sub_lbl)

    def announce(self, round_number: int) -> None:
        self._round_lbl.setText(f"ROUND {round_number}")
        if round_number == 3:
            self._sub_lbl.setText("★  Double Points  ★")
            self._sub_lbl.show()
        else:
            self._sub_lbl.hide()

        p = self.parent()
        self.setGeometry(0, 0, p.width(), p.height())
        self.show()
        self.raise_()
        self._slide(QPoint(0, -self.height()), QPoint(0, 0), 320,
                    QEasingCurve.Type.OutCubic, self._hold)

    def _hold(self) -> None:
        QTimer.singleShot(1600, self._slide_out)

    def _slide_out(self) -> None:
        self._slide(QPoint(0, 0), QPoint(0, -self.height()), 280,
                    QEasingCurve.Type.InCubic, self._done)

    def _done(self) -> None:
        self.hide()
        self.finished.emit()

    def _slide(self, start: QPoint, end: QPoint, ms: int,
               curve: QEasingCurve.Type, on_finish) -> None:
        if self._anim:
            self._anim.stop()
            self._anim = None
        anim = QPropertyAnimation(self, b"pos", self)
        anim.setDuration(ms)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setEasingCurve(curve)
        anim.finished.connect(on_finish)
        anim.start()
        self._anim = anim


def _tile_style(cleared: bool, accent: str = GOLD) -> str:
    bg = TILE_CLEARED_BG if cleared else TILE_BG
    fg = "#444460" if cleared else GOLD
    border = TILE_CLEARED_BORDER if cleared else TILE_BORDER
    top_accent = TILE_CLEARED_BORDER if cleared else accent
    hover = "" if cleared else f"QPushButton:hover {{ background-color: #22508b; border-color: {accent}; }}"
    return f"""
        QPushButton {{
            background-color: {bg};
            color: {fg};
            border: 2px solid {border};
            border-top: 3px solid {top_accent};
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

        self._overlay = RoundAnnouncementOverlay(self)

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
                btn.setStyleSheet(_tile_style(cleared=False, accent=GENRE_COLORS.get(gid, GOLD)))
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
            btn.setStyleSheet(_tile_style(cleared=cleared, accent=GENRE_COLORS.get(gid, GOLD)))
        self.scoreboard.refresh(state)

    def announce_round(self, round_number: int) -> None:
        """Show round announcement overlay for rounds 2 and 3."""
        if round_number > 1:
            self._overlay.announce(round_number)
