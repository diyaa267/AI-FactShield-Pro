"""Evidence-first news verification for AI FactShield Pro.

The verifier combines:
1. A small, clearly-labelled offline demo evidence pack for placement demonstrations.
3. The local ML model as a secondary signal.

Important:
- REAL requires supporting evidence, not just a positive ML prediction.
- FAKE is used for strong contradictions, explicit fact-check signals, or
  high-confidence false-news patterns.
- MISLEADING means related evidence exists but the submitted wording changes
  the meaning/details.
- UNVERIFIED means there is not enough evidence either way.
"""
from __future__ import annotations

import html
import json
import re
import urllib.parse
import urllib.request
import os
import datetime as dt
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DEMO_FILE = BASE / "dataset" / "demo_evidence.json"

TRUSTED_SOURCES = {
    "reuters": 1.18,
    "associated press": 1.16,
    "ap news": 1.16,
    "bbc": 1.12,
    "the hindu": 1.10,
    "indian express": 1.08,
    "times of india": 1.03,
    "hindustan times": 1.03,
    "economic times": 1.02,
    "reserve bank of india": 1.20,
    "press information bureau": 1.20,
    "pib": 1.20,
    "who": 1.18,
    "un": 1.16,
}

STOPWORDS = {
    "the","a","an","and","or","of","to","in","on","for","with","from","is","are",
    "was","were","be","been","being","that","this","these","those","as","at","by",
    "it","its","into","after","before","about","likely","reportedly","according",
    "said","says","claim","claims","news","today","yesterday","will","would",
    "could","may","might","has","have","had","their","they","them","than",
    "official","reported","report","accordingto",
    "એ","છે","અને","માં","થી","ને","કે","આ","તે","હતા","હતી","નો","ની","ના",
    "का","के","की","में","से","और","यह","वह","है","था","थी","ने","को","पर",
}

# Phrases that are strong enough to identify an obviously false/demo claim.
# These are deliberately narrow; they are not a general-purpose truth engine.
OBVIOUS_FALSE_PATTERNS = [
    r"\b(permanently|forever|for ever)\b.{0,80}\b(internet|internet\s+service)\b.{0,60}\b(shut|shutdown|closed|stop)\b",
    r"\b(every|all)\b.{0,80}\b(bank accounts?|atms?|cash withdrawals?)\b.{0,60}\b(frozen|closed|banned|stop|stopped)\b",
    r"\b(one crore|100 percent|100%)\b.{0,100}\b(every citizen|everyone|all citizens)\b",
    r"\b(cure every disease|live forever|makes people live forever)\b",
    r"\b(guaranteed|secret message|anonymous source)\b.{0,120}\b(money|gold|laptop|prize|reward|cure)\b",
    r"\bforward\b.{0,100}\b(bank account|account)\b.{0,80}\b(closed|close|frozen)\b",
]

# Direct contradiction rules. These are intentionally narrow.
CONTRADICTION_RULES = [
    (
        re.compile(r"\b(permanently\s+stop|stop\s+supporting|abandon\s+support)\b.*\b(rupee|currency)\b", re.I),
        re.compile(r"\b(intervened|intervention|support(?:ed|s)?\s+the\s+rupee|support(?:ed|s)?\s+rupee)\b", re.I),
    ),
    (
        re.compile(r"\b(close|shut|halt|end|stop)\b.*\b(all\s+)?foreign[-\s]?exchange\s+(operations?|activities?|market)\b", re.I),
        re.compile(r"\b(foreign[-\s]?exchange\s+market|fx\s+market|swap\s+windows?|intervention)\b", re.I),
    ),
    (
        re.compile(r"\b(permanently\s+close|permanently\s+shut|will\s+close)\b", re.I),
        re.compile(r"\b(launched|continues|continued|announced|operating|operations|intervened|intervention)\b", re.I),
    ),
    (
        re.compile(r"\b(repo\s+rate)\b.{0,80}\b(unchanged|unchanged\s+at)\b", re.I),
        re.compile(r"\b(reduced|cut|lowered)\b.{0,50}\b(repo\s+rate)\b", re.I),
    ),
]


def _contradicts_claim(claim: str, evidence_text: str) -> bool:
    return any(
        claim_re.search(claim) and evidence_re.search(evidence_text)
        for claim_re, evidence_re in CONTRADICTION_RULES
    )

FALSE_MARKERS = (
    "fake", "false", "hoax", "fabricated", "misleading", "not true", "incorrect",
    "debunked", "fact check", "fact-check", "no evidence", "did not happen",
)

# Common forms/abbreviations. This makes matching much more useful for headlines
# such as "RBI MPC" versus a user sentence saying "Reserve Bank of India".
NORMALIZE = {
    "rbi": "reservebankindia",
    "reserve": "reservebankindia",
    "bank": "bank",
    "rupee": "rupee",
    "inr": "rupee",
    "usd": "dollar",
    "cenbank": "reservebankindia",
    "centralbank": "reservebankindia",
    "intervened": "intervention",
    "intervenes": "intervention",
    "intervening": "intervention",
    "intervention": "intervention",
    "raised": "raise",
    "raises": "raise",
    "reduced": "reduce",
    "reduces": "reduce",
    "unchanged": "unchanged",
    "unchangedat": "unchanged",
    "percent": "percent",
    "percentage": "percent",
    "bps": "basispoints",
    "basis": "basispoints",
    "points": "basispoints",
}

def _tokens(text: str) -> set[str]:
    raw = re.findall(r"[\w\u0900-\u097F\u0A80-\u0AFF]+", text.lower())
    result = set()
    for word in raw:
        if len(word) <= 2 or word in STOPWORDS:
            continue
        result.add(NORMALIZE.get(word, word))
    return result


def _numbers(text: str) -> set[str]:
    # Keep monetary/rate/year numbers as supporting evidence.
    return set(re.findall(r"\b\d+(?:\.\d+)?\b", text))


def _source_weight(source: str) -> float:
    low = source.lower()
    for name, weight in TRUSTED_SOURCES.items():
        if name in low:
            return weight
    return 0.92


def _score(claim: str, title: str, description: str = "") -> float:
    """Score semantic/news overlap from 0..100.

    Entity/event tokens and matching numbers are deliberately weighted more than
    generic word overlap. This fixes cases where a genuine dated news claim was
    previously downgraded to MISLEADING simply because the headline used
    different wording.
    """
    c = _tokens(claim)
    e = _tokens(title + " " + description)
    if not c or not e:
        return 0.0

    overlap = len(c & e) / max(len(c), 1)
    meaningful = len(c & e) / max(min(len(c), 14), 1)
    phrase = SequenceMatcher(None, claim.lower(), title.lower()).ratio()
    title_phrase = SequenceMatcher(
        None, " ".join(sorted(c)), " ".join(sorted(_tokens(title)))
    ).ratio()

    cn, en = _numbers(claim), _numbers(title + " " + description)
    number_match = len(cn & en) / max(len(cn), 1) if cn else 0.0

    score = (
        overlap * 30
        + meaningful * 32
        + phrase * 8
        + title_phrase * 8
        + number_match * 22
    )
    return round(min(100.0, score), 1)


def _clean_query(claim: str) -> str:
    text = re.sub(r"https?://\S+", " ", claim)
    text = re.sub(r"[\"'“”‘’]", " ", text)
    tokens = re.findall(r"[\w\u0900-\u097F\u0A80-\u0AFF]+", text)

    useful = []
    for token in tokens:
        low = token.lower()
        if low not in STOPWORDS and len(token) > 2:
            useful.append(token)

    # Query 18 useful terms; Google News performs better than sending the whole
    # pasted article/paragraph.
    return " ".join(useful[:18])


def _load_demo() -> list[dict]:
    try:
        return json.loads(DEMO_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _demo_matches(claim: str) -> list[dict]:
    results = []
    for item in _load_demo():
        item = dict(item)
        item["score"] = _score(
            claim, item.get("title", ""), item.get("description", "")
        )
        item["source_weight"] = _source_weight(item.get("source", ""))
        item["demo"] = True
        item["rank_score"] = round(item["score"] * item["source_weight"], 1)
        results.append(item)
    return sorted(results, key=lambda x: x["rank_score"], reverse=True)


def _claim_date_window(claim: str):
    """Return an optional date window from dates explicitly present in a claim.

    Supports YYYY-MM-DD, DD Month YYYY, Month DD YYYY and standalone years.
    The window is used only to improve retrieval; it never invents evidence.
    """
    months = {
        "january":1,"february":2,"march":3,"april":4,"may":5,"june":6,
        "july":7,"august":8,"september":9,"october":10,"november":11,"december":12,
    }
    m = re.search(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", claim)
    if m:
        try:
            d = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return d, d + dt.timedelta(days=1)
        except ValueError:
            pass
    m = re.search(r"\b(\d{1,2})\s+([A-Za-z]+)\s+(20\d{2})\b", claim)
    if m and m.group(2).lower() in months:
        try:
            d = dt.date(int(m.group(3)), months[m.group(2).lower()], int(m.group(1)))
            return d, d + dt.timedelta(days=1)
        except ValueError:
            pass
    m = re.search(r"\b([A-Za-z]+)\s+(\d{1,2}),?\s+(20\d{2})\b", claim)
    if m and m.group(1).lower() in months:
        try:
            d = dt.date(int(m.group(3)), months[m.group(1).lower()], int(m.group(2)))
            return d, d + dt.timedelta(days=1)
        except ValueError:
            pass
    m = re.search(r"\b([A-Za-z]+)\s+(20\d{2})\b", claim)
    if m and m.group(1).lower() in months:
        y = int(m.group(2)); mon = months[m.group(1).lower()]
        first = dt.date(y, mon, 1)
        last = dt.date(y + (1 if mon == 12 else 0), 1 if mon == 12 else mon + 1, 1)
        return first, last
    years = re.findall(r"\b(20\d{2})\b", claim)
    if years:
        y = int(years[-1])
        if 1900 <= y <= 2100:
            return dt.date(y,1,1), dt.date(y+1,1,1)
    return None, None


def _search_gdelt(claim: str, limit: int = 8) -> list[dict]:
    """Backup live search using GDELT DOC 2.0 when Google News is unavailable."""
    compact = _clean_query(claim)
    if not compact:
        return []
    params = urllib.parse.urlencode({
        "query": compact,
        "mode": "artlist",
        "maxrecords": limit,
        "timespan": "3m",
        "sort": "datedesc",
        "format": "json",
    })
    url = "https://api.gdeltproject.org/api/v2/doc/doc?" + params
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AI-FactShield-Pro/4.0"})
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8", errors="ignore"))
    except Exception:
        return []

    results = []
    for item in data.get("articles", [])[:limit]:
        title = str(item.get("title") or item.get("name") or "").strip()
        link = str(item.get("url") or item.get("link") or "").strip()
        if not title or not link:
            continue
        source = str(item.get("domain") or item.get("sourcecountry") or "GDELT source").strip()
        date = str(item.get("seendate") or item.get("date") or "").strip()
        results.append({
            "title": title,
            "link": link,
            "published": date,
            "source": source,
            "score": _score(claim, title, ""),
            "source_weight": _source_weight(source),
            "demo": False,
        })
    return results


def search_news(claim: str, limit: int = 8, include_demo: bool = False) -> list[dict]:
    """Return only the local demo evidence pack. No live/API news is used."""
    if not include_demo:
        return []
    demo = _demo_matches(claim)
    for item in demo:
        item["rank_score"] = round(item.get("score", 0) * item.get("source_weight", 1.0), 1)
    return sorted(demo, key=lambda x: x.get("rank_score", 0), reverse=True)[:limit]


def _has_false_marker(text: str) -> bool:
    low = text.lower()
    return any(marker in low for marker in FALSE_MARKERS)


def _obvious_false(claim: str) -> bool:
    return any(re.search(pattern, claim, re.I | re.S)
               for pattern in OBVIOUS_FALSE_PATTERNS)


# Material add-ons that change a true reported event into a misleading claim.
# These are intentionally narrow and are evaluated only when supporting evidence
# for the underlying event exists.
MATERIAL_MISLEADING_PATTERNS = [
    re.compile(r"\b(repo\s+rate|policy\s+rate)\b.{0,100}\b(loan|loans|bank)\b.{0,100}\b(free|zero\s+interest|interest[-\s]?free)\b", re.I | re.S),
    re.compile(r"\b(rate\s+cut|repo\s+rate\s+cut|rate\s+reduction)\b.{0,120}\b(all\s+(bank\s+)?loans?|every\s+loan)\b.{0,100}\b(free|zero)\b", re.I | re.S),
]

def _material_misleading(claim: str) -> bool:
    return any(pattern.search(claim) for pattern in MATERIAL_MISLEADING_PATTERNS)


def _event_match_score(claim: str, evidence: dict) -> float:
    """Extra score for high-value entities/events.

    This is used only as a supporting adjustment and never creates evidence
    when no matching source exists.
    """
    text = f"{evidence.get('title','')} {evidence.get('description','')}".lower()
    claim_low = claim.lower()

    groups = [
        ("rbi", "reserve bank", "rupee", "foreign exchange", "intervention"),
        ("repo rate", "monetary policy", "rbi", "reserve bank"),
        ("samsung", "chip", "chipmaking", "prices"),
        ("evergrande", "founder", "life prison", "sentenced"),
        ("trump", "approval", "reuters/ipsos", "poll"),
    ]

    bonus = 0.0
    for group in groups:
        claim_hits = sum(x in claim_low for x in group)
        evidence_hits = sum(x in text for x in group)
        if claim_hits >= 2 and evidence_hits >= 2:
            bonus += 8.0
    return bonus


def _future_claim_date(claim: str) -> bool:
    start, _ = _claim_date_window(claim)
    return bool(start and start > dt.date.today())


def _claim_has_numbers_conflict(claim: str, evidence: dict) -> bool:
    """Detect hard numeric conflicts such as 6.00 vs 5.50 or 25% vs 50%."""
    cn = _numbers(claim)
    en = _numbers(evidence.get("title", "") + " " + evidence.get("description", ""))
    if not cn or not en:
        return False

    # If the claim contains rates/percentages/bps, require at least one
    # meaningful numeric overlap when the evidence is otherwise very similar.
    low = claim.lower()
    rate_context = any(x in low for x in ("repo rate", "policy rate", "interest rate", "percent", "%", "basis point", "bps"))
    if rate_context:
        claim_decimals = set(re.findall(r"\b\d+\.\d+\b", claim))
        evidence_decimals = set(re.findall(r"\b\d+\.\d+\b", evidence.get("title","") + " " + evidence.get("description","")))
        if claim_decimals and evidence_decimals and not (claim_decimals & evidence_decimals):
            return True
    return False


def _same_event(claim: str, evidence: dict) -> bool:
    """Require meaningful entity/topic overlap before treating a result as support.

    This is intentionally generic so current-news verification works for
    technology, politics, business, sports, science and regional news instead
    of relying only on a small hard-coded entity list.
    """
    c = _tokens(claim)
    e = _tokens(evidence.get("title", "") + " " + evidence.get("description", ""))
    if not c or not e:
        return False

    shared = c & e
    overlap_claim = len(shared) / max(len(c), 1)
    overlap_evidence = len(shared) / max(len(e), 1)

    # Exact/near-exact headlines are strong event matches. For longer prose,
    # require enough shared terms on the claim side and at least one meaningful
    # token in common.
    phrase = SequenceMatcher(None, claim.lower(), evidence.get("title", "").lower()).ratio()
    if phrase >= 0.84 and len(shared) >= 3:
        return True
    return len(shared) >= 3 and overlap_claim >= 0.30 and overlap_evidence >= 0.12


def _strong_false_claim_pattern(claim: str) -> bool:
    """Narrow high-impact false patterns useful for a placement demo.

    These patterns do not label ordinary unknown claims as fake. They target
    extraordinary institutional claims that can be checked against official
    evidence when available.
    """
    patterns = [
        r"\b(indian government|government of india)\b.{0,120}\b(stop using|abandon|replace)\b.{0,80}\b(indian rupee|rupee)\b.{0,80}\b(us dollar|u\.?s\.?\s*dollar|dollar)\b",
        r"\b(rbi|reserve bank of india|indian central bank)\b.{0,120}\b(close|shut|stop|end|halt)\b.{0,80}\b(all foreign exchange|foreign exchange operations?)\b",
        r"\b(government|india)\b.{0,120}\b(underwater city|alien|time machine|miracle cure)\b.{0,120}\b(officially confirmed|official confirmation)\b",
        r"\b(underwater city|alien|time machine|miracle cure)\b.{0,160}\b(officially confirmed|official confirmation)\b.{0,120}\b(government|india)\b",
    ]
    return any(re.search(p, claim, re.I | re.S) for p in patterns)


def _exact_or_near_exact_headline(claim: str, evidence: dict) -> bool:
    title = evidence.get("title", "")
    if not title:
        return False
    a = re.sub(r"[^\w\s]", " ", claim.lower())
    b = re.sub(r"[^\w\s]", " ", title.lower())
    a = re.sub(r"\s+", " ", a).strip()
    b = re.sub(r"\s+", " ", b).strip()
    return a == b or SequenceMatcher(None, a, b).ratio() >= 0.90


def _exact_demo_match(claim: str):
    """Return an exact offline demo story match, if any."""
    normalized = re.sub(r"[^\w\s]", " ", str(claim).lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    best = None
    best_ratio = 0.0
    for item in _load_demo():
        title = re.sub(r"[^\w\s]", " ", str(item.get("title", "")).lower())
        title = re.sub(r"\s+", " ", title).strip()
        ratio = SequenceMatcher(None, normalized, title).ratio() if title else 0.0
        if normalized == title:
            return item
        if ratio > best_ratio:
            best_ratio, best = ratio, item
    return best if best_ratio >= 0.94 else None


def verify_claim(claim: str, model_result: dict) -> dict:
    """Evidence-first verifier.

    Verdict policy:
      REAL        = strong matching reporting/official evidence.
      FAKE        = direct contradiction, reliable fact-check/false marker,
                    or a narrow high-impact false pattern with no support.
      MISLEADING  = a real event is present but the submitted claim adds or
                    changes a material detail.
      UNVERIFIED  = insufficient evidence; never treated as proof of falsehood.

    This is deliberately safer than allowing a TF-IDF classifier or fuzzy
    headline match to decide truth on its own.
    """
    demo = _exact_demo_match(claim)
    ml_label = str(model_result.get("prediction", "real")).lower()
    ml_conf = float(model_result.get("confidence", 60))

    # Demo mode is deliberately offline and deterministic. Exact demo cards
    # are the only evidence source for the placement demonstration.
    if demo:
        verdict = str(demo.get("verdict", "unverified")).lower()
        if verdict == "real":
            confidence = 96.0
            explanation = "This demo story is backed by the project's offline demo evidence pack. No live news service is used in demo mode."
        else:
            confidence = 97.0
            explanation = "This is a deliberately fabricated demo story included to demonstrate the FAKE detection workflow. No live news service is used in demo mode."
        best = dict(demo)
        best["demo"] = True
        best["score"] = 100.0
        best["rank_score"] = 100.0
        return {
            "verdict": verdict,
            "verification_confidence": confidence,
            "explanation": explanation,
            "evidence": [best],
            "best_evidence": best,
            "evidence_available": True,
        }

    # Non-demo claims are intentionally not connected to live news anymore.
    # The local ML model can still classify them, but verification remains UNVERIFIED.
    evidence = []
    future = False

    # Re-score and keep only evidence that refers to the same event/topic.
    for item in evidence:
        base = float(item.get("score", 0))
        item["score"] = round(min(100.0, base + _event_match_score(claim, item)), 1)
        item["rank_score"] = round(item["score"] * item.get("source_weight", 1.0), 1)

    evidence.sort(key=lambda x: x.get("rank_score", 0), reverse=True)

    same_event_items = [e for e in evidence if _same_event(claim, e)]
    support = [
        e for e in same_event_items
        if e["score"] >= 48 and not _has_false_marker(
            e.get("title", "") + " " + e.get("description", "")
        )
        and not _claim_has_numbers_conflict(claim, e)
    ]
    strong = [e for e in support if e["score"] >= 60]
    trusted = [e for e in support if e.get("source_weight", 1.0) >= 1.08]
    exact_trusted = [e for e in evidence if _exact_or_near_exact_headline(claim, e) and e.get("source_weight", 1.0) >= 1.03]

    contradictory = [
        e for e in same_event_items
        if e["score"] >= 40 and _contradicts_claim(
            claim, e.get("title", "") + " " + e.get("description", "")
        )
    ]

    factcheck_false = [
        e for e in same_event_items
        if _has_false_marker(e.get("title", "") + " " + e.get("description", ""))
        and e["score"] >= 40
    ]

    # A headline selected directly from the live-news feed can be verified
    # strongly when it is backed by a trusted source. This prevents the local
    # ML classifier from overriding current evidence.
    if exact_trusted and not any(_has_false_marker(e.get("title", "") + " " + e.get("description", "")) for e in exact_trusted):
        best = max(exact_trusted, key=lambda e: e.get("rank_score", e.get("score", 0)))
        verdict = "real"
        confidence = min(99, round(86 + best.get("score", 0) * 0.12, 1))
        explanation = (
            "The submitted headline closely matches current reporting from a trusted news source. "
            "The live article is treated as the primary evidence; the ML model is only a supporting signal."
        )

    # continue with normal evidence rules
    # If an event is real but the user's wording adds an unsupported material
    # consequence, it is MISLEADING. This is evaluated before REAL.
    elif _material_misleading(claim) and (support or strong):
        best = max(support, key=lambda e: e.get("rank_score", e.get("score", 0)))
        verdict = "misleading"
        confidence = min(98, round(76 + best["score"] * 0.20, 1))
        explanation = (
            "The underlying news event is supported by reliable evidence, but "
            "the claim adds a material conclusion that the source does not support. "
            "The statement is therefore MISLEADING, not REAL."
        )

    elif contradictory:
        best = max(contradictory, key=lambda e: e.get("rank_score", 0))
        verdict = "fake"
        confidence = min(99, round(82 + best["score"] * 0.16, 1))
        explanation = (
            "The submitted claim makes a specific assertion that conflicts with "
            "the available reliable evidence."
        )

    elif factcheck_false:
        best = max(factcheck_false, key=lambda e: e.get("rank_score", 0))
        verdict = "fake"
        confidence = min(98, round(78 + best["score"] * 0.18, 1))
        explanation = (
            "A matching fact-check or reliable news result directly identifies "
            "the claim as false, fabricated, or unsupported."
        )

    elif _obvious_false(claim) and not strong:
        verdict = "fake"
        confidence = min(96, round(max(84, ml_conf), 1))
        best = same_event_items[0] if same_event_items else (evidence[0] if evidence else None)
        explanation = (
            "The claim contains a narrow, high-risk viral-hoax pattern and "
            "no strong supporting evidence was found."
        )

    elif _strong_false_claim_pattern(claim) and not strong:
        verdict = "fake"
        confidence = 88.0
        best = same_event_items[0] if same_event_items else (evidence[0] if evidence else None)
        explanation = (
            "The claim contains an extraordinary institutional assertion, but "
            "no reliable supporting evidence was found for that specific event."
        )

    elif strong or (trusted and support):
        best = max(
            trusted if trusted else strong,
            key=lambda e: e.get("rank_score", e.get("score", 0))
        )
        multi = len([e for e in support if e["score"] >= 48])
        verdict = "real"
        confidence = min(99, round(70 + best["score"] * 0.23 + min(multi, 4) * 3, 1))
        explanation = (
            "The claim closely matches reliable reporting or an official source "
            "for the same event and key details."
        )

    elif ml_label == "fake" and ml_conf >= 90 and not evidence:
        verdict = "fake"
        confidence = round(min(94, 60 + ml_conf * 0.35), 1)
        best = None
        explanation = (
            "The trained model finds a very strong false-news pattern and no "
            "matching current evidence was found. This is a model-assisted FAKE result."
        )

    elif same_event_items and max(e["score"] for e in same_event_items) >= 38:
        best = max(same_event_items, key=lambda e: e.get("rank_score", 0))
        verdict = "misleading"
        confidence = round(min(88, 55 + best["score"] * 0.32), 1)
        explanation = (
            "Related reporting exists, but the wording, date, numbers, or scope "
            "does not match the available evidence closely enough for REAL."
        )

    else:
        best = evidence[0] if evidence else None
        verdict = "unverified"
        confidence = round(min(82, max(55, ml_conf * 0.80)), 1)
        explanation = (
            "No sufficiently strong evidence for this exact claim was found. "
            "UNVERIFIED means the system does not have enough evidence to call "
            "it true or false."
        )

    # Offline demo mode: no future/live-news override is needed.

    return {
        "verdict": verdict,
        "verification_confidence": confidence,
        "explanation": explanation,
        "evidence": evidence[:5],
        "best_evidence": best,
        "evidence_available": bool(evidence),
    }
