"""The shape of a valid resume record, enforced by pydantic.

This is the most important file in the project. Everything else -- the offline
extractor, the LLM prompt, the database, the API -- is organised around this one
class. `Resume` is the *contract*: it says exactly what fields a clean record has,
what type each one is, and which rules they must obey. If a value breaks a rule,
pydantic raises a `ValidationError` instead of letting the bad data through.

Why bother, instead of just using a plain dict? Because the input is text a human
typed however they liked, and the model we ask to read it can get things wrong.
A schema is the wall between "some text turned into some fields" and "a record we
trust enough to save." Fail loudly here and the rest of the program stays clean.
"""

from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

# A permissive but real email check. We are not trying to match the full RFC --
# just to reject obvious rubbish like "not an email" while accepting the addresses
# people actually write.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Resume(BaseModel):
    """One person's resume, reduced to the fields we care about.

    Required:
        name    -- we refuse a record with no name; it is the one field that must
                   always be present.

    Optional (None when the resume didn't give us the fact):
        email, phone, location, current_title, years_experience, education.

    skills defaults to an empty list rather than None, because "a list of skills"
    is always the right type even when the list happens to be empty.
    """

    name: str = Field(min_length=1, description="The person's full name.")
    email: Optional[str] = Field(default=None, description="Contact email, if present.")
    phone: Optional[str] = Field(default=None, description="Contact phone, if present.")
    location: Optional[str] = Field(default=None, description="City / country, if present.")
    current_title: Optional[str] = Field(
        default=None, description="Most recent or headline job title."
    )
    years_experience: Optional[float] = Field(
        default=None,
        ge=0,
        le=60,
        description="Years of professional experience. 0-60 is the sane range.",
    )
    skills: list[str] = Field(
        default_factory=list, description="Technologies / skills, de-duplicated."
    )
    education: Optional[str] = Field(
        default=None, description="Highest / headline qualification."
    )

    # Reject unknown keys. If the extractor (or a model) tries to add a field we
    # didn't ask for, that's a bug we want to hear about, not swallow.
    model_config = {"extra": "forbid"}

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        """Trim the name and refuse it if nothing is left. Name is never optional."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be blank")
        return cleaned

    @field_validator("email", "phone", "location", "current_title", "education")
    @classmethod
    def _strip(cls, value: Optional[str]) -> Optional[str]:
        """Trim surrounding whitespace; turn an empty string into None.

        Text scraped from a document is full of stray spaces and blank values.
        Normalising here means every consumer downstream sees tidy data.
        """
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("email")
    @classmethod
    def _check_email(cls, value: Optional[str]) -> Optional[str]:
        """Lower-case a real email; reject a string that clearly isn't one."""
        if value is None:
            return None
        value = value.lower()
        if not _EMAIL_RE.match(value):
            raise ValueError(f"{value!r} does not look like an email address")
        return value

    @field_validator("skills")
    @classmethod
    def _clean_skills(cls, skills: list[str]) -> list[str]:
        """Trim each skill, drop blanks, and remove case-insensitive duplicates.

        "Python", "python " and "PYTHON" are the same skill. We keep the first
        spelling we saw and preserve order, which reads better than sorting.
        """
        seen: set[str] = set()
        out: list[str] = []
        for raw in skills:
            skill = raw.strip()
            if not skill:
                continue
            key = skill.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(skill)
        return out
