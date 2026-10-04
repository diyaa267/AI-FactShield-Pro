from flask import Blueprint, render_template
from pathlib import Path
import json

research_bp = Blueprint("research", __name__)
ROOT = Path(__file__).resolve().parents[1]


def _read_json(name):
    path = ROOT / "models" / name
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


@research_bp.get("/research")
def research():
    ml = _read_json("research_ml_metrics.json")
    replay = _read_json("research_replay_metrics.json")
    general = _read_json("large_model_metrics.json")
    return render_template(
        "research.html",
        ml=ml,
        replay=replay,
        general=general,
    )
