from flask import Blueprint, jsonify, request
from models.predictor import predict
from models.keyword_extractor import extract_keywords
from models.summarizer import summarize
from utils.verification import verify_claim
from utils.demo_news import get_demo_news
from utils.live_news import fetch_live_news
from database.live_news import save_articles, save_verification, get_verification_history

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.get("/health")
def health():
    return jsonify({"status": "ok", "service": "AI FactShield Pro", "features": ["text", "media", "evidence", "regional-language", "live-city-news"]})

@api_bp.post("/predict")
def api_predict():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text is required"}), 400
    result = predict(text)
    result["keywords"] = extract_keywords(text)
    result["summary"] = summarize(text)
    result["verification"] = verify_claim(text, result, city=data.get("city"))
    return jsonify(result)

@api_bp.get("/news")
def api_news():
    city = "Nadiad"  # controlled research study area
    category = request.args.get("category", "All")
    language = request.args.get("language", "All")
    try:
        limit = min(max(int(request.args.get("limit", 18)), 1), 50)
    except ValueError:
        limit = 18
    data = fetch_live_news(city, category, language, limit)
    data["saved_to_database"] = save_articles(data.get("articles", []), city)
    return jsonify(data)

@api_bp.get("/news/nadiad")
def api_nadiad_news():
    try: limit = min(max(int(request.args.get("limit", 18)), 1), 50)
    except ValueError: limit = 18
    data = fetch_live_news("Nadiad", request.args.get("category", "All"), request.args.get("language", "All"), limit)
    data["saved_to_database"] = save_articles(data.get("articles", []), "Nadiad")
    return jsonify(data)

@api_bp.post("/verify")
def api_verify_news():
    data = request.get_json(silent=True) or {}
    claim = (data.get("claim") or data.get("text") or "").strip()
    city = (data.get("city") or "Nadiad").strip()
    if not claim:
        return jsonify({"error": "claim is required"}), 400
    model_result = predict(claim)
    verification = verify_claim(claim, model_result, city=city)
    save_verification(claim, city, verification)
    return jsonify({"claim": claim, "city": city, "result": str(verification.get("verdict", "fake")).upper(), "prediction": model_result, "verification": verification})

@api_bp.get("/verification-history")
def api_verification_history():
    try: limit = min(max(int(request.args.get("limit", 50)), 1), 100)
    except ValueError: limit = 50
    return jsonify({"count": limit, "items": [dict(row) for row in get_verification_history(limit)]})


@api_bp.get("/research/metrics")
def api_research_metrics():
    """Return the saved Nadiad research replay metrics for browser/Postman."""
    from pathlib import Path
    import json

    root = Path(__file__).resolve().parents[1]
    candidates = [
        root / "models" / "research_replay_metrics.json",
        root / "models" / "research_ablation_metrics.json",
    ]

    for path in candidates:
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8-sig"))
                if isinstance(payload, dict):
                    # Keep the existing research benchmark exactly as stored.
                    payload["status"] = "ok"
                    return jsonify(payload), 200
            except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
                continue

    return jsonify({
        "status": "error",
        "message": "Research metrics file not found. Expected models/research_replay_metrics.json or models/research_ablation_metrics.json."
    }), 500
