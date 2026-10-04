"""Live, city-scoped news aggregation and evidence search.

The feed is intentionally evidence-oriented:
- NewsAPI + GNews are used when API keys are configured.
- Google News RSS is used as a no-key discovery/source layer.
- Feed results are restricted to today's articles in India time.
- "All" is built from several category queries and then interleaved, so one
  category cannot dominate the page.
- Gujarati is handled by Gujarati query terms because NewsAPI's documented
  language list does not include Gujarati; GNews language filtering likewise
  does not list Gujarati.
"""
from __future__ import annotations

import datetime as dt
import email.utils
import html
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

IST = ZoneInfo("Asia/Kolkata")

CITIES = {
    "Nadiad": {"aliases": ["Nadiad", "નડિયાદ", "નડીઆદ"], "state": "Gujarat"},
}


# Queries are deliberately broad enough to find local reporting, but each is
# fetched separately for the All view so categories stay balanced.
CATEGORIES = {
    "All": "",
    "Politics": "politics OR government OR election OR minister OR assembly",
    "Business": "business OR economy OR market OR company OR finance OR industry",
    "Sports": "sports OR cricket OR football OR olympics",
    "Technology": "technology OR AI OR software OR startup OR digital",
    "Health": "health OR hospital OR medical OR doctor OR disease",
    "Crime": "crime OR police OR arrest OR theft OR accident OR investigation",
    "Local": "civic OR municipal OR traffic OR road OR weather OR city",
}

LANGUAGES = {"All": ["en", "gu"], "English": ["en"], "Gujarati": ["gu"]}

PRIMARY_LOCAL_SOURCE = ("Public App", "public.app")

PREFERRED_SOURCES = [
    PRIMARY_LOCAL_SOURCE,
    ("Gujarat First", "gujaratfirst.com"),
    ("Times of India", "timesofindia.indiatimes.com"),
    ("Loktej", "loktej.com"),
    ("Gujarat Samachar", "gujaratsamachar.com"),
    ("Sandesh", "sandesh.com"),
    ("Divya Bhaskar", "divyabhaskar.co.in"),
]

CITY_SOURCE_QUERIES = {city: data["aliases"] for city, data in CITIES.items()}


def _key(name: str) -> str:
    return os.environ.get(name, "").strip()


def available_providers() -> list[str]:
    out = []
    if _key("NEWS_API_KEY"):
        out.append("NewsAPI")
    if _key("GNEWS_API_KEY"):
        out.append("GNews")
    if _key("GOOGLE_FACTCHECK_API_KEY"):
        out.append("Google Fact Check")
    out.append("Google News RSS")
    out.append("GDELT")
    return out


def _request_json(url: str, params: dict, headers: dict | None = None, timeout: int = 15, retries: int = 2) -> dict:
    """Small resilient HTTP client used by all live providers.

    Retries are deliberately short so one provider outage never blocks the whole
    news pipeline. Secrets can be supplied through headers rather than rendered
    into application URLs/logs where the provider supports it.
    """
    query = urllib.parse.urlencode(params)
    full_url = url + (("&" if "?" in url else "?") + query if query else "")
    request_headers = {
        "User-Agent": "AI-FactShield-Pro/10.0 (+live-evidence-verification)",
        "Accept": "application/json",
        **(headers or {}),
    }
    last_error = None
    for attempt in range(max(1, retries + 1)):
        try:
            req = urllib.request.Request(full_url, headers=request_headers)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8", errors="ignore"))
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                import time
                time.sleep(0.35 * (attempt + 1))
    raise last_error or RuntimeError("provider request failed")


def _clean(value) -> str:
    value = html.unescape(str(value or ""))
    return re.sub(r"\s+", " ", value).strip()


def _domain(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def _source_reliability(source: str, domain: str) -> str:
    """Classify source type for explainability; never treat this as proof."""
    d = (domain or "").lower()
    s = (source or "").lower()
    if d.endswith(".gov.in") or ".gov.in" in d or d.endswith(".nic.in"):
        return "official"
    if any(x in s for x in ("reuters", "associated press", "bbc", "the hindu", "indian express")):
        return "major_news"
    if any(x in s for x in ("fact check", "fact-check", "boom", "alt news", "vishvas")):
        return "fact_check"
    return "news_source"


def _source_name(name: str, url: str) -> str:
    source = _clean(name)
    domain = _domain(url)
    for preferred, preferred_domain in PREFERRED_SOURCES:
        if preferred_domain in domain or preferred.lower() in source.lower():
            return preferred
    return source or domain or "Unknown source"


def _category_for(title: str, description: str = "") -> str:
    text = f"{title} {description}".lower()
    for category, query in CATEGORIES.items():
        if category == "All":
            continue
        terms = [x for x in re.findall(r"[a-z]+", query.lower()) if len(x) > 3]
        if any(term in text for term in terms):
            return category
    return "Local"


def _parse_date(value: str | None) -> dt.datetime | None:
    text = _clean(value)
    if not text:
        return None
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        try:
            parsed = email.utils.parsedate_to_datetime(text)
        except Exception:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(IST)


def _today_window() -> tuple[dt.datetime, dt.datetime]:
    now = dt.datetime.now(IST)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, now


def _is_recent(value: str | None, hours: int = 48) -> bool:
    parsed = _parse_date(value)
    if not parsed:
        return False
    now = dt.datetime.now(IST)
    return now - dt.timedelta(hours=hours) <= parsed <= now + dt.timedelta(minutes=5)


def _is_today(value: str | None) -> bool:
    parsed = _parse_date(value)
    if not parsed:
        return False
    start, now = _today_window()
    return start <= parsed <= now + dt.timedelta(minutes=5)


def _normalize(article: dict, provider: str) -> dict | None:
    title = _clean(article.get("title"))
    url = _clean(article.get("url") or article.get("link"))
    if not title or not url:
        return None
    description = _clean(article.get("description") or article.get("content"))
    source_obj = article.get("source") or {}
    source = source_obj.get("name") if isinstance(source_obj, dict) else source_obj
    published = _clean(article.get("publishedAt") or article.get("published") or article.get("pubDate"))
    image = _clean(article.get("urlToImage") or article.get("image"))
    parsed = _parse_date(published)
    return {
        "title": title,
        "description": description[:600],
        "url": url,
        "image": image,
        "source": _source_name(source or "", url),
        "domain": _domain(url),
        "published": published,
        "published_ist": parsed.strftime("%Y-%m-%d %H:%M") if parsed else "",
        "category": _category_for(title, description),
        "provider": provider,
        "source_reliability": _source_reliability(_source_name(source or "", url), _domain(url)),
    }


def _city_terms(city: str) -> str:
    aliases = CITY_SOURCE_QUERIES.get(city, [city])
    return " OR ".join(f'"{x}"' for x in aliases)


def _city_query(city: str, category: str = "All", language: str = "en") -> str:
    city_part = f"({_city_terms(city)})"
    cat = CATEGORIES.get(category, "")
    if cat:
        city_part += f" AND ({cat})"
    # Language-specific keywords improve Gujarati/Hindi recall without using an
    # unsupported language code in providers that do not document Gujarati.
    if language == "gu":
        city_part += " AND (ગુજરાત OR ગુજરાતી OR નડિયાદ OR નડીઆદ)"
    elif language == "hi":
        city_part += " AND (हिंदी OR गुजरात OR नडियाद)"
    return city_part


def _relevant_to_city(item: dict, city: str) -> bool:
    text = f"{item.get('title','')} {item.get('description','')}".lower()
    aliases = [x.lower() for x in CITY_SOURCE_QUERIES.get(city, [city])]
    return any(alias in text for alias in aliases)


def _fetch_newsapi_query(query: str, language: str | None, limit: int) -> list[dict]:
    key = _key("NEWS_API_KEY")
    if not key:
        return []
    start, now = _today_window()
    params = {
        "q": query,
        "pageSize": min(max(limit, 1), 100),
        "sortBy": "publishedAt",
        "from": start.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "to": now.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    # NewsAPI's documented language list does not include Gujarati. For Gujarati
    # we rely on Gujarati query terms and do not send an invalid language code.
    if language in {"en", "hi"}:
        params["language"] = language
    try:
        data = _request_json("https://newsapi.org/v2/everything", params, headers={"X-Api-Key": key})
    except Exception:
        return []
    if data.get("status") != "ok":
        return []
    out = []
    for raw in data.get("articles", []):
        item = _normalize(raw, "NewsAPI")
        if item and _is_recent(item["published"], 48):
            item["language_hint"] = language or "en"
            out.append(item)
    return out


def _fetch_gnews_query(query: str, language: str | None, limit: int) -> list[dict]:
    key = _key("GNEWS_API_KEY")
    if not key:
        return []
    start, now = _today_window()
    params = {
        "q": query,
        "country": "in",
        "max": min(max(limit, 1), 100),
        "from": start.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "to": now.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    if language in {"en", "hi"}:
        params["lang"] = language
    try:
        data = _request_json("https://gnews.io/api/v4/search", params, headers={"X-Api-Key": key})
    except Exception:
        return []
    out = []
    for raw in data.get("articles", []):
        item = _normalize(raw, "GNews")
        if item and _is_recent(item["published"], 48):
            item["language_hint"] = language or "en"
            out.append(item)
    return out


def _fetch_google_rss(city: str, category: str, language: str, limit: int, source_domain: str | None = None, claim: str | None = None) -> list[dict]:
    # Keep the discovery query broad enough to avoid Google News returning zero
    # results because of too many AND terms. Category filtering is applied after
    # retrieval when the feed is the All view.
    query = _city_query(city, category, language) if category != "All" else f"({_city_terms(city)})"
    if claim:
        query = f'({query}) ({claim[:220]})'
    query += " when:1d"
    if source_domain:
        query += f" site:{source_domain}"
    if language == "gu":
        # Google News supports Gujarati presentation, but forcing several Gujarati
        # keywords can accidentally exclude Gujarati stories whose headline uses
        # Nadiad/Gujarat in Latin script. Keep the city/category query broad and
        # let the Gujarati edition perform the language selection.
        if not claim:
            query = f"({_city_terms(city)})"
            if category != "All" and CATEGORIES.get(category):
                query += f" AND ({CATEGORIES[category]})"
            query += " when:1d"
            if source_domain:
                query += f" site:{source_domain}"
        hl, ceid = "gu", "IN:gu"
    elif language == "hi":
        hl, ceid = "hi", "IN:hi"
    else:
        hl, ceid = "en-IN", "IN:en"
    params = urllib.parse.urlencode({"q": query, "hl": hl, "gl": "IN", "ceid": ceid})
    try:
        req = urllib.request.Request("https://news.google.com/rss/search?" + params, headers={"User-Agent": "AI-FactShield-Pro/6.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            root = ET.fromstring(response.read())
    except Exception:
        return []
    out = []
    for node in root.findall(".//item")[: max(limit, 1)]:
        raw = {
            "title": node.findtext("title"),
            "link": node.findtext("link"),
            "description": re.sub(r"<[^>]+>", " ", node.findtext("description") or ""),
            "source": node.findtext("source"),
            "pubDate": node.findtext("pubDate"),
        }
        item = _normalize(raw, "Google News RSS")
        if item and _is_recent(item["published"], 48):
            item["language_hint"] = language
            out.append(item)
    return out



def _extract_article_text(url: str, max_chars: int = 12000) -> str:
    """Fetch readable article text from the live URL without storing it."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 AI-FactShield-Pro/7.0",
                "Accept-Language": "en-IN,en;q=0.9,gu;q=0.8,hi;q=0.7",
            },
        )
        with urllib.request.urlopen(req, timeout=6) as response:
            raw = response.read(900_000).decode("utf-8", errors="ignore")
    except Exception:
        return ""

    # Remove non-content blocks first.
    raw = re.sub(r"(?is)<(script|style|noscript|svg|nav|footer|header|form|aside)[^>]*>.*?</\1>", " ", raw)
    # Prefer article/main containers when present.
    blocks = re.findall(r"(?is)<(?:article|main)[^>]*>(.*?)</(?:article|main)>", raw)
    text_source = max(blocks, key=len) if blocks else raw
    text_source = re.sub(r"(?is)<br\s*/?>", "\n", text_source)
    text_source = re.sub(r"(?is)</p\s*>", "\n", text_source)
    text_source = re.sub(r"<[^>]+>", " ", text_source)
    text_source = html.unescape(text_source)
    text_source = re.sub(r"\s+", " ", text_source).strip()
    # Avoid returning tiny navigation/title-only pages as article content.
    if len(text_source) < 300:
        return ""
    return text_source[:max_chars]


def _enrich_with_live_content(articles: list[dict]) -> list[dict]:
    """Attach best-effort current article content to fetched stories.

    Content is held only in the response object; it is not written to the local
    dataset or database by this function.
    """
    if not articles:
        return articles
    def one(item):
        content = _extract_article_text(item.get("url", ""))
        if content:
            item = dict(item)
            item["content"] = content
            # Keep the feed card small while giving verification the full text.
            item["description"] = content[:1200]
        else:
            item = dict(item)
            item["content"] = item.get("description", "")
        return item
    out = [None] * len(articles)
    workers = min(6, len(articles))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(one, item): i for i, item in enumerate(articles)}
        for future in as_completed(futures):
            i = futures[future]
            try:
                out[i] = future.result()
            except Exception:
                out[i] = articles[i]
    return [x for x in out if x]


def _title_key(title: str) -> str:
    text = re.sub(r"[^\w\u0900-\u097F\u0A80-\u0AFF]+", " ", title.lower())
    return re.sub(r"\s+", " ", text).strip()


def _dedupe(items: list[dict], limit: int = 18) -> list[dict]:
    seen_titles = set()
    seen_urls = set()
    out = []
    for item in items:
        key = _title_key(item["title"])
        url = item.get("url", "")
        if key in seen_titles or url in seen_urls:
            continue
        seen_titles.add(key)
        seen_urls.add(url)
        out.append(item)
        if len(out) >= limit:
            break
    return out


def _balance_languages(items: list[dict], limit: int) -> list[dict]:
    """Keep Gujarati visible in an All-language feed when live Gujarati items exist."""
    unique = _dedupe(items, max(limit * 3, limit))
    gu = [x for x in unique if x.get("language_hint") == "gu" or any("\u0A80" <= ch <= "\u0AFF" for ch in x.get("title", ""))]
    other = [x for x in unique if x not in gu]
    if not gu:
        return unique[:limit]
    target = min(max(3, limit // 3), len(gu))
    out = []
    oi = 0
    for gi in range(target):
        out.append(gu[gi])
        if oi < len(other):
            out.append(other[oi])
            oi += 1
        if len(out) >= limit:
            return out[:limit]
    for item in other[oi:]:
        if len(out) >= limit:
            break
        out.append(item)
    for item in gu[target:]:
        if len(out) >= limit:
            break
        out.append(item)
    return _dedupe(out, limit)


def _round_robin_category(items_by_category: dict[str, list[dict]], limit: int) -> list[dict]:
    out = []
    idx = {key: 0 for key in items_by_category}
    keys = list(items_by_category)
    while len(out) < limit and keys:
        progressed = False
        for key in keys:
            i = idx[key]
            values = items_by_category[key]
            if i < len(values):
                out.append(values[i])
                idx[key] += 1
                progressed = True
                if len(out) >= limit:
                    break
        if not progressed:
            break
    return out


def _fetch_gdelt_news(city: str, category: str = "All", limit: int = 12) -> list[dict]:
    """No-key current-news fallback using GDELT's live document index.

    GDELT is used for discovery only; the evidence verifier independently checks
    stories before assigning REAL/FAKE.
    """
    aliases = CITY_SOURCE_QUERIES.get(city, [city])
    city_query = " OR ".join(f'"{x}"' for x in aliases)
    cat = CATEGORIES.get(category, "")
    query = f"({city_query})"
    if cat:
        query += f" ({cat})"
    params = urllib.parse.urlencode({
        "query": query,
        "mode": "artlist",
        "maxrecords": min(max(limit, 1), 50),
        "timespan": "1d",
        "sort": "datedesc",
        "format": "json",
    })
    try:
        req = urllib.request.Request(
            "https://api.gdeltproject.org/api/v2/doc/doc?" + params,
            headers={"User-Agent": "AI-FactShield-Pro/8.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8", errors="ignore"))
    except Exception:
        return []
    out=[]
    for raw in data.get("articles", []):
        title=_clean(raw.get("title") or raw.get("name"))
        url=_clean(raw.get("url") or raw.get("link"))
        if not title or not url: continue
        published=_clean(raw.get("seendate") or raw.get("date"))
        # GDELT seendate is often YYYYMMDDhhmmss in UTC.
        if re.fullmatch(r"\d{14}", published):
            try:
                d=dt.datetime.strptime(published, "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc).astimezone(IST)
                published=d.isoformat()
            except Exception: pass
        item=_normalize({
            "title": title,
            "url": url,
            "description": raw.get("snippet") or raw.get("description") or "",
            "source": raw.get("domain") or raw.get("sourcecountry") or "GDELT source",
            "publishedAt": published,
            "image": raw.get("socialimage") or "",
        }, "GDELT")
        if item and _is_recent(item.get("published"), 36) and _relevant_to_city(item, city):
            out.append(item)
    return _dedupe(out, limit)


def _fetch_category(city: str, category: str, languages: list[str], per_source: int = 5) -> list[dict]:
    """Fetch one category with a small number of provider calls.

    For All, callers pass a combined category query; this avoids dozens of
    sequential API requests while still giving the UI enough stories to mix.
    """
    jobs = []
    for lang in languages:
        query = _city_query(city, category, lang)
        jobs.extend([
            lambda q=query, l=lang: _fetch_newsapi_query(q, l, per_source),
            lambda q=query, l=lang: _fetch_gnews_query(q, l, per_source),
            lambda l=lang: _fetch_google_rss(city, category, l, per_source),
        ])
    combined = []
    with ThreadPoolExecutor(max_workers=min(6, len(jobs) or 1)) as pool:
        futures = [pool.submit(job) for job in jobs]
        for future in as_completed(futures):
            try:
                combined.extend(future.result())
            except Exception:
                pass
    return _dedupe(sorted(combined, key=lambda x: _parse_date(x.get("published")) or dt.datetime.min.replace(tzinfo=dt.timezone.utc), reverse=True), per_source * 3)


def fetch_live_news(city: str, category: str = "All", language: str = "All", limit: int = 18) -> dict:
    city = city if city in CITIES else "Nadiad"
    category = category if category in CATEGORIES else "All"
    language = language if language in LANGUAGES else "All"
    languages = LANGUAGES[language]

    if category == "All":
        # Fetch English and Gujarati independently. The Gujarati edition gets a
        # deliberately broad Nadiad query so a single English result cannot
        # crowd the entire feed.
        combined = []
        for lang in languages:
            q = _city_query(city, "All", lang) + " AND (" + " OR ".join(CATEGORIES[c] for c in CATEGORIES if c != "All") + ")"
            combined.extend(_fetch_newsapi_query(q, lang, max(24, limit * 2)))
            combined.extend(_fetch_gnews_query(q, lang, max(24, limit * 2)))
            combined.extend(_fetch_google_rss(city, "All", lang, max(18, limit * 2)))
        # No-key current-news fallback. Run both broad and category-aware GDELT
        # discovery so sparse category matching does not collapse the feed.
        combined.extend(_fetch_gdelt_news(city, "All", max(18, limit * 2)))
        for cat in ("Local", "Politics", "Business", "Sports", "Technology", "Health", "Crime"):
            combined.extend(_fetch_gdelt_news(city, cat, max(3, limit // 2)))
        combined = [x for x in combined if _relevant_to_city(x, city)]
        # Keep category diversity first, then language diversity.
        buckets = {c: [] for c in CATEGORIES if c != "All"}
        for item in sorted(combined, key=lambda x: _parse_date(x.get("published")) or dt.datetime.min.replace(tzinfo=dt.timezone.utc), reverse=True):
            buckets.setdefault(item.get("category", "Local"), []).append(item)
        mixed = _round_robin_category(buckets, limit * 3)
        mixed = _dedupe(mixed, limit * 3)

        # Prefer a genuine Gujarati item whenever the live providers returned one,
        # while still keeping English stories in the feed. If fewer Gujarati
        # stories exist, the remaining slots are filled by other live sources.
        gu = [x for x in mixed if x.get("language_hint") == "gu" or any("\u0A80" <= ch <= "\u0AFF" for ch in x.get("title", ""))]
        other = [x for x in mixed if x not in gu]
        balanced = []
        gu_target = min(max(3, limit // 3), len(gu))
        for i in range(gu_target):
            balanced.append(gu[i])
            if len(balanced) >= limit:
                break
            if i < len(other):
                balanced.append(other[i])
        balanced.extend(other[len(balanced)//2:])
        balanced.extend(gu[gu_target:])
        articles = _dedupe(balanced, limit)
    else:
        articles = _fetch_category(city, category, languages, per_source=max(8, limit // 2))[:limit]
        articles = _dedupe(articles + _fetch_gdelt_news(city, category, max(8, limit)), limit)

    # Primary local source: Public App has a dedicated Kheda/Nadiad feed and is
    # used as the local-news discovery layer. We still verify its stories against
    # independent APIs below; a Public App story is never treated as proof by itself.
    regional = []
    regional_langs = ["gu"] if language in {"All", "Gujarati"} else languages[:1]
    for lang in regional_langs:
        regional.extend(_fetch_google_rss(city, category, lang, 8, source_domain="public.app"))
    for _name, domain in PREFERRED_SOURCES:
        for lang in regional_langs:
            regional.extend(_fetch_google_rss(city, category, lang, 2, source_domain=domain))
    regional = [x for x in regional if _relevant_to_city(x, city)]
    regional.sort(key=lambda x: _parse_date(x.get("published")) or dt.datetime.min.replace(tzinfo=dt.timezone.utc), reverse=True)
    articles = _dedupe(articles + regional, limit)

    # Official Kheda/Nadiad government evidence is searched separately.
    official = []
    for lang in (["gu", "en"] if language == "All" else languages):
        official.extend(_fetch_google_rss(city, category, lang, 4, source_domain="kheda.nic.in"))
        official.extend(_fetch_google_rss(city, category, lang, 4, source_domain="nadiadnmc.in"))
    official = [x for x in official if _relevant_to_city(x, city)]
    articles = _balance_languages(official + regional + articles, limit) if language == "All" else _dedupe(official + regional + articles, limit)
    # Fresh article content is fetched after discovery. Nothing from this live
    # response is written into the training dataset or database here.
    articles = _enrich_with_live_content(articles)

    return {
        "city": city,
        "state": CITIES[city]["state"],
        "category": category,
        "language": language,
        "date_scope": "Current + recent 48 hours (IST)",
        "articles": articles,
        "count": len(articles),
        "providers": available_providers(),
        "api_configured": bool(_key("NEWS_API_KEY") or _key("GNEWS_API_KEY")),
        "api_mode": "API-first" if (_key("NEWS_API_KEY") or _key("GNEWS_API_KEY")) else "resilient no-key mode",
        "source_policy": "No single publisher is treated as truth; independent corroboration is required for VERIFIED REAL.",
        "message": "Current/recent Nadiad news fetched from live providers with no-key fallbacks where available." if articles else "No recent Nadiad articles matched. Check Render internet access and provider availability.",
    }


def _provider_claim_search(provider: str, query: str, language: str | None, limit: int) -> list[dict]:
    if provider == "NewsAPI":
        return _fetch_newsapi_query(query, language, limit)
    if provider == "GNews":
        return _fetch_gnews_query(query, language, limit)
    return []


def search_live_claim(claim: str, city: str = "Nadiad", limit: int = 12, language: str = "All") -> list[dict]:
    """Search several current-news query variants for verification evidence."""
    city = city if city in CITIES else "Nadiad"
    claim_clean = re.sub(r"\s+", " ", claim).strip()
    tokens = re.findall(r"[\w\u0900-\u097F\u0A80-\u0AFF]+", claim_clean)
    useful = [t for t in tokens if len(t) > 2][:20]
    core = " ".join(useful)
    aliases = _city_terms(city)
    queries = []
    if useful:
        headline = " ".join(useful[:10])
        queries.append(f'({aliases}) "{headline}"')
        queries.append(f"({aliases}) ({core})")
    else:
        queries.append(f"({aliases}) news")
    queries.append(f"({aliases}) ({core}) (fake OR false OR hoax OR debunked OR fact check)")

    if language in LANGUAGES:
        langs = LANGUAGES[language]
    elif any("\u0A80" <= c <= "\u0AFF" for c in claim_clean):
        langs = ["gu", "en", "hi"]
    elif any("\u0900" <= c <= "\u097F" for c in claim_clean):
        langs = ["hi", "en", "gu"]
    else:
        # Cross-language retrieval is deliberately broad for the Nadiad study:
        # an English claim can still have the strongest local evidence in
        # Gujarati or Hindi reporting.
        langs = ["en", "gu", "hi"]
    jobs = []
    for query in queries:
        for lang in langs:
            jobs.extend([
                lambda p="NewsAPI", q=query, l=lang: _provider_claim_search(p, q, l, max(4, limit // 2)),
                lambda p="GNews", q=query, l=lang: _provider_claim_search(p, q, l, max(4, limit // 2)),
                lambda q=query, l=lang: _fetch_google_rss(city, "All", l, max(4, limit // 2), claim=core or None),
            ])
    for lang in langs:
        jobs.append(lambda l=lang: _fetch_google_rss(city, "All", l, 6, source_domain="public.app", claim=core or None))
    for _name, domain in PREFERRED_SOURCES[:4]:
        for lang in langs:
            jobs.append(lambda d=domain, l=lang: _fetch_google_rss(city, "All", l, 2, source_domain=d, claim=core or None))

    combined = []
    with ThreadPoolExecutor(max_workers=min(10, len(jobs) or 1)) as pool:
        futures = [pool.submit(job) for job in jobs]
        for future in as_completed(futures):
            try:
                combined.extend(future.result())
            except Exception:
                pass

    # Do not discard evidence merely because the independent article headline
    # omits the city name. The claim query already contains the city context,
    # and event matching below decides whether the article actually supports it.
    return _dedupe(combined, limit * 3)
