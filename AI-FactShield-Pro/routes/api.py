from flask import Blueprint, jsonify, request
from models.predictor import predict
from models.keyword_extractor import extract_keywords
from models.summarizer import summarize
from utils.verification import verify_claim
from utils.demo_news import get_demo_news

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.get("/health")
def health():
    return jsonify({"status": "ok", "service": "AI FactShield Pro", "features": ["text", "media", "evidence", "regional-language"]})

@api_bp.post("/predict")
def api_predict():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text is required"}), 400
    result = predict(text)
    result["keywords"] = extract_keywords(text)
    result["summary"] = summarize(text)
    result["verification"] = verify_claim(text, result)
    return jsonify(result)

@api_bp.get("/news")
def api_news():
    return jsonify({"results": get_demo_news(), "mode": "offline-demo"})
