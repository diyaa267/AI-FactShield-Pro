from flask import Blueprint, render_template, session, redirect, url_for
from database.history import stats, get_history
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@dashboard_bp.route("/")
def dashboard():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login.login"))
    return render_template("dashboard.html", stats=stats(user_id), recent=get_history(user_id, 6))
