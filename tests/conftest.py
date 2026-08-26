"""Shared test fixtures.

Everything here runs OFFLINE with no API key and no network -- the offline
extractor is deterministic, the database is in-memory, and the API is exercised
through FastAPI's TestClient (which never opens a real port). That's what lets
`pytest` pass on a bare laptop and in CI.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from extractor import database as db
from extractor.api import create_app

# A couple of the sample resumes, inline, so the tests don't depend on files
# having been generated first.
PRIYA = """\
Priya Sharma
Senior Data Engineer
Email: priya.sharma@example.com
Phone: +44 7911 123456
Location: London, UK

Skills: Python, SQL, Apache Spark, Airflow, dbt, AWS, Docker, Kafka

Education
BSc Computer Science, University of Manchester, 2017
"""

MARCUS = """\
MARCUS LEE  |  marcus.lee23@example.com  |  (415) 555-0198  |  San Francisco, CA

Backend Software Engineer

5 yrs building APIs and services at scale.

Core skills
- Go
- Python
- PostgreSQL

Bachelor of Science in Software Engineering - San Jose State University
"""


@pytest.fixture
def priya_text() -> str:
    return PRIYA


@pytest.fixture
def marcus_text() -> str:
    return MARCUS


@pytest.fixture
def conn():
    """A fresh in-memory SQLite database for one test."""
    c = db.connect(":memory:")
    yield c
    c.close()


@pytest.fixture
def client(tmp_path):
    """A TestClient wired to a throwaway on-disk database in a temp folder."""
    app = create_app(db_path=str(tmp_path / "test.db"))
    with TestClient(app) as c:
        yield c
