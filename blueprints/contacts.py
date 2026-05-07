from flask import Blueprint, flash, redirect, render_template, request, url_for

from extensions import db
from models import Company, Contact

bp = Blueprint("contacts", __name__, url_prefix="/contacts")


def _form_to_contact(form, contact):
    contact.name = form["name"].strip()
    contact.title = form.get("title") or None
    contact.email = form.get("email") or None
    contact.phone = form.get("phone") or None
    contact.linkedin_url = form.get("linkedin_url") or None
    contact.notes = form.get("notes") or None
    cid = form.get("company_id")
    contact.company_id = int(cid) if cid else None


@bp.route("")
def list_view():
    contacts = (
        Contact.query.order_by(Contact.name).all()
    )
    return render_template("contacts/list.html", contacts=contacts)


@bp.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        if not request.form.get("name", "").strip():
            flash("Name is required.", "danger")
            return redirect(url_for("contacts.new"))
        contact = Contact(name="")
        _form_to_contact(request.form, contact)
        db.session.add(contact)
        db.session.commit()
        flash("Contact created.", "success")
        return redirect(url_for("contacts.list_view"))
    return render_template(
        "contacts/form.html",
        contact=None,
        companies=Company.query.order_by(Company.name).all(),
    )


@bp.route("/<int:contact_id>/edit", methods=["GET", "POST"])
def edit(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    if request.method == "POST":
        _form_to_contact(request.form, contact)
        db.session.commit()
        flash("Contact updated.", "success")
        return redirect(url_for("contacts.list_view"))
    return render_template(
        "contacts/form.html",
        contact=contact,
        companies=Company.query.order_by(Company.name).all(),
    )


@bp.route("/<int:contact_id>/delete", methods=["POST"])
def delete(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    db.session.delete(contact)
    db.session.commit()
    flash("Contact deleted.", "success")
    return redirect(url_for("contacts.list_view"))
