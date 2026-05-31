#!/usr/bin/env python3
"""
add-scrap-server.py — Local extraction server for the GM Screen.

Starts a browser-based tool for visually selecting content blocks from web pages
and saving them as GM Screen entries.

Usage:
    python scripts/add-scrap-server.py [--port 8766]

Then open http://localhost:8766 in your browser.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import webbrowser
from datetime import date
from http import HTTPStatus
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = REPO_ROOT / "gm-screen-data.json"
VENV_BIN = REPO_ROOT / ".venv" / "bin"

CATEGORIES = ["npcs", "encounters", "locations", "items", "tables", "rules", "inspiration"]


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:60].strip("-")


def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            return json.load(f)
    return {"entries": []}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def extract_blocks(url):
    """Fetch a URL and parse it into selectable content blocks."""
    # Try MarkItDown first for markdown, but also get raw HTML for images
    resp = requests.get(url, timeout=20, headers={"User-Agent": "GMScreen/1.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove script/style/nav/footer
    for tag in soup.find_all(["script", "style", "noscript", "nav", "footer", "header"]):
        tag.decompose()

    # Find the main content area (try common selectors)
    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find(class_=re.compile(r"post|content|entry|article", re.I))
        or soup.find("body")
    )
    if not main:
        main = soup

    blocks = []
    block_id = 0

    for el in main.children:
        if not hasattr(el, "name") or el.name is None:
            # Text node
            text = el.strip() if isinstance(el, str) else ""
            if text:
                blocks.append({
                    "id": block_id,
                    "type": "text",
                    "tag": "p",
                    "text": text,
                    "html": f"<p>{text}</p>",
                    "images": [],
                })
                block_id += 1
            continue

        _extract_element(el, blocks, block_id, url)
        block_id = len(blocks)

    return blocks


def _extract_element(el, blocks, start_id, base_url):
    """Recursively extract an element into blocks."""
    if not hasattr(el, "name") or el.name is None:
        return

    block_id = len(blocks)
    tag = el.name

    # Skip empty elements (but keep img tags and elements containing images)
    text = el.get_text(strip=True)
    if not text and tag != "img" and not el.find("img"):
        return

    # Collect images within this element
    images = []
    for img in el.find_all("img"):
        src = img.get("src", "")
        if src:
            # Resolve relative URLs
            if src.startswith("/"):
                parsed = urlparse(base_url)
                src = f"{parsed.scheme}://{parsed.netloc}{src}"
            elif not src.startswith("http"):
                src = base_url.rsplit("/", 1)[0] + "/" + src
            images.append({
                "src": src,
                "alt": img.get("alt", ""),
            })

    # Treat elements that are just image wrappers as image blocks
    # (e.g. Discourse lightbox-wrapper divs, <a> tags wrapping an <img>)
    if images:
        # Check if the element's text is only image metadata (filenames, dimensions)
        from copy import copy
        el_copy = copy(el)
        for meta in el_copy.find_all(class_=re.compile(r"meta|caption|filename|info")):
            meta.decompose()
        remaining_text = el_copy.get_text(strip=True)
        if not remaining_text:
            for image in images:
                blocks.append({
                    "id": len(blocks),
                    "type": "image",
                    "tag": "img",
                    "text": image["alt"],
                    "html": f'<img src="{image["src"]}" alt="{image["alt"]}"/>',
                    "images": [image],
                })
            return

    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        blocks.append({
            "id": block_id,
            "type": "heading",
            "tag": tag,
            "text": text,
            "html": str(el),
            "images": images,
        })
    elif tag in ("ul", "ol"):
        items = []
        for li in el.find_all("li", recursive=False):
            items.append(li.get_text(strip=True))
        blocks.append({
            "id": block_id,
            "type": "list",
            "tag": tag,
            "text": text,
            "html": str(el),
            "items": items,
            "images": images,
        })
    elif tag == "img":
        src = el.get("src", "")
        if src:
            if src.startswith("/"):
                parsed = urlparse(base_url)
                src = f"{parsed.scheme}://{parsed.netloc}{src}"
            elif not src.startswith("http"):
                src = base_url.rsplit("/", 1)[0] + "/" + src
            blocks.append({
                "id": block_id,
                "type": "image",
                "tag": "img",
                "text": el.get("alt", ""),
                "html": str(el),
                "images": [{"src": src, "alt": el.get("alt", "")}],
            })
    elif tag in ("blockquote",):
        blocks.append({
            "id": block_id,
            "type": "quote",
            "tag": tag,
            "text": text,
            "html": str(el),
            "images": images,
        })
    elif tag == "div":
        # Recurse into divs
        for child in el.children:
            if hasattr(child, "name") and child.name:
                _extract_element(child, blocks, len(blocks), base_url)
            elif isinstance(child, str) and child.strip():
                blocks.append({
                    "id": len(blocks),
                    "type": "text",
                    "tag": "p",
                    "text": child.strip(),
                    "html": f"<p>{child.strip()}</p>",
                    "images": [],
                })
    else:
        # p, span, etc — treat as text block
        blocks.append({
            "id": block_id,
            "type": "text",
            "tag": tag,
            "text": text,
            "html": str(el),
            "images": images,
        })


# ============================================================
# HTTP Server
# ============================================================
class ExtractHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Quiet logging
        pass

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html, status=200):
        body = html.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self._send_html(FRONTEND_HTML)
        elif parsed.path == "/extract":
            qs = parse_qs(parsed.query)
            url = qs.get("url", [None])[0]
            if not url:
                self._send_json({"error": "Missing url parameter"}, 400)
                return
            try:
                blocks = extract_blocks(url)
                self._send_json({"blocks": blocks, "url": url})
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/save":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                entry = json.loads(body)
                # Generate ID if missing
                if not entry.get("id"):
                    entry["id"] = slugify(entry.get("title", "untitled"))
                if not entry.get("added"):
                    entry["added"] = date.today().isoformat()

                data = load_data()
                data["entries"].append(entry)
                save_data(data)

                count = len(data["entries"])
                print(f"  ✅ Saved: {entry.get('title', '?')} ({count} total entries)")
                self._send_json({"ok": True, "count": count})
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        else:
            self.send_error(HTTPStatus.NOT_FOUND)


# ============================================================
# Frontend HTML
# ============================================================
FRONTEND_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GM Screen — Content Extractor</title>
<style>
  :root {
    --bg: #fafafa; --bg2: #fff; --text: #2d3436; --text2: #636e72;
    --accent: #6c5ce7; --accent-hover: #5b4cdb; --border: #dfe6e9;
    --font-body: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    --font-display: "Palatino Linotype", "Book Antiqua", Palatino, Georgia, serif;
  }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: var(--font-body); background: var(--bg); color: var(--text); line-height: 1.6; }

  .layout { display: flex; min-height: 100vh; }

  /* ---- Sidebar ---- */
  .sidebar {
    width: 340px; flex-shrink: 0; background: var(--bg2); border-right: 1px solid var(--border);
    padding: 1.5rem; overflow-y: auto; position: sticky; top: 0; height: 100vh;
    display: flex; flex-direction: column; gap: 1rem;
  }
  .sidebar h1 { font-family: var(--font-display); font-size: 1.3rem; margin-bottom: 0.25rem; }
  .sidebar .sub { font-size: 0.85rem; color: var(--text2); margin-bottom: 0.5rem; }

  .field { display: flex; flex-direction: column; gap: 0.25rem; }
  .field label { font-size: 0.8rem; font-weight: 600; color: var(--text2); text-transform: uppercase; letter-spacing: 0.03em; }
  .field input, .field select, .field textarea {
    padding: 0.45rem 0.6rem; border: 1px solid var(--border); border-radius: 6px;
    font-size: 0.9rem; background: var(--bg); font-family: inherit;
  }
  .field input:focus, .field select:focus, .field textarea:focus { outline: none; border-color: var(--accent); }
  .field textarea { resize: vertical; min-height: 60px; }

  .url-row { display: flex; gap: 0.5rem; }
  .url-row input { flex: 1; }
  .fetch-btn, .save-btn {
    padding: 0.45rem 1rem; border: none; border-radius: 6px; font-weight: 600;
    cursor: pointer; font-size: 0.88rem; transition: all 0.15s;
  }
  .fetch-btn { background: var(--accent); color: #fff; white-space: nowrap; }
  .fetch-btn:hover { background: var(--accent-hover); }
  .fetch-btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .save-btn { background: #00b894; color: #fff; width: 100%; margin-top: auto; padding: 0.7rem; font-size: 1rem; }
  .save-btn:hover { background: #00a381; }
  .save-btn:disabled { opacity: 0.5; cursor: not-allowed; }

  .selection-count {
    font-size: 0.85rem; color: var(--text2); padding: 0.5rem 0;
    border-top: 1px solid var(--border); border-bottom: 1px solid var(--border);
  }
  .selection-count strong { color: var(--accent); }

  .status { font-size: 0.85rem; color: var(--text2); text-align: center; }
  .status.error { color: #d63031; }
  .status.success { color: #00b894; }

  .source-section { border-top: 1px solid var(--border); padding-top: 0.75rem; }
  .source-section h3 { font-size: 0.85rem; margin-bottom: 0.5rem; color: var(--text); }

  /* ---- Content area ---- */
  .content { flex: 1; padding: 1.5rem 2rem; min-width: 0; }
  .content-header { margin-bottom: 1rem; }
  .content-header h2 { font-family: var(--font-display); font-size: 1.2rem; color: var(--text2); }

  .empty-state {
    text-align: center; padding: 4rem 2rem; color: var(--text2); font-style: italic;
  }

  /* ---- Blocks ---- */
  .block {
    padding: 0.75rem 1rem; margin-bottom: 0.4rem; border: 2px solid transparent;
    border-radius: 8px; cursor: pointer; transition: all 0.1s; position: relative;
    background: var(--bg2);
  }
  .block:hover { border-color: var(--border); }
  .block.selected { border-color: var(--accent); background: #f0edff; }

  .block-badge {
    position: absolute; top: 0.5rem; right: 0.5rem;
    font-size: 0.65rem; font-weight: 600; text-transform: uppercase;
    padding: 0.1rem 0.4rem; border-radius: 4px; color: #fff; letter-spacing: 0.03em;
  }
  .block-badge.heading { background: #636e72; }
  .block-badge.list { background: #6c5ce7; }
  .block-badge.text { background: #b2bec3; }
  .block-badge.image { background: #00b894; }
  .block-badge.quote { background: #e17055; }

  .block-order {
    position: absolute; top: 0.5rem; left: 0.5rem;
    font-size: 0.7rem; font-weight: 700; color: var(--accent);
    background: #f0edff; border-radius: 4px; padding: 0.1rem 0.35rem;
    display: none;
  }
  .block.selected .block-order { display: inline-block; }

  /* Block type selector - only shown on selected blocks */
  .block-type-select {
    position: absolute; bottom: 0.5rem; right: 0.5rem;
    font-size: 0.75rem; padding: 0.15rem 0.3rem; border: 1px solid var(--accent);
    border-radius: 4px; background: #fff; color: var(--accent); cursor: pointer;
  }
  .block-type-select { display: none; }
  .block.selected .block-type-select { display: inline-block; }

  .block h1, .block h2, .block h3, .block h4 {
    font-family: var(--font-display); margin: 0;
  }
  .block h1 { font-size: 1.4rem; }
  .block h2 { font-size: 1.15rem; }
  .block h3 { font-size: 1rem; }
  .block h4 { font-size: 0.95rem; }

  .block p { margin: 0; font-size: 0.92rem; }
  .block ol, .block ul { margin: 0.25rem 0 0.25rem 1.5rem; font-size: 0.88rem; }
  .block li { margin-bottom: 0.15rem; }
  .block blockquote { border-left: 3px solid var(--accent); padding-left: 0.75rem; font-style: italic; margin: 0; }

  .block img {
    max-width: 100%; max-height: 200px; border-radius: 4px; margin-top: 0.25rem; object-fit: contain;
  }
  .block .img-url {
    font-size: 0.7rem; color: var(--text2); word-break: break-all; margin-top: 0.25rem;
  }

  @media (max-width: 800px) {
    .layout { flex-direction: column; }
    .sidebar { width: 100%; height: auto; position: static; border-right: none; border-bottom: 1px solid var(--border); }
  }
</style>
</head>
<body>
<div class="layout">
  <!-- Sidebar -->
  <div class="sidebar">
    <div>
      <h1>Content Extractor</h1>
      <p class="sub">Fetch a page, click blocks to select, save to GM Screen.</p>
    </div>

    <div class="field">
      <label>URL</label>
      <div class="url-row">
        <input type="text" id="url-input" placeholder="https://..." />
        <button class="fetch-btn" id="fetch-btn" onclick="fetchPage()">Fetch</button>
      </div>
    </div>

    <div class="selection-count" id="selection-count">
      <strong>0</strong> blocks selected
    </div>

    <div class="field">
      <label>Entry Title</label>
      <input type="text" id="entry-title" placeholder="e.g., Zelda-Style NPC Tables" />
    </div>

    <div class="field">
      <label>Type</label>
      <select id="entry-type">
        <option value="table">Roll Table</option>
        <option value="prose" selected>Prose / Encounter</option>
        <option value="image">Image</option>
        <option value="snippet">Snippet</option>
      </select>
    </div>

    <div class="field">
      <label>Category</label>
      <select id="entry-category">
        <option value="npcs">NPCs</option>
        <option value="encounters" selected>Encounters</option>
        <option value="locations">Locations</option>
        <option value="items">Items</option>
        <option value="tables">Tables</option>
        <option value="rules">Rules</option>
        <option value="inspiration">Inspiration</option>
      </select>
    </div>

    <div class="field">
      <label>Description (optional)</label>
      <textarea id="entry-desc" placeholder="Short italic description..."></textarea>
    </div>

    <div class="source-section">
      <h3>Source Attribution</h3>
      <div class="field">
        <label>Author</label>
        <input type="text" id="source-author" />
      </div>
      <div class="field">
        <label>Source Title</label>
        <input type="text" id="source-title" />
      </div>
      <div class="field">
        <label>URL (auto-filled)</label>
        <input type="text" id="source-url" readonly />
      </div>
      <div class="field">
        <label>Date</label>
        <input type="text" id="source-date" placeholder="YYYY-MM-DD" />
      </div>
    </div>

    <div class="status" id="status"></div>
    <button class="save-btn" id="save-btn" onclick="saveEntry()" disabled>Save to GM Screen</button>
  </div>

  <!-- Content area -->
  <div class="content">
    <div class="content-header" id="content-header">
      <h2 id="content-title">Paste a URL and click Fetch</h2>
    </div>
    <div id="blocks-container">
      <div class="empty-state">Extracted content blocks will appear here. Click blocks to select them for your entry.</div>
    </div>
  </div>
</div>

<script>
let allBlocks = [];
let selectedIds = new Set();
let pageUrl = '';

async function fetchPage() {
  const url = document.getElementById('url-input').value.trim();
  if (!url) return;

  const btn = document.getElementById('fetch-btn');
  btn.disabled = true;
  btn.textContent = 'Fetching...';
  setStatus('');

  try {
    const resp = await fetch('/extract?url=' + encodeURIComponent(url));
    const data = await resp.json();

    if (data.error) {
      setStatus(data.error, 'error');
      return;
    }

    allBlocks = data.blocks;
    pageUrl = data.url;
    selectedIds.clear();

    document.getElementById('source-url').value = pageUrl;
    document.getElementById('content-title').textContent =
      `${allBlocks.length} blocks extracted`;

    // Try to auto-detect title from first heading
    const firstHeading = allBlocks.find(b => b.type === 'heading');
    if (firstHeading) {
      document.getElementById('source-title').value = firstHeading.text;
    }

    renderBlocks();
    updateCount();
  } catch (e) {
    setStatus('Fetch failed: ' + e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Fetch';
  }
}

function renderBlocks() {
  const container = document.getElementById('blocks-container');
  container.innerHTML = '';

  allBlocks.forEach(block => {
    const el = document.createElement('div');
    el.className = 'block' + (selectedIds.has(block.id) ? ' selected' : '');
    el.dataset.id = block.id;

    // Badge
    const badge = document.createElement('span');
    badge.className = 'block-badge ' + block.type;
    badge.textContent = block.type;
    el.appendChild(badge);

    // Selection order indicator
    const order = document.createElement('span');
    order.className = 'block-order';
    if (selectedIds.has(block.id)) {
      order.textContent = [...selectedIds].indexOf(block.id) + 1;
    }
    el.appendChild(order);

    // Block type selector (for selected blocks)
    const typeSelect = document.createElement('select');
    typeSelect.className = 'block-type-select';
    ['prose', 'table', 'statblock', 'image', 'skip'].forEach(t => {
      const opt = document.createElement('option');
      opt.value = t;
      opt.textContent = t;
      if (block.type === 'list' && t === 'table') opt.selected = true;
      else if (block.type === 'image' && t === 'image') opt.selected = true;
      else if (block.type === 'text' && t === 'prose') opt.selected = true;
      else if (block.type === 'heading' && t === 'prose') opt.selected = true;
      else if (block.type === 'quote' && t === 'prose') opt.selected = true;
      typeSelect.appendChild(opt);
    });
    typeSelect.addEventListener('click', e => e.stopPropagation());
    typeSelect.addEventListener('change', e => {
      e.stopPropagation();
      block._role = e.target.value;
    });
    el.appendChild(typeSelect);

    // Content preview
    const content = document.createElement('div');
    content.innerHTML = sanitizeHtml(block.html);
    el.appendChild(content);

    // Click to toggle selection
    el.addEventListener('click', () => {
      if (selectedIds.has(block.id)) {
        selectedIds.delete(block.id);
        el.classList.remove('selected');
      } else {
        selectedIds.add(block.id);
        el.classList.add('selected');
      }
      updateCount();
      // Re-render to update order numbers
      updateOrderNumbers();
    });

    container.appendChild(el);
  });
}

function sanitizeHtml(html) {
  // Strip script tags and event handlers for safe preview
  return html
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/\son\w+="[^"]*"/gi, '')
    .replace(/\son\w+='[^']*'/gi, '');
}

function updateOrderNumbers() {
  const ids = [...selectedIds];
  document.querySelectorAll('.block').forEach(el => {
    const id = parseInt(el.dataset.id);
    const order = el.querySelector('.block-order');
    if (selectedIds.has(id)) {
      order.textContent = ids.indexOf(id) + 1;
    }
  });
}

function updateCount() {
  const count = selectedIds.size;
  document.getElementById('selection-count').innerHTML =
    `<strong>${count}</strong> block${count !== 1 ? 's' : ''} selected`;
  document.getElementById('save-btn').disabled = count === 0;
}

function setStatus(msg, type = '') {
  const el = document.getElementById('status');
  el.textContent = msg;
  el.className = 'status' + (type ? ' ' + type : '');
}

async function saveEntry() {
  const title = document.getElementById('entry-title').value.trim();
  if (!title) {
    setStatus('Please enter a title.', 'error');
    return;
  }

  const entryType = document.getElementById('entry-type').value;
  const category = document.getElementById('entry-category').value;
  const description = document.getElementById('entry-desc').value.trim();

  // Build content from selected blocks
  const selected = allBlocks.filter(b => selectedIds.has(b.id));
  let content = {};

  if (entryType === 'table') {
    content = buildTableContent(selected);
  } else if (entryType === 'prose') {
    content = buildProseContent(selected);
  } else if (entryType === 'image') {
    content = buildImageContent(selected);
  } else if (entryType === 'snippet') {
    content = buildSnippetContent(selected);
  }

  // Build source
  const source = {};
  const author = document.getElementById('source-author').value.trim();
  const sourceTitle = document.getElementById('source-title').value.trim();
  const sourceUrl = document.getElementById('source-url').value.trim();
  const sourceDate = document.getElementById('source-date').value.trim();
  if (author) source.author = author;
  if (sourceTitle) source.title = sourceTitle;
  if (sourceUrl) source.url = sourceUrl;
  if (sourceDate) source.date = sourceDate;

  const entry = {
    id: '',
    type: entryType,
    category: category,
    title: title,
    description: description || undefined,
    content: content,
    tags: [],
    source: source,
  };

  try {
    const resp = await fetch('/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(entry),
    });
    const data = await resp.json();
    if (data.ok) {
      setStatus(`Saved! (${data.count} total entries)`, 'success');
      selectedIds.clear();
      updateCount();
      renderBlocks();
    } else {
      setStatus('Save failed: ' + (data.error || 'Unknown error'), 'error');
    }
  } catch (e) {
    setStatus('Save failed: ' + e.message, 'error');
  }
}

function buildTableContent(blocks) {
  const tables = [];
  let currentName = null;

  blocks.forEach(block => {
    const role = block._role || (block.type === 'list' ? 'table' : 'prose');

    if (role === 'table' && block.items && block.items.length > 0) {
      tables.push({
        name: currentName || block.text.substring(0, 60) || 'Table',
        die: 'd' + block.items.length,
        items: block.items,
      });
      currentName = null;
    } else if (block.type === 'heading') {
      currentName = block.text;
    }
  });

  return { tables: tables, rollAll: tables.length > 1 };
}

function buildProseContent(blocks) {
  const htmlParts = [];
  let statblock = null;
  let image = null;

  blocks.forEach(block => {
    const role = block._role || 'prose';

    if (role === 'statblock') {
      statblock = block.text;
    } else if (role === 'image' || block.type === 'image') {
      if (block.images && block.images.length > 0) {
        image = block.images[0].src;
      }
    } else {
      htmlParts.push(block.html);
    }

    // Also grab any images embedded in non-image blocks
    if (role !== 'image' && block.images && block.images.length > 0 && !image) {
      image = block.images[0].src;
    }
  });

  const content = { html: htmlParts.join('') };
  if (statblock) content.statblock = statblock;
  if (image) content.image = image;
  return content;
}

function buildImageContent(blocks) {
  for (const block of blocks) {
    if (block.images && block.images.length > 0) {
      return { url: block.images[0].src, caption: block.images[0].alt || '' };
    }
  }
  return { url: '', caption: '' };
}

function buildSnippetContent(blocks) {
  return { html: blocks.map(b => b.html).join('') };
}

// Handle Enter in URL input
document.getElementById('url-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') fetchPage();
});
</script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="GM Screen content extraction server")
    parser.add_argument("--port", type=int, default=8766, help="Port to serve on (default: 8766)")
    parser.add_argument("--no-open", action="store_true", help="Don't auto-open browser")
    args = parser.parse_args()

    server = HTTPServer(("127.0.0.1", args.port), ExtractHandler)
    url = f"http://localhost:{args.port}"
    print(f"GM Screen Extractor running at {url}")
    print(f"Data file: {DATA_FILE.relative_to(REPO_ROOT)}")
    print("Press Ctrl+C to stop.\n")

    if not args.no_open:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


if __name__ == "__main__":
    main()
