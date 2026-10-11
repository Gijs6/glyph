from flask import Blueprint, flash, redirect, render_template, request, url_for

from models import Menu, MenuItem, Page, db

menus_bp = Blueprint("menus", __name__, url_prefix="/menus")


@menus_bp.get("/")
def list_menus():
    menus = Menu.query.order_by(Menu.name.asc()).all()
    return render_template("menus/list.jinja", menus=menus)


@menus_bp.get("/new")
def new_menu():
    return render_template("menus/form.jinja", menu=None)


@menus_bp.post("/")
def create_menu():
    name = (request.form.get("name") or "").strip()

    if not name:
        flash("Enter a name.", "error")
        return render_template("menus/form.jinja", menu=Menu(name=name)), 400

    menu = Menu(name=name)
    db.session.add(menu)
    db.session.commit()

    flash("Menu added.", "success")
    return redirect(url_for("menus.edit_menu", menu_id=menu.id), code=303)


@menus_bp.get("/<menu_id>")
def edit_menu(menu_id):
    menu = Menu.query.get_or_404(menu_id)
    pages = Page.query.order_by(Page.title.asc()).all()
    return render_template("menus/edit.jinja", menu=menu, pages=pages)


@menus_bp.delete("/<menu_id>")
def delete_menu(menu_id):
    menu = Menu.query.get_or_404(menu_id)
    db.session.delete(menu)
    db.session.commit()
    flash("Menu deleted.", "success")
    return redirect(url_for("menus.list_menus"), code=303)


@menus_bp.post("/<menu_id>/items")
def add_item(menu_id):
    menu = Menu.query.get_or_404(menu_id)

    label = (request.form.get("label") or "").strip()
    page_id = request.form.get("page_id") or None
    url = (request.form.get("url") or "").strip() or None

    if not label or (not page_id and not url):
        flash("Enter a label, and pick a page or enter a URL.", "error")
        return redirect(url_for("menus.edit_menu", menu_id=menu.id))

    next_position = (
        db.session.query(db.func.max(MenuItem.position))
        .filter(MenuItem.menu_id == menu.id)
        .scalar()
        or 0
    ) + 1
    item = MenuItem(
        menu_id=menu.id,
        label=label,
        page_id=page_id if not url else None,
        url=url,
        position=next_position,
    )
    db.session.add(item)
    db.session.commit()
    flash("Menu item added.", "success")
    return redirect(url_for("menus.edit_menu", menu_id=menu.id), code=303)


@menus_bp.put("/<menu_id>/items/<item_id>")
def update_item(menu_id, item_id):
    item = MenuItem.query.filter_by(id=item_id, menu_id=menu_id).first_or_404()

    label = (request.form.get("label") or "").strip()
    page_id = request.form.get("page_id") or None
    url = (request.form.get("url") or "").strip() or None

    if not label or (not page_id and not url):
        flash("Enter a label, and pick a page or enter a URL.", "error")
        return redirect(url_for("menus.edit_menu", menu_id=menu_id))

    item.label = label
    item.page_id = page_id if not url else None
    item.url = url
    db.session.commit()
    flash("Menu item saved.", "success")
    return redirect(url_for("menus.edit_menu", menu_id=menu_id), code=303)


@menus_bp.delete("/<menu_id>/items/<item_id>")
def delete_item(menu_id, item_id):
    item = MenuItem.query.filter_by(id=item_id, menu_id=menu_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Menu item deleted.", "success")
    return redirect(url_for("menus.edit_menu", menu_id=menu_id), code=303)


@menus_bp.post("/<menu_id>/items/<item_id>/move")
def move_item(menu_id, item_id):
    direction = request.form.get("direction")
    items = list(
        MenuItem.query.filter_by(menu_id=menu_id).order_by(MenuItem.position.asc())
    )
    index = next((i for i, item in enumerate(items) if item.id == item_id), None)

    if index is None:
        return redirect(url_for("menus.edit_menu", menu_id=menu_id))

    swap_with = index - 1 if direction == "up" else index + 1
    if 0 <= swap_with < len(items):
        items[index].position, items[swap_with].position = (
            items[swap_with].position,
            items[index].position,
        )
        db.session.commit()

    return redirect(url_for("menus.edit_menu", menu_id=menu_id), code=303)
