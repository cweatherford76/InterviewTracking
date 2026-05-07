from datetime import datetime

from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from extensions import db
from models import (
    Contact,
    INTERVIEW_FORMATS,
    INTERVIEW_STATUSES,
    Interview,
    InterviewParticipant,
    InterviewQuestion,
    Job,
)

bp = Blueprint("interviews", __name__)


def _parse_dt(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M")


def _parse_int(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _form_to_interview(form, interview):
    scheduled_at = _parse_dt(form.get("scheduled_at"))
    if scheduled_at is None:
        raise ValueError("scheduled_at is required")
    interview.scheduled_at = scheduled_at
    interview.duration_minutes = _parse_int(form.get("duration_minutes")) or 60
    interview.round_name = form.get("round_name") or None
    interview.format = form.get("format") or "video"
    interview.location_or_link = form.get("location_or_link") or None
    interview.status = form.get("status") or "scheduled"
    interview.preparation_notes = form.get("preparation_notes") or None
    interview.outcome_notes = form.get("outcome_notes") or None
    interview.overall_impression = _parse_int(form.get("overall_impression"))


@bp.route("/jobs/<int:job_id>/interviews/new", methods=["GET", "POST"])
def new(job_id):
    job = Job.query.get_or_404(job_id)
    if request.method == "POST":
        interview = Interview(job_id=job.id, scheduled_at=datetime.utcnow())
        try:
            _form_to_interview(request.form, interview)
        except ValueError as e:
            flash(str(e), "danger")
            return redirect(url_for("interviews.new", job_id=job.id))
        db.session.add(interview)
        db.session.commit()
        flash("Interview created.", "success")
        return redirect(url_for("interviews.detail", interview_id=interview.id))
    return render_template(
        "interviews/form.html",
        job=job,
        interview=None,
        formats=INTERVIEW_FORMATS,
        statuses=INTERVIEW_STATUSES,
    )


@bp.route("/interviews/<int:interview_id>")
def detail(interview_id):
    interview = Interview.query.get_or_404(interview_id)
    return render_template(
        "interviews/detail.html",
        interview=interview,
        contacts=Contact.query.order_by(Contact.name).all(),
        formats=INTERVIEW_FORMATS,
        statuses=INTERVIEW_STATUSES,
    )


@bp.route("/interviews/<int:interview_id>/edit", methods=["GET", "POST"])
def edit(interview_id):
    interview = Interview.query.get_or_404(interview_id)
    if request.method == "POST":
        try:
            _form_to_interview(request.form, interview)
        except ValueError as e:
            flash(str(e), "danger")
            return redirect(url_for("interviews.edit", interview_id=interview.id))
        db.session.commit()
        flash("Interview updated.", "success")
        return redirect(url_for("interviews.detail", interview_id=interview.id))
    return render_template(
        "interviews/form.html",
        job=interview.job,
        interview=interview,
        formats=INTERVIEW_FORMATS,
        statuses=INTERVIEW_STATUSES,
    )


@bp.route("/interviews/<int:interview_id>/delete", methods=["POST"])
def delete(interview_id):
    interview = Interview.query.get_or_404(interview_id)
    job_id = interview.job_id
    db.session.delete(interview)
    db.session.commit()
    flash("Interview deleted.", "success")
    return redirect(url_for("jobs.detail", job_id=job_id))


# ---------------- Questions (HTMX inline) ----------------


@bp.route("/interviews/<int:interview_id>/questions", methods=["POST"])
def add_question(interview_id):
    interview = Interview.query.get_or_404(interview_id)
    text = (request.form.get("question") or "").strip()
    if not text:
        return ("", 204)
    next_pos = (
        max((q.position for q in interview.questions), default=-1) + 1
    )
    q = InterviewQuestion(
        interview_id=interview.id,
        position=next_pos,
        question=text,
        my_answer=request.form.get("my_answer") or None,
        notes=request.form.get("notes") or None,
        was_difficult=bool(request.form.get("was_difficult")),
    )
    db.session.add(q)
    db.session.commit()
    return render_template("interviews/_question_row.html", q=q)


@bp.route("/interviews/questions/<int:question_id>", methods=["POST"])
def update_question(question_id):
    q = InterviewQuestion.query.get_or_404(question_id)
    q.question = (request.form.get("question") or q.question).strip()
    q.my_answer = request.form.get("my_answer") or None
    q.notes = request.form.get("notes") or None
    q.was_difficult = bool(request.form.get("was_difficult"))
    db.session.commit()
    return render_template("interviews/_question_row.html", q=q)


@bp.route("/interviews/questions/<int:question_id>/delete", methods=["POST"])
def delete_question(question_id):
    q = InterviewQuestion.query.get_or_404(question_id)
    db.session.delete(q)
    db.session.commit()
    return ("", 200)


# ---------------- Participants (HTMX inline) ----------------


@bp.route("/interviews/<int:interview_id>/participants", methods=["POST"])
def add_participant(interview_id):
    interview = Interview.query.get_or_404(interview_id)
    contact_id = request.form.get("contact_id")
    p = InterviewParticipant(
        interview_id=interview.id,
        contact_id=int(contact_id) if contact_id else None,
        name=request.form.get("name") or None,
        title=request.form.get("title") or None,
        email=request.form.get("email") or None,
        phone=request.form.get("phone") or None,
        role=request.form.get("role") or None,
    )
    if not p.contact_id and not p.name:
        return ("", 204)
    db.session.add(p)
    db.session.commit()
    return render_template("interviews/_participant_row.html", p=p)


@bp.route("/interviews/participants/<int:participant_id>/delete", methods=["POST"])
def delete_participant(participant_id):
    p = InterviewParticipant.query.get_or_404(participant_id)
    db.session.delete(p)
    db.session.commit()
    return ("", 200)


# ---------------- Calendar drag-reschedule ----------------


@bp.route("/api/interviews/<int:interview_id>/reschedule", methods=["PATCH", "POST"])
def reschedule(interview_id):
    interview = Interview.query.get_or_404(interview_id)
    data = request.get_json(silent=True) or request.form
    new_start = data.get("scheduled_at") or data.get("start")
    if not new_start:
        abort(400, "scheduled_at required")
    try:
        # Accept either ISO format from JS or our form format
        dt = datetime.fromisoformat(new_start.replace("Z", "+00:00"))
    except ValueError:
        try:
            dt = datetime.strptime(new_start, "%Y-%m-%dT%H:%M")
        except ValueError:
            abort(400, "invalid datetime")
    interview.scheduled_at = dt.replace(tzinfo=None)
    db.session.commit()
    return jsonify({"ok": True, "scheduled_at": interview.scheduled_at.isoformat()})
