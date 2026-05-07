from datetime import datetime, timedelta, date

from extensions import db
from models import Company, Conversation, Interview, Job, Tag


def test_dashboard_renders(client):
    rv = client.get("/")
    assert rv.status_code == 200
    assert b"Interview Tracker" in rv.data


def test_jobs_list_empty(client):
    rv = client.get("/jobs")
    assert rv.status_code == 200


def test_create_company_then_job_via_routes(app, client):
    rv = client.post(
        "/companies/new",
        data={"name": "Acme"},
        follow_redirects=True,
    )
    assert rv.status_code == 200

    company = Company.query.filter_by(name="Acme").first()
    assert company is not None

    tag = Tag(name="remote", color="#0ea5e9")
    db.session.add(tag)
    db.session.commit()

    rv = client.post(
        "/jobs/new",
        data={
            "company_id": str(company.id),
            "title": "Senior Engineer",
            "status": "interested",
            "rating": "5",
            "tag_ids": [str(tag.id)],
            "application_deadline": (date.today() + timedelta(days=7)).isoformat(),
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    job = Job.query.first()
    assert job.title == "Senior Engineer"
    assert job.rating == 5
    assert job.tags[0].name == "remote"


def test_pipeline_renders(client):
    rv = client.get("/jobs/pipeline")
    assert rv.status_code == 200
    assert b"Interested" in rv.data


def test_calendar_events_endpoint(app, client):
    company = Company(name="Acme")
    db.session.add(company)
    db.session.flush()
    job = Job(
        company_id=company.id,
        title="Eng",
        application_deadline=date.today() + timedelta(days=2),
    )
    db.session.add(job)
    db.session.flush()
    db.session.add(
        Interview(
            job_id=job.id,
            scheduled_at=datetime.utcnow() + timedelta(days=1),
            duration_minutes=45,
            round_name="Phone",
        )
    )
    db.session.add(
        Conversation(
            job_id=job.id,
            occurred_at=datetime.utcnow(),
            channel="email",
            follow_up_date=date.today() + timedelta(days=3),
        )
    )
    db.session.commit()

    start = (datetime.utcnow() - timedelta(days=30)).isoformat()
    end = (datetime.utcnow() + timedelta(days=30)).isoformat()
    rv = client.get(f"/api/calendar/events?start={start}&end={end}")
    assert rv.status_code == 200
    data = rv.get_json()
    types = {item["extendedProps"]["type"] for item in data}
    assert types == {"interview", "deadline", "followup"}


def test_calendar_page_renders(client):
    rv = client.get("/calendar")
    assert rv.status_code == 200
    assert b"FullCalendar" in rv.data or b"calendar" in rv.data
