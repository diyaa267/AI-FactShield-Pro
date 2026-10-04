# AI-FactShield Pro — Model Card

## Role
The local classifier is a **secondary linguistic signal**. It must not be presented as a ground-truth oracle for newly published events.

## Current bundled model
- Feature representation: word TF-IDF (1–2 grams) + character TF-IDF (3–5 grams)
- Classifier: balanced LinearSVC
- Bundled training corpus: project-local labeled data consolidated into `dataset/master_large_real_fake.csv`
- Current deduplicated corpus in this build: 50 balanced labeled rows
- Held-out evaluation: 13 rows
- Accuracy: 76.92%
- Macro F1: 0.77

## Why live evidence is required
A language classifier can learn writing patterns but cannot know whether a newly reported event actually happened. Therefore the production decision layer searches current independent sources, checks event/entity/number overlap, detects fact-check/debunk markers, and counts independent domains.

## Verdict policy
- **VERIFIED REAL**: strong independent corroboration.
- **FAKE**: strong contradiction or matching fact-check/debunk evidence.
- The live verifier has a binary REAL/FAKE public output. When evidence is insufficient, `decision_basis=ml_fallback` identifies that the ML model supplied the binary decision.

## Production training recommendation
Before publishing a model-quality benchmark, replace the small bundled corpus with a large, licensed, deduplicated Gujarati/Hindi/English fact-check/news dataset and run a time-based unseen test. Never manufacture samples to inflate accuracy.
