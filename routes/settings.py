from flask import Blueprint, flash, redirect, render_template, request, url_for

from models import Menu
from utils.settings import (
    HEADER_MENU_KEY,
    SITE_LANGUAGE_KEY,
    SITE_LANGUAGES,
    SITE_TITLE_KEY,
    get_setting,
    set_setting,
)

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.get("/")
def index():
    return render_template(
        "settings/index.jinja",
        site_title=get_setting(SITE_TITLE_KEY, "My Site"),
        header_menu_id=get_setting(HEADER_MENU_KEY),
        site_language=get_setting(SITE_LANGUAGE_KEY, "en"),
        languages=SITE_LANGUAGES,
        menus=Menu.query.order_by(Menu.name.asc()).all(),
    )


@settings_bp.post("/")
def update():
    site_title = (request.form.get("site_title") or "").strip()
    header_menu_id = request.form.get("header_menu_id") or None
    site_language = request.form.get("site_language") or "en"

    if site_language not in dict(SITE_LANGUAGES):
        site_language = "en"

    set_setting(SITE_TITLE_KEY, site_title or "My Site")
    set_setting(HEADER_MENU_KEY, header_menu_id)
    set_setting(SITE_LANGUAGE_KEY, site_language)

    flash("Settings saved.", "success")
    return redirect(url_for("settings.index"), code=303)
