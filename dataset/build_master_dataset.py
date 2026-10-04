"""Normalize downloaded public datasets into dataset/master_large_real_fake.csv.

Binary mapping:
- LIAR: true/mostly-true -> REAL; false/barely-true/pants-fire -> FAKE; half-true dropped.
- IFND: 1 -> REAL, 0 -> FAKE.
- Hindi true/fake files: REAL/FAKE respectively.
- FakeNewsNet: *_real -> REAL, *_fake -> FAKE (title + URL only).
- TALLIP: flexible parser for binary labels.
- WELFake/ISOT: title + body with their published binary labels.
"""
from __future__ import annotations
import csv, json, re, zipfile
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'dataset'/'raw_public'
OUT=ROOT/'dataset'/'master_large_real_fake.csv'


def clean(x):
    x=re.sub(r"\s+"," ",str(x or "")).strip()
    return x

def add(rows,text,label,source,language="English"):
    text=clean(text)
    if len(text)<20 or label not in {"real","fake"}: return
    rows.append({"text":text,"label":label,"source_dataset":source,"language":language})

def infer_lang(text):
    if re.search(r'[\u0A80-\u0AFF]',text): return 'Gujarati'
    if re.search(r'[\u0900-\u097F]',text): return 'Hindi'
    return 'English'

def read_any(path):
    try: return pd.read_csv(path,encoding='utf-8',on_bad_lines='skip')
    except Exception:
        try: return pd.read_csv(path,encoding='latin-1',on_bad_lines='skip')
        except Exception: return pd.DataFrame()

def from_df(rows,df,source,forced_label=None,default_label=None):
    if df.empty:return
    cols={str(c).strip().lower():c for c in df.columns}
    text_col=next((cols[c] for c in ['text','statement','content','title'] if c in cols),None)
    title_col=next((cols[c] for c in ['title','headline'] if c in cols),None)
    label_col=next((cols[c] for c in ['label','class','target','value','verdict'] if c in cols),None)
    if not text_col:return
    for _,r in df.iterrows():
        text=clean((str(r.get(title_col,''))+' '+str(r.get(text_col,''))) if title_col and title_col!=text_col else r.get(text_col,''))
        lab=forced_label or default_label
        if not lab and label_col:
            v=str(r.get(label_col,'')).strip().lower()
            if v in {'1','real','true','reliable','credible','0.0'}: lab='real'
            elif v in {'0','fake','false','unreliable','1.0'}: lab='fake'
        if lab: add(rows,text,lab,source,infer_lang(text))

def extract_zip(path,dest):
    if not path.exists():return
    try:
        with zipfile.ZipFile(path) as z:z.extractall(dest)
    except Exception:pass

def process(rows):
    # Existing project examples remain part of the master set.
    for f in [ROOT/'dataset'/'train.csv',ROOT/'dataset'/'test.csv',ROOT/'dataset'/'news.csv']:
        df=read_any(f); from_df(rows,df,'AI-FactShield existing')

    liar=RAW/'liar.zip'; extract_zip(liar,RAW/'liar_extracted')
    for f in RAW.rglob('*.tsv'):
        if 'liar' not in str(f).lower(): continue
        try:
            df=pd.read_csv(f,sep='\t',header=None,encoding='utf-8',on_bad_lines='skip')
            for _,r in df.iterrows():
                if len(r)<3: continue
                lab=str(r.iloc[1]).lower(); text=str(r.iloc[2])
                mapping={'true':'real','mostly-true':'real','false':'fake','barely-true':'fake','pants-fire':'fake'}
                if lab in mapping:add(rows,text,mapping[lab],'LIAR',infer_lang(text))
        except Exception: pass

    tallip=RAW/'tallip.zip'; extract_zip(tallip,RAW/'tallip_extracted')
    for f in RAW.rglob('*'):
        if f.suffix.lower() not in {'.csv','.tsv'} or 'tallip_extracted' not in str(f): continue
        df=read_any(f) if f.suffix.lower()=='.csv' else pd.read_csv(f,sep='\t',header=None,on_bad_lines='skip')
        if df.empty: continue
        # generic row parser: last/first label and longest text field
        for _,r in df.iterrows():
            vals=[clean(v) for v in r.tolist()]
            labs=[v.lower() for v in vals if v.lower() in {'fake','real','0','1','true','false'}]
            if not labs: continue
            lv=labs[-1]; lab='real' if lv in {'real','1','true'} else 'fake'
            text=max((v for v in vals if v.lower()!=lv),key=len,default='')
            add(rows,text,lab,'TALLIP',infer_lang(text))

    df=read_any(RAW/'ifnd.csv')
    if not df.empty:
        cols={str(c).lower():c for c in df.columns}; tc=cols.get('statement') or cols.get('text'); lc=cols.get('label')
        if tc and lc:
            for _,r in df.iterrows(): add(rows,r.get(tc,''),'real' if str(r.get(lc,'')).strip()=='1' else 'fake','IFND',infer_lang(str(r.get(tc,''))))

    for name,label in [('hindi_true','real'),('hindi_fake','fake')]:
        df=read_any(RAW/f'{name}.csv'); from_df(rows,df,f'Hindi dataset {label.upper()}',forced_label=label)

    for name in ['fakenewsnet_politifact_fake','fakenewsnet_politifact_real','fakenewsnet_gossipcop_fake','fakenewsnet_gossipcop_real']:
        df=read_any(RAW/f'{name}.csv'); forced='fake' if '_fake' in name else 'real'
        if not df.empty:
            cols={str(c).lower():c for c in df.columns}; tc=cols.get('title'); uc=cols.get('url')
            for _,r in df.iterrows(): add(rows,f"{r.get(tc,'')} {r.get(uc,'')}",forced,'FakeNewsNet', 'English')

    # WELFake
    df=read_any(RAW/'welfake.csv')
    if not df.empty:
        cols={str(c).lower():c for c in df.columns}; tc=cols.get('title'); xc=cols.get('text'); lc=cols.get('label')
        if tc and xc and lc:
            for _,r in df.iterrows():
                lv=str(r.get(lc,'')).strip().lower(); lab='real' if lv in {'1','real','true'} else 'fake'
                add(rows,f"{r.get(tc,'')} {r.get(xc,'')}",lab,'WELFake',infer_lang(str(r.get(xc,''))))

    # ISOT zip
    isot=RAW/'isot.zip'; extract_zip(isot,RAW/'isot_extracted')
    for f,label in [(p,'real') for p in RAW.rglob('True.csv') if 'isot_extracted' in str(p)] + [(p,'fake') for p in RAW.rglob('Fake.csv') if 'isot_extracted' in str(p)]:
        df=read_any(f)
        if df.empty: continue
        cols={str(c).lower():c for c in df.columns}; tc=cols.get('title'); xc=cols.get('text')
        if tc and xc:
            for _,r in df.iterrows(): add(rows,f"{r.get(tc,'')} {r.get(xc,'')}",label,'ISOT',infer_lang(str(r.get(xc,''))))


def main():
    rows=[]; process(rows)
    # exact normalized text dedupe; keep one label only when duplicate agrees
    best={}
    for r in rows:
        k=re.sub(r'\W+',' ',r['text'].lower()).strip()
        if k and k not in best: best[k]=r
    data=list(best.values())
    import random; random.Random(42).shuffle(data)
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['text','label','source_dataset','language']); w.writeheader(); w.writerows(data)
    from collections import Counter
    print('MASTER:',len(data)); print('LABELS:',Counter(x['label'] for x in data)); print('LANG:',Counter(x['language'] for x in data)); print('SOURCES:',Counter(x['source_dataset'] for x in data).most_common())

if __name__=='__main__': main()
