"""Tests for the offline rule-based extractor."""

from __future__ import annotations

from extractor.extract import extract, extract_offline
from extractor.schema import Resume


def test_extract_returns_a_resume(priya_text):
    assert isinstance(extract_offline(priya_text), Resume)


def test_priya_all_fields(priya_text):
    r = extract_offline(priya_text)
    assert r.name == "Priya Sharma"
    assert r.email == "priya.sharma@example.com"
    assert r.phone == "+44 7911 123456"
    assert r.location == "London, UK"
    assert r.current_title == "Senior Data Engineer"
    assert r.years_experience is None  # Priya's sample states no "N years"
    assert "Python" in r.skills and "Apache Spark" in r.skills
    assert r.education.startswith("BSc Computer Science")


def test_marcus_messy_layout(marcus_text):
    r = extract_offline(marcus_text)
    assert r.name == "Marcus Lee"  # ALL-CAPS name is title-cased
    assert r.email == "marcus.lee23@example.com"
    assert r.phone == "(415) 555-0198"  # parenthesised, no leading +
    assert r.location == "San Francisco, CA"
    assert r.years_experience == 5.0  # "5 yrs" -> 5
    assert r.skills[:3] == ["Go", "Python", "PostgreSQL"]  # bullet list parsed


def test_date_range_is_not_mistaken_for_a_phone():
    # "(2020-2024)" must NOT be read as a phone number.
    text = "Jon Doe\njon@example.com\nEngineer at Acme (2020-2024)\n"
    r = extract_offline(text)
    assert r.phone is None


def test_extract_dispatches_to_offline_by_default(priya_text):
    # extract(...) with real=False must equal extract_offline(...).
    assert extract(priya_text).model_dump() == extract_offline(priya_text).model_dump()


def test_missing_fields_are_none():
    r = extract_offline("Jane Roe\njane.roe@example.com\n")
    assert r.name == "Jane Roe"
    assert r.phone is None
    assert r.years_experience is None
    assert r.skills == []
