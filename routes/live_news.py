from flask import Blueprint, jsonify, render_template, request
from urllib.parse import urlparse
from utils.live_news import CITIES, CATEGORIES, LANGUAGES, fetch_live_news, available_providers
from utils.verification import verify_claim
from models.predictor import predict
from utils.api_health import system_metadata

live_news_bp = Blueprint("live_news", __name__, url_prefix="/live-news")


@live_news_bp.get("/")
def index():
    city = "Nadiad"  # controlled research study area
    category = request.args.get("category", "All")
    language = request.args.get("language", "All")
    data = fetch_live_news(city, category, language, 12)
    return render_template(
        "live_news.html",
        data=data,
        cities=list(CITIES),
        categories=list(CATEGORIES),
        languages=list(LANGUAGES),
    )


@live_news_bp.get("/api")
def api():
    city = "Nadiad"  # controlled research study area
    category = request.args.get("category", "All")
    language = request.args.get("language", "All")
    limit = min(max(int(request.args.get("limit", 18)), 1), 50)
    return jsonify(fetch_live_news(city, category, language, limit))


@live_news_bp.get("/api/health")
def health():
    """Machine-readable deployment/provider health information."""
    payload = system_metadata()
    payload["status"] = "ok"
    return jsonify(payload)


@live_news_bp.post("/verify")
def verify():
    data = request.get_json(silent=True) or request.form
    claim = (data.get("claim") or data.get("title") or "").strip()
    city = (data.get("city") or "Nadiad").strip()
    if not claim:
        return jsonify({"error": "claim is required"}), 400
    model = predict(claim)
    verification = verify_claim(claim, model, city=city)
    return jsonify({
        "claim": claim,
        "city": city,
        "prediction": model,
        "verification": verification,
    })


@live_news_bp.post("/verify-article")
def verify_article():
    """Automatically verify one fetched live-news article; no manual claim entry."""
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    content = (data.get("content") or description).strip()
    source = (data.get("source") or "").strip()
    url = (data.get("url") or "").strip()
    city = (data.get("city") or "Nadiad").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400

    claim = title if not content else f"{title}. {content[:12000]}"
    model = predict(claim)
    source_domain = urlparse(url).netloc.lower().replace("www.", "") if url else source
    verification = verify_claim(claim, model, city=city, source_domain=source_domain, headline=title)
    return jsonify({
        "title": title,
        "city": city,
        "result": str(verification.get("verdict", "fake")).upper(),
        "confidence": verification.get("verification_confidence", 0),
        "model_prediction": model.get("prediction", ""),
        "model_confidence": model.get("confidence", 0),
        "explanation": verification.get("explanation", ""),
        "evidence": verification.get("evidence", [])[:6],
        "support_count": verification.get("support_count", 0),
        "contradiction_count": verification.get("contradiction_count", 0),
        "evidence_domains": verification.get("evidence_domains", 0),
        "model": model.get("model_type", ""),
        "evidence_confirmed": bool(verification.get("evidence_confirmed", False)),
        "providers": sorted({str(e.get("provider", "")) for e in verification.get("evidence", []) if e.get("provider")})
    })
