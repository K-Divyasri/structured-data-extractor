"""The prompt we send a real model when we want it to do the extraction.

The offline extractor (see extract.py) uses regexes and needs no model. But the
whole point of the project is the *AI-engineer* pattern: hand messy text to a
language model and get back strict, schema-shaped JSON. This file builds that
request.

The trick that makes it reliable is telling the model the EXACT JSON shape we
want -- generated straight from the pydantic schema so the prompt can never drift
out of sync with the code that validates the answer -- and instructing it to
return that and nothing else. Then pydantic checks whatever comes back.
"""

from __future__ import annotations

import json

from .schema import Resume

Message = dict[str, str]

# The instructions. Short, blunt, and explicit about the output format -- the three
# things that make structured-output prompts behave.
_SYSTEM = """\
You are a precise resume parser. You are given the raw text of one resume and you
extract a fixed set of fields from it.

Rules:
- Return ONLY a single JSON object. No prose, no markdown, no code fences.
- Use these keys exactly: name, email, phone, location, current_title,
  years_experience, skills, education.
- If a field is not present in the resume, use null (for skills, use []).
- name is required -- always return the person's full name.
- years_experience must be a number (e.g. 7 or 5.5), not a sentence.
- skills must be a JSON array of short strings, e.g. ["Python", "SQL"].
- education is the highest / headline qualification as one short string.
- Do not invent facts. Only report what the text supports.
"""


def _example_shape() -> str:
    """A filled-in example of the JSON we want, derived from the schema itself.

    Building this from `Resume` (rather than hand-typing it) means if we add a
    field to the schema, the example the model sees updates automatically.
    """
    example = Resume(
        name="Jane Doe",
        email="jane.doe@example.com",
        phone="+1 555 0100",
        location="Austin, TX",
        current_title="Data Scientist",
        years_experience=6,
        skills=["Python", "SQL", "scikit-learn"],
        education="MSc Statistics, UT Austin",
    )
    return json.dumps(example.model_dump(), indent=2)


def build_messages(resume_text: str) -> list[Message]:
    """Turn one resume's raw text into the chat messages for a real LLM call."""
    system = f"{_SYSTEM}\nReturn JSON shaped exactly like this example:\n{_example_shape()}"
    user = f"Resume text:\n\"\"\"\n{resume_text}\n\"\"\"\n\nJSON:"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
