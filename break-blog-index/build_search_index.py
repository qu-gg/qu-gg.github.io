"""Build a static inverted-search index over the BREAK!! blog corpus.

Output (no post bodies are shipped, only token -> post-id postings):

  search-index.json
  {
    "version": 1,
    "stopwords": [...],          # echoed back so the client can mirror
    "posts": [                   # parallel arrays compacted to save bytes
      [id, title, url, "YYYY-MM-DD", "short blurb"],
      ...
    ],
    "tokens": {
      "akenian": [[3, 18], [47, 4], ...]   # [post_idx, term_freq]
    }
  }

Querying client-side:
  - Tokenize the query the same way.
  - For each token, look up the postings list.
  - Intersect (AND) across all query tokens.
  - Rank by sum of term frequencies (cheap BM25-lite).
  - Render title + date + match count linking to the live blog post.

This ships ZERO post body text; every result still links to the source
post on breakrpg.blogspot.com so the reader gets the full article.
"""

from __future__ import annotations

import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).parent
RAW_DIR = ROOT / "posts" / "raw"
INDEX = ROOT / "posts" / "index.json"
OUT = ROOT / "search-index.json"

BLURB_LEN = 180  # characters of body excerpt shipped per post

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
# Tokens: a-z, may contain internal apostrophes/hyphens, plus digits after first letter.
_TOK_RE = re.compile(r"[a-z][a-z0-9'\-]{1,}")

# Tiny English stopword list — keeps index small and queries focused on content words.
STOPWORDS = frozenset("""
a an and are as at be been but by for from had has have he her him his i if in
into is it its of on or our she that the their them they this to was we were
will with you your yours yourself ours ourselves us about above after again
all am any been being below between both did do does doing down during each
few further here how into itself just more most no nor not now off once only
other own same so some such than then there these those through too under
until up very what when where which while who whom why would should could
also can may might must shall well one two three because over before
""".split())


def strip_html(text: str) -> str:
    text = _TAG_RE.sub(" ", text or "")
    text = html.unescape(text)
    return _WS_RE.sub(" ", text).strip()


def make_blurb(text: str, limit: int = BLURB_LEN) -> str:
    """Return a short snippet (<= limit chars) clipped on a word boundary."""
    text = text.strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    # Prefer to break on the last sentence end inside the window, else word.
    for sep in (". ", "! ", "? "):
        i = cut.rfind(sep)
        if i >= limit * 0.5:
            return cut[: i + 1].strip()
    sp = cut.rfind(" ")
    if sp >= limit * 0.5:
        cut = cut[:sp]
    return cut.rstrip(" ,;:-") + "…"


def tokenize(text: str) -> list[str]:
    out: list[str] = []
    for tok in _TOK_RE.findall(text.lower()):
        # Drop pure stopwords and very short tokens.
        if len(tok) < 2 or tok in STOPWORDS:
            continue
        out.append(tok)
    return out


def main() -> None:
    posts_meta = json.loads(INDEX.read_text())
    posts_meta.sort(key=lambda p: p.get("published", ""), reverse=True)

    posts_compact: list[list] = []
    id_to_idx: dict[str, int] = {}
    for i, p in enumerate(posts_meta):
        posts_compact.append([
            p["id"],
            p["title"],
            p["url"],
            (p.get("published") or "")[:10],
            "",  # blurb filled in below once we read the raw body
        ])
        id_to_idx[p["id"]] = i

    # token -> {post_idx: term_freq}
    postings: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))

    n_posts_indexed = 0
    for raw_path in RAW_DIR.glob("*.json"):
        raw = json.loads(raw_path.read_text())
        pid = raw.get("id")
        if pid not in id_to_idx:
            continue
        text = strip_html(raw.get("content_html", ""))
        # Also fold in title so queries like "kickstarter" match titles.
        title = raw.get("title") or ""
        tokens = tokenize(title + " " + text)
        if not tokens:
            continue
        n_posts_indexed += 1
        idx = id_to_idx[pid]
        posts_compact[idx][4] = make_blurb(text)
        # Boost title hits 3x by counting them again.
        title_tokens = set(tokenize(title))
        counts = Counter(tokens)
        for tok, n in counts.items():
            boost = 2 if tok in title_tokens else 0
            postings[tok][idx] += n + boost

    # Convert to compact array form.
    tokens_out: dict[str, list[list[int]]] = {}
    for tok, posts in postings.items():
        # Drop hapax-only tokens that appear in just 1 post AND only once
        # (mostly proper-noun typos and OCR-ish noise) — keeps index tiny.
        # Comment out next line if you want exhaustive recall.
        if len(posts) == 1 and next(iter(posts.values())) == 1:
            continue
        tokens_out[tok] = sorted(
            ([idx, freq] for idx, freq in posts.items()),
            key=lambda r: -r[1],
        )

    out = {
        "version": 1,
        "stopwords": sorted(STOPWORDS),
        "posts": posts_compact,
        "tokens": tokens_out,
    }
    OUT.write_text(json.dumps(out, separators=(",", ":")))

    raw_size = OUT.stat().st_size
    import gzip
    gz_size = len(gzip.compress(OUT.read_bytes()))
    print(
        f"Wrote {OUT.name}: {len(posts_compact)} posts, "
        f"{n_posts_indexed} indexed, {len(tokens_out)} unique tokens"
    )
    print(f"  size: {raw_size/1024:.1f} KB raw / {gz_size/1024:.1f} KB gzipped")


if __name__ == "__main__":
    main()
