import os
import shutil

from jinja2 import FileSystemLoader

from app import app
from models import Menu, Page, db
from utils.settings import (
    HEADER_MENU_KEY,
    SITE_LANGUAGE_KEY,
    SITE_TITLE_KEY,
    get_setting,
)

STYLES_DIR = "export/styles"
TEMPLATES_DIR = "export/templates"
OUTPUT_DIR = "export/site"
STYLE_FILES = ["fonts.css", "colors.css", "theming.css", "blocks.css"]


def build_stylesheet():
    parts = []
    for filename in STYLE_FILES:
        path = os.path.join(STYLES_DIR, filename)
        with open(path) as f:
            parts.append(f.read())
    return "\n".join(parts)


def export_site():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

    assets_dir = os.path.join(OUTPUT_DIR, "assets")
    os.mkdir(assets_dir)
    with open(os.path.join(assets_dir, "style.css"), "w") as f:
        f.write(build_stylesheet())

    jinja_env = app.jinja_env.overlay(loader=FileSystemLoader(TEMPLATES_DIR))

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
            html = jinja_env.get_template("page.jinja").render(
                page=page,
                header_menu=header_menu,
                site_title=site_title,
                site_language=site_language,
            )
            target = os.path.join(OUTPUT_DIR, f"{page.path}.html")
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w") as f:
                f.write(html)

            if page.is_homepage:
                with open(os.path.join(OUTPUT_DIR, "index.html"), "w") as f:
                    f.write(html)

        print(f"Exported {len(pages)} page(s) to {OUTPUT_DIR}/")


if __name__ == "__main__":
    export_site()
