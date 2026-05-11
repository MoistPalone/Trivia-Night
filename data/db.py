import sqlite3
from pathlib import Path

from bundle_path import bundle_path

DB_PATH = bundle_path("data", "questions.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS genres (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS questions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    genre_id        INTEGER NOT NULL REFERENCES genres(id),
    difficulty      INTEGER NOT NULL CHECK(difficulty BETWEEN 1 AND 5),
    points          INTEGER NOT NULL,
    question_text   TEXT NOT NULL,
    answer_text     TEXT NOT NULL,
    answer_keywords TEXT NOT NULL,
    UNIQUE(genre_id, difficulty, question_text)
);

CREATE TABLE IF NOT EXISTS question_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL REFERENCES questions(id),
    played_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def require_db() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Question database not found at {DB_PATH}.\n"
            "Run: python data/seed/seeder.py"
        )
    return get_connection()
