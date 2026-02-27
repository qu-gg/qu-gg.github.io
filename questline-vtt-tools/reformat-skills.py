#!/usr/bin/env python3
"""
Reformat player-quirk-and-abilities.skills:
  1. Move subtext into notes as italic (*...*) prefix
  2. Reformat notes for better readability:
     - Bold "Requires..." check lines
     - Bold "Success:" / "Failure:" labels
     - Indent sub-items after Success/Failure
     - Bold "Rank N:" headers
     - De-bullet intro text when followed by check/outcome structure
     - Format "!" restriction markers as plain text
     - Handle section headers
     - Detect trailing notes after outcome blocks
  3. Indent sub-items after colon-introduction bullet lines
  4. Standardize page references to (pXXX) format

Usage:
    python reformat-skills.py [--dry-run]
"""

import json
import re
import sys

INPUT_FILE = "/home/rxm/Projects/qu-gg.github.io/player-quirk-and-abilities.skills"


def process_file(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for entry in data:
        process_entry(entry)

    # Write JSON, then normalize page references across the whole file
    raw = json.dumps(data, indent=2, ensure_ascii=False)
    raw = normalize_page_refs(raw)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(raw)

    print(f"Processed {len(data)} entries → {output_path}")


def process_entry(entry):
    """Move subtext into notes and reformat."""
    notes = entry.get("notes", "")
    subtext = entry.get("subtext", "")

    reformatted = reformat_notes(notes)

    if subtext and subtext.strip():
        entry["notes"] = f"*{subtext.strip()}*\n\n{reformatted}".strip()
    else:
        entry["notes"] = reformatted

    entry["subtext"] = ""


# ── Page reference normalization ────────────────────────────

def normalize_page_refs(text):
    """Standardize all page references to (pXXX) format.

    Handles:
      (-> pXXX), (-> pXXX, pXXX), bare pXXX), (-> 263), page ranges.
    """
    # Main normalization: (-> pXXX), pXXX), (pXXX) → (pXXX)
    text = re.sub(r'\(?\s*-?>?\s*p(\d+)\s*\)?', r'(p\1)', text)
    # Missing 'p' prefix: (-> 263) → (p263)
    text = re.sub(r'\(->\s*(\d+)\)', r'(p\1)', text)
    # Fix page ranges mangled by first pass: (p255)-256) → (p255-256)
    text = re.sub(r'\(p(\d+)\)-(\d+)\)', r'(p\1-\2)', text)
    # Ensure space before page ref when preceded by a word char: word(pXXX) → word (pXXX)
    text = re.sub(r'(\w)\(p(\d+)', r'\1 (p\2', text)
    return text


# ── Sub-list indentation ────────────────────────────────────

# Lines that shouldn't be indented even if they follow a colon-intro
_SUBLIST_STANDALONE_RE = re.compile(
    r'^(After you use|You can(?:no| no)t use|You cannot use|'
    r'This Ability|This ability|This spell|This bonus|'
    r'Once activated|Once attempted|Gain \d|'
    r'Your Pack functions|If lost or destroyed|'
    r'After starting|After a failed|No further|'
    r'A new cloud|You can only summon|'
    r'Anyone mean enough)', re.I)


def fix_colon_intros(notes):
    """Add sub-list indentation after colon-introduction lines."""
    lines = notes.split("\n")
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Detect colon-introduction: "- text:" or "  - text:"
        m = re.match(r'^(\s*- ).+:\s*$', line)
        if m and i + 1 < len(lines):
            indent_prefix = m.group(1)  # "- " or "  - "
            next_line = lines[i + 1] if i + 1 < len(lines) else ""

            # Case A – same-level bullets need indenting
            if next_line.startswith(indent_prefix) and not next_line.startswith("  " + indent_prefix):
                result.append(line)
                i += 1
                while i < len(lines):
                    cur = lines[i]
                    if not cur.strip():
                        break
                    if not cur.startswith(indent_prefix):
                        break
                    if cur.startswith("  " + indent_prefix):
                        result.append(cur)
                        i += 1
                        continue
                    text = cur[len(indent_prefix):].strip()
                    if text.startswith("**"):
                        if re.match(r'\*\*(Rank|Requires|Success|Failure)', text):
                            break
                        bold_end = text.find("**", 2)
                        if bold_end > 0 and bold_end > 40:
                            break
                    if re.match(r'^Rank\s+\d+', text):
                        break
                    if re.match(r'.+:\s*$', text):
                        break
                    if _SUBLIST_STANDALONE_RE.match(text):
                        break
                    result.append(f"  {cur}")
                    i += 1
                continue

            # Case B – indented colon-intro followed by root-level bold
            # outcomes (e.g. nested "must make a Might Check:" inside
            # an outer Success block).  Indent them as children.
            base_indent = len(indent_prefix) - len(indent_prefix.lstrip())
            if (base_indent > 0
                    and next_line.startswith("- **")
                    and not next_line.startswith("  ")):
                child_pad = " " * (base_indent + 2)
                result.append(line)
                i += 1
                seen_success = False
                seen_failure = False
                while i < len(lines):
                    cur = lines[i]
                    if not cur.strip():
                        break
                    # Accept root "- " and already-indented "  - " lines
                    if not (cur.startswith("- ") or cur.startswith("  - ")):
                        break
                    text = cur.lstrip().lstrip("- ").strip()
                    # Track success/failure; stop after a complete pair
                    if text.startswith("**Success:**"):
                        seen_success = True
                    elif text.startswith("**Failure:**"):
                        if seen_failure:   # second Failure = outer scope
                            break
                        seen_failure = True
                    elif seen_success and seen_failure:
                        break
                    if _SUBLIST_STANDALONE_RE.match(text):
                        break
                    if re.match(r'^Rank\s+\d+', text):
                        break
                    result.append(child_pad + cur)
                    i += 1
                continue

        result.append(line)
        i += 1

    return "\n".join(result)


# ── Parsing ──────────────────────────────────────────────────

def parse_lines(raw):
    """Split raw notes into structured line dicts."""
    parts = raw.strip().split("\n")

    # Pre-process: split mushed lines like
    #   "Ugly and noisy.  Requires an Aura Check Success: …"
    # into separate logical lines.
    expanded = []
    for p in parts:
        m = re.match(
            r'^(.*?\.\s{2,})((?:\?\s*)?Requires\s.+?(?:Check|Contest))\s+'
            r'(Success:\s*.+)',
            p, re.I,
        )
        if m:
            expanded.append(m.group(1).rstrip())
            expanded.append(m.group(2).strip())
            expanded.append(m.group(3).strip())
        else:
            expanded.append(p)
    parts = expanded

    result = []
    i = 0
    while i < len(parts):
        s = parts[i].strip()

        if not s:
            result.append({"kind": "empty", "text": "", "bullet": False})
            i += 1
            continue

        # Standalone "-" → merge with next line
        if s == "-" and i + 1 < len(parts):
            nxt = parts[i + 1].strip()
            if nxt and not nxt.startswith("- "):
                result.append({"kind": "u", "text": nxt, "bullet": True})
                i += 2
                continue

        # Lines starting with "-<digit>" (e.g. "-1 to Defense Rating")
        # should be a bullet "- -1 to Defense Rating"
        if re.match(r'^-\d', s):
            result.append({"kind": "u", "text": s, "bullet": True})
            i += 1
            continue

        if s.startswith("- "):
            result.append({"kind": "u", "text": s[2:].strip(), "bullet": True})
        else:
            result.append({"kind": "u", "text": s, "bullet": False})
        i += 1

    # Trim leading/trailing empties
    while result and result[0]["kind"] == "empty":
        result.pop(0)
    while result and result[-1]["kind"] == "empty":
        result.pop()

    return result


# ── Classification ───────────────────────────────────────────

# Patterns for trailing notes that should NOT be indented as sub-items
TRAILING_RE = re.compile(
    r'^(This Ability|This ability|This spell|This bonus|'
    r'Once per|You can(?:no| no)t|You cannot|After use|After starting|'
    r'Use of this|A target may|Creatures that|An individual|'
    r'Sure Kill|Using a Sword|Gain \d|Only a single|If the weapon|'
    r'Your Wraths Blade|Your Hearts Blade|'
    r'After the Storm|You must repeat|'
    r'The Soothing effect|'
    r'Prisma can only|He must be|She ignores|'
    r'Marlow vanishes|Jarah may|Jarah remains|'
    r'Paris wont return|Delilah would|'
    r'A new cloud cannot|You can only summon|'
    r'You can dissipate|Anyone mean enough|'
    r'After a failed|No further|'
    r'Once activated|Once attempted|'
    r'The divination|An individual surface|'
    r'Vexed Dispel can|'
    r'Youll need|'
    r'The armor lasts|After you use|'
    r'Your Other Self retains|'
    r'Your Other Self can|In addition to|'
    r'Once Amhika|'
    r'If lost or destroyed|Your Pack functions)', re.I)


def classify(lines):
    """Assign a kind to each line."""
    for ln in lines:
        if ln["kind"] == "empty":
            continue
        t = ln["text"]

        # Standalone ? marker
        if t.strip() in ("?", "?:"):
            ln["kind"] = "skip"
            continue

        # Strip leading "?" for check detection
        cleaned = t
        if cleaned.startswith("?"):
            cleaned = cleaned[1:].strip()

        # "Requires..." at the start
        if re.match(r'^Requires\b', cleaned):
            ln["kind"] = "check"
            ln["text"] = cleaned
            # Try to split "Requires a Contest <details>" into header + sub-detail
            m = re.match(r'^(Requires\s+a\s+Contest)\s*:?\s+(.+)', cleaned, re.I)
            if m and m.group(2).strip():
                ln["text"] = m.group(1)
                ln["check_detail"] = m.group(2).strip()
            continue

        # "...requires a/an Check/Contest" not at start (e.g. "Ending Berserk Mode requires an Aura Check")
        if (re.search(r'requires\s+(a |an )', cleaned, re.I)
                and re.search(r'Check|Contest', cleaned, re.I)):
            ln["kind"] = "check"
            ln["text"] = cleaned
            continue

        # Standalone "Requires an Aura Check:" style without the "a/an" before Check/Contest
        if re.match(r'^Requires\s+', cleaned, re.I):
            ln["kind"] = "check"
            ln["text"] = cleaned
            continue

        # Success / Failure
        m = re.match(r'^Success\s*:\s*(.*)', t)
        if m:
            ln["kind"] = "success"
            ln["text"] = m.group(1).strip()
            continue

        m = re.match(r'^x?\s*Failure\s*:\s*(.*)', t)
        if m:
            ln["kind"] = "failure"
            ln["text"] = m.group(1).strip()
            continue

        # Ally success / failure
        m = re.match(r'^Ally\s+success\s*:\s*(.*)', t, re.I)
        if m:
            ln["kind"] = "ally_success"
            ln["text"] = m.group(1).strip()
            continue

        m = re.match(r'^Ally\s+failure\s*:\s*(.*)', t, re.I)
        if m:
            ln["kind"] = "ally_failure"
            ln["text"] = m.group(1).strip()
            continue

        # Rank headers
        if re.match(r'^Rank\s+\d+', t):
            ln["kind"] = "rank"
            continue

        # "!" restriction marker
        if t.startswith("!") and not t.startswith("!!"):
            ln["kind"] = "restriction"
            ln["text"] = t.lstrip("! ").strip()
            continue

        # Section headers: non-bullet, ends with ":", multi-word, not a common sentence start
        if (not ln["bullet"] and t.endswith(":")
                and len(t.split()) >= 3
                and not re.match(r'^(For example|In addition|If |Otherwise|The |A |An |After |During )', t)):
            ln["kind"] = "header"
            continue

        ln["kind"] = "text"


# ── Output building ──────────────────────────────────────────

def has_outcomes(lines):
    return any(l["kind"] in ("success", "failure") for l in lines)


def blank(out):
    """Add blank line if last isn't blank."""
    if out and out[-1] != "":
        out.append("")


def bold_label(text):
    """
    If text starts with a short capitalized label followed by ':',
    bold the label. E.g. "Heal: After a Fight..." → "**Heal:** After a Fight..."
    Only for labels 1-3 short words that look like named concepts.
    """
    m = re.match(r'^([A-Z][a-zA-Z\']*(?:\s+[a-zA-Z][a-zA-Z\']*){0,3}):\s+(.+)', text)
    if not m:
        return text
    label = m.group(1)
    rest = m.group(2)
    # Exclude verb-starting or sentence-like patterns
    skip_starts = (
        "Choose", "Select", "Pick", "Make", "Take", "Use", "Any", "All",
        "The", "Each", "Your", "You", "If", "When", "During", "After",
        "Before", "For", "In", "On", "At", "With", "Only", "No", "Not",
        "Do", "Does", "While", "Once", "Note", "Unlike", "Otherwise",
        "Exception", "Characters", "Already", "Normal", "Attempting",
        "Armor", "Targets", "Victims", "A ", "An ", "Successful",
    )
    first_word = label.split()[0]
    if first_word in skip_starts or label in skip_starts:
        return text
    # Label words shouldn't be too long (likely a sentence fragment)
    if any(len(w) > 15 for w in label.split()):
        return text
    if len(label) > 35:
        return text
    # Don't bold if already bold
    if label.startswith("**"):
        return text
    return f"**{label}:** {rest}"


def build_output(lines):
    """Build formatted output string from classified lines."""
    out = []
    state = "top"
    outcomes = has_outcomes(lines)

    first_idx = next((i for i, l in enumerate(lines) if l["kind"] != "empty"), None)

    # Find last success/failure index for trailing-note detection
    last_outcome_idx = max(
        (i for i, l in enumerate(lines) if l["kind"] in ("success", "failure")),
        default=-1
    )

    for i, ln in enumerate(lines):
        k = ln["kind"]
        t = ln["text"]

        if k == "empty":
            blank(out)
            continue

        if k == "skip":
            continue

        # ── Check requirement ──
        if k == "check":
            blank(out)
            out.append(f"**{t}**")
            if "check_detail" in ln:
                out.append(f"- {ln['check_detail']}")
            state = "check"
            continue

        # ── Success / Failure ──
        if k == "success":
            out.append(f"- **Success:** {t}")
            state = "success"
            continue

        if k == "failure":
            out.append(f"- **Failure:** {t}")
            state = "failure"
            continue

        if k == "ally_success":
            out.append(f"  - **Ally success:** {t}")
            continue

        if k == "ally_failure":
            out.append(f"  - **Ally failure:** {t}")
            continue

        # ── Rank header ──
        if k == "rank":
            m = re.match(r'^(Rank\s+\d+)\s*:?\s*(.*)', t)
            if m:
                blank(out)
                out.append(f"**{m.group(1)}:**")
                rest = m.group(2).strip()
                if rest:
                    out.append(f"- {bold_label(rest)}")
            state = "rank"
            continue

        # ── Restriction ──
        if k == "restriction":
            blank(out)
            out.append(t)
            state = "top"
            continue

        # ── Section header ──
        if k == "header":
            blank(out)
            if not t.startswith("**"):
                out.append(f"**{t}**")
            else:
                out.append(t)
            state = "header"
            continue

        # ── Regular text ──

        # Trailing note detection: after the last outcome block,
        # lines matching TRAILING_RE should be de-indented
        if (i > last_outcome_idx > -1
                and TRAILING_RE.match(t)):
            blank(out)
            out.append(t)
            state = "top"
            continue

        # First content line → de-bullet as intro if we have outcomes
        if i == first_idx and outcomes and ln["bullet"]:
            out.append(t)
            state = "intro"
            continue

        # Context-dependent formatting
        if state in ("success", "failure"):
            out.append(f"  - {bold_label(t)}")
        elif state in ("rank", "check", "header"):
            out.append(f"- {bold_label(t)}")
        else:
            if ln["bullet"]:
                out.append(f"- {bold_label(t)}")
            else:
                out.append(bold_label(t))

    # Trim
    while out and out[-1] == "":
        out.pop()
    while out and out[0] == "":
        out.pop(0)

    return "\n".join(out)


# ── Main entry point ─────────────────────────────────────────

def reformat_notes(raw):
    if not raw or not raw.strip():
        return ""

    lines = parse_lines(raw)
    if not lines:
        return ""

    content = [l for l in lines if l["kind"] != "empty"]
    if len(content) == 1:
        # Single-line entry → plain text
        return content[0]["text"]

    classify(lines)
    result = build_output(lines)
    return fix_colon_intros(result)


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    out_path = INPUT_FILE + ".new" if dry_run else INPUT_FILE
    process_file(INPUT_FILE, out_path)
