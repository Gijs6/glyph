from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError

from models import Page, db, now
from utils.auth import current_user
from utils.blocks import BLOCK_TYPES

pages_bp = Blueprint("pages", __name__, url_prefix="/pages")


def parent_options(exclude_id=None):
    query = Page.query
    if exclude_id:
        query = query.filter(Page.id != exclude_id)
    return query.order_by(Page.title.asc()).all()


def read_page_form():
    return {
        "title": (request.form.get("title") or "").strip(),
        "slug": (request.form.get("slug") or "").strip().lower(),
        "meta_description": (request.form.get("meta_description") or "").strip()
        or None,
        "parent_id": request.form.get("parent_id") or None,
        "is_active": request.form.get("is_active") == "on",
    }


@pages_bp.get("/")
def list_pages():
    show_archived = request.args.get("archived") == "1"
    pages = (
        Page.query.filter_by(is_archived=show_archived).order_by(Page.title.asc()).all()
    )
    return render_template("pages/list.jinja", pages=pages, show_archived=show_archived)


@pages_bp.get("/new")
def new_page():
    return render_template(
        "pages/form.jinja", page=None, parents=parent_options(), block_types=BLOCK_TYPES
    )


@pages_bp.post("/")
def create_page():
    fields = read_page_form()

    if not fields["title"] or not fields["slug"]:
        flash("Enter a title and a slug.", "error")
        page = Page(**fields)
        return render_template(
            "pages/form.jinja",
            page=page,
            parents=parent_options(),
            block_types=BLOCK_TYPES,
        ), 400

    page = Page(
        author_id=current_user().id, **{k: v for k, v in fields.items() if k != "slug"}
    )
    try:
        page.slug = fields["slug"]
        db.session.add(page)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        flash(str(e), "error")
        return render_template(
            "pages/form.jinja",
            page=page,
            parents=parent_options(),
            block_types=BLOCK_TYPES,
        ), 400
    except IntegrityError:
        db.session.rollback()
        flash("That slug is already in use. Pick another one.", "error")
        return render_template(
            "pages/form.jinja",
            page=page,
            parents=parent_options(),
            block_types=BLOCK_TYPES,
        ), 400

    flash("Page added.", "success")
    return redirect(url_for("pages.edit_page", page_id=page.id), code=303)


@pages_bp.get("/<page_id>/edit")
def edit_page(page_id):
    page = Page.query.get_or_404(page_id)
    return render_template(
        "pages/form.jinja",
        page=page,
        parents=parent_options(exclude_id=page.id),
        block_types=BLOCK_TYPES,
    )


@pages_bp.put("/<page_id>")
def update_page(page_id):
    page = Page.query.get_or_404(page_id)
    fields = read_page_form()

    if not fields["title"] or not fields["slug"]:
        flash("Enter a title and a slug.", "error")
        return render_template(
            "pages/form.jinja",
            page=page,
            parents=parent_options(exclude_id=page.id),
            block_types=BLOCK_TYPES,
        ), 400

    for key, value in fields.items():
        if key != "slug":
            setattr(page, key, value)

    try:
        page.slug = fields["slug"]
        page.updated_at = now()
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        flash(str(e), "error")
        return render_template(
            "pages/form.jinja",
            page=page,
            parents=parent_options(exclude_id=page.id),
            block_types=BLOCK_TYPES,
        ), 400
    except IntegrityError:
        db.session.rollback()
        flash("That slug is already in use. Pick another one.", "error")
        return render_template(
            "pages/form.jinja",
            page=page,
            parents=parent_options(exclude_id=page.id),
            block_types=BLOCK_TYPES,
        ), 400

    flash("Page saved.", "success")
    return redirect(url_for("pages.edit_page", page_id=page.id), code=303)


@pages_bp.post("/<page_id>/homepage")
def set_homepage(page_id):
    page = Page.query.get_or_404(page_id)
    Page.query.filter(Page.id != page_id).update({"is_homepage": False})
    page.is_homepage = True
    db.session.commit()
    flash(f'"{page.title}" is now the homepage.', "success")
    return redirect(url_for("pages.edit_page", page_id=page.id), code=303)


@pages_bp.post("/<page_id>/archive")
def archive_page(page_id):
    page = Page.query.get_or_404(page_id)
    page.is_archived = True
    db.session.commit()
    flash(f'"{page.title}" archived.', "success")
    return redirect(url_for("pages.list_pages"), code=303)


@pages_bp.post("/<page_id>/unarchive")
def unarchive_page(page_id):
    page = Page.query.get_or_404(page_id)
    page.is_archived = False
    db.session.commit()
    flash(f'"{page.title}" restored.', "success")
    return redirect(url_for("pages.edit_page", page_id=page.id), code=303)


@pages_bp.delete("/<page_id>")
def delete_page(page_id):
    page = Page.query.get_or_404(page_id)
    db.session.delete(page)
    db.session.commit()
    flash("Page deleted.", "success")
    return redirect(url_for("pages.list_pages"), code=303)
