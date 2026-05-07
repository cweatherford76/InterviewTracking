from flask import Blueprint, flash, redirect, render_template, request, url_for

from extensions import db
from models import Tag

bp = Blueprint("tags", __name__, url_prefix="/tags")


@bp.route("", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        color = (request.form.get("color") or "#6c757d").strip()
        if name and not Tag.query.filter_by(name=name).first():
            db.session.add(Tag(name=name, color=color))
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
