# AI-FactShield Pro — Live Engineering Architecture

```text
                         ┌─────────────────────┐
                         │   Live News APIs     │
                         │ NewsAPI / GNews      │
                         └──────────┬──────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
          Google News RSS        GDELT          Article URL
                 │                  │                  │
                 └──────────────────┼──────────────────┘
                                    ▼
                         ┌─────────────────────┐
                         │ Normalize / Dedupe  │
                         │ date + source + URL │
                         └──────────┬──────────┘
                                    ▼
                         ┌─────────────────────┐
                         │  Content Extraction │
                         └──────────┬──────────┘
                                    ▼
                         ┌─────────────────────┐
                         │ Local ML Classifier │
                         │ secondary signal    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Evidence Retrieval  │
                         │ independent sources │
                         │ fact-check / govt   │
                         └──────────┬──────────┘
                                    ▼
                         ┌─────────────────────┐
                         │ Evidence Scoring    │
                         │ event/entity/date   │
                         │ numbers + diversity │
                         └──────────┬──────────┘
                                    ▼
               ┌────────────────────┼────────────────────┐
               ▼                    ▼                    ▼
        REAL                    FAKE
```

## Core principle
No single publisher, API, or ML prediction is treated as proof.

## API secrets
Set `NEWS_API_KEY`, `GNEWS_API_KEY`, and optionally `GOOGLE_FACTCHECK_API_KEY` as deployment environment variables. Never commit real keys to Git or JavaScript.

## Resilience
If a paid/API provider is unavailable, Google News RSS and GDELT remain available as discovery/evidence sources. A provider outage must not be converted into a FAKE verdict.

## Uncertainty
The public product intentionally exposes only REAL/FAKE. Independent live evidence is preferred; when evidence is inconclusive, the trained ML classifier supplies the binary fallback and the API reports the decision basis.
