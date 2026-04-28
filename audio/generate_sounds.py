"""
Generate placeholder WAV sound effects for Trivia Night.
Run once: python audio/generate_sounds.py
Replace with real audio files (same names) for final polish.
"""
import math
import struct
import wave
from pathlib import Path

SOUNDS_DIR = Path(__file__).parent.parent / "assets" / "sounds"
SAMPLE_RATE = 44100


def _sine(freq: float, t: float) -> float:
    return math.sin(2 * math.pi * freq * t)


def _write(filename: str, frames: list[float], volume: float = 0.6) -> None:
    path = SOUNDS_DIR / filename
    clamped = [max(-1.0, min(1.0, s * volume)) for s in frames]
    packed = struct.pack(f"<{len(clamped)}h", *[int(s * 32767) for s in clamped])
    with wave.open(str(path), "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(packed)
    print(f"  wrote {path.name}")


def _tone(freq: float, duration_s: float, fade_frac: float = 0.3) -> list[float]:
    n = int(SAMPLE_RATE * duration_s)
    fade_n = int(n * fade_frac)
    frames = []
    for i in range(n):
        t = i / SAMPLE_RATE
        s = _sine(freq, t)
        if i < fade_n:
            s *= i / fade_n
        elif i > n - fade_n:
            s *= (n - i) / fade_n
        frames.append(s)
    return frames


def _chord(freqs: list[float], duration_s: float, fade_frac: float = 0.3) -> list[float]:
    parts = [_tone(f, duration_s, fade_frac) for f in freqs]
    n = len(parts[0])
    return [sum(p[i] for p in parts) / len(parts) for i in range(n)]


def _sequence(segments: list[tuple[float, float]]) -> list[float]:
    """List of (freq, duration_s) segments joined with 20ms silence."""
    silence = [0.0] * int(SAMPLE_RATE * 0.02)
    out: list[float] = []
    for i, (freq, dur) in enumerate(segments):
        out.extend(_tone(freq, dur, fade_frac=0.25))
        if i < len(segments) - 1:
            out.extend(silence)
    return out


def generate_correct() -> None:
    # Two-note ascending ding: C5 → E5
    frames = _sequence([(523.25, 0.18), (659.25, 0.28)])
    _write("correct.wav", frames, volume=0.65)


def generate_wrong() -> None:
    # Descending buzz: E3 → C3, with slight detune for harshness
    n = int(SAMPLE_RATE * 0.35)
    frames = []
    for i in range(n):
        t = i / SAMPLE_RATE
        ratio = i / n
        freq = 164.81 - ratio * 20  # descending E3
        s = 0.6 * _sine(freq, t) + 0.4 * _sine(freq * 1.015, t)
        fade = min(i / 400, 1.0) * max(0.0, 1.0 - (i - n + 800) / 800)
        frames.append(s * fade)
    _write("wrong.wav", frames, volume=0.6)


def generate_timeout() -> None:
    # Three short alarm beeps
    frames = _sequence([(880.0, 0.08), (880.0, 0.08), (880.0, 0.12)])
    _write("timeout.wav", frames, volume=0.55)


def generate_tick_urgent() -> None:
    # Sharp high click — 1kHz, very short
    frames = _tone(1046.5, 0.045, fade_frac=0.5)
    _write("tick_urgent.wav", frames, volume=0.35)


def generate_round_complete() -> None:
    # Upward arpeggio C4→E4→G4→C5
    frames = _sequence([(261.63, 0.12), (329.63, 0.12), (392.0, 0.12), (523.25, 0.22)])
    _write("round_complete.wav", frames, volume=0.6)


def generate_sudden_death() -> None:
    # Dramatic low pulse: two low hits
    hit1 = _chord([110.0, 146.83], 0.3, fade_frac=0.1)
    hit2 = _chord([82.41, 110.0], 0.45, fade_frac=0.08)
    gap = [0.0] * int(SAMPLE_RATE * 0.12)
    _write("sudden_death.wav", hit1 + gap + hit2, volume=0.6)


def generate_game_over() -> None:
    # Victory fanfare: C4-E4-G4, then sustained C5 chord
    arp = _sequence([(261.63, 0.1), (329.63, 0.1), (392.0, 0.1)])
    chord = _chord([523.25, 659.25, 783.99], 0.6, fade_frac=0.15)
    gap = [0.0] * int(SAMPLE_RATE * 0.05)
    _write("game_over.wav", arp + gap + chord, volume=0.6)


if __name__ == "__main__":
    print("Generating sound effects…")
    generate_correct()
    generate_wrong()
    generate_timeout()
    generate_tick_urgent()
    generate_round_complete()
    generate_sudden_death()
    generate_game_over()
    print("Done.")
