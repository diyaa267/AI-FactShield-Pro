# Live AI upgrade

## One-time training

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
py dataset\download_public_datasets.py --include-welfake --include-isot
py dataset\build_master_dataset.py
py scripts\train_large_model.py
py app.py
```

The training script uses a balanced sample capped at 80,000 rows to keep Windows RAM usage practical. It combines word-level and character-level TF-IDF features with a class-balanced LinearSVC. `models/large_model_metrics.json` records the real test accuracy from your downloaded dataset; no accuracy is hard-coded.

## Live evidence

Add `NEWS_API_KEY` and/or `GNEWS_API_KEY` to `.env` for broader current coverage. Google News RSS and GDELT remain no-key discovery layers.

## Important

A text classifier cannot know whether a brand-new story is true from wording alone. Current REAL/FAKE results are therefore evidence-first: current independent reporting is used when available, while ML is a fallback.
