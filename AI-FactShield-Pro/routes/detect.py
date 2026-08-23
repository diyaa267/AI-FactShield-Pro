from pathlib import Path
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, send_from_directory
from models.predictor import predict
from models.keyword_extractor import extract_keywords
from models.summarizer import summarize
from database.history import add_history
from utils.validation import clean_text
from utils.helpers import allowed_file, safe_name
from utils.media import extract_pdf_text, extract_image_text, extract_video_text, extract_audio_text
from utils.verification import verify_claim
from config import Config
from utils.demo_news import get_demo_news


detect_bp = Blueprint("detect", __name__, url_prefix="/detect")


def analyze_text(text, source_type="Text", filename=None, media_url=None):
    text = clean_text(text)
    if not text:
        return None
    model_result = predict(text)
    model_result["text"] = text
    model_result["keywords"] = extract_keywords(text)
    model_result["summary"] = summarize(text)
    model_result["source_type"] = source_type
    model_result["filename"] = filename
    model_result["media_url"] = media_url
    model_result["verification"] = verify_claim(text, model_result)
    return model_result


@detect_bp.route("/", methods=["GET", "POST"])
def detect():
    result = None
    if request.method == "POST":
        text = clean_text(request.form.get("text"))
        result = analyze_text(text, "Text")
        if not result:
            flash("Please enter news content first.", "warning")
            return render_template("detect.html", result=None, demo_news=get_demo_news())
        _save_history(result)
    return render_template("detect.html", result=result, demo_news=get_demo_news())


@detect_bp.route("/demo-media", methods=["POST"])
def demo_media():
    """Analyze a packaged demo media item without requiring a real file upload."""
    claim = clean_text(request.form.get("claim"))
    source_type = request.form.get("source_type", "Image")
    filename = request.form.get("filename", "demo-media")
    media_url = None
    if source_type == "Image":
        media_url = url_for("static", filename=f"images/demo/{filename}")
    elif source_type == "Video":
        media_url = url_for("static", filename=f"videos/{filename}")
    elif source_type == "Audio":
        media_url = url_for("static", filename=f"audio/{filename}")

    result = analyze_text(claim, source_type, filename, media_url)
    if not result:
        flash("Demo media claim is empty.", "warning")
        return redirect(url_for("detect.detect"))
    result["demo_media"] = True
    _save_history(result)
    return render_template("detect.html", result=result, demo_news=get_demo_news())


@detect_bp.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or not file.filename:
        flash("Select a file first.", "warning")
        return redirect(url_for("detect.detect"))
    if not allowed_file(file.filename, Config.ALLOWED_EXTENSIONS):
        flash("Unsupported file type.", "danger")
        return redirect(url_for("detect.detect"))

    filename = safe_name(file.filename)
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext in {"png", "jpg", "jpeg", "webp"}:
        folder_name = "images"
    elif ext == "pdf":
        folder_name = "pdf"
    elif ext in {"mp4", "mov", "avi"}:
        folder_name = "videos"
    elif ext in {"wav", "flac", "aiff"}:
        folder_name = "audio"
    else:
        folder_name = "documents"
    folder = Path(Config.UPLOAD_FOLDER) / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / filename
    file.save(path)

    extractors = {
        "txt": lambda p: Path(p).read_text(encoding="utf-8", errors="ignore"),
        "pdf": extract_pdf_text,
        "png": extract_image_text, "jpg": extract_image_text, "jpeg": extract_image_text, "webp": extract_image_text,
        "mp4": extract_video_text, "mov": extract_video_text, "avi": extract_video_text,
        "wav": extract_audio_text, "flac": extract_audio_text, "aiff": extract_audio_text,
    }
    extractor = extractors.get(ext)
    text = extractor(path) if extractor else ""

    # The claim box can provide fallback text when a media file has no
    # extractable OCR/speech text. This is especially useful for demo videos.
    fallback_text = clean_text(request.form.get("text"))
    if not text.strip() and fallback_text:
        text = fallback_text

    if text.startswith("PDF extraction failed:"):
        flash(text, "danger")
        return redirect(url_for("detect.detect"))
    if not text.strip():
        if ext in {"png", "jpg", "jpeg", "webp"}:
            flash("Image saved, but OCR text could not be extracted. Install Tesseract OCR for multilingual image reading.", "warning")
        elif ext in {"mp4", "mov", "avi"}:
            flash("Video saved. OCR requires OpenCV + Tesseract; no readable frame text was found.", "warning")
        elif ext in {"wav", "flac", "aiff"}:
            flash("Audio saved, but speech could not be transcribed. WAV speech recognition needs an available speech engine/internet.", "warning")
        else:
            flash("No readable text was found in the uploaded file.", "warning")
        return redirect(url_for("detect.detect"))

    source_type = {"pdf":"PDF", "txt":"Document", "png":"Image", "jpg":"Image", "jpeg":"Image", "webp":"Image",
                   "mp4":"Video", "mov":"Video", "avi":"Video", "wav":"Audio", "flac":"Audio", "aiff":"Audio"}.get(ext, "File")
    media_url = url_for("detect.uploaded_media", folder=folder_name, filename=filename)
    result = analyze_text(text, source_type, filename, media_url)
    if not result:
        flash("No readable claim was found. Add a claim in the Claim or News Content box and process the media again.", "warning")
        return redirect(url_for("detect.detect"))
    _save_history(result)
    return render_template("detect.html", result=result, demo_news=get_demo_news())


@detect_bp.route("/uploaded-media/<folder>/<filename>")
def uploaded_media(folder, filename):
    """Serve an uploaded media file back to the verification page for preview."""
    allowed_folders = {"images", "videos", "audio", "pdf", "documents"}
    if folder not in allowed_folders:
        return ("Not found", 404)
    return send_from_directory(Path(Config.UPLOAD_FOLDER) / folder, filename)


def _save_history(result):
    user_id = session.get("user_id")
    if user_id:
        verification = result.get("verification", {})
        add_history(
            user_id,
            result["text"],
            verification.get("verdict", result["prediction"]),
            verification.get("verification_confidence", result["confidence"]),
            result["language"],
            ", ".join(result["keywords"]),
            result["summary"],
        )
    else:
        # Do not block demo usage: results remain visible even when not logged in.
        pass
