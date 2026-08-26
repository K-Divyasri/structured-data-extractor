"""Save validated resumes to SQLite and read them back.

Extracting clean JSON is only half the job the spec asks for -- the other half is
*persisting* it. We use SQLite, which is part of Python's standard library: no
server to install, the whole database is a single file on disk. That's perfect
for a portfolio project and, honestly, for a lot of real ones too.

Design choices worth noticing:

  * One row per resume. The scalar fields (name, email, ...) each get a column.
  * `skills` is a list, and SQL columns hold single values, so we store it as a
    JSON string in a TEXT column and parse it back on the way out. (A "proper"
    normalised design would use a second table; JSON-in-a-column is the pragmatic
    choice at this size and a very common real pattern.)
  * Everything goes through the `Resume` model first, so only validated data is
    ever written.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .schema import Resume

# The table. `id` auto-increments; `source` records where the text came from (a
# filename, say) so you can trace a row back to its resume.
_SCHEMA = """
CREATE TABLE IF NOT EXISTS resumes (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    name              TEXT NOT NULL,
    email             TEXT,
    phone             TEXT,
    location          TEXT,
    current_title     TEXT,
    years_experience  REAL,
    skills            TEXT NOT NULL DEFAULT '[]',
    education         TEXT,
    source            TEXT
);
"""


def connect(db_path: str | Path = "resumes.db") -> sqlite3.Connection:
    """Open (creating if needed) the SQLite database and ensure the table exists.

    `row_factory = sqlite3.Row` lets us read columns by name (row["email"])
    instead of by numeric position, which keeps the reading code readable.
    Passing ":memory:" as the path gives a throwaway in-memory DB -- exactly what
    the tests use so they never touch disk.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(_SCHEMA)
    conn.commit()
    return conn


def connect_shared(db_path: str | Path = "resumes.db") -> sqlite3.Connection:
    """Like connect(), but usable from more than one thread.

    FastAPI runs plain (non-async) endpoint functions in a thread pool, so the one
    connection the app holds may be touched by different threads. SQLite guards
    against that by default; `check_same_thread=False` tells it we know what we're
    doing (our requests are short and serialised enough for a demo).
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute(_SCHEMA)
    conn.commit()
    return conn


def save_resume(conn: sqlite3.Connection, resume: Resume, source: str | None = None) -> int:
    """Insert one validated Resume. Returns the new row's id.

    Note the input type: this takes a `Resume`, not a dict. You cannot save
    unvalidated data through this function -- the type system won't let you -- which
    is the persistence layer quietly enforcing the schema.
    """
    cur = conn.execute(
        """
        INSERT INTO resumes
            (name, email, phone, location, current_title, years_experience, skills, education, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            resume.name,
            resume.email,
            resume.phone,
            resume.location,
            resume.current_title,
            resume.years_experience,
            json.dumps(resume.skills),
            resume.education,
            source,
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Turn a DB row back into a plain dict, parsing the skills JSON."""
    data = dict(row)
    data["skills"] = json.loads(data["skills"])
    return data


def get_all(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Return every stored resume, newest first."""
    rows = conn.execute("SELECT * FROM resumes ORDER BY id DESC").fetchall()
    return [_row_to_dict(r) for r in rows]


def get_by_id(conn: sqlite3.Connection, resume_id: int) -> dict[str, Any] | None:
    """Return one stored resume by id, or None if there's no such row."""
    row = conn.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,)).fetchone()
    return _row_to_dict(row) if row else None


def count(conn: sqlite3.Connection) -> int:
    """How many resumes are stored."""
    return int(conn.execute("SELECT COUNT(*) FROM resumes").fetchone()[0])
