#!/usr/bin/env python3
"""
inject-pdf-toc.py — Inject bookmarks and TOC hyperlinks into The Helical Expeditions PDF.

This script takes the browser-exported PDF and:
  1. Auto-detects adventure page numbers by searching the PDF text
  2. Adds a bookmark outline (sidebar navigation in PDF readers) for each adventure
     in the format: [Sub-region Name] Adventure Name
  3. Adds clickable hyperlinks on the Table of Contents pages so each entry
     jumps directly to its adventure.

Usage:
    python inject-pdf-toc.py <input.pdf> [output.pdf]

If no output path is given, writes to <input>_bookmarked.pdf.

Dependencies:
    pip install PyMuPDF
"""

import sys
import os
import fitz  # PyMuPDF


# ============================================================
# Book structure — mirrors helical-expeditions-book.html
# Adventures are sorted by sublocation order within each region,
# matching the JS sort in getOrderedAdventures().
# ============================================================

# Front matter entries that appear on the TOC pages
FRONT_MATTER = [
    "Introduction",
    "Using This Book",
    "Reference Pages",
]

# Book structure: region → (sublocations_order, adventures)
# Adventures listed in their original array order per the HTML.
# The script sorts them by sublocation index, same as the JS compiler.
BOOK_STRUCTURE = {
    "Blazing Garden": {
        "sublocations": ["Taaga", "Thunda Sands", "Sol Alliance", "No-Folk Land", "Pride Coast"],
        "adventures": [
            {"title": "Prickly's Prickly Situation", "sublocation": "Thunda Sands"},
            {"title": "The Emberclaw Brigade",       "sublocation": "Taaga"},
            {"title": "Of Cats and a Rat",            "sublocation": "Pride Coast"},
            {"title": "Thunda Circuit",               "sublocation": "Thunda Sands"},
            {"title": "Forced Landing!",              "sublocation": "No-Folk Land"},
            {"title": "Horror in the Deynali",        "sublocation": "Sol Alliance"},
        ],
    },
    "The Twilight Meridian": {
        "sublocations": ["Seven Holy Isles", "Night Haven", "Sunken Isles", "Stahlfeld", "Galvanus Archipelago"],
        "adventures": [
            {"title": "Pity at Portian Docks",        "sublocation": "Galvanus Archipelago"},
            {"title": "Danger for a Rokko-Do",        "sublocation": "Seven Holy Isles"},
            {"title": "Sinking the Float Stone Mine",  "sublocation": "Seven Holy Isles"},
            {"title": "Deal with a Sea Witch",        "sublocation": "Sunken Isles"},
            {"title": "Nobility Beneath Waves",       "sublocation": "Galvanus Archipelago"},
            {"title": "A Grey Matter",                "sublocation": "Night Haven"},
            {"title": "Cog's Finest Gadgeteer",       "sublocation": "Stahlfeld"},
        ],
    },
    "Wistful Dark": {
        "sublocations": ["Crystalia", "Murk", "Shard", "Shadowed Lands", "The Eaten Isle", "Aiden", "Hollow Queen's Kingdom"],
        "adventures": [
            {"title": "Crystal Clear?",                "sublocation": "Crystalia"},
            {"title": "Hold the Wall",                 "sublocation": "Aiden"},
            {"title": "Day of Rekindled Lights",       "sublocation": "Shadowed Lands"},
            {"title": "They Dug Too Deep",             "sublocation": "Hollow Queen's Kingdom"},
            {"title": "Mystery of Mrs Miggins' Pies",  "sublocation": "Murk"},
            {"title": "To Deal a Sigil",               "sublocation": "Shard"},
            {"title": "A View Between Time",           "sublocation": "The Eaten Isle"},
        ],
    },
}

# TOC page search: which printed page numbers contain the table of contents.
# These are auto-detected if possible, but this fallback is used otherwise.
TOC_PRINTED_PAGES = [3, 4]


def get_sorted_adventures(region_data):
    """Sort adventures by sublocation order, matching the JS compiler's sort."""
    subloc_order = region_data["sublocations"]
    adventures = region_data["adventures"]
    return sorted(adventures, key=lambda a: subloc_order.index(a["sublocation"]))


def find_page_for_title(doc, title, start_page=0):
    """
    Search the PDF for a page containing the given title text.
    Returns 0-based page index or None if not found.
    Searches from start_page forward to find the earliest occurrence.
    """
    for page_idx in range(start_page, len(doc)):
        page = doc[page_idx]
        if page.search_for(title):
            return page_idx
    return None


def auto_detect_pages(doc):
    """
    Auto-detect page numbers for all front matter and adventures
    by searching the PDF text.
    Returns (front_matter_pages, adventure_pages, toc_pages).
    - front_matter_pages: list of (title, pdf_page_idx)
    - adventure_pages: ordered list of (region, sublocation, title, pdf_page_idx)
    - toc_pages: list of pdf_page_idx for TOC pages
    """
    print("  Auto-detecting page numbers...")

    # Find TOC pages (search for "Contents" heading)
    toc_pages = []
    for page_idx in range(min(10, len(doc))):  # TOC is in first 10 pages
        page = doc[page_idx]
        text = page.get_text()
        if "Contents" in text and ("Adventures Across" in text or "Continued" in text):
            toc_pages.append(page_idx)
    if not toc_pages:
        print("    Warning: Could not auto-detect TOC pages, using defaults.")
        toc_pages = [p - 1 for p in TOC_PRINTED_PAGES]  # Convert to 0-indexed
    print(f"    TOC pages (0-indexed): {toc_pages}")

    # Find front matter pages
    front_matter_pages = []
    for title in FRONT_MATTER:
        page_idx = find_page_for_title(doc, title, start_page=2)  # Skip title/filler
        if page_idx is not None:
            # Make sure we're not finding it on the TOC page
            if page_idx not in toc_pages:
                front_matter_pages.append((title, page_idx))
                print(f"    '{title}' → page {page_idx + 1} (PDF idx {page_idx})")
            else:
                # Search again past the TOC
                page_idx = find_page_for_title(doc, title, start_page=max(toc_pages) + 1)
                if page_idx is not None:
                    front_matter_pages.append((title, page_idx))
                    print(f"    '{title}' → page {page_idx + 1} (PDF idx {page_idx})")
                else:
                    print(f"    Warning: Could not find front matter '{title}'")
        else:
            print(f"    Warning: Could not find front matter '{title}'")

    # Find adventure pages (search in order they appear in the book)
    adventure_pages = []
    # Start searching after front matter
    search_start = max(toc_pages[-1] if toc_pages else 0, 
                       front_matter_pages[-1][1] if front_matter_pages else 0) + 1

    for region_name, region_data in BOOK_STRUCTURE.items():
        sorted_advs = get_sorted_adventures(region_data)
        for adv in sorted_advs:
            title = adv["title"]
            subloc = adv["sublocation"]
            page_idx = find_page_for_title(doc, title, start_page=search_start)
            if page_idx is not None:
                adventure_pages.append((region_name, subloc, title, page_idx))
                print(f"    [{subloc}] {title} → page {page_idx + 1} (PDF idx {page_idx})")
                # Next search starts after this adventure (adventures are ~4 pages)
                search_start = page_idx + 1
            else:
                print(f"    Warning: Could not find adventure '{title}'")

    return front_matter_pages, adventure_pages, toc_pages


def build_outline(doc, front_matter_pages, adventure_pages, toc_pages):
    """
    Build the PDF TOC/outline entries.
    Returns list of [level, title, 1-based-page] for PyMuPDF's set_toc.
    """
    toc = []

    # Cover page (first page)
    toc.append([1, "Cover", 1])

    # Table of Contents
    if toc_pages:
        toc.append([1, "Table of Contents", toc_pages[0] + 1])

    # Front matter
    for title, pdf_idx in front_matter_pages:
        toc.append([1, title, pdf_idx + 1])

    # Adventures by region
    current_region = None
    for region, subloc, title, pdf_idx in adventure_pages:
        if region != current_region:
            # Add region as top-level entry
            toc.append([1, region, pdf_idx + 1])
            current_region = region
        label = f"[{subloc}] {title}"
        toc.append([2, label, pdf_idx + 1])

    # Back cover (last page)
    toc.append([1, "Back Cover", len(doc)])

    return toc


def add_bookmarks(doc, toc):
    """Add PDF outline (bookmarks) using PyMuPDF's set_toc."""
    max_page = len(doc)
    # Clamp page numbers to valid range
    clamped_toc = []
    for level, title, page_num in toc:
        clamped = min(max(page_num, 1), max_page)
        clamped_toc.append([level, title, clamped])
    doc.set_toc(clamped_toc)
    print(f"  Added {len(clamped_toc)} bookmarks to PDF outline.")


def add_toc_hyperlinks(doc, front_matter_pages, adventure_pages, toc_pages):
    """
    Scan the Table of Contents pages for text matching adventure/front-matter titles
    and add clickable link annotations that jump to the target page.
    """
    # Build lookup: title text → 0-based pdf page index
    link_targets = {}
    for title, pdf_idx in front_matter_pages:
        link_targets[title] = pdf_idx
    for region, subloc, title, pdf_idx in adventure_pages:
        link_targets[title] = pdf_idx

    links_added = 0
    max_page = len(doc)

    for toc_pdf_idx in toc_pages:
        if toc_pdf_idx < 0 or toc_pdf_idx >= max_page:
            print(f"  Warning: TOC page PDF idx {toc_pdf_idx} out of range, skipping.")
            continue

        page = doc[toc_pdf_idx]

        for title, target_pdf_idx in link_targets.items():
            clamped_idx = min(max(target_pdf_idx, 0), max_page - 1)
            printed_page = str(target_pdf_idx + 1)

            # Link on the adventure/section title text
            text_instances = page.search_for(title)
            for rect in text_instances:
                link_rect = fitz.Rect(rect.x0 - 2, rect.y0 - 2, rect.x1 + 2, rect.y1 + 2)
                link = {
                    "kind": fitz.LINK_GOTO,
                    "from": link_rect,
                    "page": clamped_idx,
                    "to": fitz.Point(0, 0),
                }
                page.insert_link(link)
                links_added += 1

            # Also link on the printed page number shown on the TOC.
            # To avoid false matches (e.g. "5" inside "55"), only link a page
            # number hit if it sits on roughly the same y-coordinate as a title hit.
            if text_instances:
                title_y_coords = [(r.y0 + r.y1) / 2 for r in text_instances]
                page_num_hits = page.search_for(printed_page)
                for rect in page_num_hits:
                    hit_y = (rect.y0 + rect.y1) / 2
                    # Check if this page number is on the same line as a title match
                    if any(abs(hit_y - ty) < 10 for ty in title_y_coords):
                        link_rect = fitz.Rect(rect.x0 - 2, rect.y0 - 2, rect.x1 + 2, rect.y1 + 2)
                        link = {
                            "kind": fitz.LINK_GOTO,
                            "from": link_rect,
                            "page": clamped_idx,
                            "to": fitz.Point(0, 0),
                        }
                        page.insert_link(link)
                        links_added += 1

    print(f"  Added {links_added} hyperlinks on TOC pages.")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        print(__doc__.strip())
        sys.exit(0 if sys.argv[1:] else 1)

    input_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    else:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_bookmarked{ext}"

    print(f"Opening: {input_path}")
    doc = fitz.open(input_path)
    print(f"  PDF has {len(doc)} pages.")

    # Auto-detect all page numbers
    front_matter_pages, adventure_pages, toc_pages = auto_detect_pages(doc)

    print("\nAdding bookmarks...")
    toc = build_outline(doc, front_matter_pages, adventure_pages, toc_pages)
    add_bookmarks(doc, toc)

    print("Adding TOC hyperlinks...")
    add_toc_hyperlinks(doc, front_matter_pages, adventure_pages, toc_pages)

    print(f"\nSaving: {output_path}")
    if output_path == input_path:
        doc.save(output_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
    else:
        doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    print("Done!")


if __name__ == "__main__":
    main()
