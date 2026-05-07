from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, render_template
from sqlalchemy import func

from extensions import db
from models import Conversation, Interview, Job, JOB_STATUSES

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    now = datetime.now(timezone.utc)
    week_out = now + timedelta(days=7)
    today = date.today()
    week_out_date = today + timedelta(days=7)

    upcoming_interviews = (
        Interview.query.filter(
            Interview.scheduled_at >= now,
            Interview.scheduled_at <= week_out,
            Interview.status == "scheduled",
        )
        .order_by(Interview.scheduled_at)
        .all()
    )

    follow_ups = (
        Conversation.query.filter(
            Conversation.follow_up_date.isnot(None),
            Conversation.follow_up_date <= week_out_date,
        )
        .order_by(Conversation.follow_up_date)
        .all()
    )

    status_counts_q = (
        db.session.query(Job.status, func.count(Job.id)).group_by(Job.status).all()
    )
    counts_by_status = dict(status_counts_q)
    status_counts = [
        (value, label, counts_by_status.get(value, 0))
        for value, label in JOB_STATUSES
    ]

    recent_jobs = Job.query.order_by(Job.updated_at.desc()).limit(8).all()

    return render_template(
        "dashboard.html",
        upcoming_interviews=upcoming_interviews,
        follow_ups=follow_ups,
        status_counts=status_counts,
        recent_jobs=recent_jobs,
        today=today,
    )
