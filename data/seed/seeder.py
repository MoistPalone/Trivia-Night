"""Read JSON seed files and insert questions into the SQLite database."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.db import get_connection, migrate

SEED_DIR = Path(__file__).parent
SEED_FILES = ["history.json", "science.json", "geography.json",
              "arts.json", "people.json", "music.json"]


def seed_file(conn, path: Path) -> tuple[int, int]:
    """Insert questions from one JSON file. Returns (inserted, skipped)."""
    data = json.loads(path.read_text())
    genre_name = data["genre"]

    conn.execute(
        "INSERT OR IGNORE INTO genres (name) VALUES (?)", (genre_name,)
    )
    row = conn.execute(
        "SELECT id FROM genres WHERE name = ?", (genre_name,)
    ).fetchone()
    genre_id = row["id"]

    inserted = skipped = 0
    for q in data["questions"]:
        keywords_json = json.dumps(q["answer_keywords"])
        try:
            conn.execute(
                """INSERT INTO questions
                   (genre_id, difficulty, points, question_text, answer_text, answer_keywords)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    genre_id,
                    q["difficulty"],
                    q["points"],
                    q["question"],
                    q["answer"],
                    keywords_json,
                ),
            )
            inserted += 1
        except Exception:
            skipped += 1

    return inserted, skipped


def main() -> None:
    conn = get_connection()
    migrate(conn)

    total_inserted = total_skipped = 0
    for filename in SEED_FILES:
        path = SEED_DIR / filename
        if not path.exists():
            print(f"  SKIP  {filename} (not found)")
            continue
        inserted, skipped = seed_file(conn, path)
        total_inserted += inserted
        total_skipped += skipped
        print(f"  OK    {filename}: {inserted} inserted, {skipped} skipped")

    conn.commit()
    conn.close()

    count_conn = get_connection()
    total = count_conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    count_conn.close()

    print(f"\nTotal questions in DB: {total}")
    print(f"Session inserted: {total_inserted}, skipped: {total_skipped}")


if __name__ == "__main__":
    main()
