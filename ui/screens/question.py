from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from ui.utils.transitions import paint_bg_gradient
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.widgets.timer_widget import TimerWidget

BG = "#0d1b2a"
GOLD = "#c9a84c"
TILE_BG = "#1a3a6b"
TEXT_COLOR = "#e8e8e8"
PAUSED_COLOR = "#8888aa"

MAX_ANSWER_LEN = 200


class QuestionScreen(QWidget):
    answer_submitted = pyqtSignal(str)   # raw answer text
    timed_out = pyqtSignal()
    pause_requested = pyqtSignal(int)    # player_index
    resume_requested = pyqtSignal()
    urgent_tick = pyqtSignal()           # relayed from timer widget, once/s when ≤10s remain

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._active_player_index: int = 0
        self._paused: bool = False
        self._allow_pause: bool = True
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(60, 40, 60, 40)
        outer.setSpacing(24)

        # Genre + difficulty label (top)
        self._meta_label = QLabel("")
        self._meta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._meta_label.setFont(QFont("Sans", 12))
        self._meta_label.setStyleSheet(f"color: {GOLD}; background: transparent;")
        outer.addWidget(self._meta_label)

        # Question text
        self._question_label = QLabel("")
        self._question_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._question_label.setFont(QFont("Sans", 22, QFont.Weight.Bold))
        self._question_label.setStyleSheet(f"color: {TEXT_COLOR}; background: transparent;")
        self._question_label.setWordWrap(True)
        outer.addWidget(self._question_label, stretch=1)

        # Timer
        self._timer_widget = TimerWidget()
        outer.addWidget(self._timer_widget)

        # Answer input row
        input_row = QHBoxLayout()
        input_row.setSpacing(12)

        self._answer_input = QLineEdit()
        self._answer_input.setPlaceholderText("Type your answer…")
        self._answer_input.setMaxLength(MAX_ANSWER_LEN)
        self._answer_input.setFont(QFont("Sans", 18))
        self._answer_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: #132030;
                color: {TEXT_COLOR};
                border: 2px solid #2a5a9b;
                border-radius: 6px;
                padding: 10px 14px;
            }}
            QLineEdit:focus {{
                border-color: {GOLD};
            }}
        """)
        self._answer_input.returnPressed.connect(self._submit)
        input_row.addWidget(self._answer_input, stretch=1)

        self._submit_btn = QPushButton("Submit")
        self._submit_btn.setFont(QFont("Sans", 14, QFont.Weight.Bold))
        self._submit_btn.setFixedHeight(48)
        self._submit_btn.setFixedWidth(120)
        self._submit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {GOLD};
                color: #0d1b2a;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{ background-color: #dbb85c; }}
            QPushButton:pressed {{ background-color: #b8922a; }}
            QPushButton:disabled {{ background-color: #444; color: #888; }}
        """)
        self._submit_btn.clicked.connect(self._submit)
        input_row.addWidget(self._submit_btn)

        outer.addLayout(input_row)

        # Pause status bar
        self._pause_bar = QHBoxLayout()
        self._pause_label = QLabel("")
        self._pause_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pause_label.setFont(QFont("Sans", 11))
        self._pause_label.setStyleSheet(f"color: {PAUSED_COLOR}; background: transparent;")
        self._pause_bar.addWidget(self._pause_label)
        outer.addLayout(self._pause_bar)

        # Escape = pause/resume
        esc = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        esc.activated.connect(self._toggle_pause)

        self._timer_widget.expired.connect(self._on_expired)
        self._timer_widget.urgent_tick.connect(self.urgent_tick)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def load_question(
        self,
        genre_name: str,
        difficulty: int,
        points: int,
        question_text: str,
        active_player_index: int,
        active_player_name: str,
        pause_uses_remaining: int,
        allow_pause: bool = True,
    ) -> None:
        self._active_player_index = active_player_index
        self._paused = False
        self._allow_pause = allow_pause
        self._pause_uses_remaining = pause_uses_remaining

        self._meta_label.setText(f"{genre_name}  ·  ${points}")
        self._question_label.setText(question_text)

        if allow_pause and pause_uses_remaining > 0:
            self._pause_label.setText(
                f"{active_player_name}'s turn  ·  Esc to pause  ·  {pause_uses_remaining} pause(s) left"
            )
        elif allow_pause:
            self._pause_label.setText(f"{active_player_name}'s turn  ·  No pauses remaining")
        else:
            self._pause_label.setText(f"{active_player_name}'s turn  ·  ⚡ Sudden Death")

        self._answer_input.clear()
        self._answer_input.setEnabled(True)
        self._submit_btn.setEnabled(True)
        self._answer_input.setFocus()

        self._timer_widget.start()

    def on_pause_granted(self) -> None:
        self._paused = True
        self._timer_widget.pause()
        self._answer_input.setEnabled(False)
        self._submit_btn.setEnabled(False)
        self._pause_label.setText("⏸  Paused — press Esc to resume")

    def on_pause_denied(self) -> None:
        self._pause_label.setText("No pauses remaining.")

    def on_resume(self) -> None:
        self._paused = False
        self._timer_widget.resume()
        self._answer_input.setEnabled(True)
        self._submit_btn.setEnabled(True)
        self._pause_label.setText(
            f"Esc to pause  ·  {self._pause_uses_remaining - 1} pause(s) left"
        )
        self._answer_input.setFocus()

    def stop_timer(self) -> None:
        self._timer_widget.stop()

    # ------------------------------------------------------------------ #
    # Internals                                                            #
    # ------------------------------------------------------------------ #

    def _submit(self) -> None:
        if self._paused:
            return
        text = self._answer_input.text().strip()
        self._timer_widget.stop()
        self._answer_input.setEnabled(False)
        self._submit_btn.setEnabled(False)
        self.answer_submitted.emit(text)

    def _on_expired(self) -> None:
        self._answer_input.setEnabled(False)
        self._submit_btn.setEnabled(False)
        self.timed_out.emit()

    def paintEvent(self, event) -> None:
        paint_bg_gradient(self, event)

    def _toggle_pause(self) -> None:
        if not self._allow_pause:
            return
        if self._paused:
            self.resume_requested.emit()
        else:
            self.pause_requested.emit(self._active_player_index)
