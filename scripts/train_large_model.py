from __future__ import annotations
from pathlib import Path
import csv, pickle, json, random
from collections import Counter
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'dataset'/'master_large_real_fake.csv'
MODEL=ROOT/'models'/'large_live_model.pkl'
METRICS=ROOT/'models'/'large_model_metrics.json'

MAX_ROWS=80000

def load_rows():
    rows=[]
    with DATA.open('r',encoding='utf-8') as f:
        for r in csv.DictReader(f):
            text=str(r.get('text','')).strip(); label=str(r.get('label','')).lower().strip()
            if text and label in {'real','fake'}: rows.append(r)
    # balanced cap prevents a huge English source from dominating regional data
    by={"real":[],"fake":[]}
    for r in rows: by[r['label']].append(r)
    rng=random.Random(42)
    for v in by.values(): rng.shuffle(v)
    n=min(len(by['real']),len(by['fake']),MAX_ROWS//2)
    selected=by['real'][:n]+by['fake'][:n]; rng.shuffle(selected)
    return selected

rows=load_rows()
if len(rows)<30: raise RuntimeError('Need at least 30 normalized rows. Add public datasets for stronger training.')
texts=[r['text'] for r in rows]; labels=[r['label'] for r in rows]
Xtr,Xte,ytr,yte=train_test_split(texts,labels,test_size=.25,random_state=42,stratify=labels)
features=FeatureUnion([
 ('word',TfidfVectorizer(lowercase=True,strip_accents='unicode',ngram_range=(1,2),min_df=2,max_features=180000,sublinear_tf=True,max_df=.98)),
 ('char',TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),min_df=2,max_features=100000,sublinear_tf=True,max_df=.995)),
])
print(f'Training rows: {len(Xtr):,}; test rows: {len(Xte):,}')
Xtrv=features.fit_transform(Xtr); Xtev=features.transform(Xte)
clf=LinearSVC(C=1.5,class_weight='balanced',max_iter=5000)
clf.fit(Xtrv,ytr)
pred=clf.predict(Xtev)
acc=accuracy_score(yte,pred)
print('Accuracy:',round(acc,4))
print(classification_report(yte,pred))
print('Confusion matrix:',confusion_matrix(yte,pred).tolist())
MODEL.parent.mkdir(exist_ok=True)
pickle.dump({'features':features,'classifier':clf,'labels':['fake','real'],'rows_used':len(rows)},MODEL.open('wb'),protocol=pickle.HIGHEST_PROTOCOL)
metrics={'accuracy':acc,'rows_used':len(rows),'train_rows':len(Xtr),'test_rows':len(Xte),'labels':dict(Counter(labels)),'confusion_matrix':confusion_matrix(yte,pred).tolist()}
METRICS.write_text(json.dumps(metrics,indent=2),encoding='utf-8')
print('Saved:',MODEL)
print('Saved metrics:',METRICS)
