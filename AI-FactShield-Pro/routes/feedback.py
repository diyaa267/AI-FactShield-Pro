from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.feedback import add_feedback
feedback_bp = Blueprint("feedback", __name__)

@feedback_bp.route("/feedback", methods=["GET","POST"])
def feedback():
    if request.method == "POST":
        add_feedback(session.get("user_id"), request.form.get("rating", 5), request.form.get("message",""))
        flash("Thank you for your feedback!", "success")
        return redirect(url_for("feedback.feedback"))
    return render_template("feedback.html")
