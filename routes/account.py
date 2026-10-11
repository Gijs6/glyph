from flask import Blueprint, flash, redirect, render_template, request, url_for

from models import db
from utils.auth import current_user

account_bp = Blueprint("account", __name__, url_prefix="/account")


@account_bp.route("/")
def index():
    user = current_user()
    return render_template("account/account.jinja", user=user)


@account_bp.route("/password", methods=["POST"])
def change_password():
    user = current_user()

    current_password = request.form.get("current_password", "")
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not user.check_password(current_password):
        flash("Incorrect current password.", "error")
        return redirect(url_for("account.index"))

    if password != confirm_password:
        flash("Your passwords don't match.", "error")
        return redirect(url_for("account.index"))

    try:
        user.set_password(password)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        flash(str(e), "error")
        return redirect(url_for("account.index"))

    flash("Password saved.", "success")
    return redirect(url_for("account.index"))
