# Trivia Night

Need to find something to do for an hour? Give this lightweight trivia game a try. Lots of general knowledge questions across 6 categories, increasing difficulty, and even a Sudden Death round if two players finish neck and neck.

## Features

- **2–4 players** — pick your headcount at the welcome screen and everyone gets their own scoreboard panel
- **6 categories** — History, Science, Geography, Arts, People, Music
- **5 difficulty tiers** — $100 to $500 per question; Round 3 doubles all points
- **Sudden Death tiebreaker** — first correct buzz-in wins when players are level at the end
- **Fuzzy answer matching** — close enough counts; typos and minor variations are forgiven
- **Sound effects** — ambient ticking clock during questions, result stings, round fanfares; mutable via the 🔊 button
- **Visual polish** — gradient tile board with per-genre accent colours, animated hover glow, smooth score count-up, and round announcement overlays

## Requirements

```
Python 3.11+
PyQt6
rapidfuzz
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running

```bash
python data/seed/seeder.py   # first run only — builds the question database
python main.py
```

Have fun!!
