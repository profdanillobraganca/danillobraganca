#!/usr/bin/env python3
"""
Extrator de posts de blogs sobre Inteligência Artificial & Democracia
Fontes: RSS feeds de institutos e publicações de referência na área
"""

import requests
import xml.etree.ElementTree as ET
import json
import re
from datetime import datetime, timezone
from html import unescape

# ── FONTES RSS ─────────────────────────────────────────────────────────────
FEEDS = [
    {
        "source": "AI Now Institute",
        "url": "https://ainowinstitute.org/feed",
        "lang": "en",
    },
    {
        "source": "MIT Technology Review – AI",
        "url": "https://www.technologyreview.com/feed/",
        "lang": "en",
    },
    {
        "source": "Brookings – Technology",
        "url": "https://www.brookings.edu/topic/technology-innovation/feed/",
        "lang": "en",
    },
    {
        "source": "Stanford HAI",
        "url": "https://hai.stanford.edu/news/rss.xml",
        "lang": "en",
    },
    {
        "source": "Future of Life Institute",
        "url": "https://futureoflife.org/feed/",
        "lang": "en",
    },
    {
        "source": "Algorithm Watch",
        "url": "https://algorithmwatch.org/en/feed/",
        "lang": "en",
    },
    {
        "source": "Nexo Jornal – Tecnologia",
        "url": "https://www.nexojornal.com.br/tags/tecnologia.rss",
        "lang": "pt",
    },
    {
        "source": "The Conversation – AI",
        "url": "https://theconversation.com/us/topics/artificial-intelligence-ai-762/articles.atom",
        "lang": "en",
    },
]

# ── PALAVRAS-CHAVE ──────────────────────────────────────────────────────────
KEYWORDS_EN = [
    "democracy", "democratic", "governance", "regulation", "accountability",
    "transparency", "disinformation", "misinformation", "surveillance",
    "civil rights", "human rights", "bias", "fairness", "public policy",
    "election", "political", "power", "inequality", "social justice",
    "algorithmic", "deepfake", "manipulation",
]

KEYWORDS_PT = [
    "democracia", "democrático", "governança", "regulação", "regulamento",
    "prestação de contas", "transparência", "desinformação", "vigilância",
    "direitos civis", "direitos humanos", "viés", "política pública",
    "eleição", "político", "desigualdade", "justiça social",
    "algoritmo", "deepfake", "manipulação",
]

ALL_KEYWORDS = KEYWORDS_EN + KEYWORDS_PT


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return unescape(text).strip()


def is_relevant(title: str, summary: str) -> bool:
    haystack = (title + " " + summary).lower()
    return any(kw in haystack for kw in ALL_KEYWORDS)


def fetch_feed(source: str, url: str) -> list[dict]:
    headers = {"User-Agent": "Mozilla/5.0 (blog-extractor/1.0)"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"  [ERRO] {source}: {e}")
        return []

    try:
        root = ET.fromstring(r.content)
    except ET.ParseError as e:
        print(f"  [XML ERRO] {source}: {e}")
        return []

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "content": "http://purl.org/rss/1.0/modules/content/",
    }

    items = []

    # RSS 2.0
    for item in root.findall(".//item"):
        title = strip_html(item.findtext("title") or "")
        link = item.findtext("link") or ""
        summary = strip_html(
            item.findtext("description") or
            item.findtext("content:encoded", namespaces=ns) or ""
        )
        pub_date = item.findtext("pubDate") or ""
        items.append({"title": title, "link": link, "summary": summary[:300],
                       "date": pub_date, "source": source})

    # Atom
    for entry in root.findall("atom:entry", ns):
        title = strip_html(entry.findtext("atom:title", namespaces=ns) or "")
        link_el = entry.find("atom:link", ns)
        link = link_el.get("href", "") if link_el is not None else ""
        summary = strip_html(
            entry.findtext("atom:summary", namespaces=ns) or
            entry.findtext("atom:content", namespaces=ns) or ""
        )
        pub_date = entry.findtext("atom:published", namespaces=ns) or \
                   entry.findtext("atom:updated", namespaces=ns) or ""
        items.append({"title": title, "link": link, "summary": summary[:300],
                       "date": pub_date, "source": source})

    return items


def main():
    print("\n🔍  Buscando posts sobre IA & Democracia...\n")
    all_posts = []

    for feed in FEEDS:
        print(f"  → {feed['source']}")
        raw = fetch_feed(feed["source"], feed["url"])
        relevant = [p for p in raw if is_relevant(p["title"], p["summary"])]
        print(f"     {len(raw)} posts encontrados, {len(relevant)} relevantes")
        all_posts.extend(relevant)

    # Deduplicar por título
    seen = set()
    unique = []
    for p in all_posts:
        key = p["title"].lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(p)

    print(f"\n✅  Total de posts relevantes (únicos): {len(unique)}\n")
    print("=" * 72)

    for i, post in enumerate(unique, 1):
        print(f"\n{i:02d}. [{post['source']}]")
        print(f"    {post['title']}")
        if post["date"]:
            print(f"    📅 {post['date'][:25]}")
        print(f"    🔗 {post['link']}")
        if post["summary"]:
            preview = post["summary"][:180].replace("\n", " ")
            print(f"    {preview}…")

    # Exportar JSON
    out_file = "posts_ia_democracia.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)

    print(f"\n📄  Exportado para {out_file} ({len(unique)} posts)")


if __name__ == "__main__":
    main()
