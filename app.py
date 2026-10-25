import os
from datetime import timedelta, timezone

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session, url_for

from migrations import run_migrations
from models import Page, db
from routes import register_routes
from utils.auth import current_user, is_logged_in, sign_in_dev_user
from utils.errors import register_errors
from utils.filters import register_filters
from utils.toasts import htmx_redirect, register_toasts
from utils.version import register_version

load_dotenv(override=True)

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", os.urandom(100).hex())
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URI", "sqlite:///glyph.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=31)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = True

db.init_app(app)
register_filters(app)
register_routes(app)
register_toasts(app)
register_version(app, "cursor")
register_errors(app, "cursor", user=lambda: session.get("user", {}).get("email"))

with app.app_context():
    db.create_all()
    run_migrations()


@app.before_request
def sync_session_user():
    session.permanent = True

    if app.debug and not is_logged_in() and not session.get("dev_signed_out"):
        sign_in_dev_user()

    allowed_endpoints = {
        "auth.login",
        "auth.forgot_password",
        "auth.reset_password",
        "auth.logout",
        "static",
    }
    if request.endpoint in allowed_endpoints or request.endpoint is None:
        return

    if not is_logged_in():
        return htmx_redirect(url_for("auth.login"))

    user = current_user()
    if not user:
        session.clear()
        return htmx_redirect(url_for("auth.login"))

    last_login = session.get("last_login_time", 0)
    if user.password_revoked_at:
        revoked_at = user.password_revoked_at
        if revoked_at.tzinfo is None:
            revoked_at = revoked_at.replace(tzinfo=timezone.utc)
        if revoked_at.timestamp() > last_login:
            session.clear()
            return redirect(url_for("auth.login"))

    session["user"] = {
        "id": user.id,
        "email": user.email,
        "role": user.role,
    }


@app.context_processor
def inject_auth():
    return dict(is_logged_in=is_logged_in, current_user=current_user)


@app.route("/")
def index():
    recent_pages = Page.query.order_by(Page.updated_at.desc()).limit(5).all()
    counts = {
        "pages": Page.query.count(),
    }
    return render_template("dashboard.jinja", recent_pages=recent_pages, counts=counts)


@app.errorhandler(403)
def forbidden(e):
    return render_template(
        "error.jinja",
        code=403,
        title="Forbidden",
        description="You don't have permission to view this page.",
    ), 403


@app.errorhandler(404)
def page_not_found(e):
    return render_template(
        "error.jinja",
        code=404,
        title="Not found",
        description="The page you're looking for doesn't exist.",
    ), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template(
        "error.jinja",
        code=500,
        title="Server error",
        description="Something went wrong on our end. Try again later.",
    ), 500


if __name__ == "__main__":
    app.config["SESSION_COOKIE_SECURE"] = False
    app.run(host="0.0.0.0", port=4000, debug=True)
