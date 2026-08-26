"""A tiny FastAPI service around the extractor.

This is the stretch goal from the spec: "a small FastAPI endpoint that accepts
text and returns JSON." It turns the library into a *service* other programs (or
a front-end, or `curl`) can call over HTTP.

Endpoints:

    GET  /            a friendly hello + a pointer to the docs
    GET  /health      returns {"status": "ok"} -- what a load balancer pings
    POST /extract     body: {"text": "...", "save": true}  ->  the extracted Resume
    GET  /resumes     every resume saved so far
    GET  /resumes/{id}  one saved resume

Two things worth calling out because they're the reason to use FastAPI at all:

  1. The request and response bodies are pydantic models, so FastAPI validates
     incoming JSON for us and rejects a malformed request with a clear 422 error
     before our code even runs.
  2. FastAPI reads those same models to generate interactive API docs at /docs.
     Start the server and open http://127.0.0.1:8000/docs -- you get a form to try
     every endpoint from the browser, for free.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import __version__
from . import database as db
from .extract import extract
from .schema import Resume

# Where the API stores resumes. Overridable via env var so tests can point it at
# a temp file and the real deploy can point it at a mounted volume.
DB_PATH = os.environ.get("EXTRACTOR_DB", "resumes.db")


class ExtractRequest(BaseModel):
    """The body you POST to /extract."""

    text: str = Field(min_length=1, description="Raw resume text to parse.")
    save: bool = Field(default=True, description="Also store the result in the DB.")
    real: bool = Field(
        default=False,
        description="Use a real LLM (needs an API key) instead of the offline extractor.",
    )


class ExtractResponse(BaseModel):
    """What /extract sends back: the parsed resume plus its DB id (if saved)."""

    id: Optional[int] = None
    resume: Resume


def create_app(db_path: str | Path = DB_PATH) -> FastAPI:
    """Build the FastAPI app.

    Written as a factory (a function that returns the app) so a test can create a
    fresh app pointed at a throwaway database. The connection is opened once and
    reused; SQLite with check_same_thread=False is fine for this single-process
    demo (a bigger service would use a connection pool).
    """
    app = FastAPI(
        title="Structured Data Extractor",
        version=__version__,
        description="Turn messy resume text into validated JSON and store it.",
    )
    conn = db.connect_shared(db_path)

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "service": "structured-data-extractor",
            "version": __version__,
            "docs": "/docs",
            "try": "POST /extract with a JSON body {\"text\": \"...\"}",
        }

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/extract", response_model=ExtractResponse)
    def do_extract(req: ExtractRequest) -> ExtractResponse:
        try:
            resume = extract(req.text, real=req.real)
        except Exception as exc:  # extraction/validation failure -> 422
            raise HTTPException(status_code=422, detail=f"Could not extract: {exc}") from exc
        new_id = db.save_resume(conn, resume, source="api") if req.save else None
        return ExtractResponse(id=new_id, resume=resume)

    @app.get("/resumes")
    def list_resumes() -> list[dict]:
        return db.get_all(conn)

    @app.get("/resumes/{resume_id}")
    def one_resume(resume_id: int) -> dict:
        row = db.get_by_id(conn, resume_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"No resume with id {resume_id}")
        return row

    return app


# The module-level app uvicorn runs in production: `uvicorn extractor.api:app`.
app = create_app()
