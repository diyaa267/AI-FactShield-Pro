import re

STOPWORDS = {
    "the","and","is","are","a","an","of","to","in","on","for","this","that",
    "का","के","की","और","है","हैं","में","से","यह","वह",
    "અને","છે","માં","થી","આ","તે","ના","ની"
}

def extract_keywords(text, limit=8):
    words = re.findall(r"[A-Za-zÀ-ÿ\u0900-\u097F\u0A80-\u0AFF]{3,}", text.lower())
    result = []
    for word in words:
        if word not in STOPWORDS and word not in result:
            result.append(word)
        if len(result) >= limit:
            break
    return result
