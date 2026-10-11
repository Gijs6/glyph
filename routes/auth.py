from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from models import PasswordResetToken, User, db
from utils.auth import is_logged_in, sign_in, sign_in_dev_user
from utils.mail import send_reset_mail

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if is_logged_in():
            return redirect(url_for("index"))
        return render_template("auth/login.jinja")

    if current_app.debug:
        sign_in_dev_user()
        return redirect(url_for("index"))

    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        flash("Enter your email address and password.", "error")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        sign_in(user)
        flash(f"Signed in as {user.email}.", "success")
        return redirect(url_for("index"))

    flash("Incorrect email address or password.", "error")
    return redirect(url_for("auth.login"))


@auth_bp.post("/logout")
def logout():
    session.clear()
    if current_app.debug:
        session["dev_signed_out"] = True
    flash("Signed out.", "success")
    return redirect(url_for("auth.login"), code=303)


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "GET":
        if is_logged_in():
            return redirect(url_for("index"))
        return render_template("auth/forgot_password.jinja")

    email = (request.form.get("email") or "").strip().lower()
    if not email:
        flash("Enter your email address.", "error")
        return redirect(url_for("auth.forgot_password"))

    user = User.query.filter_by(email=email).first()
    if user:
        PasswordResetToken.query.filter_by(user_id=user.id, used=False).update(
            {"used": True}
        )
        reset_token = PasswordResetToken(user_id=user.id)
        db.session.add(reset_token)
        db.session.commit()

        reset_url = url_for(
            "auth.reset_password", token=reset_token.token, _external=True
        )
        send_reset_mail(reset_url, email)

    flash(
        "If there's an account for this email address, we've sent it a reset link.",
        "success",
    )
    return redirect(url_for("auth.login"))


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if request.method == "GET":
        session.clear()
        reset_token = PasswordResetToken.query.filter_by(token=token).first()
        if not reset_token or not reset_token.is_valid():
            flash(
                "This reset link has expired or was already used. Ask for a new one.",
                "error",
            )
            return redirect(url_for("auth.login"))
        return render_template("auth/reset_password.jinja", token=token)

    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    reset_token = PasswordResetToken.query.filter_by(token=token).first()
    if not reset_token or not reset_token.is_valid():
        flash(
            "This reset link has expired or was already used. Ask for a new one.",
            "error",
        )
        return redirect(url_for("auth.login"))

    if not password or password != confirm_password:
        flash("Your passwords don't match.", "error")
        return redirect(url_for("auth.reset_password", token=token))

    user = reset_token.user
    try:
        user.set_password(password)
    except ValueError as e:
        db.session.rollback()
        flash(str(e), "error")
        return redirect(url_for("auth.reset_password", token=token))

    user.password_revoked_at = None
    reset_token.mark_used()
    db.session.commit()

    flash("Password saved. Sign in with your new password.", "success")
    return redirect(url_for("auth.login"))
