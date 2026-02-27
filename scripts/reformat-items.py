#!/usr/bin/env python3
"""Reformat item descriptions in a .items file.

Transformations (applied to every item's 'description' field):
  1. Strip trailing whitespace on every line.
  2. Fix bold-comma splice:  **Weapon Ability**:, Name:  →  **Weapon Ability — Name:**
  3. Bold unbolded outcome labels:  - Success:  →  - **Success:**
  4. Break wall-of-text paragraphs into bullets where safe sentence-split patterns exist.
  5. Fix stray newlines inside vehicle/item descriptions (broken lines).
  6. Normalise multiple trailing blank lines / trailing whitespace on the whole description.

Usage:
    python scripts/reformat-items.py [--dry-run]
"""

import json
import re
import sys
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
ITEMS_FILE = ROOT / "questline-vtt-tools" / "BREAK!! Core Book Items.items"


# ═════════════════════════════════════════════════════════════════════════════
# Pass 1: Fix broken lines (stray newlines mid-sentence)
# ═════════════════════════════════════════════════════════════════════════════

def fix_broken_lines(text: str) -> str:
    """Merge lines that were broken mid-sentence (a bare newline not preceded
    by a period/colon and not followed by a bullet, bold, or blank line)."""
    lines = text.split("\n")
    merged = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Look ahead: if this line doesn't end a sentence and next line is
        # continuation text (not a bullet, blank, or bold-start)
        while (
            i + 1 < len(lines)
            and line.rstrip()                          # current is non-empty
            and not line.rstrip().endswith((".", ":", "!"))
            and lines[i + 1].strip()                   # next is non-empty
            and not lines[i + 1].lstrip().startswith(("-", "*", "#"))
            and not lines[i + 1].lstrip().startswith("**")
            and not lines[i + 1].strip().startswith("**")
        ):
            # Merge
            next_line = lines[i + 1]
            line = line.rstrip() + "\n" + next_line  # keep as-is for now; we'll rejoin below
            i += 1
        merged.append(line)
        i += 1
    return "\n".join(merged)


# ═════════════════════════════════════════════════════════════════════════════
# Pass 2: Strip trailing whitespace per line
# ═════════════════════════════════════════════════════════════════════════════

def strip_trailing_spaces(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.split("\n"))


# ═════════════════════════════════════════════════════════════════════════════
# Pass 3: Fix bold-comma splice  **Weapon Ability**:, Name: ...
# ═════════════════════════════════════════════════════════════════════════════

_BOLD_COMMA_RE = re.compile(
    r"\*\*Weapon Ability\*\*:\s*,\s*([^:]+):\s*"
)

def fix_bold_comma_splice(text: str) -> str:
    """**Weapon Ability**:, Sneaky Swipe: ...  →  **Weapon Ability — Sneaky Swipe:** ..."""
    def _repl(m):
        name = m.group(1).strip()
        return f"**Weapon Ability — {name}:** "
    return _BOLD_COMMA_RE.sub(_repl, text)


# ═════════════════════════════════════════════════════════════════════════════
# Pass 4: Bold unbolded outcome labels inside bullet lists
# ═════════════════════════════════════════════════════════════════════════════

_OUTCOME_LABELS = re.compile(
    r"^(- )(Success|Failure|Check|Contest)(:)", re.MULTILINE
)

def bold_outcome_labels(text: str) -> str:
    """- Success: ...  →  - **Success:** ..."""
    return _OUTCOME_LABELS.sub(r"\1**\2:**", text)


# ═════════════════════════════════════════════════════════════════════════════
# Pass 5: Break wall-of-text paragraphs into bullets
# ═════════════════════════════════════════════════════════════════════════════

def _split_provides_list(text: str) -> str:
    """For Mechanical Motion-style 'provides:' lists embedded in prose.
    Pattern: '... provides: A. B. C. This armor requires ...'
    """
    m = re.search(
        r"(Mechanical Motion provides:\s*)(.*?)(\.\s*This armor requires)",
        text, re.DOTALL,
    )
    if not m:
        return text
    intro = m.group(1).rstrip()
    items_str = m.group(2).strip()
    tail = m.group(3)

    # Split on period-space-capital patterns
    parts = re.split(r"\.\s+(?=[A-Z+])", items_str)
    bullets = "\n".join(f"  - {p.strip().rstrip('.')}." for p in parts if p.strip())
    return text[: m.start()] + intro + "\n" + bullets + "\n" + tail.lstrip(". ") + text[m.end():]


def _split_special_ammo(text: str) -> str:
    """Break 'Fireberry Shot: ... Flare: ... Heavy: ... Whistling: ...' into bullets."""
    ammo_types = ["Fireberry Shot", "Flare", "Heavy", "Whistling"]
    pattern = "|".join(re.escape(a) for a in ammo_types)
    found = [a for a in ammo_types if a + ":" in text]
    if len(found) < 3:
        return text

    first_idx = min(text.index(a + ":") for a in found)
    # Find the end: "Just like regular ammunition..." or **Coins**
    end_match = re.search(r"Just like regular ammunition.*?use\.", text[first_idx:])
    if end_match:
        block_end = first_idx + end_match.end()
    else:
        coins_idx = text.find("**Coins**", first_idx)
        block_end = coins_idx if coins_idx > 0 else len(text)

    block = text[first_idx:block_end].strip()

    # Split on ammo type names
    parts = re.split(r"(?=" + pattern + r":)", block)
    bullets = []
    trailing = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        matched = False
        for a in ammo_types:
            if p.startswith(a + ":"):
                rest = p[len(a) + 1:].strip()
                bullets.append(f"- **{a}:** {rest}")
                matched = True
                break
        if not matched:
            trailing.append(p)

    new_block = "\n".join(bullets)
    if trailing:
        new_block += "\n\n" + " ".join(trailing)

    # Ensure intro text has a blank line before bullets
    prefix = text[:first_idx].rstrip()
    suffix = text[block_end:].lstrip()
    # Add blank line between prefix/bullets and bullets/suffix
    return prefix + "\n\n" + new_block + "\n\n" + suffix


def _split_assault_provides(text: str) -> str:
    """Shield Ability - Assault: 'Doing SO means: ...' into bullets."""
    m = re.search(r"Doing SO means:\s*(.*?)(?=\n\n|\Z)", text, re.DOTALL)
    if not m:
        return text
    items_str = m.group(1).strip()
    parts = re.split(r"\.\s+(?=[A-Z])", items_str)
    bullets = "\n".join(f"  - {p.strip().rstrip('.')}." for p in parts if p.strip())
    return text[: m.start()] + "Doing SO means:\n" + bullets + text[m.end():]


def _split_combination_rules(text: str) -> str:
    """Weapon Ability - Combination: break the inheritance rules into bullets."""
    # Pattern: "inherit the properties...in the following way: A. B. C."
    m = re.search(
        r"(in the following way:\s*)(.*?)(\.\s*For example,)",
        text, re.DOTALL,
    )
    if not m:
        return text
    intro = "in the following way:"
    items_str = m.group(2).strip()
    tail = m.group(3)

    parts = re.split(r"\.\s+(?=[A-Z])", items_str)
    bullets = "\n".join(f"  - {p.strip().rstrip('.')}." for p in parts if p.strip())
    return (
        text[: m.start()]
        + intro + "\n"
        + bullets + "\n\n"
        + tail.lstrip(". ")
        + text[m.end():]
    )


def _split_integrated_sentences(text: str) -> str:
    """Armor Ability - Integrated: break long prose into bullets."""
    if "Integrated items are limited" not in text:
        return text

    # Find the start of the rules block
    start = text.index("Integrated items are limited")
    # Find the end (before **Coins**)
    coins_idx = text.find("**Coins**", start)
    if coins_idx < 0:
        coins_idx = len(text)
    block = text[start:coins_idx].strip()

    # Split on sentence boundaries
    sentences = re.split(r"(?<=\.)\s+", block)
    bullets = "\n".join(f"- {s.strip()}" for s in sentences if s.strip())

    # Ensure intro text ends with a newline before the bullets
    prefix = text[:start].rstrip()
    return prefix + "\n" + bullets + "\n\n" + text[coins_idx:]


def _split_combination_second_half(text: str) -> str:
    """Break the Combination weapon's second-half missile/melee rules into bullets."""
    marker = "If any Missile and Melee Weapon Types are combined"
    if marker not in text:
        return text

    start = text.index(marker)
    # Find the end: through "small size." — note the last sentence about
    # "Combining two weapons..." spans into the next paragraph, handle separately
    end_match = re.search(r"Concealed and Thrown Weapons.*?small size\.", text[start:], re.DOTALL)
    if not end_match:
        return text
    block_end = start + end_match.end()
    block = text[start:block_end]

    # Split the block on sentence boundaries (period + space + capital)
    sentences = re.split(r"(?<=\.)\s+(?=[A-Z])", block)
    bullets = "\n".join(f"- {s.strip()}" for s in sentences if s.strip())

    # Now handle the "Combining two weapons..." sentence that spans into
    # "**Weapon Ability**: will take you to the 3 Ability limit."
    suffix = text[block_end:]
    # Merge the cross-paragraph sentence: "Combining...inherent\n\n**Weapon Ability**: will..."
    merge_match = re.match(
        r"\s*Combining two weapons.*?inherent\s*\n\n\*\*Weapon Ability\*\*:\s*(.*?)(?=\n\n)",
        suffix, re.DOTALL,
    )
    if merge_match:
        rest_text = merge_match.group(1).strip()
        merged_sentence = f"Combining two weapons that each have an inherent **Weapon Ability** {rest_text}"
        suffix = suffix[merge_match.end():]
        bullets += f"\n- {merged_sentence}"

    # Ensure a newline before the bullet block (separate from preceding paragraph)
    prefix = text[:start].rstrip()
    return prefix + "\n\n" + bullets + suffix


def break_walls_of_text(text: str) -> str:
    """Apply targeted wall-of-text splitters."""
    text = _split_provides_list(text)
    text = _split_special_ammo(text)
    text = _split_assault_provides(text)
    text = _split_combination_rules(text)
    text = _split_integrated_sentences(text)
    text = _split_combination_second_half(text)
    return text


# ═════════════════════════════════════════════════════════════════════════════
# Pass 6: Trim overall description
# ═════════════════════════════════════════════════════════════════════════════

def trim_description(text: str) -> str:
    """Remove trailing blank lines, excess whitespace, and collapse triple newlines."""
    text = text.strip()
    # Collapse any runs of 3+ newlines down to 2
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text


# ═════════════════════════════════════════════════════════════════════════════
# Pipeline
# ═════════════════════════════════════════════════════════════════════════════

def reformat_description(text: str) -> str:
    text = strip_trailing_spaces(text)
    text = fix_bold_comma_splice(text)
    text = bold_outcome_labels(text)
    text = break_walls_of_text(text)
    text = trim_description(text)
    return text


def main():
    dry_run = "--dry-run" in sys.argv

    with open(ITEMS_FILE) as f:
        items = json.load(f)

    changed = 0
    unchanged = 0
    changes_log = []

    for it in items:
        old_desc = it.get("description", "")
        new_desc = reformat_description(old_desc)
        if old_desc != new_desc:
            changed += 1
            # Categorise what changed
            diffs = []
            if old_desc.rstrip() != new_desc.rstrip():
                pass  # content change
            # Detect specific change types
            if "**Weapon Ability —" in new_desc and "**Weapon Ability —" not in old_desc:
                diffs.append("fix bold-comma")
            if "**Success:**" in new_desc and "**Success:**" not in old_desc:
                diffs.append("bold outcomes")
            if "**Failure:**" in new_desc and "**Failure:**" not in old_desc:
                diffs.append("bold outcomes")
            # Check bullet insertion
            if new_desc.count("\n-") > old_desc.count("\n-") or new_desc.count("\n  -") > old_desc.count("\n  -"):
                diffs.append("split wall-of-text")
            if len(new_desc) < len(old_desc):
                diffs.append("trim whitespace")
            elif not diffs:
                diffs.append("whitespace")

            if dry_run:
                changes_log.append((it["name"], diffs))

            it["description"] = new_desc
        else:
            unchanged += 1

    print(f"Total items:  {len(items)}")
    print(f"Changed:      {changed}")
    print(f"Unchanged:    {unchanged}")

    if dry_run:
        print("\nChanges preview:")
        for name, diffs in changes_log:
            print(f"  {name:45s} | {', '.join(diffs)}")
        print("\n[DRY RUN] No files were modified.")
    else:
        with open(ITEMS_FILE, "w") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        print(f"\nWrote → {ITEMS_FILE}")


if __name__ == "__main__":
    main()
