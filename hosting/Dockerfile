# Dockerfile for the Structured Data Extractor FastAPI service.
#
# IMPORTANT: build this with the build context set to the repo root, NOT
# `hosting/`. The repo root is the folder you push to GitHub and the one
# that holds `extractor/`, `requirements.txt`, `web_app.py`, etc.
#
#   docker build -f hosting/Dockerfile -t extractor .
#   docker run -p 8000:8000 extractor
#
# Then open http://127.0.0.1:8000/docs
#
# The image runs the API offline by default (no API key, no cost). Set
# GEMINI_API_KEY only if you plan to call POST /extract with {"real": true}.

FROM python:3.12-slim

# Keep Python from writing .pyc files and make logs show up immediately.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install dependencies first so Docker can cache this layer. Only requirements.txt
# changing busts the cache -- editing your Python code does not re-run pip.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the app (the `extractor` package, web_app.py, data, etc.).
COPY . .

# Run as a non-root user. If anything ever goes wrong inside the container, the
# process has no more power than it needs. Give it ownership of /app so SQLite
# can create resumes.db at runtime.
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# Document the port. The real port is whatever the platform sets via $PORT.
EXPOSE 8000

# Exec form (JSON array) so uvicorn is PID 1 and receives stop signals cleanly.
# We need $PORT expanded at runtime, so we go through sh -c. Render, Cloud Run,
# and Hugging Face Spaces all inject $PORT; the default above covers local runs.
CMD ["sh", "-c", "uvicorn extractor.api:app --host 0.0.0.0 --port ${PORT}"]
