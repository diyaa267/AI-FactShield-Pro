from flask import Blueprint, render_template, session, redirect, url_for, send_file, flash
from database.history import get_history
from database.reports import save_report
from utils.csv_export import export_history
from utils.pdf_generator import generate_pdf_report
from pathlib import Path
from config import Config

report_bp = Blueprint("report", __name__, url_prefix="/report")


@report_bp.route("/")
def report():
    if not session.get("user_id"):
        return redirect(url_for("login.login"))
    return render_template("report.html", history=get_history(session["user_id"]))


@report_bp.route("/csv")
def csv_report():
    if not session.get("user_id"):
        return redirect(url_for("login.login"))
    filename = f"history_{session['user_id']}.csv"
    path = Path(Config.REPORT_FOLDER) / "csv" / filename
    export_history(get_history(session["user_id"]), path)
    save_report(session["user_id"], "csv", filename)
    return send_file(path, as_attachment=True, download_name=filename)


@report_bp.route("/pdf/<int:history_id>")
def pdf_report(history_id):
    if not session.get("user_id"):
        return redirect(url_for("login.login"))

    rows = get_history(session["user_id"], 1000)
    row = next((r for r in rows if r["id"] == history_id), None)
    if row is None:
        flash("Report not found.", "danger")
        return redirect(url_for("report.report"))

    data = {
        "prediction": row["prediction"],
        "confidence": row["confidence"],
        "language": row["language"],
        "source_type": "Saved verification",
        "text": row["input_text"],
        "summary": row["summary"],
        "keywords": (row["keywords"] or "").split(", "),
        "verification": {
            "verdict": row["prediction"],
            "verification_confidence": row["confidence"],
            "explanation": "Saved verification result from AI FactShield Pro.",
        },
    }

    filename = f"verification_{history_id}.pdf"
    path = Path(Config.REPORT_FOLDER) / "pdf" / filename
    generate_pdf_report(data, path)
    save_report(session["user_id"], "pdf", filename)
    return send_file(
        path,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf",
    )
