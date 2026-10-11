import os
import shutil

from app import app
from models import Menu, Page, db
from utils.settings import (
    HEADER_MENU_KEY,
    SITE_LANGUAGE_KEY,
    SITE_TITLE_KEY,
    get_setting,
)

EXPORT_DIR = "build"
ASSET_FILES = ["fonts.css", "colors.css", "theming.css", "export.css"]


def build_stylesheet():
    parts = []
    for filename in ASSET_FILES:
        path = os.path.join("static/styles", filename)
        with open(path) as f:
            parts.append(f.read())
    return "\n".join(parts)


def build():
    if os.path.exists(EXPORT_DIR):
        shutil.rmtree(EXPORT_DIR)
    os.makedirs(EXPORT_DIR)

    assets_dir = os.path.join(EXPORT_DIR, "assets")
    os.mkdir(assets_dir)
    with open(os.path.join(assets_dir, "style.css"), "w") as f:
        f.write(build_stylesheet())

    with app.app_context():
        site_title = get_setting(SITE_TITLE_KEY, "My Site")
        site_language = get_setting(SITE_LANGUAGE_KEY, "en")
        header_menu_id = get_setting(HEADER_MENU_KEY)
        header_menu = db.session.get(Menu, header_menu_id) if header_menu_id else None

        pages = [page for page in Page.query.all() if page.is_live]
        if not pages:
            print("No pages to export.")
            return

        for page in pages:
            html = app.jinja_env.get_template("export/page.jinja").render(
                page=page,
                header_menu=header_menu,
                site_title=site_title,
                site_language=site_language,
            )
            with open(os.path.join(EXPORT_DIR, f"{page.slug}.html"), "w") as f:
                f.write(html)

            if page.is_homepage:
                with open(os.path.join(EXPORT_DIR, "index.html"), "w") as f:
                    f.write(html)

        print(f"Exported {len(pages)} page(s) to {EXPORT_DIR}/")


if __name__ == "__main__":
    build()
