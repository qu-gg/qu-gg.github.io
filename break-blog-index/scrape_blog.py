"""Scrape every post from breakrpg.blogspot.com via the Blogger JSON feed.

The Blogger Atom feed exposes structured metadata (title, published date,
author, labels/categories, full HTML content, links). We page through it 100
posts at a time and store:

  posts/raw/<post_id>.json  -- the trimmed entry from the feed
  posts/index.json          -- compact list of {id, title, url, published,
                               labels, author, summary} for every post

Re-running is safe: the script overwrites each file.
"""

from __future__ import annotations

import html
import json
import re
import time
import urllib.request
from pathlib import Path

FEED_URL = (
    "https://breakrpg.blogspot.com/feeds/posts/default"
    "?alt=json&max-results={n}&start-index={i}"
)
PAGE_SIZE = 100
ROOT = Path(__file__).parent
RAW_DIR = ROOT / "posts" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def fetch(start_index: int, page_size: int = PAGE_SIZE) -> dict:
    url = FEED_URL.format(n=page_size, i=start_index)
    req = urllib.request.Request(url, headers={"User-Agent": "break-blog-index/0.1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def strip_html(text: str, limit: int = 400) -> str:
    text = _TAG_RE.sub(" ", text or "")
    text = html.unescape(text)
    text = _WS_RE.sub(" ", text).strip()
    return text[:limit]


def alternate_link(entry: dict) -> str:
    for link in entry.get("link", []):
        if link.get("rel") == "alternate":
            return link.get("href", "")
    return ""


def trim_entry(entry: dict) -> dict:
    return {
        "id": entry["id"]["$t"].rsplit("post-", 1)[-1],
        "title": entry.get("title", {}).get("$t", ""),
        "url": alternate_link(entry),
        "published": entry.get("published", {}).get("$t", ""),
        "updated": entry.get("updated", {}).get("$t", ""),
        "author": (entry.get("author") or [{}])[0].get("name", {}).get("$t", ""),
        "labels": [c["term"] for c in entry.get("category", [])],
        "comments": int((entry.get("thr$total") or {}).get("$t", "0") or 0),
        "content_html": entry.get("content", {}).get("$t", ""),
    }


def main() -> None:
    all_posts: list[dict] = []
    start = 1
    total = None
    while True:
        feed = fetch(start)["feed"]
        if total is None:
            total = int(feed["openSearch$totalResults"]["$t"])
            print(f"Total posts reported: {total}")
        entries = feed.get("entry", []) or []
        if not entries:
            break
        for entry in entries:
            trimmed = trim_entry(entry)
            (RAW_DIR / f"{trimmed['id']}.json").write_text(
                json.dumps(trimmed, indent=2, ensure_ascii=False)
            )
            all_posts.append(
                {
                    "id": trimmed["id"],
                    "title": trimmed["title"],
                    "url": trimmed["url"],
                    "published": trimmed["published"],
                    "author": trimmed["author"],
                    "labels": trimmed["labels"],
                    "comments": trimmed["comments"],
                    "summary": strip_html(trimmed["content_html"]),
                }
            )
        print(f"  fetched {start}..{start + len(entries) - 1}")
        start += len(entries)
        if start > total:
            break
        time.sleep(0.5)

    all_posts.sort(key=lambda p: p["published"], reverse=True)
    (ROOT / "posts" / "index.json").write_text(
        json.dumps(all_posts, indent=2, ensure_ascii=False)
    )
    print(f"Saved {len(all_posts)} posts -> posts/index.json")


if __name__ == "__main__":
    main()
