# Research Basis — AI-FactShield Pro (2025–2026)

## Scope
The implementation uses Nadiad, Gujarat as a controlled geographical study area. This keeps live retrieval, evidence comparison, and evaluation reproducible for a final-semester engineering project.

## Research directions reflected in the implementation
1. **Iterative retrieval and verification** — FIRE, Findings of NAACL 2025: https://aclanthology.org/2025.findings-naacl.158/
2. **Redundant evidence filtering / multi-source reasoning** — IMRRF, NAACL 2025: https://aclanthology.org/2025.naacl-long.461/
3. **Cross-lingual fact-check retrieval** — EMNLP 2025 multilingual fact-checking work: https://aclanthology.org/2025.emnlp-main.1480/
4. **Multilingual/retrieval bias evaluation** — EACL 2026: https://aclanthology.org/2026.eacl-long.240/
5. **Verification-oriented reasoning** — LoGAR, Findings of ACL 2026: https://aclanthology.org/2026.findings-acl.238/

## Implemented engineering mapping
- Live providers: NewsAPI/GNews when configured, Google News RSS and GDELT fallback.
- Claim verification: live retrieval + independent evidence + fact-check evidence + trained ML classifier.
- Cross-language retrieval: Gujarati/English query variants for Nadiad.
- Evidence deduplication: domain/event similarity prevents simple reposts from being counted as independent corroboration.
- Iterative evidence search: multiple retrieval strategies are attempted before ML fallback.
- Binary product output: REAL or FAKE only in the public UI.
- External API testing: REST endpoints are tested with Postman; there is deliberately no API Testing page in the website.

## Important scientific limitation
The included ML model is a project model, not a claim of production-level accuracy. The report should present held-out metrics and live-evidence evaluation honestly rather than claiming 99% accuracy.
