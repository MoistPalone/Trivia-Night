from PyQt6.QtWidgets import QMainWindow, QStackedWidget

from game.engine import Engine
from ui.screens.board import BoardScreen
from ui.screens.welcome import WelcomeScreen

BG = "#0d1b2a"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.engine = Engine()

        self.setWindowTitle("Trivia Night")
        self.setMinimumSize(1100, 780)
        self.setStyleSheet(f"background-color: {BG};")

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.welcome = WelcomeScreen()
        self.board = BoardScreen()

        self.stack.addWidget(self.welcome)
        self.stack.addWidget(self.board)

        self.welcome.game_started.connect(self._on_game_started)
        self.board.tile_selected.connect(self._on_tile_selected)

    # ------------------------------------------------------------------ #
    # Transitions                                                          #
    # ------------------------------------------------------------------ #

    def _on_game_started(self, p1: str, p2: str) -> None:
        self.engine.start_game(p1, p2)
        self.board.refresh(self.engine.state)
        self.stack.setCurrentWidget(self.board)

    def _on_tile_selected(self, genre_id: int, difficulty: int) -> None:
        # Session 5: fetch question, call engine.select_question(), show question screen
        pass
