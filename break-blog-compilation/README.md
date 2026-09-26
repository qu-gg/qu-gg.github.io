# BREAK!! Blog Compendium

This folder contains the reader for the BREAK!! Devblog compendium. It organizes the selected articles by subject into one browser-based book with a table of contents and browser print support.

## Run locally

From the repository root:

```bash
python3 -m http.server 8765
```

Open <http://127.0.0.1:8765/break-blog-compilation/>. The reader fetches `compendium-data.json` and the tracked article bodies from `source-posts/`, so opening `index.html` directly from the filesystem will not work in browsers that block local fetches.

## Source handling

`compendium-data.json` stores the curated article order and source IDs. The reader loads the exact captured bodies from the tracked `source-posts/` directory; `capture-additional-posts.py` refreshes that directory from the official Blogger feed using only IDs present in the manifest. It keeps source text and semantic HTML, preserves external links and media URLs, retains readable source text colors plus emphasis such as bold, italics, decoration, alignment, and highlights, and removes executable elements and layout-disruptive font overrides before applying the compendium layout. Generic Blogspot wrappers are flattened into natural-flow content units while source separators are preserved inline. Article bodies are not paginated by JavaScript: each article is one continuous section, screen scrolling remains natural, and the browser handles print page breaking. Each article begins on a new printed page and can continue across as many native pages as needed.

The current manifest contains 79 articles organized into:

- Character Options
- Design Toolkit
- Adversaries
- Adventure Sites
- Gear & Crafting
- Setting

Setting subsections include `Culture`, `Factions`, `Places`, and `People`.

The source archive and individual authors remain the authority for the original content. This is an unofficial presentation layer.

The monthly `refresh-blog-compendium.yml` workflow refreshes only the IDs selected by the manifest and commits their exact captured source records under `source-posts/`. It does not scrape or publish the complete official archive.
