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
- Explainable verdicts: **Likely True, Likely Fake, Misleading, Unverified**
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

The verification engine uses the local demo evidence pack for the placement demonstration. Results are deliberately presented as supporting evidence, with **Unverified** used when a non-demo claim has no local evidence.

## Project structure

The original AI-FactShield-Pro structure is preserved. Additional helper modules are placed under `utils/` so the project remains organized.

## Placement-ready verification improvements

- Evidence-first REAL/FAKE/MISLEADING/UNVERIFIED verdicts
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
- **MISLEADING**: related reporting exists but important wording/details do not match.
- **UNVERIFIED**: insufficient evidence.

Demo verification is fully offline and uses the clearly labelled local demo evidence pack. No live news API is required for the placement demonstration.

## Date-aware news verification
For placement demonstration, the verifier is intentionally offline. Exact matches against the four demo stories return deterministic REAL or FAKE results. Other user-entered claims remain UNVERIFIED unless the local demo evidence matches them; the ML classifier remains a supporting signal.


## Placement Demo Mode
The project includes four offline sample news cards with images and short video previews. Selecting a card loads the story into the detector and uses the local demo evidence pack, so the demonstration does not depend on live news APIs or internet access.
