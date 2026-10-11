from datetime import datetime, timezone

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError

from models import Menu, Page, PasswordResetToken, User, db
from utils.auth import current_user, is_admin
from utils.mail import send_reset_mail

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
def require_admin():
    if not is_admin():
        abort(403)


@admin_bp.route("/")
def index():
    counts = {
        "users": User.query.count(),
        "pages": Page.query.count(),
        "menus": Menu.query.count(),
    }
    return render_template("admin/admin.jinja", counts=counts)


@admin_bp.route("/users")
def users():
    all_users = User.query.order_by(User.created_at.asc()).all()
    return render_template("admin/users.jinja", users=all_users)


@admin_bp.route("/users/new", methods=["GET", "POST"])
def new_user():
    if request.method == "GET":
        return render_template("admin/users_new.jinja")

    email = (request.form.get("email") or "").strip().lower()
    role = "admin" if request.form.get("is_admin") == "on" else "user"

    if not email:
        flash("Enter an email address.", "error")
        return redirect(url_for("admin.new_user"))

    user = User(email=email, role=role)
    try:
        db.session.add(user)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        flash(str(e), "error")
        return redirect(url_for("admin.new_user"))
    except IntegrityError:
        db.session.rollback()
        flash("There's already an account with this email address.", "error")
        return redirect(url_for("admin.new_user"))

    reset_token = PasswordResetToken(user_id=user.id)
    db.session.add(reset_token)
    db.session.commit()

    reset_url = url_for("auth.reset_password", token=reset_token.token, _external=True)

    if send_reset_mail(reset_url, user.email):
        flash(f"User added. Sent a setup email to {email}.", "success")
    else:
        flash(
            f"User added, but the setup email to {email} couldn't be sent. "
            "Share the reset link with them yourself.",
            "error",
        )
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<id>/role", methods=["POST"])
def toggle_role(id):
    user = User.query.get_or_404(id)

    if user.id == current_user().id:
        flash("You can't change your own role.", "error")
        return redirect(url_for("admin.users"))

    user.role = "user" if user.is_admin else "admin"
    db.session.commit()
    flash(
        f"{user.email} is now {'an admin' if user.is_admin else 'a user'}.", "success"
    )
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<id>/reset-password", methods=["POST"])
def reset_password(id):
    user = User.query.get_or_404(id)

    user.password_hash = None
    user.password_revoked_at = datetime.now(timezone.utc)

    PasswordResetToken.query.filter_by(user_id=user.id, used=False).update(
        {"used": True}
    )
    reset_token = PasswordResetToken(user_id=user.id)
    db.session.add(reset_token)
    db.session.commit()

    reset_url = url_for("auth.reset_password", token=reset_token.token, _external=True)

    if send_reset_mail(reset_url, user.email):
        flash(f"Password revoked. Sent a reset email to {user.email}.", "success")
    else:
        flash(
            f"Password revoked, but the reset email to {user.email} couldn't be sent. "
            "Share the reset link with them yourself.",
            "error",
        )
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<id>/delete", methods=["POST"])
def delete_user(id):
    user = User.query.get_or_404(id)

    if user.id == current_user().id:
        flash("You can't delete your own account.", "error")
        return redirect(url_for("admin.users"))

    PasswordResetToken.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    flash(f"Deleted {user.email}.", "success")
    return redirect(url_for("admin.users"))
