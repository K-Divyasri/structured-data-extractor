"""Tests for the Resume schema -- the validation wall."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from extractor.schema import Resume


def test_minimal_valid_resume():
    r = Resume(name="Ada Lovelace")
    assert r.name == "Ada Lovelace"
    assert r.email is None
    assert r.skills == []  # defaults to an empty list, never None


def test_name_is_required():
    with pytest.raises(ValidationError):
        Resume()  # type: ignore[call-arg]


def test_empty_name_rejected():
    with pytest.raises(ValidationError):
        Resume(name="   ")  # strips to empty -> fails min_length


def test_email_is_lowercased_and_validated():
    r = Resume(name="X", email="Jane.DOE@Example.com")
    assert r.email == "jane.doe@example.com"


def test_bad_email_rejected():
    with pytest.raises(ValidationError):
        Resume(name="X", email="not-an-email")


def test_years_experience_range():
    with pytest.raises(ValidationError):
        Resume(name="X", years_experience=999)


def test_skills_are_deduped_case_insensitively():
    r = Resume(name="X", skills=["Python", "python ", "PYTHON", "SQL"])
    assert r.skills == ["Python", "SQL"]  # first spelling kept, order preserved


def test_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        Resume(name="X", nickname="Y")  # type: ignore[call-arg]


def test_blank_optional_becomes_none():
    r = Resume(name="X", location="  ")
    assert r.location is None
