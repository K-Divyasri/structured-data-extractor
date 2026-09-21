# Deploy checklist — Structured Data Extractor

This is the project's "definition of done." Walk it top to bottom. Don't tick a box you
haven't actually verified by running the command — "should work" isn't the same as "works."

Commands assume you're at the repo root unless noted.

## Runs locally

- [ ] Fresh virtual environment, dependencies installed cleanly:
      `python -m venv .venv ; .\.venv\Scripts\Activate.ps1` then `pip install -r requirements.txt`
- [ ] The sample data exists (regenerate if needed): `python generate_data.py`
- [ ] The CLI extracts a resume without error:
      `python -m extractor data\resumes\priya_sharma.txt`
- [ ] JSON output works and validates: `python -m extractor data\resumes\*.txt --json`
- [ ] Saving works and the row count goes up:
      `python -m extractor data\resumes\*.txt --save --db resumes.db`
- [ ] The API starts and the docs load:
      `uvicorn extractor.api:app --reload` then open http://127.0.0.1:8000/docs
- [ ] `GET /health` returns `{"status":"ok"}` (try it in /docs or with curl).
- [ ] `POST /extract` with `{"text":"...","save":false}` returns a parsed resume.
- [ ] (Optional) The Streamlit demo runs: `streamlit run web_app.py`

## Tests pass

- [ ] `pytest` from the repo root is all green (27 tests, well over the bar).
- [ ] You ran it in the fresh venv, not just your everyday one, so you know the deps are complete.
- [ ] Tests are offline — they ran with NO `GEMINI_API_KEY` set and NO network.

## README is recruiter-ready

- [ ] `README.md` exists and covers: the problem, skills demonstrated,
      tech stack, how it works, how to run it, and what you learned.
- [ ] A real sample-output block is pasted in (not paraphrased) — CLI output and a
      `POST /extract` request + response.
- [ ] A screenshot is embedded (`docs/cli-output.png` or a shot of `/docs`). Placeholder
      is fine until you capture the real one, but capture it before you call this done.

## Secrets are clean

- [ ] `.gitignore` contains `.env` (plus `*.db`, `__pycache__/`, `.venv/`).
- [ ] `git status` shows `.env` is NOT tracked.
- [ ] `git ls-files` output contains NO `.env` (only `.env.example`) and NO `*.db`. If a
      secret is there, remove it and rotate the key — see the hosting guide's troubleshooting.
- [ ] No API key is hardcoded anywhere in the source.

## Requirements are pinned enough

- [ ] `requirements.txt` lists every runtime dep with a `>=` floor (pydantic, fastapi,
      uvicorn, litellm, python-dotenv). A clean `pip install -r requirements.txt` succeeds.
- [ ] `requirements-dev.txt` pulls in the app plus pytest/httpx/ruff.

## Pushed to GitHub

- [ ] Repo created empty on github.com (no auto README/license), named
      `structured-data-extractor`, public.
- [ ] `git init` → `git add .` → `git commit` → `git branch -M main` →
      `git remote add origin ...` → `git push -u origin main` all done.
- [ ] Files visible on the GitHub repo page after a refresh; `.env` and `*.db` absent.

## CI is green

- [ ] `.github/workflows/ci.yml` is committed and pushed.
- [ ] The Actions tab shows a completed run with a green checkmark.
- [ ] If it was red, you read the log and fixed the cause (usually a missing dep), then
      re-ran to green.

## Deployed (pick at least one)

- [ ] **Streamlit demo** live on Hugging Face Spaces or Streamlit Community Cloud, public
      URL opens and the Extract button returns JSON.
- [ ] **FastAPI service** live on Render / Hugging Face Spaces (Docker) / Cloud Run:
      `curl https://YOUR-URL/health` returns `{"status":"ok"}` and `/docs` loads.
- [ ] Deploy URL added to the README so a recruiter can click it.

## Repo pinned

- [ ] `structured-data-extractor` is pinned on your GitHub profile so it shows up first.

When every box is ticked, the project is done and presentable. Send the repo link (and the
live URL) with confidence.
