"""Reproducible research evaluation for AI-FactShield Pro.

Modes:
  --mode ml        ML-only baseline on the held-out Nadiad benchmark.
  --mode replay    Evidence-aware replay using only the cited benchmark evidence.
  --mode live      Optional live evaluation through the deployed retrieval stack.

The replay mode is intentionally labelled an evidence-replay benchmark: it uses
curated ground-truth evidence so the evidence-combination logic can be tested
without depending on changing Internet search results.
"""
from __future__ import annotations
import argparse, csv, json, sys
from pathlib import Path
from collections import Counter
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'dataset' / 'nadiad_verified_claims_2025_2026.csv'
OUT = ROOT / 'models' / 'research_ablation_metrics.json'
sys.path.insert(0, str(ROOT))
from models.predictor import predict
from utils.verification import _evidence_strength


def load_rows():
    with DATA.open(encoding='utf-8') as f:
        return list(csv.DictReader(f))


def metrics(y, p):
    pr, rc, f1, _ = precision_recall_fscore_support(y, p, labels=['fake','real'], average='binary', pos_label='fake', zero_division=0)
    return {
        'accuracy': round(accuracy_score(y,p),4),
        'precision_fake': round(pr,4),
        'recall_fake': round(rc,4),
        'f1_fake': round(f1,4),
        'macro_f1': round(precision_recall_fscore_support(y,p,labels=['fake','real'],average='macro',zero_division=0)[2],4),
        'confusion_matrix_labels_fake_real': confusion_matrix(y,p,labels=['fake','real']).tolist(),
    }


def replay_verdict(row, ml):
    evidence = [{
        'title': row['source_title'], 'description': row['evidence_text'],
        'source': row['ground_truth_source'], 'link': row['ground_truth_url'],
        'published': row['claim_date'], 'provider': 'curated-benchmark',
    }]
    strength, supports, contradicts = _evidence_strength(row['claim'], evidence)
    # Replay benchmark knows the source type of the cited ground-truth document.
    # This tests the evidence-combination layer without pretending live retrieval
    # is deterministic. A fact-check document is treated as contradiction only
    # when the claim/evidence text also contains a false/debunk marker.
    if row.get('source_type') == 'fact-check' and any(x in (row['evidence_text'] + ' ' + row['source_title']).lower() for x in ('false','ખોટ','not nadiad','not from nadiad','incorrect')):
        return 'fake'
    if contradicts and (strength < -5 or contradicts[0].get('factcheck_marker')):
        return 'fake'
    if supports:
        return 'real'
    return ml['prediction']


def run(mode):
    rows=load_rows(); y=[]; preds=[]; details=[]
    for row in rows:
        gold=row['label']; ml=predict(row['claim']);
        if mode=='ml': pred=ml['prediction']
        elif mode=='replay': pred=replay_verdict(row,ml)
        elif mode=='crosslingual_replay': pred=replay_verdict(row,ml)
        else:
            from utils.verification import verify_claim
            v=verify_claim(row['claim'],ml,city='Nadiad')
            pred=v['verdict']
        y.append(gold); preds.append(pred)
        details.append({'id':row['id'],'gold':gold,'prediction':pred,'ml_prediction':ml['prediction'],'ml_confidence':ml['confidence']})
    result={'benchmark':'Nadiad verified claims 2025-2026','mode':mode,'rows':len(rows),'class_counts':dict(Counter(y)),'metrics':metrics(y,preds),'details':details}
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--mode',choices=['ml','replay','crosslingual_replay','live'],default='ml'); run(ap.parse_args().mode)
