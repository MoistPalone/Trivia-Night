from dataclasses import dataclass, field

MAX_PAUSES_PER_ROUND = 2


@dataclass
class Player:
    name: str
    score: int = 0
    genres_cleared: set = field(default_factory=set)  # genre IDs cleared this round
    pause_count: int = 0  # resets each round; capped at MAX_PAUSES_PER_ROUND

    @property
    def can_pause(self) -> bool:
        return self.pause_count < MAX_PAUSES_PER_ROUND

    def reset_for_round(self) -> None:
        self.genres_cleared = set()
        self.pause_count = 0
