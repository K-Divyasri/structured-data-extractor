"""A one-page Streamlit UI for the extractor -- the easy free demo.

The FastAPI service (extractor/api.py) is the "real" deliverable, but an API is
awkward to show a recruiter: they'd have to run curl. This little Streamlit page
gives you a public URL where anyone can paste resume text and watch it turn into
clean JSON. It reuses the exact same library functions as the API and the CLI --
nothing is re-implemented here.

Run it locally:

    streamlit run web_app.py

Deploy it free on Hugging Face Spaces or Streamlit Community Cloud (see
../hosting/HOSTING_GUIDE.md). It defaults to OFFLINE mode so it costs nothing and
needs no key even when hosted.
"""

from __future__ import annotations

import streamlit as st

from extractor import database as db
from extractor.extract import extract

SAMPLE = """\
Priya Sharma
Senior Data Engineer
Email: priya.sharma@example.com
Phone: +44 7911 123456
Location: London, UK

Summary
Data engineer with 7 years of experience building pipelines.

Skills: Python, SQL, Apache Spark, Airflow, dbt, AWS, Docker, Kafka

Education
BSc Computer Science, University of Manchester, 2017
"""


def main() -> None:
    st.set_page_config(page_title="Structured Data Extractor", page_icon="📄")
    st.title("📄 Structured Data Extractor")
    st.caption("Paste a resume. Get validated JSON. Store it. Runs offline, no API key.")

    text = st.text_area("Resume text", value=SAMPLE, height=320)
    col1, col2 = st.columns(2)
    do_save = col1.checkbox("Save to database", value=False)

    if col2.button("Extract", type="primary"):
        if not text.strip():
            st.error("Paste some resume text first.")
            return
        try:
            resume = extract(text)  # offline, deterministic
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not extract a valid record: {exc}")
            return

        st.subheader("Extracted record")
        st.json(resume.model_dump())

        if do_save:
            conn = db.connect("resumes.db")
            new_id = db.save_resume(conn, resume, source="web")
            st.success(f"Saved as row #{new_id} ({db.count(conn)} total in the database).")


if __name__ == "__main__":
    main()
