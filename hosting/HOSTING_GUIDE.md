# Publishing the Structured Data Extractor

This project is two things at once, and that shapes how you host it.

- A **FastAPI service** (`extractor/api.py`) — the real deliverable. It has a `/extract`
  endpoint, interactive docs, and a database behind it. This is the thing that says "I can
  build a backend."
- A **Streamlit demo** (`web_app.py`) — a one-page website where anyone can paste resume
  text and watch it turn into JSON. It reuses the exact same library. This is the thing a
  recruiter can *click* without touching a terminal.

You'll put the code on GitHub first (with tests running automatically), then pick a free
host for one or both. Everything here runs **offline by default** — the deterministic
extractor needs no API key — so a public deploy costs nothing. The optional `--real` /
`{"real": true}` path uses an LLM, and only then do you need a key.

A note on layout before you start: this repo publishes the **whole project folder**
(`05-structured-data-extractor/`), with `build_from_scratch/` as a subfolder. That way your
GitHub page shows the learning material *and* the polished package. The commands below run
from the **project root** unless they say otherwise.

---

## Step 0 — Install Git and make a GitHub account

Git tracks versions of your files on your laptop. GitHub is the website that stores a copy
online. Different things: Git is local, GitHub lives on the internet. You need both.

### Install Git

1. Go to https://git-scm.com/download/win. The download starts on its own.
2. Run the installer. Click Next through every screen — the defaults are fine.
3. Open a **new** PowerShell window (new, so it picks up the install) and check:

```powershell
git --version
```

If you see something like `git version 2.45.0`, you're set. If PowerShell doesn't recognize
`git`, close every terminal, open a fresh one, and try again.

### Make a GitHub account

1. Go to https://github.com and sign up (use `mathuransada@gmail.com`, the one on file).
   Verify the email.
2. Pick a username you'd put on a CV — recruiters see it. `divya-dev` beats `xX_coder_Xx`.

### Tell Git who you are (once per machine)

```powershell
git config --global user.name "Your Name"
git config --global user.email "mathuransada@gmail.com"
```

---

## Step 1 — Know what must NOT go in the repo

Two files must never leave your laptop, and the shipped `.gitignore` already blocks both:

- **`.env`** — if you ever use `--real`, this holds your `GEMINI_API_KEY`. A key is a
  password. Commit it and it's on the public internet **forever** (Git keeps history; bots
  scrape GitHub within minutes and run up a bill on your account). The repo ships
  `.env.example` instead — variable names with blank values, safe to commit.
- **`*.db`** — the SQLite files the tool creates at runtime (`resumes.db`). That's output,
  not source. It's regenerated whenever the tool runs. No reason to publish it.

Open `build_from_scratch/.gitignore` and confirm it lists at least `.env`, `*.db`,
`__pycache__/`, and `.venv/`. It does — but check, because this is the part that bites
people. The rule: **source, config, docs, and sample data go in; secrets, databases, and
machine junk stay out.**

---

## Step 2 — Make the local repo and commit

From the **project root** (`05-structured-data-extractor/`, the folder with
`build_from_scratch/` and `generate_data.py` in it):

```powershell
git init
git add .
git commit -m "Initial commit: Structured Data Extractor (resume text -> validated JSON -> SQLite -> FastAPI)"
```

`git init` creates the hidden `.git` folder. `git add .` stages everything except what
`.gitignore` excludes. `git commit` saves the snapshot.

Now the single most important check in this guide:

```powershell
git status
git ls-files | Select-String "\.env|\.db"
```

The second command should print **only** `.env.example` (never `.env`), and **no** `.db`
file. If a `.env` or a `resumes.db` shows up as tracked, you committed something you
shouldn't — fix it with the troubleshooting section at the bottom before you push.

---

## Step 3 — Create the empty repo on GitHub and push

1. On github.com (signed in), top-right **+** then **New repository**.
2. Name it `structured-data-extractor` (lowercase, hyphens).
3. Description: *"Turn messy resume text into validated JSON, store it in SQLite, and serve
   it over a FastAPI endpoint. Runs offline, no API key."*
4. Leave it **Public**.
5. Do **not** tick "Add a README", ".gitignore", or "license" — the repo must be empty or
   your first push collides.
6. **Create repository.**

Then, back in PowerShell at the project root:

```powershell
git branch -M main
git remote add origin https://github.com/YOURNAME/structured-data-extractor.git
git push -u origin main
```

The first push opens a browser sign-in to authenticate. Do it. GitHub turned off terminal
passwords years ago — use the browser sign-in (easiest) or a Personal Access Token as the
password (troubleshooting below). Refresh the repo page; your code is live.

---

## Step 4 — Add CI so the tests run on every push

CI (Continuous Integration) proves your tests pass on a clean machine, not just your laptop,
every time you push. Green checkmark = recruiters notice, and it catches the classic "works
on my machine" bug. This project's suite is **offline and keyless**, so CI never needs a
secret and never costs anything.

There's a ready workflow in this folder at `hosting/github_actions/ci.yml`. It only runs if
it lives at `.github/workflows/` in the repo. From the project root:

```powershell
mkdir .github\workflows
copy hosting\github_actions\ci.yml .github\workflows\ci.yml
git add .github\workflows\ci.yml
git commit -m "Add GitHub Actions CI (offline pytest on every push)"
git push
```

Open the repo's **Actions** tab and watch it run: checkout, install Python 3.12, install
`build_from_scratch/requirements-dev.txt`, run `pytest` from `build_from_scratch/`. Green
means all 27 tests passed on GitHub's machine. If it's red, click the failed step and read
the log bottom-up — the real error is in the last few lines.

Once green, grab a status badge (Actions page → `...` → **Create status badge**) and paste
the markdown at the top of `build_from_scratch/README.md`.

---

## Path A — the Streamlit demo (easiest public URL)

`web_app.py` is the fastest way to get a link you can send someone. It runs offline, so it
needs no key and costs nothing. Two good free hosts — pick one.

### A1. Streamlit Community Cloud

1. Go to https://share.streamlit.io and sign in with GitHub.
2. **New app** → pick your `structured-data-extractor` repo and the `main` branch.
3. **Main file path:** `build_from_scratch/web_app.py`.
4. Advanced settings → set the Python version to 3.12 if offered. Streamlit reads
   dependencies from `build_from_scratch/requirements.txt` automatically.
5. **Deploy.** First build takes a couple of minutes. You get a
   `https://YOURNAME-....streamlit.app` URL.

If Streamlit can't find the package, it's almost always the main-file path — it must point
inside `build_from_scratch/` so `from extractor... import` resolves.

### A2. Hugging Face Spaces (Streamlit SDK)

1. Go to https://huggingface.co/spaces → **Create new Space**.
2. Name it, choose **Streamlit** as the SDK, keep it **Public**, pick the free CPU tier.
3. Easiest path: in the Space's **Files** tab, upload `web_app.py`, the `extractor/` folder,
   `requirements.txt`, and the `data/` folder from `build_from_scratch/`. Spaces expects the
   app entry file at the Space root, so `web_app.py` and `extractor/` sit at the top level.
4. Spaces installs `requirements.txt` and launches Streamlit automatically. The build log is
   on the Space page; when it finishes you have a public URL.

Either way, the demo defaults to offline mode — no secret needed. Done: you have a link.

---

## Path B — the FastAPI service via Docker

The API is the deliverable that shows real backend skills. All three hosts below run the
same Docker image. The image is defined in `hosting/Dockerfile`, and its **build context is
`build_from_scratch/`** (that's where `extractor/` and `requirements.txt` live). The start
command every host runs is:

```
uvicorn extractor.api:app --host 0.0.0.0 --port $PORT
```

You do **not** hardcode the port. The host injects `$PORT`; the Dockerfile's `CMD` reads it
(defaulting to 8000 for local runs). `--host 0.0.0.0` makes the server listen on all
interfaces, which is required inside a container — `127.0.0.1` would only be reachable from
inside the box and the host's health check would fail.

### Build and test the image locally first

```powershell
cd build_from_scratch
docker build -f ..\hosting\Dockerfile -t extractor .
docker run -p 8000:8000 extractor
```

Open http://127.0.0.1:8000/docs. If that works locally, it'll work on the host.

### B1. Render (free web service)

1. Push your repo to GitHub (Steps 2–3) if you haven't.
2. https://render.com → sign in with GitHub → **New** → **Web Service** → pick the repo.
3. Render detects the Dockerfile. Set **Root Directory** to `build_from_scratch` and
   **Dockerfile Path** to `../hosting/Dockerfile` (so the build context is
   `build_from_scratch/`, matching the local build above).
4. Instance type: **Free**. Render sets `$PORT` for you — leave the start command as the
   Dockerfile's `CMD`.
5. **Create Web Service.** First build takes a few minutes; you get a
   `https://your-service.onrender.com` URL.

Free Render services spin down after ~15 minutes idle and cold-start on the next request
(the first hit takes a few seconds). Fine for a portfolio.

### B2. Hugging Face Spaces (Docker SDK)

1. **Create new Space** → SDK **Docker** → free CPU tier → Public.
2. Put the `build_from_scratch/` contents at the Space root (so `extractor/`,
   `requirements.txt`, `web_app.py`, `data/` are top-level) and add the `Dockerfile` from
   `hosting/` at the root too.
3. Spaces expects the container to listen on **port 7860**. Either set an env var `PORT=7860`
   in the Space **Settings**, or just rely on the Dockerfile reading `$PORT`. Spaces sets it.
4. Push/upload; the Space builds the image and runs it. The `/docs` page loads at your Space
   URL once the build is green.

### B3. Google Cloud Run (free tier)

1. Install the gcloud CLI and run `gcloud init` (sign in, pick/create a project).
2. From `build_from_scratch/`, one command builds and deploys:

```powershell
gcloud run deploy extractor --source . --region us-central1 --allow-unauthenticated
```

   (`--source .` uses Cloud Build; it'll pick up a Dockerfile if present, so copy
   `hosting/Dockerfile` into `build_from_scratch/` first, or point Cloud Build at it.)
3. Cloud Run sets `$PORT` (usually 8080) and the container reads it. It prints an
   `https://extractor-....run.app` URL. Cloud Run's free tier covers a portfolio's traffic.

---

## Secrets — only if you enable `--real`

Offline mode (the default everywhere above) needs **no secret**. You only need a key if you
want the LLM path: the CLI's `--real` flag or `POST /extract` with `{"real": true}`. The key
is `GEMINI_API_KEY` (free from https://aistudio.google.com/apikey). It goes in each host's
Secrets UI — **never** in the repo.

- **Streamlit Community Cloud:** App → **Settings** → **Secrets**, add
  `GEMINI_API_KEY = "..."`. (The shipped `web_app.py` is offline-only, so you'd only need
  this if you extend it.)
- **Hugging Face Spaces:** Space → **Settings** → **Variables and secrets** → **New secret**,
  name `GEMINI_API_KEY`.
- **Render:** Service → **Environment** → **Add Environment Variable**, key `GEMINI_API_KEY`.
- **Cloud Run:** add `--set-env-vars GEMINI_API_KEY=...` to the deploy command, or set it in
  the console under the service's **Variables**.

The app reads it from the environment via `python-dotenv`; you never write it into any file
that's committed. Optionally set `EXTRACTOR_MODEL` the same way to switch models.

---

## A word on the database

The service stores resumes in **SQLite** — a single file (`resumes.db`) on the container's
disk. That's perfect for local runs and a demo, but on all these free hosts that disk is
**ephemeral**: when the container restarts (a redeploy, or a free-tier sleep/wake), the file
is wiped and your saved rows are gone. `/health` and `/extract` still work; only the
*persistence* resets.

For a real production app you'd point the same code at a managed Postgres — **Supabase** or
**Neon** both have generous free tiers and give you a durable database with a connection
string. The upgrade is conceptually small: swap the SQLite calls in `database.py` for a
Postgres driver and read the connection URL from an env var. Keep the default SQLite for this
project — it's the right choice for learning and for a demo, and naming the upgrade in your
README shows you know where the line is.

Set `EXTRACTOR_DB` (env var) if you want the SQLite file at a specific path — e.g. on a
mounted volume — but on free tiers it's still ephemeral.

---

## Verify the deploy

Once your FastAPI service is live, prove it from your laptop. Replace `YOUR-URL` with the
host's URL.

**Health check** (this is what the platform pings):

```powershell
curl https://YOUR-URL/health
```

Expect `{"status":"ok"}`.

**Extract a resume** (offline, don't save):

```powershell
curl -X POST https://YOUR-URL/extract `
  -H "Content-Type: application/json" `
  -d '{"text":"Priya Sharma\nSenior Data Engineer\nEmail: priya.sharma@example.com\nSkills: Python, SQL, Spark\n7 years of experience","save":false}'
```

You'll get back JSON with `resume.name` = `"Priya Sharma"` and the fields it could parse.

**Open the docs:** browse to `https://YOUR-URL/docs`. FastAPI's interactive page lets you try
every endpoint (`/`, `/health`, `/extract`, `/resumes`, `/resumes/{id}`) from the browser —
the easiest thing to screenshot for your README.

If `/health` works but `/extract` 422s, you sent an empty or malformed `text` field — the
schema requires at least one character. That's the validation doing its job.

---

## Troubleshooting (Git)

**You committed `.env` or a `.db` by accident.** For a key, treat it as compromised — go to
Google AI Studio and **rotate it** immediately (if you pushed, it's already public). Then
untrack the file (keeps it on disk):

```powershell
git rm --cached .env
git commit -m "Remove committed .env"
git push
```

`git rm --cached` only stops tracking it going forward — the old value still sits in Git
history, which is exactly why you rotate the key rather than trusting the delete.

**`error: failed to push` / push rejected.** The remote has commits yours doesn't — usually
because you let GitHub add a README/license. Replay your work on top:

```powershell
git pull origin main --rebase
git push
```

**Authentication fails on push.** GitHub won't accept your account password in the terminal.
Easiest fix: install the GitHub CLI from https://cli.github.com, run `gh auth login`, follow
the browser prompts. Or generate a Personal Access Token (Settings → Developer settings →
Tokens (classic), `repo` scope) and paste it as the password when prompted.

**`git: command not found` right after installing.** You're in a terminal opened before the
install. Close every PowerShell window and open a fresh one.
