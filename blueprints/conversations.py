from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from extensions import db
from models import CONVERSATION_CHANNELS, Contact, Conversation, Job

bp = Blueprint("conversations", __name__)


def _parse_dt(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M")


def _parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def _form_to_conversation(form, conv):
    occurred = _parse_dt(form.get("occurred_at"))
    if occurred:
        conv.occurred_at = occurred
    conv.channel = form.get("channel") or "email"
    conv.subject = form.get("subject") or None
    conv.notes = form.get("notes") or None
    conv.follow_up_date = _parse_date(form.get("follow_up_date"))
    cid = form.get("contact_id")
    conv.contact_id = int(cid) if cid else None


@bp.route("/jobs/<int:job_id>/conversations/new", methods=["GET", "POST"])
def new(job_id):
    job = Job.query.get_or_404(job_id)
    if request.method == "POST":
        conv = Conversation(job_id=job.id, occurred_at=datetime.utcnow())
        _form_to_conversation(request.form, conv)
        db.session.add(conv)
        db.session.commit()
        flash("Conversation logged.", "success")
        return redirect(url_for("jobs.detail", job_id=job.id))
    return render_template(
        "conversations/form.html",
        job=job,
        conversation=None,
        channels=CONVERSATION_CHANNELS,
        contacts=Contact.query.order_by(Contact.name).all(),
    )


@bp.route("/conversations/<int:conversation_id>/edit", methods=["GET", "POST"])
def edit(conversation_id):
    conv = Conversation.query.get_or_404(conversation_id)
    if request.method == "POST":
        _form_to_conversation(request.form, conv)
        db.session.commit()
        flash("Conversation updated.", "success")
        return redirect(url_for("jobs.detail", job_id=conv.job_id))
    return render_template(
        "conversations/form.html",
        job=conv.job,
        conversation=conv,
        channels=CONVERSATION_CHANNELS,
        contacts=Contact.query.order_by(Contact.name).all(),
    )


@bp.route("/conversations/<int:conversation_id>/delete", methods=["POST"])
def delete(conversation_id):
    conv = Conversation.query.get_or_404(conversation_id)
    job_id = conv.job_id
    db.session.delete(conv)
    db.session.commit()
    flash("Conversation deleted.", "success")
    return redirect(url_for("jobs.detail", job_id=job_id))
