from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from models import db


MIGRATIONS = [
    "ALTER TABLE page ADD COLUMN parent_id VARCHAR(8) REFERENCES page(id)",
    "ALTER TABLE page ADD COLUMN meta_description VARCHAR(300)",
    "ALTER TABLE page ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1",
    "ALTER TABLE page ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT 0",
]


def run_migrations():
    for statement in MIGRATIONS:
        try:
            db.session.execute(text(statement))
            db.session.commit()
        except OperationalError:
            db.session.rollback()
