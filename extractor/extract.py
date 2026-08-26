"""Turn one resume's text into a validated `Resume` -- offline or with a real model.

Two modes, one return type:

  OFFLINE (default)  A deterministic, rule-based reader: regexes and a few simple
                     heuristics find the email, the phone, a skills section, and
                     so on. No API key, no network, no cost. It is genuinely
                     useful and it is honest about what it can't do -- a title
                     hidden in prose, or a city with no comma after it, it will
                     miss. Those misses are the argument for the LLM.

  REAL               Sends the text to a language model via LiteLLM, asking for
                     strict JSON, and validates the reply. This is the
                     AI-engineer pattern the project is really about.

Both paths end at the SAME wall: the `Resume` pydantic model. Whatever produced
the fields, they only become a `Resume` if they pass validation. The rest of the
program can therefore trust any `Resume` it is handed.
"""

from __future__ import annotations

import json
import os
import re

from .prompts import build_messages
from .schema import Resume

# --------------------------------------------------------------------------- #
#  Small building blocks: one regex / helper per field                        #
# --------------------------------------------------------------------------- #

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

# Phone patterns, tried in order. Each is deliberately shaped so a four-digit
# year or a "(2020-2024)" date range can't masquerade as a phone number: the
# labelled and the "+international" forms need a label or a leading +, and the
# parenthesised form needs a closing ) right after the area code (which a year
# range like "(2020-2024)" does not have).
_PHONE_RES = [
    re.compile(r"(?:phone|tel|mobile|cell)\s*[:\-]?\s*([+(]?\d[\d ().\-]{6,}\d)", re.I),
    re.compile(r"(\+\d[\d ().\-]{7,}\d)"),
    re.compile(r"(\(\d{2,4}\)[\d ().\-]{5,}\d)"),
]

# "7 years", "5 yrs", "over 9 years of experience", "5.5 years".
_YEARS_RE = re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years|year|yrs|yr)\b", re.I)

# A "City, ST" / "City, Country" pair of capitalised words. Only ever run over the
# top few header lines, so a phrase like "Science, IIT" deep in the body can't win.
_LOCATION_RE = re.compile(r"([A-Z][a-zA-Z.]+(?: [A-Z][a-zA-Z.]+)*,\s*[A-Z][a-zA-Z.]+)")

# Words that mark a job title. Used to spot the title line in the header.
_TITLE_WORDS = (
    "engineer", "developer", "scientist", "manager", "analyst", "architect",
    "designer", "administrator", "consultant", "specialist", "lead",
)

# Degree markers for the fallback education scan.
_DEGREE_RE = re.compile(
    r"\b(ph\.?d|doctor|m\.?tech|b\.?tech|m\.?sc|b\.?sc|m\.?eng|b\.?eng|mba|"
    r"master|bachelor|b\.?a\b|m\.?a\b|b\.?s\b|m\.?s\b)",
    re.I,
)

# Lines that begin a new section -- used to know where a skills/education block ends.
_SECTION_STOPWORDS = (
    "experience", "work history", "work", "roles", "employment", "profile",
    "summary", "education", "projects", "skills", "technologies", "certifications",
)

# A small gazetteer of technologies, used ONLY as a fallback when a resume has no
# skills section at all (like the very short one, or the one written in prose).
# A real model needs none of this; it's here so offline mode isn't useless on the
# hard cases.
_KNOWN_SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "Go", "C++", "C#", "Ruby",
    "Rust", "Scala", "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis",
    "React", "Vue", "Angular", "Node.js", "Django", "FastAPI", "Flask",
    "Spark", "Apache Spark", "Airflow", "dbt", "Kafka", "Hadoop",
    "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform", "Ansible",
    "Jenkins", "Prometheus", "Grafana", "gRPC", "Bash",
    "PyTorch", "TensorFlow", "scikit-learn", "pandas", "NumPy", "MLflow",
    "CUDA", "OpenCV", "Linear Algebra", "NLP",
]


def _first_nonempty_lines(text: str, n: int) -> list[str]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return lines[:n]


def _find_name(text: str) -> str:
    """Best guess at the person's name.

    Resumes almost always lead with the name. We take the first non-empty line,
    keep only the part before a separator like `|` or `//` (some people cram
    contact details onto that line), and title-case it if it's shouting in caps.
    """
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        # Strip a "Name:" label if present.
        line = re.sub(r"^name\s*[:\-]\s*", "", line, flags=re.I)
        # Take the chunk before the first separator.
        line = re.split(r"\s*[|/]{1,2}\s*", line)[0].strip()
        if line.isupper():
            line = line.title()
        return line or "Unknown"
    return "Unknown"


def _find_email(text: str) -> str | None:
    m = _EMAIL_RE.search(text)
    return m.group(0) if m else None


def _find_phone(text: str) -> str | None:
    for pattern in _PHONE_RES:
        m = pattern.search(text)
        if not m:
            continue
        candidate = m.group(1).strip()
        digits = re.sub(r"\D", "", candidate)
        if 7 <= len(digits) <= 15:  # sanity check: a real phone length
            return candidate
    return None


def _find_location(text: str) -> str | None:
    header = "\n".join(_first_nonempty_lines(text, 6))
    m = re.search(r"location\s*[:\-]\s*(.+)", header, re.I)
    if m:
        return m.group(1).strip()
    m = _LOCATION_RE.search(header)
    if not m:
        return None
    candidate = m.group(1).strip()
    # Guard against a skills line like "React, TypeScript" looking like "City, ST":
    # if either side of the comma is a known technology, it isn't a location.
    known_lower = {s.lower() for s in _KNOWN_SKILLS}
    if any(part.strip().lower() in known_lower for part in candidate.split(",")):
        return None
    return candidate


def _find_years(text: str) -> float | None:
    m = _YEARS_RE.search(text)
    return float(m.group(1)) if m else None


def _find_title(text: str) -> str | None:
    """Look for a short header line that names a job title."""
    for line in _first_nonempty_lines(text, 8):
        low = line.lower()
        if "@" in line or len(line) > 60:
            continue
        if any(word in low for word in _TITLE_WORDS):
            # Cut off any trailing sentence ("... with 9 years of experience").
            for sep in (".", " with ", ",", " - ", "  "):
                if sep in line:
                    line = line.split(sep)[0]
            return line.strip()
    return None


def _section_block(text: str, headers: tuple[str, ...]) -> str | None:
    """Return the text under the first matching section header.

    Grabs anything on the header line after a colon, plus the following lines,
    stopping at a blank line or the next section header. This is how we read a
    "Skills:" or "Education" block no matter how it's laid out.
    """
    lines = text.splitlines()
    header_re = re.compile(r"^\s*(?:" + "|".join(headers) + r")\b\s*[:\-]?\s*(.*)$", re.I)
    for i, line in enumerate(lines):
        m = header_re.match(line)
        if not m:
            continue
        collected: list[str] = []
        inline = m.group(1).strip()
        if inline:
            collected.append(inline)
        for follow in lines[i + 1 :]:
            stripped = follow.strip()
            if not stripped:
                break
            low = stripped.lower().rstrip(":")
            if any(low == sw or low.startswith(sw + " ") for sw in _SECTION_STOPWORDS):
                break
            collected.append(stripped)
        return "\n".join(collected) if collected else None
    return None


def _parse_items(block: str) -> list[str]:
    """Split a skills block into individual items (handles commas and bullets)."""
    items: list[str] = []
    for line in block.splitlines():
        line = line.strip().lstrip("-*•").strip()
        if not line:
            continue
        for part in line.split(","):
            part = part.strip()
            if part:
                items.append(part)
    return items


def _find_skills(text: str) -> list[str]:
    # Order matters: longer, more specific headers first so "technologies i use"
    # wins over a bare "technologies" (otherwise "I use:" leaks into the skills).
    block = _section_block(
        text, ("technical skills", "core skills", "key skills", "technologies i use", "technologies", "skills")
    )
    if block:
        return _parse_items(block)
    # Fallback: no skills section -- scan for known technologies by name.
    found: list[str] = []
    for skill in _KNOWN_SKILLS:
        if re.search(r"(?<![A-Za-z0-9])" + re.escape(skill) + r"(?![A-Za-z0-9])", text):
            found.append(skill)
    return found


def _find_education(text: str) -> str | None:
    block = _section_block(text, ("education", "academic", "qualifications"))
    if block:
        return block.splitlines()[0].strip()
    # Fallback: the first line mentioning a degree.
    for line in text.splitlines():
        if _DEGREE_RE.search(line):
            return line.strip()
    return None


# --------------------------------------------------------------------------- #
#  Offline extractor: assemble the fields, then validate                      #
# --------------------------------------------------------------------------- #
def extract_offline(text: str) -> Resume:
    """Pull fields out of `text` with rules only, and validate them into a Resume.

    Note the shape of this: gather a plain dict of guesses, then hand it to
    `Resume(**data)`. The pydantic model is the gate. If the rules produced a bad
    email or a nonsense years value, validation is where it's caught.
    """
    data = {
        "name": _find_name(text),
        "email": _find_email(text),
        "phone": _find_phone(text),
        "location": _find_location(text),
        "current_title": _find_title(text),
        "years_experience": _find_years(text),
        "skills": _find_skills(text),
        "education": _find_education(text),
    }
    return Resume(**data)


# --------------------------------------------------------------------------- #
#  Real extractor: LiteLLM -> JSON -> validate                                #
# --------------------------------------------------------------------------- #
DEFAULT_MODEL = os.environ.get("EXTRACTOR_MODEL", "gemini/gemini-1.5-flash")


def _extract_json(raw: str) -> str:
    """Pull the first {...} object out of a model reply (it may add stray text)."""
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in the model response.")
    return match.group(0)


def extract_real(text: str, model: str | None = None) -> Resume:
    """Ask a real model to parse the resume, then validate its JSON into a Resume.

    LiteLLM is imported lazily so that offline mode -- the default everywhere in
    this project -- doesn't even require litellm to be installed.
    """
    from litellm import completion  # noqa: PLC0415  (lazy on purpose)

    messages = build_messages(text)
    response = completion(model=model or DEFAULT_MODEL, messages=messages, temperature=0)
    raw = response.choices[0].message.content or ""
    return Resume.model_validate_json(_extract_json(raw))


# --------------------------------------------------------------------------- #
#  The one function the rest of the program calls                             #
# --------------------------------------------------------------------------- #
def extract(text: str, *, real: bool = False, model: str | None = None) -> Resume:
    """Extract a validated Resume from resume text.

    real=False (default) uses the offline rule-based extractor -- no key needed.
    real=True calls a language model through LiteLLM.
    """
    if real:
        return extract_real(text, model=model)
    return extract_offline(text)
