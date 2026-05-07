# Interview Tracker

A locally hosted web app for tracking your job search end-to-end: postings of interest, applications, conversations, multiple interview rounds, company details, ratings, tags, and a calendar of past/upcoming events.

Designed for **single-user, local use**. Your data lives in a single SQLite file next to the app — easy to back up, easy to move.

## Features

- **Job postings** — title, company, location, remote type, salary range, links to the original post and a local folder of related files
- **Companies & contacts** — track companies you're interested in and the people you've spoken to
- **Application tracking** — when, where, how you applied; deadlines; source
- **Conversations** — log emails, calls, and messages with optional follow-up dates
- **Interviews** — multiple rounds per job, with interviewers, questions asked, your answers, prep notes, and post-interview impressions
- **Status pipeline** — Interested → Applied → Interviewing → Offer / Rejected / Withdrawn (Kanban view)
- **Tags / labels** — free-form labels for filtering (e.g. `remote`, `backend`, `dream-job`)
- **Ratings** — 1–5 rating per job and per interview
- **Calendar** — month / week / day views showing interviews, application deadlines, and follow-ups; drag to reschedule interviews
- **List & filter views** — search and filter jobs by status, tag, company, or text

## Tech Stack

- **Backend:** Python 3.11+, Flask, Flask-SQLAlchemy, Flask-Migrate (Alembic)
- **Database:** SQLite (single file, no server)
- **Frontend:** Jinja2 templates + HTMX for interactivity, Bootstrap 5 for styling
- **Calendar:** FullCalendar 6
- **No build step** — run it with one command

## Quick Start

```bash
# 1. Create a virtualenv and install deps
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Initialize the database
flask --app app db upgrade

# 3. (Optional) Seed sample data so you can poke around
python seed.py

# 4. Run the app
flask --app app run --debug
# Open http://127.0.0.1:5000
```

## Project Layout

```
.
├── app.py                  # Flask app factory + entrypoint
├── config.py               # DB path, secret key
├── extensions.py           # db, migrate
├── models.py               # SQLAlchemy models
├── seed.py                 # optional sample data
├── requirements.txt
├── blueprints/             # route modules (jobs, interviews, calendar, ...)
├── templates/              # Jinja2 templates
├── static/                 # css, js (htmx vendored), favicon
├── migrations/             # Alembic migrations
└── tests/                  # pytest smoke tests
```

## Backup

The entire database is one file: `interview_tracker.db`. To back up: stop the app, copy the file. To restore: replace the file.

## Documentation

- [PRD.md](./PRD.md) — full product requirements, data model, and scope

## License

Personal-use project. No license specified.
