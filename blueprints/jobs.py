from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from sqlalchemy import or_

from extensions import db
from models import (
    Company,
    Job,
    JOB_STATUSES,
    JOB_STATUS_VALUES,
    REMOTE_TYPES,
    Tag,
)

bp = Blueprint("jobs", __name__, url_prefix="/jobs")


def _parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def _parse_int(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _form_to_job(form, job):
    job.company_id = int(form["company_id"])
    job.title = form["title"].strip()
    job.location = form.get("location") or None
    job.remote_type = form.get("remote_type") or None
    job.job_post_url = form.get("job_post_url") or None
    job.local_folder_path = form.get("local_folder_path") or None
    job.salary_min = _parse_int(form.get("salary_min"))
    job.salary_max = _parse_int(form.get("salary_max"))
    job.salary_notes = form.get("salary_notes") or None
    job.description = form.get("description") or None
    job.source = form.get("source") or None
    job.application_date = _parse_date(form.get("application_date"))
    job.application_method = form.get("application_method") or None
    job.application_deadline = _parse_date(form.get("application_deadline"))
    job.status = form.get("status") or "interested"
    if job.status not in JOB_STATUS_VALUES:
        job.status = "interested"
    job.rating = _parse_int(form.get("rating"))
    job.notes = form.get("notes") or None

    tag_ids = form.getlist("tag_ids")
    if tag_ids:
        job.tags = Tag.query.filter(Tag.id.in_([int(t) for t in tag_ids])).all()
    else:
        job.tags = []
    return job


@bp.route("")
def list_view():
    q = Job.query
    status = request.args.get("status")
    company_id = request.args.get("company_id", type=int)
    tag_id = request.args.get("tag_id", type=int)
    search = (request.args.get("q") or "").strip()

    if status:
        q = q.filter(Job.status == status)
    if company_id:
        q = q.filter(Job.company_id == company_id)
    if tag_id:
        q = q.filter(Job.tags.any(Tag.id == tag_id))
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Job.title.ilike(like), Job.description.ilike(like)))

    jobs = q.order_by(Job.updated_at.desc()).all()

    return render_template(
        "jobs/list.html",
        jobs=jobs,
        statuses=JOB_STATUSES,
        companies=Company.query.order_by(Company.name).all(),
        tags=Tag.query.order_by(Tag.name).all(),
        current_status=status,
        current_company_id=company_id,
        current_tag_id=tag_id,
        current_search=search,
    )


@bp.route("/pipeline")
def pipeline():
    jobs = Job.query.order_by(Job.updated_at.desc()).all()
    columns = []
    for value, label in JOB_STATUSES:
        columns.append((value, label, [j for j in jobs if j.status == value]))
    return render_template("jobs/pipeline.html", columns=columns)


@bp.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        if not request.form.get("company_id"):
            flash("Company is required.", "danger")
            return redirect(url_for("jobs.new"))
        job = Job(company_id=int(request.form["company_id"]), title="")
        _form_to_job(request.form, job)
        db.session.add(job)
        db.session.commit()
        flash("Job created.", "success")
        return redirect(url_for("jobs.detail", job_id=job.id))

    return render_template(
        "jobs/form.html",
        job=None,
        companies=Company.query.order_by(Company.name).all(),
        tags=Tag.query.order_by(Tag.name).all(),
        statuses=JOB_STATUSES,
        remote_types=REMOTE_TYPES,
        selected_tag_ids=set(),
    )


@bp.route("/<int:job_id>")
def detail(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template("jobs/detail.html", job=job, statuses=JOB_STATUSES)


@bp.route("/<int:job_id>/edit", methods=["GET", "POST"])
def edit(job_id):
    job = Job.query.get_or_404(job_id)
    if request.method == "POST":
        _form_to_job(request.form, job)
        db.session.commit()
        flash("Job updated.", "success")
        return redirect(url_for("jobs.detail", job_id=job.id))

    return render_template(
        "jobs/form.html",
        job=job,
        companies=Company.query.order_by(Company.name).all(),
        tags=Tag.query.order_by(Tag.name).all(),
        statuses=JOB_STATUSES,
        remote_types=REMOTE_TYPES,
        selected_tag_ids={t.id for t in job.tags},
    )


@bp.route("/<int:job_id>/status", methods=["POST"])
def update_status(job_id):
    job = Job.query.get_or_404(job_id)
    status = request.form.get("status")
    if status not in JOB_STATUS_VALUES:
        abort(400)
    job.status = status
    db.session.commit()
    if request.headers.get("HX-Request"):
        return ("", 204)
    return redirect(url_for("jobs.pipeline"))


@bp.route("/<int:job_id>/delete", methods=["POST"])
def delete(job_id):
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash("Job deleted.", "success")
    return redirect(url_for("jobs.list_view"))
