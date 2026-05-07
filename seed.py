"""Populate the database with sample data for kicking the tires."""
from datetime import datetime, timedelta, date

from app import app
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


def run():
    with app.app_context():
        db.create_all()

        if Company.query.count() > 0:
            print("Database already has data; skipping seed.")
            return

        acme = Company(
            name="Acme Robotics",
            website="https://acme.example.com",
            industry="Robotics",
            size="201-500",
            headquarters="Boston, MA",
            notes="Strong eng culture, lots of internal tooling.",
        )
        globex = Company(
            name="Globex",
            website="https://globex.example.com",
            industry="SaaS",
            size="51-200",
            headquarters="Remote",
            notes="Fully remote, async-first.",
        )
        db.session.add_all([acme, globex])
        db.session.flush()

        remote = Tag(name="remote", color="#0ea5e9")
        backend = Tag(name="backend", color="#7c3aed")
        dream = Tag(name="dream-job", color="#ef4444")
        db.session.add_all([remote, backend, dream])
        db.session.flush()

        alice = Contact(
            company_id=acme.id, name="Alice Chen", title="Engineering Manager",
            email="alice@acme.example.com", phone="555-0101",
        )
        bob = Contact(
            company_id=globex.id, name="Bob Patel", title="Recruiter",
            email="bob@globex.example.com",
        )
        db.session.add_all([alice, bob])
        db.session.flush()

        job1 = Job(
            company_id=acme.id,
            title="Senior Backend Engineer",
            location="Boston, MA",
            remote_type="hybrid",
            job_post_url="https://acme.example.com/careers/sbe",
            local_folder_path="/home/me/jobs/Acme",
            salary_min=170000,
            salary_max=210000,
            salary_notes="Plus equity + bonus",
            description="Build distributed control plane for robotic fleets.",
            source="LinkedIn",
            application_date=date.today() - timedelta(days=10),
            application_method="LinkedIn easy apply",
            application_deadline=date.today() + timedelta(days=14),
            status="interviewing",
            rating=5,
            tags=[backend, dream],
            notes="Recruiter very responsive. Strong fit for distributed systems experience.",
        )
        job2 = Job(
            company_id=globex.id,
            title="Staff Platform Engineer (Remote)",
            location="Remote",
            remote_type="remote",
            job_post_url="https://globex.example.com/jobs/staff-platform",
            salary_min=200000,
            salary_max=240000,
            description="Lead developer experience for the Globex SaaS platform.",
            source="Referral via friend",
            status="applied",
            rating=4,
            application_date=date.today() - timedelta(days=3),
            application_method="Referral",
            tags=[remote, backend],
        )
        job3 = Job(
            company_id=acme.id,
            title="Tech Lead, Simulation",
            location="Boston, MA",
            remote_type="onsite",
            status="interested",
            rating=3,
            tags=[backend],
            notes="Interesting role, need to learn more about the team.",
        )
        db.session.add_all([job1, job2, job3])
        db.session.flush()

        # Interview history for job1
        iv1 = Interview(
            job_id=job1.id,
            scheduled_at=datetime.utcnow() - timedelta(days=5, hours=2),
            duration_minutes=30,
            round_name="Recruiter Phone Screen",
            format="phone",
            status="completed",
            outcome_notes="Went well. Moving to technical screen.",
            overall_impression=4,
        )
        iv2 = Interview(
            job_id=job1.id,
            scheduled_at=datetime.utcnow() + timedelta(days=2, hours=3),
            duration_minutes=60,
            round_name="Technical Screen",
            format="video",
            location_or_link="https://meet.example.com/abc-defg-hij",
            status="scheduled",
            preparation_notes="Review Raft, leader election, time-bounded leases.",
        )
        db.session.add_all([iv1, iv2])
        db.session.flush()

        db.session.add_all([
            InterviewParticipant(
                interview_id=iv1.id, contact_id=alice.id, role="Hiring Manager"
            ),
            InterviewParticipant(
                interview_id=iv2.id, name="Carol Smith", title="Staff Engineer",
                email="carol@acme.example.com", role="Tech Interviewer",
            ),
            InterviewQuestion(
                interview_id=iv1.id, position=0,
                question="Tell me about your last project.",
                my_answer="Walked through the fleet orchestration service.",
            ),
            InterviewQuestion(
                interview_id=iv1.id, position=1,
                question="Why are you leaving your current role?",
                my_answer="Looking for more autonomy and ownership.",
                was_difficult=True,
            ),
        ])

        db.session.add(
            Conversation(
                job_id=job1.id, contact_id=alice.id,
                occurred_at=datetime.utcnow() - timedelta(days=8),
                channel="email",
                subject="Re: Application for SBE",
                notes="Alice replied confirming receipt and inviting to a call.",
                follow_up_date=date.today() + timedelta(days=3),
            )
        )
        db.session.add(
            Conversation(
                job_id=job2.id, contact_id=bob.id,
                occurred_at=datetime.utcnow() - timedelta(days=2),
                channel="phone",
                subject="Initial chat",
                notes="Bob walked through the process; expects 4 rounds.",
                follow_up_date=date.today() + timedelta(days=5),
            )
        )

        db.session.commit()
        print("Seeded 2 companies, 2 contacts, 3 tags, 3 jobs, 2 interviews, 2 conversations.")


if __name__ == "__main__":
    run()
