# Blog Style Guide

Reference for writing posts with the `build-blog.py` script.

---

## Creating a Post

Add a `.md` file in `blog/posts/`. The filename doesn't affect output but a convention like `YYYY-MM-DD-slug.md` keeps them sorted.

### Front Matter (required)

Every post starts with YAML front matter fenced by `---`:

```yaml
---
title: My Post Title
date: 2026-03-25
time: 11:03
tags: Session Report, Adventure Design
---
```

| Field   | Required | Notes                                                     |
|---------|----------|-----------------------------------------------------------|
| `title` | Yes      | Post title, used in the page heading and RSS.             |
| `date`  | Yes      | Publish date in `YYYY-MM-DD`. Treated as ET.              |
| `time`  | No       | Publish time in `HH:MM` (24h, ET). Defaults to `00:00`.  |
| `tags`  | No       | Comma-separated list of tags. Rendered as pills on posts. |

---

## Markdown Features

Standard Markdown is supported via Python-Markdown with these extensions enabled:

- **Extra** — abbreviations, attribute lists, definition lists, fenced code blocks, footnotes, tables.
- **CodeHilite** — syntax highlighting for fenced code blocks.
- **Smarty** — smart quotes, em-dashes, en-dashes, ellipses.
- **TOC** — auto-generates a table of contents if `[TOC]` is placed in the body.
- **NL2BR** — single newlines become `<br>`, so you don't need double-newlines for every line break.

---

## Custom Syntax

### Spoiler / Hover Text

Wrap text in double pipes to hide it behind a spoiler bar. Readers hover (desktop) or tap (mobile) to reveal.

```markdown
The villain is ||Baron Ashblade|| and he hides in ||the old clocktower||.
```

**Renders as:** blacked-out text that reveals on hover/tap.

### Item & Ability Cards

Fenced `:::item` or `:::ability` blocks render as styled card components.

```markdown
:::item
name: Everbark Figurine
type: Trinket
desc: A small wooden carving of a fox, warm to the touch.
effect: Stands watch during camp; rolls Scout for the party.
- Does not need sleep or food.
- Immune to Petrification.
stats: Hearts 2 . Attack 0 . Defense 1
:::
```

| Field    | Required | Notes                                                       |
|----------|----------|-------------------------------------------------------------|
| `name`   | Yes      | Displayed as the card heading.                              |
| `type`   | No       | Shown in brackets after the name (e.g. `[Trinket]`).       |
| `desc`   | No       | Italic flavour text. Supports `\n` for line breaks.        |
| `effect` | No       | Mechanical effect text. Supports `\n` for line breaks.     |
| `stats`  | No       | Stat line. Dots (` . `) are converted to centered dots (·).|
| `- text` | No       | Bullet list entries within the card.                        |

### Captioned Images

Add a `title` attribute to an image to wrap it in a `<figure>` with a `<figcaption>`:

```markdown
![Alt text](images/my-image.jpg "This caption appears below the image")
```

Images without a title render normally; images with a title get the caption treatment.

> **Note:** Image paths should be relative to `blog/` (e.g. `images/foo.jpg`). The build script rewrites them for the output directory automatically.

---

## Running the Build

```bash
python scripts/build-blog.py
```

**Outputs:**

| File                        | Description                                      |
|-----------------------------|--------------------------------------------------|
| `blog/posts-html/*.html`    | Individual post pages built from the template.   |
| `blog-data.json`            | Post listing metadata for the blog index page.   |
| `blog/feed.xml`             | RSS 2.0 feed.                                    |

**Dependencies:**

```bash
pip install markdown pyyaml
```

---

## Quick Reference

```markdown
---
title: My Title
date: 2026-04-01
time: 14:30
tags: Tag One, Tag Two
---

Regular **Markdown** works as expected.

[TOC]

### Spoiler
The answer is ||42||.

### Item Card
:::item
name: Cool Sword
type: Standard Melee Weapon
desc: A really cool sword.
effect: +1 Attack. Glows near goblins.
- Counts as magical.
stats: Attack 3 . Speed 2
:::

### Captioned Image
![A cool map](images/map.png "The party's route through the jungle")
```
