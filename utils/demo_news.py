"""Offline demo news cards for AI FactShield Pro. No live/API news is used."""
from __future__ import annotations
import json
from pathlib import Path
BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "dataset" / "demo_news.json"
def get_demo_news():
    try:
        return json.loads(DATA.read_text(encoding="utf-8"))
    except Exception:
        return []
