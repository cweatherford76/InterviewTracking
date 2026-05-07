from datetime import datetime, time, timedelta

from flask import Blueprint, jsonify, render_template, request, url_for

from models import Conversation, Interview, Job

bp = Blueprint("calendar", __name__)


STATUS_COLOR = {
    "scheduled": "#0d6efd",
    "completed": "#198754",
    "cancelled": "#6c757d",
    "rescheduled": "#fd7e14",
}


@bp.route("/calendar")
def index():
    return render_template("calendar/index.html")


@bp.route("/api/calendar/events")
def events():
    start = request.args.get("start")
    end = request.args.get("end")
    try:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00")) if start else None
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00")) if end else None
    except (ValueError, AttributeError):
        start_dt = end_dt = None

    interviews_q = Interview.query
    if start_dt:
        interviews_q = interviews_q.filter(Interview.scheduled_at >= start_dt.replace(tzinfo=None))
    if end_dt:
        interviews_q = interviews_q.filter(Interview.scheduled_at <= end_dt.replace(tzinfo=None))

    out = []
    for iv in interviews_q.all():
        end_at = iv.scheduled_at + timedelta(minutes=iv.duration_minutes or 60)
        out.append(
            {
                "id": f"interview-{iv.id}",
                "title": f"{iv.round_name or 'Interview'} — {iv.job.title}",
                "start": iv.scheduled_at.isoformat(),
                "end": end_at.isoformat(),
                "url": url_for("interviews.detail", interview_id=iv.id),
                "color": STATUS_COLOR.get(iv.status, "#0d6efd"),
                "extendedProps": {
                    "type": "interview",
                    "interview_id": iv.id,
                    "status": iv.status,
                },
            }
        )

    deadlines_q = Job.query.filter(Job.application_deadline.isnot(None))
    if start_dt:
        deadlines_q = deadlines_q.filter(Job.application_deadline >= start_dt.date())
    if end_dt:
        deadlines_q = deadlines_q.filter(Job.application_deadline <= end_dt.date())
    for j in deadlines_q.all():
        out.append(
            {
                "id": f"deadline-{j.id}",
                "title": f"Deadline: {j.title}",
                "start": j.application_deadline.isoformat(),
                "allDay": True,
                "url": url_for("jobs.detail", job_id=j.id),
                "color": "#dc3545",
                "extendedProps": {"type": "deadline", "job_id": j.id},
            }
        )

    follow_q = Conversation.query.filter(Conversation.follow_up_date.isnot(None))
    if start_dt:
        follow_q = follow_q.filter(Conversation.follow_up_date >= start_dt.date())
    if end_dt:
        follow_q = follow_q.filter(Conversation.follow_up_date <= end_dt.date())
    for c in follow_q.all():
        out.append(
            {
                "id": f"followup-{c.id}",
                "title": f"Follow-up: {c.job.title}",
                "start": c.follow_up_date.isoformat(),
                "allDay": True,
                "url": url_for("jobs.detail", job_id=c.job_id),
                "color": "#ffc107",
                "textColor": "#000",
                "extendedProps": {"type": "followup", "conversation_id": c.id},
            }
        )

    return jsonify(out)
