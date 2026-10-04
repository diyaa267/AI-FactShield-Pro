# AI-FactShield Pro — Nadiad Research Evaluation (2025–2026)

## 1. Research objective

The system is evaluated as a **controlled Nadiad misinformation-verification study**, rather than as a claim that the model generalizes to all Indian news.

The evaluation separates:

1. **ML-only baseline** — the trained TF-IDF word+character model makes the binary decision.
2. **Evidence replay** — the same ML signal is combined with a cited evidence document and the project's evidence-scoring/contradiction logic.
3. **Live verification** — the deployed retrieval stack can be evaluated separately with changing Internet evidence.

## 2. Dataset policy

`dataset/nadiad_verified_claims_2025_2026.csv` is a small, manually curated **evaluation benchmark**, not training data.

- 8 real Nadiad claims are sourced from 2025–2026 reporting.
- 4 false Nadiad-attribution claims come from documented Fact Crescendo fact-checks because recent Nadiad-specific false-claim coverage is sparse in indexed sources.
- Each row stores the claim, label, date, source, URL, source title and an evidence excerpt.
- The benchmark must not be described as a representative statistical sample of Nadiad news.

## 3. Results

### General model evaluation already in the project

The existing balanced general dataset contains 50 rows (25 real / 25 fake). The held-out test has 13 records and previously produced **76.92% accuracy**, with confusion matrix `[[5,2],[1,5]]`.

### Nadiad pilot benchmark

On the 12-row Nadiad benchmark:

| System | Accuracy | Fake Precision | Fake Recall | Fake F1 | Macro F1 |
|---|---:|---:|---:|---:|---:|
| ML-only | 75.00% | 100.00% | 25.00% | 40.00% | 62.11% |
| Evidence replay | 100.00%* | 100.00%* | 100.00%* | 100.00%* | 1.00* |

`*` The evidence-replay number is **not a live production accuracy**. It is a controlled replay using the cited benchmark evidence documents so that the evidence-combination layer can be tested reproducibly. The sample is only 12 claims and includes a deliberately curated fact-check set. It must not be presented as proof of 100% real-world accuracy.

The ML-only result is intentionally retained because it demonstrates the research problem: on this pilot set the text classifier predicted all four false Nadiad-attribution claims as REAL, while the evidence layer is designed to catch source/location contradictions.

## 4. Ablation interpretation

The project therefore demonstrates the following research question:

> **Does adding independent evidence change decisions that a text-only classifier gets wrong?**

On this small benchmark, yes: the evidence replay corrected all four false Nadiad-attribution cases. This is an evaluation observation, not a universal accuracy claim.

Cross-language retrieval is implemented in the live retrieval layer: Gujarati claims search Gujarati + English + Hindi sources; Hindi claims search Hindi + English + Gujarati; English claims search English + Gujarati + Hindi. This is intended to reduce dependence on a single language's local coverage.

## 5. Reproduction commands

From the project root:

```powershell
python scripts/research_ablation.py --mode ml
python scripts/research_ablation.py --mode replay
```

Optional live benchmark (requires the configured Internet/API providers and may vary with current search results):

```powershell
python scripts/research_ablation.py --mode live
```

The latest metrics are written to:

`models/research_ablation_metrics.json`

The same metrics are available through:

`GET /api/research/metrics`

for Postman/API demonstration.

## 6. Research limitations

- The Nadiad benchmark is small and manually curated.
- Four false examples are historical Nadiad-attribution fact-checks, not 2025–2026 events.
- Live web retrieval is dynamic and can change by date/provider.
- The current ML model is a TF-IDF + LinearSVC classifier, not a large language model.
- Confidence values from the LinearSVC margin are not calibrated probabilities.
- The project should therefore report benchmark results transparently rather than claiming production-level 99% accuracy.
