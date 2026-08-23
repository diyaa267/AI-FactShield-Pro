import csv
from pathlib import Path

def export_history(rows, output_path):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID","Prediction","Confidence","Language","Keywords","Created"])
        for r in rows:
            writer.writerow([r["id"], r["prediction"], r["confidence"], r["language"], r["keywords"], r["created_at"]])
    return output_path
