from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class GamePhase(Enum):
    WELCOME = auto()
    BOARD = auto()
    QUESTION = auto()
    PAUSED = auto()
    RESULT = auto()
    ROUND_SUMMARY = auto()
    SUDDEN_DEATH = auto()
    GAME_OVER = auto()


@dataclass
class QuestionContext:
    question_id: int
    genre_id: int
    difficulty: int
    base_points: int


@dataclass
class ResultContext:
    correct: bool
    points_awarded: int
    player_index: int  # index of the player who answered


@dataclass
class GameState:
    phase: GamePhase = GamePhase.WELCOME
    round_number: int = 1
    active_player_index: int = 0
    players: list = field(default_factory=list)
    board_cleared: set = field(default_factory=set)   # set of (genre_id, difficulty)
    current_question: Optional[QuestionContext] = None
    last_result: Optional[ResultContext] = None
    winner_index: Optional[int] = None
    sudden_death_order: list = field(default_factory=list)   # player indices in SD rotation
    sudden_death_turn_index: int = 0
