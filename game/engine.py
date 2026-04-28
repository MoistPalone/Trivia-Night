from __future__ import annotations

from game.player import Player
from game.scorer import calculate_points
from game.state import GamePhase, GameState, QuestionContext, ResultContext

NUM_GENRES = 6  # number of genres a player must clear to end a round


class Engine:
    def __init__(self) -> None:
        self.state = GameState()

    # ------------------------------------------------------------------ #
    # Setup                                                                #
    # ------------------------------------------------------------------ #

    def start_game(self, p1_name: str, p2_name: str) -> None:
        assert self.state.phase == GamePhase.WELCOME
        self.state.players = [Player(name=p1_name), Player(name=p2_name)]
        self.state.round_number = 1
        self.state.active_player_index = 0
        self.state.board_cleared = set()
        self.state.current_question = None
        self.state.last_result = None
        self.state.winner_index = None
        self.state.phase = GamePhase.BOARD

    # ------------------------------------------------------------------ #
    # Board → Question                                                     #
    # ------------------------------------------------------------------ #

    def select_question(
        self,
        genre_id: int,
        difficulty: int,
        question_id: int,
        base_points: int,
    ) -> None:
        assert self.state.phase == GamePhase.BOARD
        assert (genre_id, difficulty) not in self.state.board_cleared, "Tile already cleared"
        self.state.current_question = QuestionContext(
            question_id=question_id,
            genre_id=genre_id,
            difficulty=difficulty,
            base_points=base_points,
        )
        self.state.phase = GamePhase.QUESTION

    # ------------------------------------------------------------------ #
    # Pause / Resume                                                       #
    # ------------------------------------------------------------------ #

    def pause(self, player_index: int) -> bool:
        """Attempt to pause on behalf of player_index. Returns False if limit reached."""
        assert self.state.phase == GamePhase.QUESTION
        player = self.state.players[player_index]
        if not player.can_pause:
            return False
        player.pause_count += 1
        self.state.phase = GamePhase.PAUSED
        return True

    def resume(self) -> None:
        assert self.state.phase == GamePhase.PAUSED
        self.state.phase = GamePhase.QUESTION

    # ------------------------------------------------------------------ #
    # Answer evaluation                                                    #
    # ------------------------------------------------------------------ #

    def evaluate_answer(self, correct: bool) -> None:
        """Called by the UI after running the fuzzy evaluator."""
        assert self.state.phase == GamePhase.QUESTION
        q = self.state.current_question
        answering_idx = self.state.active_player_index
        points_awarded = 0

        if correct:
            points_awarded = calculate_points(q.base_points, self.state.round_number)
            player = self.state.players[answering_idx]
            player.score += points_awarded
            player.genres_cleared.add(q.genre_id)
            self.state.board_cleared.add((q.genre_id, q.difficulty))
        else:
            # Wrong answer: hand control to the other player
            self.state.active_player_index = 1 - self.state.active_player_index

        self.state.last_result = ResultContext(
            correct=correct,
            points_awarded=points_awarded,
            player_index=answering_idx,
        )
        self.state.current_question = None
        self.state.phase = GamePhase.RESULT

    def timeout(self) -> None:
        """Timer expired — treated as a wrong answer."""
        assert self.state.phase == GamePhase.QUESTION
        self.evaluate_answer(correct=False)

    # ------------------------------------------------------------------ #
    # Advancing through result / summary screens                           #
    # ------------------------------------------------------------------ #

    def advance_from_result(self) -> None:
        """Called after the 2-second result overlay completes."""
        assert self.state.phase == GamePhase.RESULT
        if self._round_is_complete():
            self._handle_round_end()
        else:
            self.state.phase = GamePhase.BOARD

    def advance_from_round_summary(self) -> None:
        assert self.state.phase == GamePhase.ROUND_SUMMARY
        self.state.round_number += 1
        for player in self.state.players:
            player.reset_for_round()
        self.state.board_cleared = set()
        self.state.phase = GamePhase.BOARD

    # ------------------------------------------------------------------ #
    # Sudden Death                                                         #
    # ------------------------------------------------------------------ #

    def evaluate_sudden_death(self, player_index: int, correct: bool) -> None:
        """
        Called when a player submits an answer during Sudden Death.
        Correct → that player wins. Wrong → stay in SUDDEN_DEATH for next question.
        """
        assert self.state.phase == GamePhase.SUDDEN_DEATH
        if correct:
            self.state.winner_index = player_index
            self.state.phase = GamePhase.GAME_OVER

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _round_is_complete(self) -> bool:
        return any(
            len(p.genres_cleared) >= NUM_GENRES for p in self.state.players
        )

    def _handle_round_end(self) -> None:
        if self.state.round_number < 3:
            self.state.phase = GamePhase.ROUND_SUMMARY
            return

        scores = [p.score for p in self.state.players]
        if scores[0] == scores[1]:
            self.state.phase = GamePhase.SUDDEN_DEATH
        else:
            self.state.winner_index = scores.index(max(scores))
            self.state.phase = GamePhase.GAME_OVER
