#!/usr/bin/env python3
"""
add-scrap.py — CLI tool for adding entries to the GM Screen database.

Usage:
    python scripts/add-scrap.py --url <URL>
    python scripts/add-scrap.py --pdf <FILE> [--pages 12-14]
    python scripts/add-scrap.py --image <URL> --caption "..."
    python scripts/add-scrap.py --manual

All modes append to gm-screen-data.json.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

# Resolve paths relative to repo root
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = REPO_ROOT / "gm-screen-data.json"
VENV_BIN = REPO_ROOT / ".venv" / "bin"

CATEGORIES = ["npcs", "encounters", "locations", "items", "tables", "rules", "inspiration"]
ENTRY_TYPES = ["table", "prose", "image", "snippet"]


def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            return json.load(f)
    return {"entries": []}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Saved to {DATA_FILE.relative_to(REPO_ROOT)}")


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:60].strip("-")


def prompt_choice(prompt, options, allow_custom=False):
    print(f"\n{prompt}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    if allow_custom:
        print(f"  {len(options) + 1}. (enter custom)")
    while True:
        try:
            val = input("> ").strip()
            idx = int(val) - 1
            if 0 <= idx < len(options):
                return options[idx]
            if allow_custom and idx == len(options):
                return input("  Custom value: ").strip()
        except ValueError:
            # Allow typing the option directly
            if val in options:
                return val
            if allow_custom and val:
                return val
        print("  Invalid choice, try again.")


def prompt_tags():
    raw = input("\nTags (comma-separated): ").strip()
    if not raw:
        return []
    return [t.strip().lower() for t in raw.split(",") if t.strip()]


def prompt_source():
    print("\n--- Source Attribution ---")
    author = input("Author: ").strip()
    title = input("Source title: ").strip()
    url = input("Source URL (blank if none): ").strip() or None
    date_str = input(f"Date (YYYY-MM-DD, blank for unknown): ").strip() or None
    note = input("Note (e.g., 'Free quickstart PDF', blank for none): ").strip() or None
    source = {}
    if author:
        source["author"] = author
    if title:
        source["title"] = title
    if url:
        source["url"] = url
    if date_str:
        source["date"] = date_str
    if note:
        source["note"] = note
    return source


def prompt_metadata(suggested_title=""):
    title = input(f"\nEntry title [{suggested_title}]: ").strip() or suggested_title
    entry_id = slugify(title)
    print(f"  ID: {entry_id}")

    entry_type = prompt_choice("Entry type:", ENTRY_TYPES)
    category = prompt_choice("Category:", CATEGORIES, allow_custom=True)
    description = input("\nDescription (optional, italic text shown under title): ").strip() or None
    tags = prompt_tags()
    source = prompt_source()

    return {
        "id": entry_id,
        "type": entry_type,
        "category": category,
        "title": title,
        "description": description,
        "tags": tags,
        "source": source,
        "added": date.today().isoformat(),
    }


# ============================================================
# --url mode
# ============================================================
def extract_from_url(url):
    """Use MarkItDown to convert a URL to Markdown, then present for editing."""
    markitdown = VENV_BIN / "markitdown"
    if not markitdown.exists():
        print("⚠️  markitdown not found in .venv/bin. Falling back to requests.")
        return extract_from_url_fallback(url)

    print(f"\n⏳ Fetching {url} via MarkItDown...")
    try:
        result = subprocess.run(
            [str(markitdown), url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            print(f"⚠️  MarkItDown error: {result.stderr[:200]}")
            return extract_from_url_fallback(url)
        return result.stdout
    except subprocess.TimeoutExpired:
        print("⚠️  MarkItDown timed out.")
        return extract_from_url_fallback(url)


def extract_from_url_fallback(url):
    """Fallback: use requests + basic text extraction."""
    try:
        import requests
        from html.parser import HTMLParser

        resp = requests.get(url, timeout=15, headers={"User-Agent": "GMScreen/1.0"})
        resp.raise_for_status()

        # Very basic HTML to text
        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text = []
                self.skip = False

            def handle_starttag(self, tag, attrs):
                if tag in ("script", "style", "noscript"):
                    self.skip = True

            def handle_endtag(self, tag):
                if tag in ("script", "style", "noscript"):
                    self.skip = False
                if tag in ("p", "br", "div", "h1", "h2", "h3", "h4", "li"):
                    self.text.append("\n")

            def handle_data(self, data):
                if not self.skip:
                    self.text.append(data)

        parser = TextExtractor()
        parser.feed(resp.text)
        return "".join(parser.text)
    except Exception as e:
        print(f"⚠️  Fallback extraction failed: {e}")
        return None


def detect_lists(markdown_text):
    """Scan markdown for numbered lists that could be roll tables."""
    tables = []
    current_name = None
    current_items = []
    in_list = False

    for line in markdown_text.split("\n"):
        # Detect headers that might name a table
        header_match = re.match(r"^#{1,4}\s+(.+)", line)
        if header_match:
            if current_items:
                tables.append({"name": current_name or "Untitled", "items": list(current_items)})
                current_items = []
            current_name = header_match.group(1).strip()
            in_list = False
            continue

        # Detect numbered list items
        list_match = re.match(r"^\s*\d+[\.\)]\s+(.+)", line)
        if list_match:
            current_items.append(list_match.group(1).strip())
            in_list = True
        elif in_list and line.strip() == "":
            if current_items:
                tables.append({"name": current_name or "Untitled", "items": list(current_items)})
                current_items = []
            in_list = False

    if current_items:
        tables.append({"name": current_name or "Untitled", "items": list(current_items)})

    return [t for t in tables if len(t["items"]) >= 3]


def mode_url(args):
    markdown = extract_from_url(args.url)
    if not markdown:
        print("❌ Could not extract content.")
        return

    # Show extracted content
    lines = markdown.strip().split("\n")
    print(f"\n--- Extracted {len(lines)} lines ---")
    for i, line in enumerate(lines[:80], 1):
        print(f"  {i:3}: {line}")
    if len(lines) > 80:
        print(f"  ... ({len(lines) - 80} more lines)")

    # Auto-detect roll tables
    detected = detect_lists(markdown)
    if detected:
        print(f"\n📋 Detected {len(detected)} potential roll table(s):")
        for i, t in enumerate(detected, 1):
            die = f"d{len(t['items'])}"
            print(f"  {i}. {t['name']} ({die}, {len(t['items'])} items)")

        use_tables = input("\nUse detected tables? (y/n/select e.g. '1,3'): ").strip().lower()
        if use_tables == "y":
            selected = detected
        elif use_tables == "n":
            selected = []
        else:
            try:
                indices = [int(x.strip()) - 1 for x in use_tables.split(",")]
                selected = [detected[i] for i in indices if 0 <= i < len(detected)]
            except (ValueError, IndexError):
                selected = []

        if selected:
            return build_table_entry(selected, args.url)

    # If no tables, present as prose
    print("\nNo roll tables detected (or skipped). Creating prose entry.")
    print("Paste/edit the content you want to keep (end with a blank line):")
    content_lines = []
    while True:
        line = input()
        if line == "":
            break
        content_lines.append(line)

    html = "<p>" + "</p><p>".join(content_lines) + "</p>"

    meta = prompt_metadata()
    meta["content"] = {"html": html}

    statblock = input("Statblock (blank for none): ").strip()
    if statblock:
        meta["content"]["statblock"] = statblock

    image_url = input("Image URL (blank for none): ").strip()
    if image_url:
        meta["content"]["image"] = image_url

    data = load_data()
    data["entries"].append(meta)
    save_data(data)


def build_table_entry(tables, source_url=None):
    """Build a table-type entry from detected tables."""
    formatted = []
    for t in tables:
        die = f"d{len(t['items'])}"
        formatted.append({
            "name": t["name"],
            "die": die,
            "items": t["items"]
        })

    roll_all = len(formatted) > 1
    if roll_all:
        ra = input(f"\nAdd 'Roll All' button for {len(formatted)} tables? (Y/n): ").strip().lower()
        roll_all = ra != "n"

    meta = prompt_metadata(suggested_title=tables[0]["name"] if len(tables) == 1 else "")
    meta["type"] = "table"
    meta["content"] = {"tables": formatted, "rollAll": roll_all}

    if source_url and "source" in meta and not meta["source"].get("url"):
        meta["source"]["url"] = source_url

    data = load_data()
    data["entries"].append(meta)
    save_data(data)


# ============================================================
# --pdf mode
# ============================================================
def mode_pdf(args):
    pdf_path = Path(args.pdf).resolve()
    if not pdf_path.exists():
        print(f"❌ File not found: {pdf_path}")
        return

    markitdown = VENV_BIN / "markitdown"
    print(f"\n⏳ Extracting from {pdf_path.name}...")

    try:
        result = subprocess.run(
            [str(markitdown), str(pdf_path)],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"⚠️  MarkItDown error: {result.stderr[:300]}")
            print("Install PDF deps with: .venv/bin/pip install markitdown[pdf]")
            return
        markdown = result.stdout
    except subprocess.TimeoutExpired:
        print("⚠️  Extraction timed out.")
        return

    # If --pages specified, try to filter (rough heuristic: look for page markers)
    if args.pages:
        print(f"  (Page filtering is approximate with PDF extraction)")

    lines = markdown.strip().split("\n")
    print(f"\n--- Extracted {len(lines)} lines ---")
    for i, line in enumerate(lines[:100], 1):
        print(f"  {i:3}: {line}")
    if len(lines) > 100:
        print(f"  ... ({len(lines) - 100} more lines)")

    print("\nSelect lines to keep (e.g., '45-80' or 'all'), or 'tables' to auto-detect:")
    sel = input("> ").strip().lower()

    if sel == "tables":
        detected = detect_lists(markdown)
        if detected:
            print(f"\n📋 Detected {len(detected)} potential roll table(s):")
            for i, t in enumerate(detected, 1):
                die = f"d{len(t['items'])}"
                print(f"  {i}. {t['name']} ({die}, {len(t['items'])} items)")
            build_table_entry(detected)
        else:
            print("No tables detected. Try selecting lines manually.")
        return

    if sel == "all":
        selected_lines = lines
    else:
        try:
            parts = sel.split("-")
            start = int(parts[0]) - 1
            end = int(parts[1]) if len(parts) > 1 else start + 1
            selected_lines = lines[start:end]
        except (ValueError, IndexError):
            print("Invalid range. Using all lines.")
            selected_lines = lines

    # Check for tables in selection
    selected_text = "\n".join(selected_lines)
    detected = detect_lists(selected_text)
    if detected:
        print(f"\n📋 Found {len(detected)} table(s) in selection.")
        use = input("Create as roll table(s)? (Y/n): ").strip().lower()
        if use != "n":
            build_table_entry(detected)
            return

    # Prose entry
    html = "<p>" + "</p><p>".join(line for line in selected_lines if line.strip()) + "</p>"
    meta = prompt_metadata()
    meta["content"] = {"html": html}
    data = load_data()
    data["entries"].append(meta)
    save_data(data)


# ============================================================
# --image mode
# ============================================================
def mode_image(args):
    print(f"\n🖼  Adding image entry: {args.image}")

    meta = prompt_metadata()
    meta["type"] = "image"
    meta["content"] = {
        "url": args.image,
        "caption": args.caption or ""
    }

    data = load_data()
    data["entries"].append(meta)
    save_data(data)


# ============================================================
# --manual mode
# ============================================================
def mode_manual(args):
    template = {
        "id": "",
        "type": "prose",
        "category": "encounters",
        "title": "TITLE HERE",
        "description": None,
        "content": {
            "html": "<p>Your content here.</p>",
            "statblock": None
        },
        "tags": [],
        "source": {
            "author": "",
            "title": "",
            "url": None,
            "date": None
        },
        "added": date.today().isoformat()
    }

    editor = os.environ.get("EDITOR", os.environ.get("VISUAL", "nano"))
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, prefix="gm-scrap-") as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
        tmp_path = f.name

    print(f"\n📝 Opening {editor} with template...")
    print("  Edit the JSON, save, and close to add the entry.")
    subprocess.run([editor, tmp_path])

    try:
        with open(tmp_path) as f:
            entry = json.load(f)
        if not entry.get("title") or entry["title"] == "TITLE HERE":
            print("❌ Entry title not set. Aborting.")
            return
        if not entry.get("id"):
            entry["id"] = slugify(entry["title"])

        data = load_data()
        data["entries"].append(entry)
        save_data(data)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        print(f"  Your file is saved at {tmp_path}")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="Add entries to the GM Screen database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/add-scrap.py --url https://todistantlands.github.io/2023/06/13/zelda-npcs.html
  python scripts/add-scrap.py --pdf ~/Downloads/quickstart.pdf --pages 22-24
  python scripts/add-scrap.py --image https://example.com/map.jpg --caption "Hex map"
  python scripts/add-scrap.py --manual
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="URL to fetch and extract content from")
    group.add_argument("--pdf", help="PDF file to extract content from")
    group.add_argument("--image", help="Image URL to add as an image entry")
    group.add_argument("--manual", action="store_true", help="Open $EDITOR with a JSON template")

    parser.add_argument("--pages", help="Page range for PDF extraction (e.g., '22-24')")
    parser.add_argument("--caption", help="Caption for --image mode")

    args = parser.parse_args()

    if args.url:
        mode_url(args)
    elif args.pdf:
        mode_pdf(args)
    elif args.image:
        mode_image(args)
    elif args.manual:
        mode_manual(args)


if __name__ == "__main__":
    main()
