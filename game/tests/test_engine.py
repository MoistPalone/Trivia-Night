import pytest
from game.engine import Engine, NUM_GENRES
from game.state import GamePhase


@pytest.fixture
def engine() -> Engine:
    e = Engine()
    e.start_game("Alice", "Bob")
    return e


def _select(engine: Engine, genre_id: int = 1, difficulty: int = 1) -> None:
    """Shorthand: select a question and move to QUESTION state."""
    engine.select_question(genre_id=genre_id, difficulty=difficulty, question_id=1, base_points=100)


def _clear_genres(engine: Engine, player_index: int, genre_ids: list[int]) -> None:
    """Directly mark genres as cleared for a player (no DB interaction)."""
    for gid in genre_ids:
        engine.state.players[player_index].genres_cleared.add(gid)


# ------------------------------------------------------------------ #
# start_game                                                           #
# ------------------------------------------------------------------ #

class TestStartGame:
    def test_transitions_to_board(self):
        e = Engine()
        e.start_game("Alice", "Bob")
        assert e.state.phase == GamePhase.BOARD

    def test_players_created(self):
        e = Engine()
        e.start_game("Alice", "Bob")
        assert e.state.players[0].name == "Alice"
        assert e.state.players[1].name == "Bob"

    def test_starts_round_one(self):
        e = Engine()
        e.start_game("Alice", "Bob")
        assert e.state.round_number == 1

    def test_player_zero_goes_first(self):
        e = Engine()
        e.start_game("Alice", "Bob")
        assert e.state.active_player_index == 0


# ------------------------------------------------------------------ #
# select_question                                                      #
# ------------------------------------------------------------------ #

class TestSelectQuestion:
    def test_transitions_to_question(self, engine):
        _select(engine)
        assert engine.state.phase == GamePhase.QUESTION

    def test_stores_question_context(self, engine):
        engine.select_question(genre_id=2, difficulty=3, question_id=99, base_points=300)
        q = engine.state.current_question
        assert q.genre_id == 2
        assert q.difficulty == 3
        assert q.question_id == 99
        assert q.base_points == 300

    def test_cannot_select_cleared_tile(self, engine):
        _select(engine)
        engine.evaluate_answer(correct=True)
        engine.advance_from_result()
        with pytest.raises(AssertionError):
            _select(engine, genre_id=1, difficulty=1)


# ------------------------------------------------------------------ #
# pause / resume                                                       #
# ------------------------------------------------------------------ #

class TestPauseResume:
    def test_pause_transitions_to_paused(self, engine):
        _select(engine)
        assert engine.pause(player_index=0) is True
        assert engine.state.phase == GamePhase.PAUSED

    def test_resume_returns_to_question(self, engine):
        _select(engine)
        engine.pause(0)
        engine.resume()
        assert engine.state.phase == GamePhase.QUESTION

    def test_pause_limit_per_player(self, engine):
        for _ in range(2):
            _select(engine)
            engine.pause(0)
            engine.resume()
            engine.evaluate_answer(correct=False)
            engine.advance_from_result()
        _select(engine)
        assert engine.pause(0) is False
        assert engine.state.phase == GamePhase.QUESTION  # unchanged

    def test_each_player_has_independent_pause_budget(self, engine):
        # exhaust player 0's pauses
        for _ in range(2):
            _select(engine)
            engine.pause(0)
            engine.resume()
            engine.evaluate_answer(correct=False)
            engine.advance_from_result()
        _select(engine)
        assert engine.pause(0) is False
        assert engine.pause(1) is True  # player 1 still has pauses


# ------------------------------------------------------------------ #
# evaluate_answer                                                      #
# ------------------------------------------------------------------ #

class TestEvaluateAnswer:
    def test_correct_awards_base_points_in_round_1(self, engine):
        _select(engine)
        engine.evaluate_answer(correct=True)
        assert engine.state.players[0].score == 100

    def test_correct_keeps_active_player(self, engine):
        _select(engine)
        engine.evaluate_answer(correct=True)
        assert engine.state.active_player_index == 0

    def test_wrong_switches_player(self, engine):
        _select(engine)
        engine.evaluate_answer(correct=False)
        assert engine.state.active_player_index == 1

    def test_correct_clears_tile(self, engine):
        _select(engine, genre_id=1, difficulty=1)
        engine.evaluate_answer(correct=True)
        assert (1, 1) in engine.state.board_cleared

    def test_wrong_does_not_clear_tile(self, engine):
        _select(engine, genre_id=1, difficulty=1)
        engine.evaluate_answer(correct=False)
        assert (1, 1) not in engine.state.board_cleared

    def test_correct_records_genre_cleared(self, engine):
        engine.select_question(genre_id=3, difficulty=2, question_id=1, base_points=200)
        engine.evaluate_answer(correct=True)
        assert 3 in engine.state.players[0].genres_cleared

    def test_transitions_to_result(self, engine):
        _select(engine)
        engine.evaluate_answer(correct=True)
        assert engine.state.phase == GamePhase.RESULT

    def test_result_context_records_answering_player(self, engine):
        _select(engine)
        engine.evaluate_answer(correct=False)
        assert engine.state.last_result.player_index == 0  # player 0 answered (wrong)

    def test_wrong_awards_zero_points(self, engine):
        _select(engine)
        engine.evaluate_answer(correct=False)
        assert engine.state.last_result.points_awarded == 0


# ------------------------------------------------------------------ #
# timeout                                                              #
# ------------------------------------------------------------------ #

class TestTimeout:
    def test_timeout_switches_player(self, engine):
        _select(engine)
        engine.timeout()
        assert engine.state.active_player_index == 1

    def test_timeout_transitions_to_result(self, engine):
        _select(engine)
        engine.timeout()
        assert engine.state.phase == GamePhase.RESULT

    def test_timeout_does_not_clear_tile(self, engine):
        _select(engine, genre_id=2, difficulty=3)
        engine.timeout()
        assert (2, 3) not in engine.state.board_cleared


# ------------------------------------------------------------------ #
# round 3 doubling                                                     #
# ------------------------------------------------------------------ #

class TestRound3Scoring:
    def test_round_3_doubles_correct_answer(self, engine):
        engine.state.round_number = 3
        _select(engine)  # base_points=100
        engine.evaluate_answer(correct=True)
        assert engine.state.players[0].score == 200

    def test_round_1_no_multiplier(self, engine):
        engine.state.round_number = 1
        _select(engine)
        engine.evaluate_answer(correct=True)
        assert engine.state.players[0].score == 100

    def test_round_2_no_multiplier(self, engine):
        engine.state.round_number = 2
        _select(engine)
        engine.evaluate_answer(correct=True)
        assert engine.state.players[0].score == 100


# ------------------------------------------------------------------ #
# round end / advance                                                  #
# ------------------------------------------------------------------ #

class TestRoundEnd:
    def test_incomplete_round_returns_to_board(self, engine):
        _select(engine)
        engine.evaluate_answer(correct=True)
        engine.advance_from_result()
        assert engine.state.phase == GamePhase.BOARD

    def test_round_1_complete_goes_to_summary(self, engine):
        _clear_genres(engine, 0, list(range(1, NUM_GENRES)))  # 5 genres pre-cleared
        engine.select_question(genre_id=NUM_GENRES, difficulty=1, question_id=1, base_points=100)
        engine.evaluate_answer(correct=True)
        engine.advance_from_result()
        assert engine.state.phase == GamePhase.ROUND_SUMMARY

    def test_summary_advances_round_number(self, engine):
        _clear_genres(engine, 0, list(range(1, NUM_GENRES)))
        engine.select_question(genre_id=NUM_GENRES, difficulty=1, question_id=1, base_points=100)
        engine.evaluate_answer(correct=True)
        engine.advance_from_result()
        engine.advance_from_round_summary()
        assert engine.state.round_number == 2

    def test_summary_resets_board_and_genres(self, engine):
        _clear_genres(engine, 0, list(range(1, NUM_GENRES)))
        engine.select_question(genre_id=NUM_GENRES, difficulty=1, question_id=1, base_points=100)
        engine.evaluate_answer(correct=True)
        engine.advance_from_result()
        engine.advance_from_round_summary()
        assert len(engine.state.players[0].genres_cleared) == 0
        assert len(engine.state.board_cleared) == 0
        assert engine.state.phase == GamePhase.BOARD

    def test_summary_resets_pause_counts(self, engine):
        engine.state.players[0].pause_count = 2
        _clear_genres(engine, 0, list(range(1, NUM_GENRES)))
        engine.select_question(genre_id=NUM_GENRES, difficulty=1, question_id=1, base_points=100)
        engine.evaluate_answer(correct=True)
        engine.advance_from_result()
        engine.advance_from_round_summary()
        assert engine.state.players[0].pause_count == 0

    def test_round_3_winner_on_clear_score_lead(self, engine):
        engine.state.round_number = 3
        engine.state.players[0].score = 1000
        engine.state.players[1].score = 500
        _clear_genres(engine, 0, list(range(1, NUM_GENRES)))
        engine.select_question(genre_id=NUM_GENRES, difficulty=1, question_id=1, base_points=0)
        engine.evaluate_answer(correct=True)
        engine.advance_from_result()
        assert engine.state.phase == GamePhase.GAME_OVER
        assert engine.state.winner_index == 0


# ------------------------------------------------------------------ #
# sudden death                                                         #
# ------------------------------------------------------------------ #

class TestSuddenDeath:
    def test_tie_after_round_3_triggers_sudden_death(self, engine):
        engine.state.round_number = 3
        # Set up a tie: player 0 answers correctly for 0 extra pts so scores stay equal
        engine.state.players[0].score = 500
        engine.state.players[1].score = 500
        _clear_genres(engine, 0, list(range(1, NUM_GENRES)))
        engine.select_question(genre_id=NUM_GENRES, difficulty=1, question_id=1, base_points=0)
        engine.evaluate_answer(correct=True)
        engine.advance_from_result()
        assert engine.state.phase == GamePhase.SUDDEN_DEATH

    def test_sudden_death_correct_ends_game(self, engine):
        engine.state.phase = GamePhase.SUDDEN_DEATH
        engine.evaluate_sudden_death(player_index=1, correct=True)
        assert engine.state.phase == GamePhase.GAME_OVER
        assert engine.state.winner_index == 1

    def test_sudden_death_wrong_stays_in_sudden_death(self, engine):
        engine.state.phase = GamePhase.SUDDEN_DEATH
        engine.evaluate_sudden_death(player_index=0, correct=False)
        assert engine.state.phase == GamePhase.SUDDEN_DEATH

    def test_sudden_death_wrong_does_not_set_winner(self, engine):
        engine.state.phase = GamePhase.SUDDEN_DEATH
        engine.evaluate_sudden_death(player_index=0, correct=False)
        assert engine.state.winner_index is None
