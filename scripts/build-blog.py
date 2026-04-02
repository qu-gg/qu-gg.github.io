#!/usr/bin/env python3
"""
Blog Builder for Studio Quagg

Reads Markdown posts from blog/posts/, converts them to HTML pages,
generates blog-data.json for the listing page, and builds an RSS feed.

Each post is a .md file with YAML front matter:
    ---
    title: My Post Title
    date: 2026-03-19
    time: 14:30           (optional, defaults to 00:00)
    tags: break, adventure-design
    ---

    Post body in Markdown here...

Usage:
    python scripts/build-blog.py

Dependencies:
    pip install markdown pyyaml
"""

import json
import re
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timedelta
from pathlib import Path

import html as html_lib

import markdown
import yaml

# ── Configuration ──────────────────────────────────────────────────
BLOG_DIR = Path(__file__).resolve().parent.parent / "blog"
POSTS_DIR = BLOG_DIR / "posts"
TEMPLATE_PATH = BLOG_DIR / "post-template.html"
HTML_OUT_DIR = BLOG_DIR / "posts-html"
OUTPUT_JSON = BLOG_DIR.parent / "blog-data.json"
OUTPUT_FEED = BLOG_DIR / "feed.xml"
BASE_URL = "https://its.quagg.studio"
ET_UTC_OFFSET_HOURS = 4  # ET (EDT) is UTC-4; add 4 hours to convert to UTC

# Markdown extensions for nice rendering
MD_EXTENSIONS = ["extra", "codehilite", "smarty", "toc", "nl2br"]


def parse_front_matter(text: str) -> tuple[dict, str]:
    """Split YAML front matter from Markdown body."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not match:
        raise ValueError("Post must start with --- front matter ---")
    meta = yaml.safe_load(match.group(1))
    body = match.group(2)
    return meta, body


# ── Card block preprocessor ───────────────────────────────────────
def expand_card_blocks(md_text: str) -> str:
    """Replace :::item and :::ability fenced blocks with .item-block HTML."""

    def _parse_block(block_type: str, content: str) -> str:
        lines = content.strip().split("\n")
        name = ""
        item_type = ""
        desc = ""
        effect = ""
        bullets = []
        stats = ""

        for line in lines:
            stripped = line.strip()
            if stripped.lower().startswith("name:"):
                name = stripped[5:].strip()
            elif stripped.lower().startswith("type:"):
                item_type = stripped[5:].strip()
            elif stripped.lower().startswith("desc:"):
                desc = stripped[5:].strip()
            elif stripped.lower().startswith("effect:"):
                effect = stripped[7:].strip()
            elif stripped.lower().startswith("stats:"):
                stats = stripped[6:].strip()
            elif stripped.startswith("- "):
                bullets.append(stripped[2:])

        # Build HTML
        parts = ['<div class="item-block">']

        # Header: name + optional type
        header = f'<span class="item-name">{name}</span>'
        if item_type:
            header += f' <span class="item-type">[{item_type}]</span>'
        parts.append(f"    <div>{header}</div>")

        if desc:
            desc = desc.replace("\\n", "<br>")
            parts.append(f'    <div class="item-desc">{desc}</div>')

        if effect:
            effect = effect.replace("\\n", "<br>")
            parts.append(f'    <div class="item-effect">{effect}</div>')

        if bullets:
            parts.append("    <ul>")
            for b in bullets:
                b = b.replace("\\n", "<br>")
                parts.append(f"        <li>{b}</li>")
            parts.append("    </ul>")

        if stats:
            stats = stats.replace(" . ", " · ")
            parts.append(f'    <div class="item-stats">{stats}</div>')

        parts.append("</div>")
        return "\n".join(parts)

    def _replacer(match):
        block_type = match.group(1)  # "item" or "ability"
        content = match.group(2)
        return _parse_block(block_type, content)

    # Match :::item or :::ability blocks (non-greedy)
    pattern = r":::(item|ability)\s*\n(.*?)\n:::"
    return re.sub(pattern, _replacer, md_text, flags=re.DOTALL)


def expand_spoiler_text(md_text: str) -> str:
    """Replace ||spoiler text|| with <span class="spoiler"> markup."""
    return re.sub(
        r'\|\|(.+?)\|\|',
        r'<span class="spoiler" tabindex="0">\1</span>',
        md_text,
    )


def wrap_captioned_images(html_text: str) -> str:
    """Wrap <img> tags that have a title attribute in <figure>/<figcaption>."""
    def _replacer(match):
        full_tag = match.group(0)
        title = match.group(1)
        # Remove the title attribute from the img tag
        img_tag = re.sub(r'\s*title="[^"]*"', '', full_tag)
        return (
            f'<figure>{img_tag}'
            f'<figcaption>{title}</figcaption></figure>'
        )

    return re.sub(r'<img\b[^>]*\btitle="([^"]+)"[^>]*/>', _replacer, html_text)


def clean_html(raw_html: str) -> str:
    """Strip HTML tags and normalize whitespace."""
    if not raw_html:
        return ""
    clean = re.sub(r'<[^>]+>', '', raw_html)
    clean = html_lib.unescape(clean)
    clean = ' '.join(clean.split())
    return clean


def truncate(text: str, length: int = 200) -> str:
    """Truncate text to specified length with ellipsis."""
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + '...'


def slugify(title: str, date_str: str) -> str:
    """Create a URL-safe slug from the post title, prefixed with the date."""
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return f"{date_str}-{slug}"


def et_to_utc(date_str: str, time_str: str) -> datetime:
    """Convert an ET date + time to a UTC datetime."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    if ":" in time_str:
        hour, minute = (int(x) for x in time_str.split(":"))
    else:
        t = int(time_str)
        hour, minute = t // 60, t % 60
    dt = dt.replace(hour=hour, minute=minute)
    return dt + timedelta(hours=ET_UTC_OFFSET_HOURS)


def build_post_html(meta: dict, body_html: str, summary: str = "", prev_post=None, next_post=None) -> str:
    """Render a full post page from the template."""
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    # Format date for display (UTC)
    utc_dt = et_to_utc(str(meta["date"]), meta.get("time", "00:00"))
    date_display = utc_dt.strftime("%B %d, %Y")

    # Build tag pills
    tags_html = ""
    tags = meta.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]
    if tags:
        tags_html = " ".join(
            f'<span class="blog-tag">{tag}</span>' for tag in tags
        )

    # Build prev/next navigation
    nav_html = '<div class="post-nav">'
    if prev_post:
        nav_html += f'<a href="{prev_post["slug"]}.html" class="post-nav-link prev">← {prev_post["title"]}</a>'
    else:
        nav_html += '<span></span>'
    if next_post:
        nav_html += f'<a href="{next_post["slug"]}.html" class="post-nav-link next">{next_post["title"]} →</a>'
    else:
        nav_html += '<span></span>'
    nav_html += '</div>'

    # Replace placeholders
    slug = meta.get("slug", "")
    post_url = f"{BASE_URL}/blog/posts-html/{slug}.html"
    html = template.replace("{{TITLE}}", meta["title"])
    html = html.replace("{{DATE}}", date_display)
    html = html.replace("{{TAGS}}", tags_html)
    html = html.replace("{{SUMMARY}}", summary)
    html = html.replace("{{URL}}", post_url)
    # Fix image paths: posts reference images/ relative to blog/, but HTML
    # lives in blog/posts-html/, so rewrite to ../images/
    body_html = re.sub(r'src="images/', 'src="../images/', body_html)
    # Wrap images with title attributes in <figure>/<figcaption>
    body_html = wrap_captioned_images(body_html)
    html = html.replace("{{CONTENT}}", body_html)
    html = html.replace("{{POST_NAV}}", nav_html)

    return html


def generate_rss(posts: list[dict]) -> str:
    """Generate an RSS 2.0 feed from post metadata."""
    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")

    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Studio Quagg Blog"
    ET.SubElement(channel, "description").text = (
        "Musings of Quagg."
    )
    ET.SubElement(channel, "link").text = f"{BASE_URL}/blog/"
    ET.SubElement(channel, "language").text = "en-us"
    ET.SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime(
        "%a, %d %b %Y %H:%M:%S +0000"
    )

    atom_link = ET.SubElement(channel, "atom:link")
    atom_link.set("href", f"{BASE_URL}/blog/feed.xml")
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")

    for post in posts:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = post["title"]

        link = f"{BASE_URL}/blog/posts-html/{post['slug']}.html"
        ET.SubElement(item, "link").text = link

        ET.SubElement(item, "description").text = post.get("summary", "")

        # utc_datetime is already in UTC
        date_obj = datetime.strptime(post["utc_datetime"], "%Y-%m-%dT%H:%M:%S")
        ET.SubElement(item, "pubDate").text = date_obj.strftime(
            "%a, %d %b %Y %H:%M:%S +0000"
        )

        guid = ET.SubElement(item, "guid")
        guid.set("isPermaLink", "true")
        guid.text = link

        if post.get("tags"):
            for tag in post["tags"]:
                ET.SubElement(item, "category").text = tag

    xml_str = ET.tostring(rss, encoding="unicode")
    dom = minidom.parseString(xml_str)
    pretty = dom.toprettyxml(indent="  ")
    lines = pretty.split("\n")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + "\n".join(lines[1:])


def main():
    if not POSTS_DIR.exists():
        print(f"No posts directory at {POSTS_DIR}")
        return

    md = markdown.Markdown(extensions=MD_EXTENSIONS)

    # ── Collect and parse all posts ────────────────────────────────
    posts = []
    for md_file in sorted(POSTS_DIR.glob("*.md")):
        print(f"Processing: {md_file.name}")
        raw = md_file.read_text(encoding="utf-8")
        meta, body = parse_front_matter(raw)

        # Validate required fields
        for field in ("title", "date"):
            if field not in meta:
                print(f"  ⚠ Skipping {md_file.name}: missing '{field}' in front matter")
                break
        else:
            slug = slugify(meta["title"], str(meta["date"]))
            # Expand :::item and :::ability blocks before Markdown conversion
            body = expand_card_blocks(body)
            # Expand ||spoiler|| syntax before Markdown conversion
            body = expand_spoiler_text(body)
            body_html = md.convert(body)
            md.reset()

            tag_list = (
                [t.strip() for t in meta["tags"].split(",")]
                if meta.get("tags")
                else []
            )

            # Generate summary from post content (strip HTML, truncate)
            plain_text = clean_html(body_html)
            summary = truncate(plain_text, 200)

            # Parse optional time field (HH:MM), default to 00:00
            # YAML may parse HH:MM as sexagesimal int, so handle both
            raw_time = meta.get("time", "00:00")
            if isinstance(raw_time, int):
                # Convert sexagesimal back: e.g. 870 → "14:30"
                time_val = f"{raw_time // 60}:{raw_time % 60:02d}"
            else:
                time_val = str(raw_time)

            # Compute UTC datetime for display, sorting, and RSS
            utc_dt = et_to_utc(str(meta["date"]), time_val)
            utc_date = utc_dt.strftime("%Y-%m-%d")
            utc_datetime_iso = utc_dt.strftime("%Y-%m-%dT%H:%M:%S")

            posts.append(
                {
                    "title": meta["title"],
                    "date": str(meta["date"]),
                    "utc_date": utc_date,
                    "utc_datetime": utc_datetime_iso,
                    "time": time_val,
                    "tags": tag_list,
                    "summary": summary,
                    "slug": slug,
                    "body_html": body_html,
                }
            )

    # Sort newest first (date + time)
    posts.sort(key=lambda p: f"{p['date']}T{p.get('time', '00:00')}", reverse=True)
    print(f"\nFound {len(posts)} valid post(s).")

    # ── Generate individual post pages ─────────────────────────────
    HTML_OUT_DIR.mkdir(exist_ok=True)
    for i, post in enumerate(posts):
        # prev = newer post (lower index), next = older post (higher index)
        prev_post = posts[i - 1] if i > 0 else None
        next_post = posts[i + 1] if i < len(posts) - 1 else None

        html = build_post_html(post, post["body_html"], post["summary"], prev_post, next_post)
        out_path = HTML_OUT_DIR / f"{post['slug']}.html"
        out_path.write_text(html, encoding="utf-8")
        print(f"  → posts-html/{out_path.name}")

    # ── Generate blog-data.json (no body_html) ─────────────────────
    json_posts = [
        {
            "title": p["title"],
            "date": p["utc_date"],
            "utc_datetime": p["utc_datetime"],
            "tags": p["tags"],
            "summary": p["summary"],
            "slug": p["slug"],
        }
        for p in posts
    ]

    output = {
        "lastUpdated": datetime.now().isoformat(),
        "posts": json_posts,
    }

    OUTPUT_JSON.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"  → blog-data.json ({len(json_posts)} posts)")

    # ── Generate RSS feed ──────────────────────────────────────────
    rss_xml = generate_rss(json_posts)
    OUTPUT_FEED.write_text(rss_xml, encoding="utf-8")
    print(f"  → blog/feed.xml")

    print("\nBlog build complete!")


if __name__ == "__main__":
    main()
