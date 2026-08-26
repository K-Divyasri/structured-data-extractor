"""The command-line interface: extract resumes from the terminal.

Run it as a module:

    python -m extractor data/resumes/priya_sharma.txt
    python -m extractor data/resumes/*.txt --save --db resumes.db
    python -m extractor data/resumes/aisha_khan.txt --json
    python -m extractor data/resumes/marcus_lee.txt --real   # needs an API key

argparse turns the flags you type into a tidy `args` object. The `main()` function
below is deliberately thin: it parses arguments, calls the library, and prints.
All the real work lives in extract.py / database.py, which is what makes them easy
to test without going through the command line at all.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import database as db
from .extract import extract
from .schema import Resume


def _pretty(resume: Resume, source: str) -> str:
    """A human-friendly block for one resume."""
    lines = [f"  {source}"]
    lines.append(f"    name           {resume.name}")
    lines.append(f"    email          {resume.email or '-'}")
    lines.append(f"    phone          {resume.phone or '-'}")
    lines.append(f"    location       {resume.location or '-'}")
    lines.append(f"    current_title  {resume.current_title or '-'}")
    yrs = "-" if resume.years_experience is None else f"{resume.years_experience:g}"
    lines.append(f"    years_exp      {yrs}")
    lines.append(f"    skills         {', '.join(resume.skills) or '-'}")
    lines.append(f"    education      {resume.education or '-'}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="extractor",
        description="Turn messy resume text into validated JSON (and optionally store it).",
    )
    p.add_argument("files", nargs="+", type=Path, help="One or more resume .txt files.")
    p.add_argument("--json", action="store_true", help="Print JSON instead of a summary.")
    p.add_argument("--save", action="store_true", help="Save each result to the database.")
    p.add_argument("--db", default="resumes.db", help="SQLite file to save into (with --save).")
    p.add_argument(
        "--real",
        action="store_true",
        help="Use a real LLM via LiteLLM (needs an API key) instead of offline rules.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    conn = db.connect(args.db) if args.save else None
    results: list[dict] = []

    for path in args.files:
        if not path.exists():
            print(f"skip: {path} (not found)", file=sys.stderr)
            continue
        text = path.read_text(encoding="utf-8")
        try:
            resume = extract(text, real=args.real)
        except Exception as exc:  # noqa: BLE001  (report and keep going)
            print(f"error: {path}: {exc}", file=sys.stderr)
            continue

        if conn is not None:
            new_id = db.save_resume(conn, resume, source=path.name)
            results.append({"id": new_id, **resume.model_dump()})
        else:
            results.append(resume.model_dump())

        if not args.json:
            print(_pretty(resume, path.name))

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))

    if conn is not None:
        print(f"\nSaved {len(results)} resume(s) to {args.db} "
              f"({db.count(conn)} total in the database).", file=sys.stderr)

    return 0 if results else 1


if __name__ == "__main__":
    raise SystemExit(main())
