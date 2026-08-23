from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.users import create_user
from utils.validation import valid_email, strong_password
register_bp = Blueprint("register", __name__)

@register_bp.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name","").strip()
        email = request.form.get("email","").strip()
        password = request.form.get("password","")
        if not name or not valid_email(email) or not strong_password(password):
            flash("Enter a valid name, email and password of at least 6 characters.", "warning")
            return render_template("register.html")
        if not create_user(name, email, password):
            flash("Email already registered.", "danger")
            return render_template("register.html")
        flash("Account created. Please log in.", "success")
        return redirect(url_for("login.login"))
    return render_template("register.html")
