from flask import Blueprint, flash, redirect, render_template, request, url_for

from extensions import db
from models import Company

bp = Blueprint("companies", __name__, url_prefix="/companies")


def _form_to_company(form, company):
    company.name = form["name"].strip()
    company.website = form.get("website") or None
    company.industry = form.get("industry") or None
    company.size = form.get("size") or None
    company.headquarters = form.get("headquarters") or None
    company.notes = form.get("notes") or None


@bp.route("")
def list_view():
    companies = Company.query.order_by(Company.name).all()
    return render_template("companies/list.html", companies=companies)


@bp.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        if not request.form.get("name", "").strip():
            flash("Name is required.", "danger")
            return redirect(url_for("companies.new"))
        company = Company(name="")
        _form_to_company(request.form, company)
        db.session.add(company)
        db.session.commit()
        flash("Company created.", "success")
        return redirect(url_for("companies.detail", company_id=company.id))
    return render_template("companies/form.html", company=None)


@bp.route("/<int:company_id>")
def detail(company_id):
    company = Company.query.get_or_404(company_id)
    return render_template("companies/detail.html", company=company)


@bp.route("/<int:company_id>/edit", methods=["GET", "POST"])
def edit(company_id):
    company = Company.query.get_or_404(company_id)
    if request.method == "POST":
        _form_to_company(request.form, company)
        db.session.commit()
        flash("Company updated.", "success")
        return redirect(url_for("companies.detail", company_id=company.id))
    return render_template("companies/form.html", company=company)


@bp.route("/<int:company_id>/delete", methods=["POST"])
def delete(company_id):
    company = Company.query.get_or_404(company_id)
    db.session.delete(company)
    db.session.commit()
    flash("Company deleted.", "success")
    return redirect(url_for("companies.list_view"))
