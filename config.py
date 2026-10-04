from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "ai-factshield-pro-dev-secret-change-me")
    NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
    GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY", "")
    GOOGLE_FACTCHECK_API_KEY = os.environ.get("GOOGLE_FACTCHECK_API_KEY", "")
    DATABASE = str(BASE_DIR / "database.db")
    UPLOAD_FOLDER = str(BASE_DIR / "uploads")
    REPORT_FOLDER = str(BASE_DIR / "reports")
    MAX_CONTENT_LENGTH = 80 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "webp", "mp4", "mov", "avi", "wav", "flac", "aiff"}
