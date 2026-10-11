import re

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from models import db


MIGRATIONS = [
    "ALTER TABLE page ADD COLUMN parent_id VARCHAR(8) REFERENCES page(id)",
    "ALTER TABLE page ADD COLUMN meta_description VARCHAR(300)",
    "ALTER TABLE page ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1",
    "ALTER TABLE page ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT 0",
]

GLOBAL_SLUG_UNIQUE = re.compile(r",\s*UNIQUE \(slug\)")


def drop_global_slug_unique():
    if db.engine.dialect.name != "sqlite":
        return

    create_sql = db.session.execute(
        text("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'page'")
    ).scalar()
    if not create_sql or not GLOBAL_SLUG_UNIQUE.search(create_sql):
        return

    new_sql = GLOBAL_SLUG_UNIQUE.sub("", create_sql).replace(
        "CREATE TABLE page", "CREATE TABLE page_new", 1
    )
    db.session.execute(text(new_sql))
    db.session.execute(text("INSERT INTO page_new SELECT * FROM page"))
    db.session.execute(text("DROP TABLE page"))
    db.session.execute(text("ALTER TABLE page_new RENAME TO page"))
    db.session.commit()


def run_migrations():
    for statement in MIGRATIONS:
        try:
            db.session.execute(text(statement))
            db.session.commit()
        except OperationalError:
            db.session.rollback()

    drop_global_slug_unique()
