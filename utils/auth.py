from datetime import datetime, timezone

from flask import session

from models import User, db


def is_logged_in():
    return "user" in session


def current_user():
    user_id = session.get("user", {}).get("id")
    return db.session.get(User, user_id) if user_id else None


def is_admin():
    return session.get("user", {}).get("role") == "admin"


def sign_in(user):
    session.clear()
    session.permanent = True
    session["last_login_time"] = datetime.now(timezone.utc).timestamp()
    session["user"] = {
        "id": user.id,
        "email": user.email,
        "role": user.role,
    }


DEV_EMAIL = "dev@glyph.test"


def sign_in_dev_user():
    user = User.query.filter_by(email=DEV_EMAIL).first()
    if user is None:
        user = User(email=DEV_EMAIL)
        db.session.add(user)
    user.role = "admin"
    db.session.commit()
    sign_in(user)
