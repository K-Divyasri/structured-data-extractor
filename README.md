# Structured Data Extractor

Turn messy resume text into a validated JSON record, store it in SQLite, and serve it over a
FastAPI endpoint. Runs offline with no API key by default; an optional flag swaps in a real
LLM.

**Problem:** Resumes are free-form text: every one is laid out differently, with typo'd
labels, bullet lists, prose, and missing fields. To do anything useful with a stack of them
(search, dedupe, load into a database) you first need the *same* clean record out of each:
name, email, phone, location, title, years of experience, skills, education. Getting
*something* back is easy. Getting the same trustworthy shape every time, and catching it
when a field is wrong, is the real work. This project does that.

**Skills demonstrated:** structured outputs, schema-driven validation (pydantic v2), regex
and heuristic parsing, SQLite persistence (stdlib `sqlite3`), a REST API with FastAPI,
optional LLM extraction via LiteLLM, argparse CLI design, type hints, pytest.

**Tech stack:** Python 3.10+, pydantic 2, FastAPI, uvicorn, SQLite (standard library);
LiteLLM + a free Gemini key for the optional `--real` path. Streamlit for the demo UI.

## How it works

The package is split so each file does one job, which is also what makes it testable:

```
extractor/
├── schema.py     the pydantic Resume model -- the CONTRACT for a valid record
├── prompts.py    builds the LLM messages (system prompt lists the exact JSON keys)
├── extract.py    text -> validated Resume: extract_offline (rules) or extract_real (LLM)
├── database.py   save a Resume to SQLite and read records back (skills stored as JSON)
├── api.py        the FastAPI app: POST /extract plus read endpoints
├── cli.py        the argparse front door: python -m extractor <files...>
└── __main__.py   makes `python -m extractor` work
```

The flow is one straight line:

```
raw text -> extract(text, real=?) -> Resume (validated) -> SQLite -> FastAPI /extract
```

The design choice that matters: **the schema is the wall.** `schema.py` defines what a valid
`Resume` is: `name` is required and non-blank, `email` is lowercased and regex-checked (a
bad address raises instead of slipping through), `years_experience` must be 0–60, `skills`
are trimmed and de-duped, and unknown keys are rejected outright (`extra: "forbid"`). Both
extractors, the offline rules and the LLM, have to produce something that passes *that same
wall* before it's ever returned or stored. That's why the API can't hand back a malformed
record: validation runs first.

The offline extractor is deterministic regex and heuristics, no key, no network. It handles
most fields on most resumes, but it honestly misses things stated only in prose (a location
written as a bare city with no comma, a title mentioned mid-sentence, an implied number of
years). Those misses are the argument for the `--real` path, which sends the text to an LLM
asked for strict JSON and validates the reply with the exact same schema.

## Run locally

```powershell
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python generate_data.py                      # writes the six sample resumes to data/resumes/

python -m extractor data\resumes\priya_sharma.txt
python -m extractor data\resumes\*.txt --save --db resumes.db --json
pytest                                        # 27 tests, all offline

uvicorn extractor.api:app --reload            # API -> http://127.0.0.1:8000/docs
streamlit run web_app.py                      # the demo UI
```

The CLI takes one or more files, with `--json` (JSON instead of the summary), `--save`
(persist to SQLite), `--db PATH`, and `--real` (use the LLM).

### Sample CLI output

`python -m extractor data\resumes\priya_sharma.txt`:

```
  priya_sharma.txt
    name           Priya Sharma
    email          priya.sharma@example.com
    phone          +44 7911 123456
    location       London, UK
    current_title  Senior Data Engineer
    years_exp      7
    skills         Python, SQL, Apache Spark, Airflow, dbt, AWS, Docker, Kafka
    education      BSc Computer Science, University of Manchester, 2017
```

### Sample API call

Start the server (`uvicorn extractor.api:app --reload`), then POST some text. Request:

```json
POST /extract
{
  "text": "Priya Sharma\nSenior Data Engineer\nEmail: priya.sharma@example.com\nPhone: +44 7911 123456\nLocation: London, UK\n\nSkills: Python, SQL, Apache Spark, Airflow, dbt, AWS, Docker, Kafka\n\nEducation\nBSc Computer Science, University of Manchester, 2017",
  "save": false
}
```

Response:

```json
{
  "id": null,
  "resume": {
    "name": "Priya Sharma",
    "email": "priya.sharma@example.com",
    "phone": "+44 7911 123456",
    "location": "London, UK",
    "current_title": "Senior Data Engineer",
    "years_experience": 7.0,
    "skills": ["Python", "SQL", "Apache Spark", "Airflow", "dbt", "AWS", "Docker", "Kafka"],
    "education": "BSc Computer Science, University of Manchester, 2017"
  }
}
```

With `"save": true` (the default), the record is written to SQLite and `id` comes back as its
row number. The other endpoints: `GET /health` returns `{"status":"ok"}`, `GET /resumes`
lists everything saved, and `GET /resumes/{id}` fetches one (404 if it doesn't exist). Open
`/docs` for the interactive version of all of them.

Optional `--real` flag: copy `.env.example` to `.env`, add a free Gemini key from
https://aistudio.google.com/apikey, then `python -m extractor data\resumes\aisha_khan.txt
--real`. Without a key, offline mode is the default and everything else works untouched.

## What I learned

- **A schema is a contract, not a suggestion.** Putting a pydantic model in front of both the
  rules and the LLM meant "valid record" had one definition, enforced in one place, and a
  bad email or an out-of-range years value fails loudly instead of quietly corrupting the
  database.
- **Deterministic parsing gets you surprisingly far, and then hits a wall.** Regex handled
  labelled fields cleanly, but couldn't read facts buried in prose. Seeing exactly where it
  broke made the case for an LLM concrete instead of hand-wavy.
- **The same functions can power a CLI, an API, and a web UI.** `extract()` and the database
  helpers are written with no printing and no I/O assumptions, so `cli.py`, `api.py`, and
  `web_app.py` each just call them. That's why the tests are short: they test the library
  directly, not through the interface.
- **FastAPI gives you validation and docs for free** by reading the same pydantic models:
  a malformed request gets a clear 422 before my code runs, and `/docs` is generated from the
  types.
