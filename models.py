from datetime import datetime, timezone

from sqlalchemy import Index
from sqlalchemy.orm import relationship

from extensions import db


def utcnow():
    return datetime.now(timezone.utc)


JOB_STATUSES = [
    ("interested", "Interested"),
    ("applied", "Applied"),
    ("interviewing", "Interviewing"),
    ("offer", "Offer"),
    ("rejected", "Rejected"),
    ("withdrawn", "Withdrawn"),
]
JOB_STATUS_VALUES = [s[0] for s in JOB_STATUSES]

REMOTE_TYPES = [("remote", "Remote"), ("hybrid", "Hybrid"), ("onsite", "On-site")]

INTERVIEW_FORMATS = [("phone", "Phone"), ("video", "Video"), ("onsite", "On-site")]

INTERVIEW_STATUSES = [
    ("scheduled", "Scheduled"),
    ("completed", "Completed"),
    ("cancelled", "Cancelled"),
    ("rescheduled", "Rescheduled"),
]

CONVERSATION_CHANNELS = [
    ("email", "Email"),
    ("phone", "Phone"),
    ("message", "Message"),
    ("other", "Other"),
]


class Company(db.Model):
    __tablename__ = "company"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    website = db.Column(db.String(500))
    industry = db.Column(db.String(120))
    size = db.Column(db.String(60))
    headquarters = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    jobs = relationship("Job", back_populates="company", cascade="all, delete-orphan")
    contacts = relationship(
        "Contact", back_populates="company", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Company {self.name}>"


class Contact(db.Model):
    __tablename__ = "contact"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(200))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(60))
    linkedin_url = db.Column(db.String(500))
    notes = db.Column(db.Text)

    company = relationship("Company", back_populates="contacts")
    conversations = relationship("Conversation", back_populates="contact")
    interview_participations = relationship(
        "InterviewParticipant", back_populates="contact"
    )

    def __repr__(self):
        return f"<Contact {self.name}>"


class Tag(db.Model):
    __tablename__ = "tag"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    color = db.Column(db.String(20), default="#6c757d")

    def __repr__(self):
        return f"<Tag {self.name}>"


job_tags = db.Table(
    "job_tag",
    db.Column("job_id", db.Integer, db.ForeignKey("job.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)


class Job(db.Model):
    __tablename__ = "job"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)

    title = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200))
    remote_type = db.Column(db.String(20))  # remote / hybrid / onsite

    job_post_url = db.Column(db.String(1000))
    local_folder_path = db.Column(db.String(1000))

    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    salary_notes = db.Column(db.String(300))

    description = db.Column(db.Text)
    source = db.Column(db.String(120))

    application_date = db.Column(db.Date)
    application_method = db.Column(db.String(120))
    application_deadline = db.Column(db.Date)

    status = db.Column(db.String(20), default="interested", nullable=False)
    rating = db.Column(db.Integer)  # 1-5

    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    company = relationship("Company", back_populates="jobs")
    tags = relationship("Tag", secondary=job_tags, backref="jobs")
    conversations = relationship(
        "Conversation",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="Conversation.occurred_at.desc()",
    )
    interviews = relationship(
        "Interview",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="Interview.scheduled_at",
    )

    __table_args__ = (
        Index("ix_job_status", "status"),
        Index("ix_job_company_id", "company_id"),
        Index("ix_job_application_deadline", "application_deadline"),
    )

    def __repr__(self):
        return f"<Job {self.title} @ company={self.company_id}>"

    @property
    def status_label(self):
        return dict(JOB_STATUSES).get(self.status, self.status)


class Conversation(db.Model):
    __tablename__ = "conversation"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey("contact.id"), nullable=True)

    occurred_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    channel = db.Column(db.String(20), default="email", nullable=False)
    subject = db.Column(db.String(300))
    notes = db.Column(db.Text)
    follow_up_date = db.Column(db.Date)

    job = relationship("Job", back_populates="conversations")
    contact = relationship("Contact", back_populates="conversations")

    __table_args__ = (Index("ix_conversation_follow_up_date", "follow_up_date"),)

    def __repr__(self):
        return f"<Conversation {self.id} job={self.job_id}>"


class Interview(db.Model):
    __tablename__ = "interview"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)

    scheduled_at = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    round_name = db.Column(db.String(120))
    format = db.Column(db.String(20), default="video")
    location_or_link = db.Column(db.String(500))

    status = db.Column(db.String(20), default="scheduled", nullable=False)
    preparation_notes = db.Column(db.Text)
    outcome_notes = db.Column(db.Text)
    overall_impression = db.Column(db.Integer)  # 1-5

    job = relationship("Job", back_populates="interviews")
    participants = relationship(
        "InterviewParticipant",
        back_populates="interview",
        cascade="all, delete-orphan",
    )
    questions = relationship(
        "InterviewQuestion",
        back_populates="interview",
        cascade="all, delete-orphan",
        order_by="InterviewQuestion.position",
    )

    __table_args__ = (Index("ix_interview_scheduled_at", "scheduled_at"),)

    def __repr__(self):
        return f"<Interview {self.id} job={self.job_id}>"


class InterviewParticipant(db.Model):
    __tablename__ = "interview_participant"

    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(
        db.Integer, db.ForeignKey("interview.id"), nullable=False
    )
    contact_id = db.Column(db.Integer, db.ForeignKey("contact.id"), nullable=True)

    name = db.Column(db.String(200))
    title = db.Column(db.String(200))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(60))
    role = db.Column(db.String(120))

    interview = relationship("Interview", back_populates="participants")
    contact = relationship("Contact", back_populates="interview_participations")

    @property
    def display_name(self):
        if self.contact and self.contact.name:
            return self.contact.name
        return self.name or "(unnamed)"

    @property
    def display_title(self):
        if self.contact and self.contact.title:
            return self.contact.title
        return self.title

    @property
    def display_email(self):
        if self.contact and self.contact.email:
            return self.contact.email
        return self.email

    @property
    def display_phone(self):
        if self.contact and self.contact.phone:
            return self.contact.phone
        return self.phone


class InterviewQuestion(db.Model):
    __tablename__ = "interview_question"

    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(
        db.Integer, db.ForeignKey("interview.id"), nullable=False
    )
    position = db.Column(db.Integer, default=0, nullable=False)
    question = db.Column(db.Text, nullable=False)
    my_answer = db.Column(db.Text)
    notes = db.Column(db.Text)
    was_difficult = db.Column(db.Boolean, default=False, nullable=False)

    interview = relationship("Interview", back_populates="questions")
