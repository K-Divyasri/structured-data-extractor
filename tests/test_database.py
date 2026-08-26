"""Tests for SQLite persistence."""

from __future__ import annotations

from extractor import database as db
from extractor.extract import extract_offline
from extractor.schema import Resume


def test_save_and_read_back(conn, priya_text):
    resume = extract_offline(priya_text)
    new_id = db.save_resume(conn, resume, source="priya.txt")
    assert new_id == 1

    row = db.get_by_id(conn, new_id)
    assert row is not None
    assert row["name"] == "Priya Sharma"
    assert row["source"] == "priya.txt"
    # skills come back as a real list, not the JSON string we stored.
    assert isinstance(row["skills"], list)
    assert "Python" in row["skills"]


def test_count_and_get_all(conn):
    db.save_resume(conn, Resume(name="A"))
    db.save_resume(conn, Resume(name="B"))
    assert db.count(conn) == 2
    rows = db.get_all(conn)
    assert [r["name"] for r in rows] == ["B", "A"]  # newest first


def test_get_missing_id_returns_none(conn):
    assert db.get_by_id(conn, 999) is None


def test_empty_skills_roundtrip(conn):
    new_id = db.save_resume(conn, Resume(name="No Skills"))
    row = db.get_by_id(conn, new_id)
    assert row["skills"] == []
