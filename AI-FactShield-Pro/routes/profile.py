from flask import Blueprint, render_template, session, redirect, url_for
from database.users import get_user
profile_bp = Blueprint("profile", __name__, url_prefix="/profile")

@profile_bp.route("/")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login.login"))
    return render_template("profile.html", user=get_user(session["user_id"]))
