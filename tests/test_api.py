"""Tests for the FastAPI service, driven through TestClient (no real network)."""

from __future__ import annotations


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_extract_endpoint_saves_and_returns(client, priya_text):
    resp = client.post("/extract", json={"text": priya_text})
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == 1
    assert body["resume"]["name"] == "Priya Sharma"
    assert "Python" in body["resume"]["skills"]


def test_extract_without_saving(client, marcus_text):
    resp = client.post("/extract", json={"text": marcus_text, "save": False})
    assert resp.status_code == 200
    assert resp.json()["id"] is None
    # And nothing was stored.
    assert client.get("/resumes").json() == []


def test_list_and_get_one(client, priya_text, marcus_text):
    client.post("/extract", json={"text": priya_text})
    client.post("/extract", json={"text": marcus_text})
    listing = client.get("/resumes").json()
    assert len(listing) == 2

    one = client.get("/resumes/1").json()
    assert one["name"] == "Priya Sharma"


def test_get_missing_resume_404(client):
    assert client.get("/resumes/999").status_code == 404


def test_empty_text_is_rejected_422(client):
    # min_length=1 on the request model -> FastAPI rejects before our code runs.
    assert client.post("/extract", json={"text": ""}).status_code == 422
