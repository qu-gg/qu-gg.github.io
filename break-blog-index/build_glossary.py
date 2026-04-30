"""Build a book-style alphabetical glossary of BREAK!! terms.

For each term in glossary.json, scan every post's full HTML body
(`posts/raw/<id>.json`) for occurrences of the term or any of its aliases,
case-insensitive, with word-boundary matching. Output a JSON file the
glossary page renders.

Output schema:
{
  "categories":   [{id, title}, ...],
  "entries": [
    {
      "term": "Old Iron",
      "category": "region",
      "aliases": [...],
      "occurrences": int,                # total mentions across corpus
      "post_count":  int,                # number of distinct posts
      "posts": [
        {"id": "...", "title": "...", "url": "...",
         "published": "...", "hits": 7, "snippet": "...one sentence of context..."},
        ...
      ]
    },
    ...
  ]
}
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
RAW_DIR = ROOT / "posts" / "raw"
GLOSSARY_CFG = ROOT / "glossary.json"
INDEX = ROOT / "posts" / "index.json"
OUT = ROOT / "glossary-data.json"

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def strip_html(text: str) -> str:
    text = _TAG_RE.sub(" ", text or "")
    text = html.unescape(text)
    return _WS_RE.sub(" ", text).strip()


def make_pattern(term: str, aliases: list[str]) -> re.Pattern:
    # Word-boundary, case-insensitive. Escape regex metachars and allow
    # internal spaces/hyphens to match flexibly (single space or hyphen).
    parts = [term, *aliases]
    escaped = []
    for p in parts:
        # Replace literal space with [ \-] to also match hyphenated forms,
        # but we keep it strict for the most part.
        e = re.escape(p)
        escaped.append(e)
    body = "|".join(escaped)
    # Use lookarounds so we don't require strict \b for terms with internal
    # punctuation like "BEES!!" or "Magi-Racer".
    return re.compile(rf"(?<![A-Za-z0-9])(?:{body})(?![A-Za-z0-9])", re.IGNORECASE)


def find_snippet(text: str, match: re.Match, span_chars: int = 110) -> str:
    start = max(0, match.start() - span_chars)
    end = min(len(text), match.end() + span_chars)
    pre = "…" if start > 0 else ""
    post = "…" if end < len(text) else ""
    return pre + text[start:end].strip() + post


def main() -> None:
    cfg = json.loads(GLOSSARY_CFG.read_text())
    posts_meta = {p["id"]: p for p in json.loads(INDEX.read_text())}

    # Pre-load and pre-strip every post's text exactly once.
    post_text: dict[str, str] = {}
    for raw_path in RAW_DIR.glob("*.json"):
        raw = json.loads(raw_path.read_text())
        post_text[raw["id"]] = strip_html(raw.get("content_html", ""))

    out_entries = []
    for entry in cfg["entries"]:
        pat = make_pattern(entry["term"], entry.get("aliases", []))
        matches_per_post: list[dict] = []
        total_hits = 0
        for pid, text in post_text.items():
            ms = list(pat.finditer(text))
            if not ms:
                continue
            meta = posts_meta.get(pid)
            if not meta:
                continue
            total_hits += len(ms)
            matches_per_post.append(
                {
                    "id": pid,
                    "title": meta["title"],
                    "url": meta["url"],
                    "published": meta["published"],
                    "hits": len(ms),
                    "snippet": find_snippet(text, ms[0]),
                }
            )
        # Sort by descending publication date.
        matches_per_post.sort(key=lambda m: -_iso_to_int(m["published"]))
        out_entries.append(
            {
                "term": entry["term"],
                "category": entry["category"],
                "aliases": entry.get("aliases", []),
                "occurrences": total_hits,
                "post_count": len(matches_per_post),
                "posts": matches_per_post,
            }
        )

    out_entries.sort(key=lambda e: e["term"].lower())

    OUT.write_text(
        json.dumps(
            {"categories": cfg["categories"], "entries": out_entries},
            indent=2,
            ensure_ascii=False,
        )
    )

    used = sum(1 for e in out_entries if e["post_count"])
    unused = [e["term"] for e in out_entries if not e["post_count"]]
    print(f"Wrote {OUT.relative_to(ROOT)} — {len(out_entries)} terms, {used} with hits.")
    if unused:
        print(f"Terms with NO matches ({len(unused)}): {', '.join(unused)}")


def _iso_to_int(iso: str) -> int:
    # 2026-04-28T... -> 20260428 (loose key for sorting)
    digits = "".join(ch for ch in iso[:10] if ch.isdigit())
    return int(digits or "0")


if __name__ == "__main__":
    main()
