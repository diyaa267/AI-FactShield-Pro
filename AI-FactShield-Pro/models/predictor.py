from .confidence import confidence_from_scores
from .fake_news_model import load_model

FAKE_TERMS = [
    "breaking", "urgent", "forward", "secret source", "miracle", "guaranteed", "100%", "instantly", "everyone", "tonight", "permanently", "free money", "secret government",
    "ब्रेकिंग", "तुरंत", "भेजें", "शेयर", "इनाम", "हमेशा के लिए", "मोकલો", "મોકલો", "શેર", "તુરંત", "બંધ થશે", "ઇનામ", "કાયમ માટે"
]
REAL_TERMS = [
    "official", "government", "research", "study", "scientists", "published", "peer-reviewed", "official website", "reuters", "according to", "report", "reported", "सत्तावार", "सरकार", "शोध", "वैज्ञानिक", "સરકારી", "અભ્યાસ", "વૈજ્ઞાનિક", "સત્તાવાર"
]


def detect_language(text):
    if any("\u0A80" <= c <= "\u0AFF" for c in text):
        return "Gujarati"
    if any("\u0900" <= c <= "\u097F" for c in text):
        return "Hindi"
    return "English"


def predict(text):
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
        # Do not allow a few suspicious words to override a strong trained signal.
        if fake >= real + 3 and label == "real":
            label = "fake"
            conf = max(conf, 72)
        elif real >= fake + 3 and label == "fake":
            label = "real"
            conf = max(55, conf - 5)
        model_type = "TF-IDF + Logistic Regression"
    else:
        if fake > real:
            label = "fake"
        elif real > fake:
            label = "real"
        else:
            label = "real" if len(text.split()) >= 12 else "fake"
        conf = confidence_from_scores(fake + (1 if label == "fake" else 0), real + (1 if label == "real" else 0))
        model_type = "Explainable keyword baseline"

    return {
        "prediction": label,
        "confidence": round(float(conf), 2),
        "language": detect_language(text),
        "model_type": model_type,
    }
