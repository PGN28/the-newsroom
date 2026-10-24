#!/usr/bin/env python3
"""Refresh The Newsroom's headline index from the GDELT DOC API.

GDELT provides article metadata, not article text or reliable summaries.
This script stores headlines, publisher domains, links and dates only.
"""
import json
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "news.json"
MAX_PER_SECTION = 12
WINDOW_HOURS = 72
API = "https://api.gdeltproject.org/api/v2/doc/doc"

QUERIES = {
    "India": '(India OR Indian government OR Supreme Court of India OR Parliament of India)',
    "Kerala": '(Kerala OR Thiruvananthapuram OR Kochi OR Kozhikode OR Malappuram)',
    "World Affairs": '(United Nations OR international relations OR foreign policy OR global economy OR war OR ceasefire OR summit)',
    "General Knowledge": '(India current affairs OR Indian economy OR international summit OR election results OR government policy OR science discovery)',
    "Law": '(Supreme Court OR High Court OR court judgment OR legislation OR legal rights OR constitutional law OR India law)',
    "Politics": '("Bharatiya Janata Party" OR BJP OR "Indian National Congress" OR Congress OR "CPI(M)" OR "Communist Party of India" OR IUML OR "Aam Aadmi Party" OR "Cockroach Janta Party" OR "Cockroach Janata Party" OR CJP)'
}
PARTIES = [
    ("BJP", ["BJP", "Bharatiya Janata Party"]),
    ("INC", ["Indian National Congress", "Congress"]),
    ("CPI(M)", ["CPI(M)", "Communist Party of India (Marxist)", "CPIM"]),
    ("CJP", ["Cockroach Janta Party", "Cockroach Janata Party", "CJP"]),
    ("IUML", ["IUML", "Indian Union Muslim League"]),
    ("AAP", ["Aam Aadmi Party", "AAP"]),
    ("CPI", ["Communist Party of India", "CPI"])
]
NEGATIVE = re.compile(r"criticis|slams|attacks|alleg|accus|condemn|opposes|opposition|hits out|questions|row over|controversy|probe into", re.I)
POSITIVE = re.compile(r"wins|launches|passes|approves|announces|inaugurat|implements|records|secures|signs|achieves|elected|victory|agreement", re.I)
IMPORTANT = re.compile(r"court|judgment|bill|law|election|budget|policy|minister|government|parliament|assembly|supreme|high court|reserve bank|rbi|inflation|gdp|climate|summit|treaty|war|ceasefire|trade|security|education|health|kerala|india", re.I)

def fetch(query, start, end):
    params = {
        "query": f"({query}) sourcelang:english",
        "mode": "ArtList", "format": "json", "maxrecords": "250",
        "sort": "HybridRel", "startdatetime": start.strftime("%Y%m%d%H%M%S"),
        "enddatetime": end.strftime("%Y%m%d%H%M%S")
    }
    url = API + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "TheNewsroomPersonalDashboard/1.0"})
    with urllib.request.urlopen(request, timeout=35) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("articles", [])

def clean_title(value):
    value = re.sub(r"\s+", " ", str(value or "")).strip()
    return value[:400]

def parse_date(value):
    if not value:
        return None
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None

def party_label(title):
    for party, aliases in PARTIES:
        if any(re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", title, re.I) for alias in aliases):
            if NEGATIVE.search(title):
                event = "Criticism"
            elif POSITIVE.search(title):
                event = "Achievement"
            else:
                event = "Development"
            return party, event
    return "", "Development"

def score(article, now):
    title = clean_title(article.get("title"))
    published = parse_date(article.get("seendate"))
    age_hours = max(0, (now - published).total_seconds() / 3600) if published else 72
    score_value = 0
    score_value += 4 if IMPORTANT.search(title) else 0
    score_value += 3 if re.search(r"\b(India|Indian|Kerala|Supreme Court|Parliament|minister|election|judgment|bill|budget)\b", title, re.I) else 0
    score_value += max(0, 3 - age_hours / 24)
    score_value += 1 if len(title) >= 35 else 0
    return score_value

def main():
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=WINDOW_HOURS)
    collected = {}
    seen_urls = set()
    for section, query in QUERIES.items():
        try:
            articles = fetch(query, start, now)
        except Exception as exc:
            print(f"Warning: {section} query failed: {exc}")
            articles = []
        print(f"{section}: fetched {len(articles)}")
        ranked = []
        section_urls = set()
        for article in articles:
            title = clean_title(article.get("title"))
            url = str(article.get("url") or "").strip()
            if not title or not url.startswith(("https://", "http://")):
                continue
            key = url.split("#", 1)[0]
            if key in section_urls:
                continue
            section_urls.add(key)
            seen_urls.add(key)
            published = parse_date(article.get("seendate"))
            domain = str(article.get("domain") or urllib.parse.urlparse(url).netloc).replace("www.", "")
            item = {
                "title": title,
                "description": "",
                "source": domain,
                "domain": domain,
                "url": url,
                "published": published.isoformat() if published else None,
                "indexed_by": "GDELT DOC API"
            }
            if section == "Politics":
                item["party"], item["event_type"] = party_label(title)
                item["parties"] = [p for p, _ in PARTIES]
            ranked.append((score(article, now), published or datetime.min.replace(tzinfo=timezone.utc), item))
        ranked.sort(key=lambda entry: (entry[0], entry[1]), reverse=True)
        collected[section] = [entry[2] for entry in ranked[:MAX_PER_SECTION]]
        # GDELT asks clients to avoid excessively rapid repeated requests.
        time.sleep(5)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": now.isoformat(),
        "source": "GDELT DOC API",
        "window_hours": WINDOW_HOURS,
        "max_per_section": MAX_PER_SECTION,
        "sections": collected
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Wrote", OUT)

if __name__ == "__main__":
    main()
