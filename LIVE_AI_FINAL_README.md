# AI-FactShield Pro — Live Evidence Verification Build

## What this build does

AI-FactShield Pro is an evidence-first fake-news analysis system for regional/local news. It does **not** assume that an ML classifier can know whether a newly published event happened.

The live pipeline is:

**News API → normalize/dedupe → article content → ML signal → independent evidence search → fact-check/official evidence → source diversity → REAL / FAKE**

## Live providers

### API-first
- **NewsAPI** — article discovery and live/top-headline workflows.
- **GNews** — search and live news ingestion.
- **Google Fact Check Tools** — optional ClaimReview/fact-check evidence.

### Resilience/fallback
- Google News RSS
- GDELT DOC 2.0

A provider outage does not become a FAKE verdict.

## Environment variables

```env
NEWS_API_KEY=
GNEWS_API_KEY=
GOOGLE_FACTCHECK_API_KEY=
SECRET_KEY=
```

Never commit real API keys. Set them in Render Environment Variables or the local `.env` file.

## Verdict policy

### VERIFIED REAL
Strong independent current reporting corroborates the same event.

### FAKE
Strong contradictory evidence or matching fact-check/debunk evidence is found.

### Binary fallback
There is not enough independent evidence. The ML result is displayed separately instead of being presented as proof.

This prevents the dangerous rule **“no evidence = fake.”**

## Bundled ML model

The included classifier is a secondary signal:
- word TF-IDF + character TF-IDF features
- balanced LinearSVC
- 50 deduplicated labeled rows in the bundled corpus
- held-out test: 13 rows
- measured accuracy: **76.92%**
- macro F1: **0.77**

This is **not** a claim of production-grade 99% accuracy. For a serious deployment, the next training cycle should use a much larger licensed Gujarati/Hindi/English corpus with a time-based unseen test set.

## Health endpoint

After deployment:

`/live-news/api/health`

It reports provider configuration without exposing API keys.

## Local run

```bash
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

## Deployment

Use the root folder of this ZIP as the application root. Do not deploy the removed legacy nested duplicate project.

## Engineering tests

The build includes `tests/test_live_engineering.py` covering:
- provider article normalization/source classification
- duplicate suppression
- the critical rule that the public UI has only REAL/FAKE; inconclusive evidence falls back to the trained ML model and records `decision_basis=ml_fallback`

## API references

- NewsAPI: https://newsapi.org/docs/endpoints
- GNews: https://gnews.io/
- Google Fact Check / ClaimReview: https://developers.google.com/search/docs/appearance/structured-data/factcheck
- GDELT DOC 2.0: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/

## API Testing Lab
The project now includes a first-class **API Testing** module at `/api-testing/`.
It supports GET/POST/PUT/PATCH/DELETE/HEAD/OPTIONS, JSON request bodies, custom headers, status-code PASS/FAIL, response headers/body, and response-time measurement. Built-in presets test the project's health and live-news APIs.

For deployed environments, private-network targets are blocked to reduce SSRF risk. Localhost is allowed for local development/testing.


## MODEL-95 LIVE VERIFICATION PATCH

Live article verification now retrieves evidence from the headline instead of the full scraped article body, and allows a strong exact/near-exact match from a recognized publisher to override the small ML fallback when no contradiction is found. This improves current-news false negatives; it does not guarantee 95% accuracy on arbitrary future news.
