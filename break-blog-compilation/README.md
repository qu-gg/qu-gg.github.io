# BREAK!! Blog Compendium

This folder contains the reader for the BREAK!! Devblog compendium. It organizes the selected articles by subject into one browser-based book with a table of contents and browser print support.

## Run locally

From the repository root:

```bash
python3 -m http.server 8765
```

Open <http://127.0.0.1:8765/break-blog-compilation/>. The reader fetches `compendium-data.json` and the tracked article bodies from `source-posts/`, so opening `index.html` directly from the filesystem will not work in browsers that block local fetches.

## Source handling

`compendium-data.json` stores the curated article order and source IDs. The reader loads the exact captured bodies from the tracked `source-posts/` directory; `capture-additional-posts.py` refreshes that directory from the official Blogger feed using only IDs present in the manifest. It keeps source text and semantic HTML, preserves external links and media URLs, retains meaningful emphasis such as bold, italics, decoration, source colors, intentional highlights, and vertical alignment, and removes executable and layout-disruptive font overrides before applying the compendium layout. Font families, font sizes, line heights, margins, padding, and ordinary paragraph alignment are normalized to the book style without changing text or image content; readable source colors and background highlights are retained. Before pagination, it normalizes empty Blogger spacer blocks, repeated breaks, and malformed sibling nested lists while preserving meaningful article text and emphasis. Generic Blogspot wrappers are flattened into natural-flow content units. Presentation-only semantic markers restore spacing around rules entries, prose subheads, and recognized inline concept labels; multi-label Blogger paragraphs are split into readable blocks without changing their text, links, or emphasis. Article bodies are split into fixed letter-sized pages in the browser, with semantic content splits where needed for local PDF production.

The current manifest contains 80 articles organized into:

- Character Options
- Design Toolkit
- Adversaries
- Adventure Sites
- Gear & Crafting
- Setting

Setting subsections include `Culture`, `Factions`, `Places`, and `People`.

The source archive and individual authors remain the authority for the original content. This is an officially endorsed independent presentation published with permission from BREAK!!'s creators; the BREAK!! logo and cover art are used with permission from Grey Wizard Press.

Article bodies are split into fixed letter-sized page shells in the browser for local PDF production. Each article begins on a fresh page, continuation pages contain only the remaining article body, and corner decorators appear only on the first and last page of an article. The browser print dialog handles the final PDF output.

Unnumbered branded padding pages are inserted after odd-length articles so the next article begins in the same position of the following two-page spread. They use a quiet dual-color rule and small black BREAK!! logo without page-corner decorators. Ten unique decorative figures are assigned once each to seeded, distributed padding-page locations so repeated browser and PDF renders remain stable. A leading padding page is also inserted automatically if front matter ever leaves the first article on the opposite side.

Tables start on a fresh page when they would otherwise break across an occupied page. Oversized tables split only between rows, preserving their header rows where available. Section leads near the bottom of a page are measured with their following content and moved forward when starting them there would strand the section across the boundary.

The monthly `refresh-blog-compendium.yml` workflow refreshes only the IDs selected by the manifest and commits their exact captured source records under `source-posts/`. It does not scrape or publish the complete official archive.

## PDF bookmarks

The browser print dialog creates the normal PDF. To add an embedded category/section/article outline afterward, install PyMuPDF if needed and run:

```bash
python3 scripts/add_compendium_pdf_outline.py compendium.pdf compendium-bookmarked.pdf
```

The outline utility adds Cover, Contents, category, section, article, and Back Cover bookmarks. It reads the captured article titles and manifest order, then maps each article bookmark to its first printed page without changing the PDF content.
