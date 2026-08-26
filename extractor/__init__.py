"""Structured Data Extractor -- messy resume text in, validated JSON out.

The one job of this package: take a blob of text a human wrote (a resume) and
return the same clean, machine-readable record every time -- name, email, phone,
skills, years of experience, education -- then store it in a database and serve it
over a tiny web API.

The public pieces:

    schema.Resume        the pydantic model that DEFINES a valid record
    extract.extract      text -> validated Resume (offline rules or a real LLM)
    database             save a Resume to SQLite and read records back
    api                  a FastAPI app exposing POST /extract

Everything runs offline with no API key by default (a deterministic rule-based
extractor), so the whole project -- notebooks, labs, tests -- works on a bare
laptop. Add a key and pass real=True to swap in a real language model.
"""

from __future__ import annotations

__version__ = "1.0.0"

# The fields we promise to pull out of every resume. Kept here so the schema, the
# extractor and the database all agree on one list.
FIELDS = (
    "name",
    "email",
    "phone",
    "location",
    "current_title",
    "years_experience",
    "skills",
    "education",
)
