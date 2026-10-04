# AI FactShield Pro

**Fake News Detection & Evidence Verification System for Regional Languages**

AI FactShield Pro is a Flask-based placement project designed as a practical information-trust workflow. It combines a lightweight ML/keyword signal with explainable evidence search and multimodal extraction.

## Core capabilities

- Text verification with ML prediction, confidence, language, summary and keywords
- English, Hindi and Gujarati starter language detection
- Image OCR workflow
- PDF text extraction
- Video frame OCR workflow
- Audio/WAV speech-to-text workflow
- Browser voice input using Web Speech API
- Offline demo evidence pack for placement demonstration
- Explainable verdicts: **REAL or FAKE**
- Evidence source, match score and publication date
- Login, saved history, dashboard and CSV reports
- Responsive dark futuristic UI

## Run on Windows PowerShell

```powershell
cd AI-FactShield-Pro
py -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

> If `python` is not recognized but `py --version` works, use `py` to create the virtual environment as shown above.

## Multimodal notes

Image/video OCR uses `pytesseract`, which is a Python wrapper around the Tesseract OCR engine. For full local OCR, install Tesseract separately and ensure it is available in PATH. The application does not crash when it is unavailable; it reports that the extraction engine is missing.

Video frame extraction uses OpenCV. Audio upload recognition supports WAV/FLAC/AIFF through SpeechRecognition when a compatible speech engine/network is available. Chrome/Edge browser voice capture is available without a Python audio driver.

## Evidence layer

The verification engine uses the local demo evidence pack for the placement demonstration. Live evidence is preferred; when live evidence is inconclusive, the trained model supplies the binary REAL/FAKE fallback and the response exposes the decision basis.

## Project structure

The original AI-FactShield-Pro structure is preserved. Additional helper modules are placed under `utils/` so the project remains organized.

## Placement-ready verification improvements

- Evidence-first REAL/FAKE claim verification
- Four offline demo news stories with image + video previews
- Trusted-source weighting for Reuters, AP, BBC, RBI, PIB and other sources
- Dated demo evidence fallback for offline placement demonstrations
- Balanced multilingual training data for English, Hindi and Gujarati
- Text, image/OCR, PDF, video-frame OCR and audio transcription pipeline
- Confidence, source, evidence and supporting-result display
- Responsive verification UI with four clickable offline demo stories
- Improved feedback page layout

See `docs/demo_claims.md` for ready-to-test placement examples.



## Quick Start (Windows)

Open the folder that contains `app.py` and `requirements.txt`.

### Easiest
Double-click `START_PROJECT.bat`.

### PowerShell
```powershell
py -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000`.

### Verification behavior
- **REAL**: strong supporting evidence from offline demo evidence or the verified demo evidence pack.
- **FAKE**: strong contradiction, reliable fact-check evidence, or a strong viral-hoax/model signal.
- **REAL**: current evidence strongly corroborates the claim.
- **FAKE**: current evidence directly contradicts/debunks the claim.
- If live evidence is insufficient, the binary ML fallback is marked low-confidence; it is not presented as source-confirmed fact.

Demo verification is fully offline and uses the clearly labelled local demo evidence pack. No live news API is required for the placement demonstration.

## Date-aware news verification
The live verifier is API/evidence-first. Exact matches against packaged demo evidence remain deterministic. For other claims it searches NewsAPI, GNews, Google News RSS, and official/local Nadiad sources; the ML classifier is only a low-confidence fallback when evidence is insufficient.


## Placement Demo Mode
The project includes four offline sample news cards with images and short video previews. Selecting a card loads the story into the detector and uses the local demo evidence pack, so the demonstration does not depend on live news APIs or internet access.

## Live City News Verification

AI FactShield Pro now includes a placement-ready live news layer for Gujarat cities:

- Nadiad
- Vadodara
- Surat
- Rajkot
- Gandhinagar

### News sources and providers

The live module uses a hybrid approach:

1. **NewsAPI** — current article search when `NEWS_API_KEY` is configured.
2. **GNews** — current multilingual article search when `GNEWS_API_KEY` is configured.
3. **Google News RSS fallback** — source discovery when API keys are unavailable or a provider does not return enough regional coverage.
4. Regional publisher queries include **Sandesh, Divya Bhaskar, Gujarat Samachar, TV9 Gujarati, ABP Asmita and Zee 24 Kalak** where indexed results are available. Publisher availability depends on the provider/index and is never hard-coded as proof of truth.

### Live verification flow

Select a city → load current news → paste a current claim → the system searches current reporting and compares evidence across sources.

Verdicts:

- **REAL** — strong corroboration from independent domains or strong official/trusted evidence.
- **FAKE** — direct contradiction or explicit fact-check/false evidence.
- **REAL** — corroborated by strong current evidence.
- **FAKE** — contradicted/debunked by strong current evidence.
- **Low-confidence fallback** — shown only when live evidence is insufficient.

The local ML classifier is a supporting signal only. It does not override strong current evidence.

### API keys

Copy `.env.example` to `.env` for local development:

```text
NEWS_API_KEY=your_newsapi_key
GNEWS_API_KEY=your_gnews_key
```

Never commit `.env` or real API keys to GitHub. On Render, add the keys under **Environment Variables**.

### Useful endpoints

- `/live-news/` — live city news UI
- `/live-news/api?city=Nadiad&category=All&language=All` — live feed JSON
- `/live-news/verify` — current claim verification
- `/api/news?city=Nadiad` — public JSON news endpoint


## Live Nadiad News Verification

The live verification module is intentionally scoped to **Nadiad, Gujarat**. It uses: 
- NewsAPI for current article discovery.
- GNews for a second independent news search.
- Google News RSS as a no-key fallback/discovery layer.
- Kheda District Government and Nadiad Municipal Corporation domains as official/local evidence sources when indexed.

The project ML model is trained on labeled fake/real news data already included in `dataset/`. For a production retraining run, a documented public dataset such as the Kaggle ISOT Fake News dataset can be used; do not commit third-party data unless its license permits redistribution.

Set `NEWS_API_KEY` and `GNEWS_API_KEY` in `.env` locally and in Render environment variables. Never commit `.env`.


## Nadiad Research Version
This version is scoped to **Nadiad, Gujarat** for controlled real-time misinformation verification. The website has no API Testing page. Use the included `docs/postman_collection.json` in Postman to test the REST APIs.

### Main API endpoints
- `GET /api/health`
- `GET /api/news/nadiad?limit=10`
- `POST /api/verify`
- `POST /live-news/verify-article`
- `GET /api/verification-history?limit=20`

### Run
```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python app.py
```
Then open `http://127.0.0.1:5000`.

## Research Evaluation Upgrade

This Nadiad research build includes a reproducible evaluation benchmark and ablation harness:

- `dataset/nadiad_verified_claims_2025_2026.csv`
- `docs/RESEARCH_EVALUATION_2025_2026.md`
- `scripts/research_ablation.py`
- `models/research_ablation_metrics.json`
- `GET /api/research/metrics` for Postman

The benchmark is kept separate from training data. The evidence-replay score is a controlled benchmark, not a claim of 100% live accuracy.
