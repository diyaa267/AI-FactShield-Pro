from pathlib import Path
import pickle
import csv

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "dataset" / "train.csv"

def train():
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
    except ImportError:
        print("scikit-learn is not installed. Run: pip install -r requirements.txt")
        return

    texts, labels = [], []
    with open(DATA, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            texts.append(row["text"])
            labels.append(row["label"])

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1,2), sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=1000))
    ])
    pipeline.fit(texts, labels)

    with open(BASE / "model.pkl", "wb") as f:
        pickle.dump(pipeline, f)
    with open(BASE / "vectorizer.pkl", "wb") as f:
        pickle.dump(pipeline.named_steps["tfidf"], f)

    print("Model trained successfully.")

if __name__ == "__main__":
    train()
