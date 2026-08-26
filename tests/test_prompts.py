"""Tests for the LLM prompt builder (no model is called)."""

from __future__ import annotations

import json

from extractor.prompts import build_messages
from extractor.schema import Resume


def test_build_messages_shape(priya_text):
    messages = build_messages(priya_text)
    assert [m["role"] for m in messages] == ["system", "user"]
    # The resume text is carried in the user message.
    assert "Priya Sharma" in messages[1]["content"]
    # The system message names every field we expect back.
    system = messages[0]["content"]
    for field in ("name", "email", "skills", "years_experience", "education"):
        assert field in system


def test_example_in_prompt_is_valid_against_schema(priya_text):
    # The worked example embedded in the system prompt must itself be a valid
    # Resume -- otherwise we'd be teaching the model a bad shape.
    system = build_messages(priya_text)[0]["content"]
    start = system.index("{")
    example = json.loads(system[start:])
    Resume(**example)  # must not raise
