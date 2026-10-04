from flask import Blueprint, render_template, session, redirect, url_for
from database.history import get_history
history_bp = Blueprint("history", __name__, url_prefix="/history")

@history_bp.route("/")
def history():
    if not session.get("user_id"):
        return redirect(url_for("login.login"))
    return render_template("history.html", history=get_history(session["user_id"]))
