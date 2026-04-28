---
mode: oncall
active: true
project: Trivia Night
wiki_path: ~/wiki/wiki/Trivia Night
sprint: "Session 8 next — QA + ship v1.0"
last_brief: 2026-04-28
---

## Active Objectives

- [x] Create project scaffold at ~/trivia-night/
- [x] Write data/db.py — SQLite schema migration
- [x] Write data/seed/seeder.py — JSON → SQLite loader
- [x] Seed history.json, science.json, geography.json (225 questions, 15 per difficulty × 5 levels)
- [x] Verify DB: SELECT COUNT(*) FROM questions → 225
- [ ] Initialize git repo and make first commit
- [ ] Session 2: seed arts.json, people.json, music.json (225 more questions → 450 total)
- [x] Session 3: game engine (state.py, player.py, engine.py, scorer.py, timer.py) — 41 tests passing
- [x] Session 4: core UI scaffold — welcome + board + scoreboard; 30 tiles render; welcome→board wired
- [x] Session 5: question screen + timer widget + result overlay + full turn cycle
- [x] Session 6: round summary + sudden death + game over screens; full game cycle playable
- [x] Session 7: audio (QSoundEffect + 7 generated WAVs) + genre color accents on board tiles
- [ ] Session 8: QA + ship v1.0

## Notes

Session opened: 2026-04-28
Session 1 completed: 2026-04-28
DB verified: 225 questions (3 genres × 5 difficulties × 15 questions each)
No git repo yet — needs git init before Session 2.
