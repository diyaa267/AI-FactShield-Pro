# Live News Sources

| Provider | Role | Secret | Notes |
|---|---|---:|---|
| NewsAPI | Primary article search / current headlines | `NEWS_API_KEY` | Backend-only integration |
| GNews | Primary search/live source | `GNEWS_API_KEY` | Free plan has a delay; real-time access requires an applicable paid/academic plan |
| Google Fact Check Tools | Fact-check evidence | `GOOGLE_FACTCHECK_API_KEY` | Evidence layer, not automatic truth |
| Google News RSS | No-key discovery fallback | No | Used for source discovery when API providers are unavailable |
| GDELT DOC 2.0 | No-key current-news/evidence fallback | No | Discovery/evidence diversity; not treated as authoritative |

## Policy

No single source is treated as proof. Independent source agreement, event/entity/date/number matching, and fact-check signals are combined before a verdict is produced.
