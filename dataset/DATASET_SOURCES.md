# AI FactShield Pro – Dataset Sources

The project uses public research datasets for offline ML training and live news providers for current evidence. It does **not** copy every article from every media website.

## Public datasets included in the downloader

- WELFake – 72,134 usable records, 35,028 real / 37,106 fake (Zenodo).
- ISOT Fake News Dataset – large real/fake article corpus.
- LIAR – 12,836 fact-checked statements; six truthfulness labels mapped to binary by dropping `half-true`.
- TALLIP multilingual fake-news dataset – English, Hindi and other languages/domains.
- IFND – India-focused real/fake dataset.
- Hindi Fake News Detection dataset – true/fake Hindi news.
- FakeNewsNet metadata – Politifact/GossipCop real/fake article titles and URLs.

Run `py dataset/download_public_datasets.py --include-welfake --include-isot`, then `py dataset/build_master_dataset.py`, then `py scripts/train_large_model.py`.

The downloader keeps source URLs in `dataset/raw_public/manifest.json`. Always follow the original dataset's license/citation terms.

## Live evidence

The live verifier searches Google News RSS, NewsAPI/GNews when configured, source-specific feeds, official Kheda/Nadiad domains and GDELT. Multiple independent domains are counted separately, duplicate/reposted headlines are deduplicated, date/numeric conflicts are considered, and fact-check/debunk markers are boosted.
