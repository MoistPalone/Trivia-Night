import json
from data.db import get_connection


def get_genres() -> list[tuple[int, str]]:
    conn = get_connection()
    rows = conn.execute("SELECT id, name FROM genres ORDER BY id").fetchall()
    conn.close()
    return [(r["id"], r["name"]) for r in rows]


def pick_question(
    genre_id: int,
    difficulty: int,
    exclude_ids: list[int] | None = None,
) -> dict | None:
    """Return a random question for the given slot, excluding recently played IDs."""
    conn = get_connection()
    exclude = exclude_ids or []
    placeholders = ",".join("?" * len(exclude))
    where_exclude = f"AND id NOT IN ({placeholders})" if exclude else ""
    row = conn.execute(
        f"""SELECT id, question_text, answer_text, answer_keywords, points
            FROM questions
            WHERE genre_id = ? AND difficulty = ? {where_exclude}
            ORDER BY RANDOM() LIMIT 1""",
        [genre_id, difficulty, *exclude],
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return {
        "id": row["id"],
        "question": row["question_text"],
        "answer": row["answer_text"],
        "keywords": json.loads(row["answer_keywords"]),
        "points": row["points"],
    }


def record_played(question_id: int) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO question_history (question_id) VALUES (?)", (question_id,)
    )
    conn.commit()
    conn.close()


def recently_played_ids(genre_id: int, difficulty: int, limit: int = 10) -> list[int]:
    """Return IDs of the most recently played questions for a given slot."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT q.id FROM question_history qh
           JOIN questions q ON qh.question_id = q.id
           WHERE q.genre_id = ? AND q.difficulty = ?
           ORDER BY qh.played_at DESC LIMIT ?""",
        (genre_id, difficulty, limit),
    ).fetchall()
    conn.close()
    return [r["id"] for r in rows]
