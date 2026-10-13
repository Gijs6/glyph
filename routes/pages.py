from flask import Blueprint, flash, redirect, render_template, request, url_for

from models import MenuItem, Page, db, now
from utils.auth import current_user
from utils.blocks import BLOCK_TYPES
from utils.filters import pluralize_filter as pluralize

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


def render_form(page, status=200):
    exclude_id = page.id if page and page.id else None
    return render_template(
        "pages/form.jinja",
        page=page,
        parents=parent_options(exclude_id=exclude_id),
        block_types=BLOCK_TYPES,
    ), status


def placement_error(page_id, slug, parent_id):
    siblings = Page.query.filter_by(slug=slug, parent_id=parent_id)
    if page_id:
        siblings = siblings.filter(Page.id != page_id)
    if siblings.first():
        return "Another page with this parent already uses that slug. Pick another one."

    seen = set()
    ancestor = db.session.get(Page, parent_id) if parent_id else None
    while ancestor is not None and ancestor.id not in seen:
        if page_id and ancestor.id == page_id:
            return "A page can't be under one of its own child pages."
        seen.add(ancestor.id)
        ancestor = ancestor.parent
    return None


@pages_bp.get("/new")
def new_page():
    return render_form(None)


@pages_bp.post("/")
def create_page():
    fields = read_page_form()

    if not fields["title"] or not fields["slug"]:
        flash("Enter a title and a slug.", "error")
        return render_form(Page(**fields), 400)

    page = Page(
        author_id=current_user().id, **{k: v for k, v in fields.items() if k != "slug"}
    )
    try:
        page.slug = fields["slug"]
    except ValueError as e:
        flash(str(e), "error")
        return render_form(page, 400)

    error = placement_error(None, page.slug, page.parent_id)
    if error:
        flash(error, "error")
        return render_form(page, 400)

    db.session.add(page)
    db.session.commit()

    flash("Page added.", "success")
    return redirect(url_for("pages.edit_page", page_id=page.id), code=303)


@pages_bp.get("/<page_id>/edit")
def edit_page(page_id):
    return render_form(Page.query.get_or_404(page_id))


@pages_bp.put("/<page_id>")
def update_page(page_id):
    page = Page.query.get_or_404(page_id)
    fields = read_page_form()

    if not fields["title"] or not fields["slug"]:
        flash("Enter a title and a slug.", "error")
        return render_form(page, 400)

    error = placement_error(page.id, fields["slug"], fields["parent_id"])
    if error:
        flash(error, "error")
        return render_form(page, 400)

    try:
        with db.session.no_autoflush:
            for key, value in fields.items():
                setattr(page, key, value)
            page.updated_at = now()
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        flash(str(e), "error")
        return render_form(Page.query.get_or_404(page_id), 400)

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
    flash(f'"{page.title}" unarchived.', "success")
    return redirect(url_for("pages.edit_page", page_id=page.id), code=303)


@pages_bp.delete("/<page_id>")
def delete_page(page_id):
    page = Page.query.get_or_404(page_id)

    uses = []
    item_count = MenuItem.query.filter_by(page_id=page.id).count()
    if item_count:
        uses.append(
            f"{item_count} menu {pluralize(item_count, 'item')} {pluralize(item_count, 'links', 'link')} to it"
        )
    child_count = page.children.count()
    if child_count:
        uses.append(f"it has {child_count} child {pluralize(child_count, 'page')}")
    if uses:
        flash(
            f'Can\'t delete "{page.title}": {" and ".join(uses)}. Remove those first.',
            "error",
        )
        return redirect(url_for("pages.edit_page", page_id=page.id), code=303)

    db.session.delete(page)
    db.session.commit()
    flash("Page deleted.", "success")
    return redirect(url_for("pages.list_pages"), code=303)
