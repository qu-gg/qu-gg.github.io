"""Capture the manifest-selected BREAK!! Devblog posts without rewriting bodies."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

FEED_URL = "https://breakrpg.blogspot.com/feeds/posts/default"
MANIFEST = Path(__file__).parent / "compendium-data.json"
OUTPUT_DIR = Path(__file__).parent / "source-posts"


def fetch_page(start_index: int) -> dict:
    query = urllib.parse.urlencode(
        {"alt": "json", "max-results": 100, "start-index": start_index}
    )
    request = urllib.request.Request(
        f"{FEED_URL}?{query}",
        headers={"User-Agent": "qu-gg-blog-compendium/1.0"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)["feed"]


def alternate_link(entry: dict) -> str:
    return next(
        (
            link.get("href", "")
            for link in entry.get("link", [])
            if link.get("rel") == "alternate"
        ),
        "",
    )


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    post_ids = [
        entry["id"]
        for category in manifest["categories"]
        for section in category.get("sections", [])
        for entry in section["entries"]
    ]
    wanted = set(post_ids)
    found: dict[str, dict] = {}
    start_index = 1

    while len(found) < len(wanted):
        feed = fetch_page(start_index)
        entries = feed.get("entry", []) or []
        for entry in entries:
            post_id = entry.get("id", {}).get("$t", "").rsplit("post-", 1)[-1]
            if post_id in wanted:
                found[post_id] = {
                    "id": post_id,
                    "title": entry.get("title", {}).get("$t", ""),
                    "url": alternate_link(entry),
                    "published": entry.get("published", {}).get("$t", ""),
                    "updated": entry.get("updated", {}).get("$t", ""),
                    "author": (entry.get("author") or [{}])[0].get("name", {}).get("$t", ""),
                    "labels": [category["term"] for category in entry.get("category", [])],
                    "comments": int((entry.get("thr$total") or {}).get("$t", "0") or 0),
                    "content_html": entry.get("content", {}).get("$t", ""),
                }
        start_index += len(entries)
        if not entries or start_index > int(feed["openSearch$totalResults"]["$t"]):
            break
        time.sleep(0.2)

    missing = sorted(wanted - found.keys())
    if missing:
        raise SystemExit(f"Missing feed records: {', '.join(missing)}")

    OUTPUT_DIR.mkdir(exist_ok=True)
    for post_id in post_ids:
        output = OUTPUT_DIR / f"{post_id}.json"
        output.write_text(json.dumps(found[post_id], indent=2, ensure_ascii=False) + "\n")
        print(f"Captured {post_id}: {found[post_id]['title']}")


if __name__ == "__main__":
    main()