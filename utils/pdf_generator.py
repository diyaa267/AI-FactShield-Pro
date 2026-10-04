from pathlib import Path
from datetime import datetime

def generate_pdf_report(data, output_path):
    """Generate a compact, professional PDF verification report."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle("FactShieldTitle", parent=styles["Title"], alignment=TA_CENTER,
                           textColor=colors.HexColor("#087ea4"), fontSize=22, spaceAfter=8)
    sub = ParagraphStyle("FactShieldSub", parent=styles["Normal"], alignment=TA_CENTER,
                         textColor=colors.HexColor("#555555"), fontSize=9, spaceAfter=18)
    body = ParagraphStyle("FactShieldBody", parent=styles["BodyText"], leading=15, spaceAfter=8)

    verification = data.get("verification") or {}
    verdict = str(verification.get("verdict", data.get("prediction", "unverified"))).upper()
    confidence = verification.get("verification_confidence", data.get("confidence", ""))

    story = [
        Paragraph("AI FACTSHIELD PRO", title),
        Paragraph("Multimodal Fake News Verification Report", sub),
        Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", body),
        Spacer(1, 8),
    ]

    table = Table([
        ["Verdict", verdict],
        ["Verification confidence", f"{confidence}%"],
        ["Language", str(data.get("language", ""))],
        ["Input type", str(data.get("source_type", "Text"))],
        ["Model signal", f"{str(data.get('prediction','')).upper()} ({data.get('confidence','')}%)"],
    ], colWidths=[160, 330])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#eef8fc")),
        ("TEXTCOLOR", (0,0), (0,-1), colors.HexColor("#087ea4")),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), .4, colors.HexColor("#d5e4ea")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("PADDING", (0,0), (-1,-1), 8),
    ]))
    story += [table, Spacer(1, 16)]
    story.append(Paragraph("<b>Why this result</b>", body))
    story.append(Paragraph(str(verification.get("explanation", "")), body))
    story.append(Paragraph("<b>Analyzed content</b>", body))
    story.append(Paragraph(str(data.get("text", "")).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"), body))

    best = verification.get("best_evidence")
    if best:
        story.append(Paragraph("<b>Best evidence</b>", body))
        evidence_text = (
            f"{best.get('source','News source')} — {best.get('title','')} "
            f"(match {best.get('score','')}%, {best.get('published','')})"
        )
        story.append(Paragraph(evidence_text, body))
        if best.get("link"):
            story.append(Paragraph(f"Source: {best['link']}", body))

    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Responsible-use note: a verification result is an evidence-assisted assessment, "
        "not a guarantee of truth. Always open the cited source before publishing or sharing.",
        sub
    ))
    doc.build(story)
    return output_path


# Backward-compatible helper used by older code.
def generate_text_report(data, output_path):
    return generate_pdf_report(data, output_path)
