from datetime import datetime, timedelta, date

from extensions import db
from models import (
    Company,
    Contact,
    Conversation,
    Interview,
    InterviewParticipant,
    InterviewQuestion,
    Job,
    Tag,
)


def test_full_flow(app):
    """Create company → job → tag → interview with 2 questions → conversation w/ follow-up."""
    company = Company(name="Acme")
    db.session.add(company)
    db.session.flush()

    tag = Tag(name="remote", color="#0ea5e9")
    db.session.add(tag)

    job = Job(
        company_id=company.id,
        title="Senior Engineer",
        status="interviewing",
        rating=5,
        application_deadline=date.today() + timedelta(days=10),
        tags=[tag],
    )
    db.session.add(job)
    db.session.flush()

    iv = Interview(
        job_id=job.id,
        scheduled_at=datetime.utcnow() + timedelta(days=1),
        duration_minutes=45,
        round_name="Tech Screen",
        format="video",
    )
    db.session.add(iv)
    db.session.flush()

    contact = Contact(name="Alice", company_id=company.id, email="alice@acme.test")
    db.session.add(contact)
    db.session.flush()

    db.session.add_all(
        [
            InterviewParticipant(
                interview_id=iv.id, contact_id=contact.id, role="Hiring Manager"
            ),
            InterviewParticipant(
                interview_id=iv.id, name="Bob", title="Engineer", role="Interviewer"
            ),
            InterviewQuestion(
                interview_id=iv.id, position=0, question="Walk me through your CV."
            ),
            InterviewQuestion(
                interview_id=iv.id,
                position=1,
                question="Design a URL shortener.",
                my_answer="Discussed sharding by hash prefix.",
                was_difficult=True,
            ),
        ]
    )

    db.session.add(
        Conversation(
            job_id=job.id,
            contact_id=contact.id,
            occurred_at=datetime.utcnow(),
            channel="email",
            subject="Initial outreach",
            follow_up_date=date.today() + timedelta(days=3),
        )
    )
    db.session.commit()

    fetched = Job.query.first()
    assert fetched.title == "Senior Engineer"
    assert fetched.tags[0].name == "remote"
    assert len(fetched.interviews) == 1
    assert len(fetched.interviews[0].questions) == 2
    assert len(fetched.interviews[0].participants) == 2
    assert fetched.interviews[0].participants[0].display_name == "Alice"
    assert fetched.interviews[0].participants[1].display_name == "Bob"
    assert fetched.conversations[0].follow_up_date == date.today() + timedelta(days=3)


def test_cascade_delete_job_removes_interviews_and_conversations(app):
    company = Company(name="Acme")
    db.session.add(company)
    db.session.flush()
    job = Job(company_id=company.id, title="X")
    db.session.add(job)
    db.session.flush()
    db.session.add(
        Interview(
            job_id=job.id,
            scheduled_at=datetime.utcnow(),
            duration_minutes=30,
            round_name="X",
        )
    )
    db.session.add(
        Conversation(job_id=job.id, occurred_at=datetime.utcnow(), channel="email")
    )
    db.session.commit()

    db.session.delete(job)
    db.session.commit()

    assert Interview.query.count() == 0
    assert Conversation.query.count() == 0
