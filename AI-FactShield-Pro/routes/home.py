from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.contact import add_contact
from utils.validation import valid_email
from utils.demo_news import get_demo_news
home_bp = Blueprint("home", __name__)

@home_bp.route("/")
def index():
    return render_template("index.html", demo_news=get_demo_news())

@home_bp.route("/about")
def about():
    return render_template("about.html")

@home_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()
        try:
            rating = max(1, min(5, int(request.form.get("rating", "5"))))
        except ValueError:
            rating = 5
        if not name or not valid_email(email) or not subject or len(message) < 5:
            flash("Please enter a valid name, email, subject and message.", "warning")
            return render_template("contact.html")
        add_contact(name, email, subject, message, session.get("user_id"), rating)
        flash("Your message has been submitted successfully. Thank you!", "success")
        return redirect(url_for("home.contact"))
    return render_template("contact.html")
