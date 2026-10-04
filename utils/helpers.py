from pathlib import Path
from werkzeug.utils import secure_filename

def allowed_file(filename, allowed):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed

def safe_name(filename):
    return secure_filename(filename)

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)
