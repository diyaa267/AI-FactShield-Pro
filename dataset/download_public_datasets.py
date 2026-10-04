"""Download public research datasets used by AI FactShield Pro.

The project does NOT scrape or redistribute every news website. Instead this script
pulls openly published research datasets, normalizes them to text/label, and leaves
live current-news verification to NewsAPI/GNews/Google News RSS/GDELT.

Run from project root:
    py dataset/download_public_datasets.py
    py dataset/build_master_dataset.py
    py scripts/train_large_model.py

Optional large sources:
    py dataset/download_public_datasets.py --include-welfake --include-isot
"""
from __future__ import annotations
import argparse, csv, io, json, os, re, urllib.request, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "dataset" / "raw_public"
RAW.mkdir(parents=True, exist_ok=True)

SOURCES = {
    "liar": "https://github.com/tfs4/liar_dataset/archive/refs/heads/master.zip",
    "tallip": "http://www.iitp.ac.in/~ai-nlp-ml/resources/data/TALLIP-FakeNews-Dataset.zip",
    "ifnd": "https://raw.githubusercontent.com/sonalgarg174/Dataset/main/IFND.csv",
    "hindi_true": "https://raw.githubusercontent.com/Siddhartha15/Hindi-Fake-News-Detection/main/Data/true_news.csv",
    "hindi_fake": "https://raw.githubusercontent.com/Siddhartha15/Hindi-Fake-News-Detection/main/Data/fake_news.csv",
    "fakenewsnet_politifact_fake": "https://raw.githubusercontent.com/KaiDMML/FakeNewsNet/master/dataset/politifact_fake.csv",
    "fakenewsnet_politifact_real": "https://raw.githubusercontent.com/KaiDMML/FakeNewsNet/master/dataset/politifact_real.csv",
    "fakenewsnet_gossipcop_fake": "https://raw.githubusercontent.com/KaiDMML/FakeNewsNet/master/dataset/gossipcop_fake.csv",
    "fakenewsnet_gossipcop_real": "https://raw.githubusercontent.com/KaiDMML/FakeNewsNet/master/dataset/gossipcop_real.csv",
    "welfake": "https://zenodo.org/records/4561253/files/WELFake_Dataset.csv?download=1",
    "isot": "https://onlineacademiccommunity.uvic.ca/isot/wp-content/uploads/sites/7295/2023/02/ISOT_Fake_News_Dataset.zip",
}


def download(name: str, url: str, timeout=120):
    ext = ".zip" if url.lower().split("?")[0].endswith(".zip") else ".csv"
    path = RAW / f"{name}{ext}"
    if path.exists() and path.stat().st_size > 1000:
        print(f"[skip] {name}: {path.name}")
        return path
    print(f"[download] {name}")
    req = urllib.request.Request(url, headers={"User-Agent": "AI-FactShield-Pro-Dataset/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r, path.open("wb") as f:
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk: break
            f.write(chunk)
    print(f"[saved] {path} ({path.stat().st_size/1024/1024:.1f} MB)")
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--include-welfake", action="store_true", help="download ~245 MB WELFake from Zenodo")
    ap.add_argument("--include-isot", action="store_true", help="download ISOT dataset")
    args = ap.parse_args()
    selected = ["liar","tallip","ifnd","hindi_true","hindi_fake","fakenewsnet_politifact_fake","fakenewsnet_politifact_real","fakenewsnet_gossipcop_fake","fakenewsnet_gossipcop_real"]
    if args.include_welfake: selected.append("welfake")
    if args.include_isot: selected.append("isot")
    manifest=[]
    for name in selected:
        try:
            p=download(name,SOURCES[name]); manifest.append({"name":name,"url":SOURCES[name],"file":str(p.relative_to(ROOT))})
        except Exception as e:
            print(f"[warning] {name} failed: {e}")
    (RAW/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
    print(f"Done. Downloaded {len(manifest)} source files.")

if __name__ == "__main__": main()
