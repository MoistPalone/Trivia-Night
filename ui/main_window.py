import random

from PyQt6.QtWidgets import QMainWindow, QStackedWidget

from answering.evaluator import evaluate
from audio.sound import SoundManager
from data.queries import get_genres, pick_question, record_played, recently_played_ids
from game.engine import Engine
from game.state import GamePhase
from ui.screens.board import BoardScreen
from ui.screens.game_over import GameOverScreen
from ui.screens.question import QuestionScreen
from ui.screens.result import ResultScreen
from ui.screens.round_summary import RoundSummaryScreen
from ui.screens.sudden_death import SuddenDeathScreen
from ui.screens.welcome import WelcomeScreen
from ui.utils.transitions import fade_to

BG = "#0d1b2a"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.engine = Engine()
        self._genres: dict[int, str] = {gid: name for gid, name in get_genres()}
        self._sound = SoundManager()

        self._current_answer: str = ""
        self._current_keywords: list[str] = []

        self.setWindowTitle("Trivia Night")
        self.setMinimumSize(1100, 780)
        self.setStyleSheet(f"background-color: {BG};")

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.welcome = WelcomeScreen()
        self.board = BoardScreen()
        self.question = QuestionScreen()
        self.result = ResultScreen()
        self.round_summary = RoundSummaryScreen()
        self.sudden_death = SuddenDeathScreen()
        self.game_over = GameOverScreen()

        for screen in (
            self.welcome,
            self.board,
            self.question,
            self.result,
            self.round_summary,
            self.sudden_death,
            self.game_over,
        ):
            self.stack.addWidget(screen)

        self.welcome.game_started.connect(self._on_game_started)
        self.board.tile_selected.connect(self._on_tile_selected)
        self.question.answer_submitted.connect(self._on_answer_submitted)
        self.question.timed_out.connect(self._on_timed_out)
        self.question.pause_requested.connect(self._on_pause_requested)
        self.question.resume_requested.connect(self._on_resume_requested)
        self.question.urgent_tick.connect(lambda: self._sound.play("tick_urgent"))
        self.result.finished.connect(self._on_result_finished)
        self.round_summary.finished.connect(self._on_round_summary_finished)
        self.sudden_death.finished.connect(self._on_sudden_death_begin)
        self.game_over.play_again.connect(self._on_play_again)

    # ------------------------------------------------------------------ #
    # Game start                                                           #
    # ------------------------------------------------------------------ #

    def _on_game_started(self, names: list) -> None:
        self.engine.start_game(names)
        self.board.refresh(self.engine.state)
        fade_to(self.stack, self.board)

    # ------------------------------------------------------------------ #
    # Board → Question                                                     #
    # ------------------------------------------------------------------ #

    def _on_tile_selected(self, genre_id: int, difficulty: int) -> None:
        exclude = recently_played_ids(genre_id, difficulty)
        row = pick_question(genre_id, difficulty, exclude_ids=exclude)
        if row is None:
            row = pick_question(genre_id, difficulty)
        if row is None:
            return

        self._sound.play("tile_select")
        self.engine.select_question(
            genre_id=genre_id,
            difficulty=difficulty,
            question_id=row["id"],
            base_points=row["points"],
        )
        record_played(row["id"])
        self._load_current_question(row, genre_id, difficulty)

    def _load_current_question(self, row: dict, genre_id: int, difficulty: int, allow_pause: bool = True) -> None:
        self._current_answer = row["answer"]
        self._current_keywords = row["keywords"]
        state = self.engine.state
        player = state.players[state.active_player_index]
        pause_left = 2 - player.pause_count if allow_pause else 0
        self.question.load_question(
            genre_name=self._genres.get(genre_id, ""),
            difficulty=difficulty,
            points=row["points"],
            question_text=row["question"],
            active_player_index=state.active_player_index,
            active_player_name=player.name,
            pause_uses_remaining=pause_left,
            allow_pause=allow_pause,
        )
        fade_to(self.stack, self.question)

    # ------------------------------------------------------------------ #
    # Answer + timeout                                                     #
    # ------------------------------------------------------------------ #

    def _on_answer_submitted(self, given: str) -> None:
        if self.engine.state.phase == GamePhase.SUDDEN_DEATH:
            self._handle_sudden_death_answer(given)
            return
        correct = evaluate(self._current_answer, given, self._current_keywords)
        self.engine.evaluate_answer(correct)
        self._sound.play("correct" if correct else "wrong")
        self._show_result()

    def _on_timed_out(self) -> None:
        if self.engine.state.phase == GamePhase.SUDDEN_DEATH:
            self._handle_sudden_death_answer("")
            return
        self._sound.play("timeout")
        self.engine.timeout()
        self._show_result()

    def _show_result(self) -> None:
        state = self.engine.state
        r = state.last_result
        answering_player = state.players[r.player_index]
        self.result.show_result(
            correct=r.correct,
            points_awarded=r.points_awarded,
            player_name=answering_player.name,
            correct_answer=self._current_answer,
        )
        fade_to(self.stack, self.result)

    # ------------------------------------------------------------------ #
    # Pause / Resume                                                       #
    # ------------------------------------------------------------------ #

    def _on_pause_requested(self, player_index: int) -> None:
        granted = self.engine.pause(player_index)
        if granted:
            self.question.on_pause_granted()
        else:
            self.question.on_pause_denied()

    def _on_resume_requested(self) -> None:
        self.engine.resume()
        self.question.on_resume()

    # ------------------------------------------------------------------ #
    # Result → next phase                                                  #
    # ------------------------------------------------------------------ #

    def _on_result_finished(self) -> None:
        self.question.stop_timer()
        state = self.engine.state

        if state.phase == GamePhase.SUDDEN_DEATH:
            self._start_sudden_death_question()
            return

        if state.phase == GamePhase.GAME_OVER:
            self._show_game_over(state)
            return

        last_was_correct = state.last_result.correct
        self.engine.advance_from_result()
        state = self.engine.state

        if state.phase == GamePhase.BOARD:
            if not last_was_correct:
                self._sound.play("turn_change")
            self.board.refresh(state)
            fade_to(self.stack, self.board)
        elif state.phase == GamePhase.ROUND_SUMMARY:
            self._sound.play("round_complete")
            self.round_summary.show_summary(state)
            fade_to(self.stack, self.round_summary)
        elif state.phase == GamePhase.SUDDEN_DEATH:
            self._sound.play("sudden_death")
            tied_names = [state.players[i].name for i in state.sudden_death_order]
            tied_score = state.players[state.sudden_death_order[0]].score
            self.sudden_death.show_sudden_death(tied_names, tied_score)
            fade_to(self.stack, self.sudden_death)
        elif state.phase == GamePhase.GAME_OVER:
            self._show_game_over(state)

    def _show_game_over(self, state) -> None:
        self._sound.play("game_over")
        self.game_over.show_winner(state)
        fade_to(self.stack, self.game_over)

    # ------------------------------------------------------------------ #
    # Round summary                                                        #
    # ------------------------------------------------------------------ #

    def _on_round_summary_finished(self) -> None:
        self.engine.advance_from_round_summary()
        state = self.engine.state
        self.board.refresh(state)
        fade_to(self.stack, self.board)
        self.board.announce_round(state.round_number)

    # ------------------------------------------------------------------ #
    # Sudden death                                                         #
    # ------------------------------------------------------------------ #

    def _on_sudden_death_begin(self) -> None:
        self._start_sudden_death_question()

    def _start_sudden_death_question(self) -> None:
        state = self.engine.state
        # Point active_player_index at the current SD turn's player
        sd_player_idx = state.sudden_death_order[state.sudden_death_turn_index]
        state.active_player_index = sd_player_idx

        genre_ids = list(self._genres.keys())
        random.shuffle(genre_ids)
        row = None
        chosen_gid = genre_ids[0]
        diff = 1
        for gid in genre_ids:
            diff = random.randint(1, 5)
            exclude = recently_played_ids(gid, diff)
            row = pick_question(gid, diff, exclude_ids=exclude) or pick_question(gid, diff)
            if row:
                chosen_gid = gid
                break
        if row is None:
            return

        record_played(row["id"])
        self._load_current_question(row, chosen_gid, diff, allow_pause=False)

    def _handle_sudden_death_answer(self, given: str) -> None:
        correct = evaluate(self._current_answer, given, self._current_keywords)
        state = self.engine.state
        answering_idx = state.active_player_index
        self.engine.evaluate_sudden_death(answering_idx, correct)
        # Engine advances sudden_death_turn_index on wrong; no manual index toggle needed
        self._sound.play("correct" if correct else "wrong")
        player = state.players[answering_idx]
        self.result.show_result(
            correct=correct,
            points_awarded=0,
            player_name=player.name,
            correct_answer=self._current_answer,
        )
        fade_to(self.stack, self.result)

    # ------------------------------------------------------------------ #
    # Game over                                                            #
    # ------------------------------------------------------------------ #

    def _on_play_again(self) -> None:
        self.engine = Engine()
        fade_to(self.stack, self.welcome)
