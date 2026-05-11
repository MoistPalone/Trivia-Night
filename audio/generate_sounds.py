"""
Generate placeholder WAV sound effects for Trivia Night.
Run once: python audio/generate_sounds.py
Replace with real audio files (same names) for final polish.
"""
import math
import random
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
    # Short electronic blip — distinct from the ambient ticking clock so it registers
    # as an urgency accent rather than a duplicate tick in the last 10 seconds.
    # Two stacked harmonics (600 Hz + 1200 Hz), 2ms snap attack, 43ms exponential decay.
    sr = SAMPLE_RATE
    n = int(sr * 0.045)
    attack_n = int(sr * 0.002)
    frames: list[float] = []
    for i in range(n):
        t = i / sr
        env = (i / attack_n) if i < attack_n else ((n - i) / (n - attack_n)) ** 1.4
        s = 0.6 * _sine(600.0, t) + 0.4 * _sine(1200.0, t)
        frames.append(s * env)
    _write("tick_urgent.wav", frames, volume=0.65)


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


def generate_tile_select() -> None:
    # Soft short click — 600Hz, 60ms, fast fade
    frames = _tone(600.0, 0.06, fade_frac=0.5)
    _write("tile_select.wav", frames, volume=0.30)


def generate_turn_change() -> None:
    # Soft ascending two-note chime: F4 → C5
    frames = _sequence([(349.23, 0.15), (523.25, 0.20)])
    _write("turn_change.wav", frames, volume=0.40)


def generate_question_ambient() -> None:
    # 3-second seamless loop: ticks at 0.25s, 1.25s, 2.25s (1/s cadence).
    # Ticks are offset from the loop boundary so QSoundEffect's ~50ms restart
    # latency falls inside the 0.75s silence window and is inaudible.
    sr = SAMPLE_RATE
    n = int(sr * 3.0)
    frames = [0.0] * n

    def add_tick(offset_s: float) -> None:
        o = int(sr * offset_s)
        noise_n = int(sr * 0.004)   # 4ms broadband click
        ring_n = int(sr * 0.018)    # 18ms tonal ring at 1800 Hz
        for i in range(noise_n):
            if o + i < n:
                env = (1.0 - i / noise_n) ** 0.5
                frames[o + i] += (2.0 * random.random() - 1.0) * env
        for i in range(ring_n):
            idx = o + noise_n + i
            if idx < n:
                t_s = idx / sr
                env = (1.0 - i / ring_n) ** 2.5
                frames[idx] += _sine(1800.0, t_s) * env * 0.55

    add_tick(0.25)
    add_tick(1.25)
    add_tick(2.25)
    frames = [max(-1.0, min(1.0, s)) for s in frames]
    _write("question_ambient.wav", frames, volume=0.62)


if __name__ == "__main__":
    print("Generating sound effects…")
    generate_correct()
    generate_wrong()
    generate_timeout()
    generate_tick_urgent()
    generate_round_complete()
    generate_sudden_death()
    generate_game_over()
    generate_tile_select()
    generate_turn_change()
    generate_question_ambient()
    print("Done.")
