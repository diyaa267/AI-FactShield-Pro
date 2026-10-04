# Research Results — AI-FactShield Pro (Nadiad Study Area)

## Experiment matrix

| Experiment | What is measured | Current result | Status |
|---|---|---:|---|
| ML-only baseline | Text classifier only | Accuracy 75.00%, Macro F1 62.11% | Reproducible |
| ML + evidence replay | ML plus frozen benchmark evidence | Accuracy 100.00%, Macro F1 100.00% | Controlled replay only |
| Cross-language retrieval | Gujarati/Hindi/English evidence retrieval | Implemented in live pipeline | Dynamic; no fixed score claimed |

## Interpretation

The evidence-aware replay corrects the location-misattribution errors that the text-only classifier misses on this small benchmark. This supports the engineering hypothesis that independent evidence is useful for local misinformation verification.

The 100% replay result is **not** a production accuracy claim. It is a deterministic test over 12 curated cases and their cited evidence documents.

## General ML benchmark

The balanced general dataset contains 50 rows (25 fake / 25 real), with 37 training rows and 13 held-out test rows. The saved model evaluation reports 76.92% held-out accuracy and confusion matrix `[[5,2],[1,5]]` with labels `[fake, real]`.

## Reproduction

```powershell
python scripts/research_ablation.py --mode ml
python scripts/research_ablation.py --mode replay
```

Optional live retrieval evaluation:

```powershell
python scripts/research_ablation.py --mode live
```

The live result depends on current provider availability and Internet search results and should be stored with a timestamp if used in the final report.
