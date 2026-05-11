import logging
from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QSoundEffect

log = logging.getLogger(__name__)

SOUNDS_DIR = Path(__file__).parent.parent / "assets" / "sounds"

_SOUND_FILES = {
    "correct": "correct.wav",
    "wrong": "wrong.wav",
    "timeout": "timeout.wav",
    "tick_urgent": "tick_urgent.wav",
    "round_complete": "round_complete.wav",
    "sudden_death": "sudden_death.wav",
    "game_over": "game_over.wav",
    "tile_select": "tile_select.wav",
    "turn_change": "turn_change.wav",
    "question_ambient": "question_ambient.wav",
}


class SoundManager:
    def __init__(self) -> None:
        self._effects: dict[str, QSoundEffect] = {}
        self._muted: bool = False
        self._load_all()

    def _load_all(self) -> None:
        for name, filename in _SOUND_FILES.items():
            path = SOUNDS_DIR / filename
            if not path.exists():
                log.warning("Sound file missing: %s — muting %s", path, name)
                continue
            effect = QSoundEffect()
            effect.setSource(QUrl.fromLocalFile(str(path.resolve())))
            effect.setVolume(0.8)
            self._effects[name] = effect

    def play(self, name: str) -> None:
        if self._muted:
            return
        effect = self._effects.get(name)
        if effect is not None:
            effect.play()
        else:
            log.debug("No sound loaded for: %s", name)

    def play_loop(self, name: str) -> None:
        if self._muted:
            return
        effect = self._effects.get(name)
        if effect is not None:
            effect.setLoopCount(QSoundEffect.Infinite)
            effect.play()

    def stop_loop(self, name: str) -> None:
        effect = self._effects.get(name)
        if effect is not None:
            effect.stop()
            effect.setLoopCount(1)

    def set_muted(self, muted: bool) -> None:
        if muted:
            for effect in self._effects.values():
                effect.stop()
        self._muted = muted

    def set_volume(self, volume: float) -> None:
        for effect in self._effects.values():
            effect.setVolume(volume)

    @property
    def muted(self) -> bool:
        return self._muted
