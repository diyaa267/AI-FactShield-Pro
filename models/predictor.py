from __future__ import annotations

from pathlib import Path
import pickle
import re
from .confidence import confidence_from_scores
from .fake_news_model import load_model

BASE = Path(__file__).resolve().parents[1]
LARGE_MODEL = BASE / "models" / "large_live_model.pkl"

FAKE_TERMS = [
    "breaking", "urgent", "forward", "secret source", "miracle", "guaranteed", "100%", "instantly",
    "everyone", "tonight", "permanently", "free money", "secret government", "share this",
    "ब्रेकिंग", "तुरंत", "भेजें", "शेयर", "इनाम", "हमेशा के लिए",
    "મોકલો", "શેર", "તુરંત", "બંધ થશે", "ઇનામ", "કાયમ માટે"
]
REAL_TERMS = [
    "official", "government", "research", "study", "scientists", "published", "peer-reviewed",
    "official website", "reuters", "according to", "report", "reported", "सत्तावार", "सरकार",
    "शोध", "वैज्ञानिक", "સરકારી", "અભ્યાસ", "વૈજ્ઞાનિક", "સત્તાવાર"
]


def detect_language(text: str) -> str:
    if any("\u0A80" <= c <= "\u0AFF" for c in text):
        return "Gujarati"
    if any("\u0900" <= c <= "\u097F" for c in text):
        return "Hindi"
    return "English"


def _load_large():
    if not LARGE_MODEL.exists():
        return None
    try:
        with LARGE_MODEL.open("rb") as f:
            return pickle.load(f)
    except Exception:
        return None


def _large_predict(text: str):
    bundle = _load_large()
    if not bundle:
        return None
    try:
        features = bundle["features"]
        clf = bundle["classifier"]
        x = features.transform([text])
        label = str(clf.predict(x)[0]).lower()
        if hasattr(clf, "decision_function"):
            margin = float(clf.decision_function(x)[0])
            # Stable sigmoid-like confidence from the classifier margin.
            raw = 1.0 / (1.0 + __import__("math").exp(-min(8.0, max(-8.0, margin))))
            conf = max(raw, 1 - raw) * 100.0
        elif hasattr(clf, "predict_proba"):
            conf = max(map(float, clf.predict_proba(x)[0])) * 100.0
        else:
            conf = 70.0
        if label not in {"real", "fake"}:
            label = "fake" if label in {"1", "true", "unreliable"} else "real"
        return label, round(max(50.0, min(98.0, conf)), 2), "TF-IDF word+character ensemble"
    except Exception:
        return None


def predict(text: str) -> dict:
    text = str(text or "").strip()
    large = _large_predict(text)
    if large:
        label, conf, model_type = large
        return {"prediction": label, "confidence": conf, "confidence_type": "classifier-margin score (not calibrated probability)", "language": detect_language(text), "model_type": model_type}

    model = load_model()
    low = text.lower()
    fake = sum(low.count(t.lower()) for t in FAKE_TERMS)
    real = sum(low.count(t.lower()) for t in REAL_TERMS)
    model_label, model_conf = None, None

    if hasattr(model, "predict"):
        try:
            model_label = str(model.predict([text])[0]).lower()
            if hasattr(model, "predict_proba"):
                probs = model.predict_proba([text])[0]
                model_conf = round(float(max(probs)) * 100, 2)
        except Exception:
            pass

    if model_label in {"fake", "real"}:
        label = model_label
        conf = model_conf or 65
        model_type = "TF-IDF + Logistic Regression (fallback)"
    else:
        label = "fake" if fake > real else "real"
        conf = confidence_from_scores(fake + (1 if label == "fake" else 0), real + (1 if label == "real" else 0))
        model_type = "Keyword fallback"

    return {"prediction": label, "confidence": round(float(conf), 2), "confidence_type": "model probability/heuristic score", "language": detect_language(text), "model_type": model_type}
