# AI-FactShield Pro — Live AI/ML Architecture

**Only final labels:** REAL / FAKE.

The app does NOT use stored news as its live feed. Live Nadiad news is fetched from configured live sources. The ML model is trained from a large multilingual historical dataset and predicts each newly fetched article. Independent live evidence is then used as a verification signal.

## Large training data
Zenodo record 10.5281/zenodo.11408513 contains Gujarati, Hindi, Marathi and Telugu fake/real news archives totaling about 194.2 MB. The four downloadable archives have published MD5 checksums and are downloaded by `dataset/download_large_datasets.py`.

## Live path
`Live Nadiad source -> article text -> language-aware preprocessing -> REAL/FAKE ML prediction -> independent live evidence -> final REAL/FAKE`

No static/demo article is used as the live feed.

## Important
A classifier is a prediction system, not a mathematical proof of truth. The UI is limited to REAL/FAKE as requested, but the backend keeps confidence and evidence metadata for auditability.
