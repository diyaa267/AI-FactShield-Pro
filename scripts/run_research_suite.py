"""Run the reproducible Nadiad research suite in one command."""
from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
for mode in ("ml", "replay"):
    print(f"\n=== Research mode: {mode} ===")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "research_ablation.py"), "--mode", mode], cwd=ROOT, check=True)
print("\nResearch suite complete. See models/research_ml_metrics.json and models/research_ablation_metrics.json")
