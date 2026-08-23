from pathlib import Path
import pickle

BASE = Path(__file__).resolve().parents[1]

def load_model():
    path = BASE / "model.pkl"
    if path.exists():
        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass
    return {"type": "keyword_baseline"}
