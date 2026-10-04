from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.users import verify_user

login_bp = Blueprint("login", __name__)

@login_bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = verify_user(request.form.get("email",""), request.form.get("password",""))
        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard.dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@login_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home.index"))
