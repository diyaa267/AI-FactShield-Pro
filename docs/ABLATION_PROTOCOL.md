# Ablation Protocol

The research comparison is intentionally separated into three layers:

### A — ML only
Text enters the TF-IDF + LinearSVC classifier. No external evidence is used.

### B — ML + independent evidence
The ML signal is combined with independently retrieved/cited evidence. Duplicate sources are collapsed and supporting/contradicting evidence is scored.

### C — ML + cross-language evidence
The same evidence-aware decision layer uses multilingual retrieval. For Nadiad, a Gujarati claim searches Gujarati + Hindi + English; a Hindi claim searches Hindi + English + Gujarati; an English claim searches English + Gujarati + Hindi.

## Why C is not given a fixed accuracy in the default report
Web retrieval is dynamic. A fixed accuracy would only be reproducible if the exact retrieval snapshot were frozen. Therefore the project reports C as an implemented live component and provides an optional live evaluation mode. This avoids manufacturing a benchmark number.

## Reproduce A and B

```powershell
python scripts/research_ablation.py --mode ml
python scripts/research_ablation.py --mode replay
```

## Evaluate the live multilingual system

```powershell
python scripts/research_ablation.py --mode live
```

Save the resulting JSON together with the date/time and provider configuration if the live result is included in the final paper.
