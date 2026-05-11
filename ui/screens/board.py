from PyQt6.QtCore import (
    QEasingCurve, QPoint, QPropertyAnimation, Qt, QTimer, QVariantAnimation, pyqtSignal,
)
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
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
TILE_CLEARED_BG = "#131320"
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


# ─────────────────────────────────────────────────────────────────────────── #
# Animated tile button                                                         #
# ─────────────────────────────────────────────────────────────────────────── #

class TileButton(QPushButton):
    """QPushButton with smooth hover glow and fade-in-as-cleared animation."""

    def __init__(self, text: str, accent: str, parent=None) -> None:
        super().__init__(text, parent)
        self._accent_rgb = (int(accent[1:3], 16), int(accent[3:5], 16), int(accent[5:7], 16))
        self._glow = 0.0
        self._clear_anim: QPropertyAnimation | None = None

        self._hover_anim = QVariantAnimation(self)
        self._hover_anim.setDuration(200)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._hover_anim.valueChanged.connect(self._on_hover)
        self._apply_normal()

    def enterEvent(self, event) -> None:
        if self.isEnabled():
            self._hover_anim.stop()
            self._hover_anim.setStartValue(self._glow)
            self._hover_anim.setEndValue(1.0)
            self._hover_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        if self.isEnabled():
            self._hover_anim.stop()
            self._hover_anim.setStartValue(self._glow)
            self._hover_anim.setEndValue(0.0)
            self._hover_anim.start()
        super().leaveEvent(event)

    def _on_hover(self, value) -> None:
        self._glow = float(value)
        self._apply_normal()

    def _apply_normal(self) -> None:
        v = self._glow
        ar, ag, ab = self._accent_rgb

        # Background: #0e2040 (dark rest) → #1e5090 (bright hover)
        bg = f"#{int(0x0e + 0x10*v):02x}{int(0x20 + 0x30*v):02x}{int(0x40 + 0x50*v):02x}"

        # Side border: dim blue at rest → full accent on hover
        dim_factor = 0.35 + 0.65 * v
        border = (f"#{min(255,int(ar*dim_factor)):02x}"
                  f"{min(255,int(ag*dim_factor)):02x}"
                  f"{min(255,int(ab*dim_factor)):02x}")

        # Top accent: genre color at 50% dim at rest, 110% (clamped) on hover
        top_dim = 0.50 + 0.60 * v
        top = f"#{min(255,int(ar*top_dim)):02x}{min(255,int(ag*top_dim)):02x}{min(255,int(ab*top_dim)):02x}"

        # Price text brightens on hover too
        gold_v = int(0xc9 + (0xff - 0xc9) * v)
        gold_g = int(0xa8 + (0xd9 - 0xa8) * v)
        text_color = f"#{gold_v:02x}{gold_g:02x}{int(0x4c + 0x2e*v):02x}"

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {text_color};
                border: 2px solid {border};
                border-top: 4px solid {top};
                border-radius: 4px;
            }}
            QPushButton:pressed {{ background-color: #0a1830; }}
        """)

    def _apply_cleared(self) -> None:
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {TILE_CLEARED_BG};
                color: #444460;
                border: 2px solid {TILE_CLEARED_BORDER};
                border-top: 3px solid {TILE_CLEARED_BORDER};
                border-radius: 4px;
            }}
        """)

    def set_cleared(self, cleared: bool) -> None:
        """Immediately apply cleared/uncleaned state with no animation."""
        self.setGraphicsEffect(None)
        self.setEnabled(not cleared)
        if cleared:
            self._hover_anim.stop()
            self._glow = 0.0
            self._apply_cleared()
        else:
            self._apply_normal()

    def set_cleared_animated(self) -> None:
        """Disable tile now; fade it in as cleared once the board has appeared."""
        self.setEnabled(False)
        self._hover_anim.stop()
        self._glow = 0.0
        self._apply_cleared()
        self.setGraphicsEffect(None)
        fx = QGraphicsOpacityEffect(self)
        fx.setOpacity(0.0)
        self.setGraphicsEffect(fx)
        # 280ms lets the board fade-in finish before the tile materialises
        QTimer.singleShot(280, lambda: self._fade_in_cleared(fx))

    def _fade_in_cleared(self, fx: QGraphicsOpacityEffect) -> None:
        if self.graphicsEffect() is not fx:
            return  # stale — effect was replaced (e.g., board reset)
        anim = QPropertyAnimation(fx, b"opacity", self)
        anim.setDuration(600)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.finished.connect(lambda: self.setGraphicsEffect(None))
        anim.start()
        self._clear_anim = anim


# ─────────────────────────────────────────────────────────────────────────── #
# Round announcement overlay                                                   #
# ─────────────────────────────────────────────────────────────────────────── #

class RoundAnnouncementOverlay(QWidget):
    """Full-screen overlay that slides in, holds, then slides out for new rounds."""

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
        self._sub_lbl.setStyleSheet("color: #e8e8e8;")
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


# ─────────────────────────────────────────────────────────────────────────── #
# Board screen                                                                  #
# ─────────────────────────────────────────────────────────────────────────── #

class BoardScreen(QWidget):
    tile_selected = pyqtSignal(int, int)  # (genre_id, difficulty)
    mute_toggled = pyqtSignal(bool)       # emits new muted state

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {BG};")
        self._genres: list[tuple[int, str]] = get_genres()
        self._tiles: dict[tuple[int, int], TileButton] = {}
        self._muted: bool = False
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(12)

        # Top bar: scoreboard + mute toggle at far right
        top_bar = QHBoxLayout()
        self.scoreboard = Scoreboard(genres=self._genres)
        top_bar.addWidget(self.scoreboard, stretch=1)

        self._mute_btn = QPushButton("🔊")
        self._mute_btn.setFixedSize(34, 34)
        self._mute_btn.setFont(QFont("Sans", 14))
        self._mute_btn.setToolTip("Toggle mute")
        self._mute_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {GOLD};
                border: 1px solid #2a3a5a;
                border-radius: 4px;
            }}
            QPushButton:hover {{ border-color: {GOLD}; }}
            QPushButton:pressed {{ background-color: #1a2a3a; }}
        """)
        self._mute_btn.clicked.connect(self._toggle_mute)
        top_bar.addWidget(self._mute_btn, alignment=Qt.AlignmentFlag.AlignTop)
        outer.addLayout(top_bar)

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
                accent = GENRE_COLORS.get(gid, GOLD)
                btn = TileButton(f"${pts}", accent)
                btn.setFont(QFont("Sans", 22, QFont.Weight.Bold))
                btn.setMinimumSize(110, 80)
                btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                btn.clicked.connect(lambda _, g=gid, d=diff: self.tile_selected.emit(g, d))
                grid.addWidget(btn, row, col)
                self._tiles[(gid, diff)] = btn

        outer.addLayout(grid)

    def refresh(self, state: GameState) -> None:
        for (gid, diff), btn in self._tiles.items():
            is_cleared = (gid, diff) in state.board_cleared
            if is_cleared and btn.isEnabled():
                btn.set_cleared_animated()   # newly cleared — fade in as grey
            else:
                btn.set_cleared(is_cleared)  # immediate (already cleared or not cleared)
        self.scoreboard.refresh(state)

    def _toggle_mute(self) -> None:
        self._muted = not self._muted
        self._mute_btn.setText("🔇" if self._muted else "🔊")
        self.mute_toggled.emit(self._muted)

    def announce_round(self, round_number: int) -> None:
        """Show round announcement overlay for rounds 2 and 3."""
        if round_number > 1:
            self._overlay.announce(round_number)
