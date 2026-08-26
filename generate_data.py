"""Write the sample resumes this project practises on.

Run this once, first:

    python generate_data.py

It drops six plain-text resumes into `data/resumes/`. They are deliberately
*messy and inconsistent* -- different layouts, different ways of writing a phone
number, a skills list here as bullet points and there as a comma-separated line,
one with a typo, one with no explicit "years of experience" at all. That mess is
the whole point: the job of this project is to turn text a human wrote however
they felt like into the same clean, validated JSON every time.

There is no randomness here. The files are hard-coded, so everyone who runs this
gets byte-for-byte the same resumes, and every notebook, lab and test can rely on
exact values. (That is why we don't use Faker or a random seed -- reproducibility
beats variety for a teaching dataset.)
"""

from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------- #
# Each resume is written in a different style on purpose. Read them and notice
# how differently humans present the SAME facts. Your extractor has to cope with
# all of it.
# --------------------------------------------------------------------------- #

RESUMES: dict[str, str] = {
    # 1. Clean, labelled, easy. The gentle one.
    "priya_sharma.txt": """\
Priya Sharma
Senior Data Engineer
Email: priya.sharma@example.com
Phone: +44 7911 123456
Location: London, UK

Summary
Data engineer with 7 years of experience building batch and streaming
pipelines. Comfortable owning a platform end to end.

Skills: Python, SQL, Apache Spark, Airflow, dbt, AWS, Docker, Kafka

Experience
Senior Data Engineer, Finch Analytics (2021 - present)
Data Engineer, Meridian Bank (2017 - 2021)

Education
BSc Computer Science, University of Manchester, 2017
""",
    # 2. Contact details jammed on one line, skills as bullets, "yrs" abbreviation.
    "marcus_lee.txt": """\
MARCUS LEE  |  marcus.lee23@example.com  |  (415) 555-0198  |  San Francisco, CA

Backend Software Engineer

5 yrs building APIs and services at scale.

Core skills
- Go
- Python
- PostgreSQL
- gRPC
- Kubernetes
- Redis

Work history
Software Engineer II @ Northwind (2020-2024)
Junior Software Engineer @ Dropbox (2019-2020)

Bachelor of Science in Software Engineering - San Jose State University
""",
    # 3. No "Skills" header at all; skills are buried in prose. No explicit years.
    "aisha_khan.txt": """\
Aisha Khan
aisha.khan@example.co.in
+91 98765 43210
Bangalore

I am a machine learning engineer who has shipped recommendation systems and
NLP features. Day to day I work in Python and PyTorch, deploy models with
FastAPI and Docker, and track experiments with MLflow. I also know my way
around scikit-learn and pandas.

Previously at Flipkart and a healthtech startup.

Education: M.Tech in Computer Science, IIT Bombay
""",
    # 4. A typo in the email label, phone written in words-ish, degree abbreviation.
    "tom_becker.txt": """\
Tom Becker
Emial: tom.becker@example.de
Tel: 030 1234567
Berlin, Germany

DevOps Engineer with over 9 years of experience.

Technologies I use: Terraform, Ansible, AWS, GCP, Jenkins, Prometheus,
Grafana, Bash, Python

Roles
- Lead DevOps Engineer, Zalando (2019-present)
- Systems Administrator, SAP (2015-2019)

B.Eng. Electrical Engineering, TU Munich
""",
    # 5. Very short, minimal. Only a name, an email and two skills.
    "sara_novak.txt": """\
Sara Novak
sara.novak@example.com

Frontend developer. 3 years experience.

React, TypeScript
""",
    # 6. All caps section headers, skills comma-separated with odd spacing, PhD.
    "daniel_owusu.txt": """\
DANIEL OWUSU
Research Scientist
daniel.owusu@example.com  //  +1 202 555 0147  //  Boston, MA

PROFILE
Research scientist, 12 years of experience in computer vision and applied ML.

SKILLS
Python ,  C++ , TensorFlow ,PyTorch, CUDA , OpenCV,  Linear Algebra

EDUCATION
PhD in Electrical Engineering, MIT, 2013
BSc in Physics, University of Ghana, 2008
""",
}


def main() -> None:
    out_dir = Path(__file__).parent / "data" / "resumes"
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, text in RESUMES.items():
        (out_dir / filename).write_text(text, encoding="utf-8")
    print(f"Wrote {len(RESUMES)} resumes to {out_dir}")
    for name in RESUMES:
        print(f"  - {name}")


if __name__ == "__main__":
    main()
