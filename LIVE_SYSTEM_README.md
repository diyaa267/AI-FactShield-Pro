# AI FactShield Pro — Live Internet Verification Build

## Actual flow
Internet → News APIs/RSS/Feeds → Current articles → Title + live article content → Language detection → ML prediction → Claim extraction → Independent web/news evidence + fact-check sources + official sources → Evidence engine → Source reliability → Support/Contradiction → Final REAL/FAKE + confidence + evidence.

## Important
- The Live News page does **not** use `dataset/news.csv`, `demo_news.json`, or `demo_evidence.json` as its news feed or evidence.
- Current stories are fetched from the Internet on request.
- Article content is fetched best-effort from the live article URL and kept only in memory for the request; this live fetcher does not save it to the training dataset.
- The original article's own domain is excluded from independent-evidence counting during automatic article verification.
- Evidence can come from Google News RSS, NewsAPI/GNews when configured, GDELT, Google Fact Check API when configured, publisher-specific feeds, and official-source feeds.
- A lack of evidence is not automatically treated as proof of fake news. Because the requested UI is binary, the system falls back conservatively to the ML signal when no live evidence is found and marks that evidence was not confirmed.

## API keys
Copy `.env.example` to `.env` and add keys if available:
- NEWS_API_KEY
- GNEWS_API_KEY
- GOOGLE_FACTCHECK_API_KEY

Google News RSS and GDELT can work without paid API keys, subject to Internet/provider availability.

## Run
Use the existing project startup method. Do **not** run the large dataset downloader just to open Live News.
