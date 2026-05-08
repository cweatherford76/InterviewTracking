import random

from flask import Blueprint, flash, redirect, render_template, request, url_for

from extensions import db
from models import Tag

bp = Blueprint("tags", __name__, url_prefix="/tags")


TAG_PALETTE = [
    "#ef4444", "#f97316", "#f59e0b", "#84cc16", "#22c55e", "#10b981",
    "#14b8a6", "#06b6d4", "#0ea5e9", "#3b82f6", "#6366f1", "#8b5cf6",
    "#a855f7", "#d946ef", "#ec4899", "#f43f5e",
]


def _pick_color():
    used = {t.color for t in Tag.query.all() if t.color}
    available = [c for c in TAG_PALETTE if c not in used]
    return random.choice(available or TAG_PALETTE)


@bp.route("", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if name and not Tag.query.filter_by(name=name).first():
            db.session.add(Tag(name=name, color=_pick_color()))
            db.session.commit()
            flash(f"Tag '{name}' added.", "success")
        return redirect(url_for("tags.index"))
    tags = Tag.query.order_by(Tag.name).all()
    return render_template("tags/index.html", tags=tags)


@bp.route("/<int:tag_id>/delete", methods=["POST"])
def delete(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    db.session.delete(tag)
    db.session.commit()
    flash("Tag deleted.", "success")
    return redirect(url_for("tags.index"))
