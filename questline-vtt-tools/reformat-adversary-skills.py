#!/usr/bin/env python3
"""
Reformat adversary-abilities.skills:
  1. Move subtext into notes as italic (*...*) prefix
  2. Reformat notes for better readability:
     - Bold "Requires..." check lines
     - Bold "Success:" / "Failure:" labels
     - Indent sub-items after Success/Failure
     - Bold "Rank N:" headers
     - Bold named labels  (e.g. "Sweep Attack:", "Numb to Pain:")
     - Handle section headers (non-bullet lines ending with ":")
     - Detect trailing notes after outcome blocks
     - Merge broken continuation lines
     - Split embedded sub-headers from surrounding text
  3. Indent sub-items after colon-introduction bullet lines
  4. Standardize page references to (pXXX) format

Usage:
    python reformat-adversary-skills.py [--dry-run]
"""

import json
import re
import sys

INPUT_FILE = "/home/rxm/Projects/qu-gg.github.io/adversary-abilities.skills"


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


def append_suffix_tags(entry):
    """Extract single-letter suffixes from fieldName and append as tags to displayName.

    e.g. fieldName "scornful-bolt-a-m" → displayName "Scornful Bolt [A][M]"
         fieldName "consumed-by-darkness-b" → displayName "Consumed By Darkness [B]"
    """
    fn = entry.get("fieldName", "")
    parts = fn.split("-")
    trailing = []
    for p in reversed(parts):
        if len(p) == 1 and p.isalpha():
            trailing.insert(0, p)
        else:
            break
    if trailing:
        tags = "".join(f"[{ch.upper()}]" for ch in trailing)
        dn = entry.get("displayName", "").rstrip()
        # Don't double-add if tags are already present
        if not dn.endswith(tags):
            entry["displayName"] = f"{dn} {tags}"


def process_entry(entry):
    """Move subtext into notes, reformat, and add suffix tags."""
    notes = entry.get("notes", "")
    subtext = entry.get("subtext", "")

    # Append suffix tags from fieldName to displayName
    append_suffix_tags(entry)

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
    r'Once activated|Once attempted|Gain \d|Adds \d|'
    r'After starting|After a failed|No further|'
    r'A new cloud|You can only summon|'
    r'Anyone mean enough|'
    r'The mana in|The Blaster|The GM may|The Curse|'
    r'Burdened targets|Restrained targets|'
    r'The Pedagogue can|The Barrier|'
    r'Up to \d)', re.I)


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
                    if not (cur.startswith("- ") or cur.startswith("  - ")):
                        break
                    text = cur.lstrip().lstrip("- ").strip()
                    if text.startswith("**Success:**"):
                        seen_success = True
                    elif text.startswith("**Failure:**"):
                        if seen_failure:
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


# ── Pre-processing ──────────────────────────────────────────

def preprocess_raw(raw):
    """Fix data issues in the raw notes before parsing."""
    parts = raw.strip().split("\n")
    result = []

    i = 0
    while i < len(parts):
        line = parts[i]
        s = line.strip()

        # 1. Merge broken hyphenated continuations:
        #    "- Once a Session the GM can re-"
        #    "- roll, or force a player to re-roll, if"
        #    "- the result negatively impacts the"
        #    "- Chosen One."
        #    → Single line: "- Once a Session the GM can re-roll, ..."
        if (s.startswith("- ") and s.endswith("-")
                and not s.endswith("->") and not s.endswith("--")):
            merged = s
            i += 1
            while i < len(parts):
                nxt = parts[i].strip()
                if nxt.startswith("- "):
                    word = nxt[2:].strip()
                    # Check if it's a true continuation (lowercase start, or
                    # continues flow of sentence)
                    if word and word[0].islower():
                        merged = merged + word
                        # If THIS line also ends with hyphen, keep merging
                        if merged.endswith("-") and not merged.endswith("->"):
                            i += 1
                            continue
                        i += 1
                        break
                    else:
                        break
                else:
                    break
            result.append(merged)
            continue

        # 2. Split embedded sub-headers from text.
        #    "...destroyed. Removing Goop: \n" → two lines
        #    Also handles: "...successful Attack.\nBone Brambles: text..."
        if not s.startswith("- "):
            # Check for "Header:" at start of a non-bullet line
            # (these are fine as-is, they'll be classified as headers)
            pass

        # 3. Handle lines with trailing header embedded:
        #    e.g. "...Injury Table (-> p267), and again ... destroyed. Removing Goop: "
        #    These end with "Word Word:" and have significant preceding text.
        #    Split at the embedded header boundary.
        embedded_m = re.search(
            r'(\.\s+|\!\s+)([A-Z][a-zA-Z\s\']*?(?:Goop|Lalka|Shot|Brambles|Lure|objects|Reference|Sight|Flight|Force|Values|Aptitudes|Machine|Prey|Mode)s?)\s*:\s*$',
            s
        )
        if embedded_m and embedded_m.start() > 10:
            before = s[:embedded_m.start() + len(embedded_m.group(1))].rstrip()
            header = embedded_m.group(2).strip() + ":"
            result.append(("- " + before) if not before.startswith("- ") else before)
            result.append(header)
            i += 1
            continue

        result.append(line)
        i += 1

    # Second pass: merge sentence-fragment bullets.
    # Lines like "- ...if\n- the result...\n- Chosen One." where a bullet
    # ends with a continuation word and the next bullets are fragments.
    _CONTINUATION_END = re.compile(
        r'\b(if|the|a|an|or|and|but|that|which|to|of|in|for|by|with|'
        r'from|into|onto|upon|at|on|is|are|was|were|be|their|your|its|'
        r'this|these|those|not|no|nor|than|as|can|could|would|should|'
        r'may|might|will|shall)\s*$', re.I)

    merged = []
    i = 0
    while i < len(result):
        line = result[i]
        s = line.strip()
        if s.startswith("- "):
            text = s[2:]
            while _CONTINUATION_END.search(text) and i + 1 < len(result):
                nxt = result[i + 1].strip()
                if nxt.startswith("- "):
                    nxt_text = nxt[2:].strip()
                    text = text.rstrip() + " " + nxt_text
                    i += 1
                else:
                    break
            merged.append("- " + text)
        else:
            merged.append(line)
        i += 1
    result = merged

    return "\n".join(result)


# ── Parsing ──────────────────────────────────────────────────

def parse_lines(raw):
    """Split raw notes into structured line dicts."""
    # Pre-process the raw text first
    raw = preprocess_raw(raw)
    parts = raw.strip().split("\n")

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
        if re.match(r'^-\d', s):
            result.append({"kind": "u", "text": s, "bullet": True})
            i += 1
            continue

        # Numbered bullet: "- 1. First create..." → keep as bullet
        if re.match(r'^- \d+\.\s', s):
            result.append({"kind": "u", "text": s[2:].strip(), "bullet": True})
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
    r'Use of this|Gain \d|Adds \d|Only a single|'
    r'The mana in|The Blaster|The GM may|The Curse|'
    r'Burdened targets|Restrained targets|'
    r'The Pedagogue can|'
    r'If the Cloud|A Cloud|The Cloud|'
    r'Once a Session|'
    r'This even extends)', re.I)


def classify(lines):
    """Assign a kind to each line."""
    for ln in lines:
        if ln["kind"] == "empty":
            continue
        t = ln["text"]

        # "Requires..." at the start
        if re.match(r'^Requires\b', t):
            ln["kind"] = "check"
            # Try to split "Requires a Contest <details>" into header + sub-detail
            m = re.match(r'^(Requires\s+a\s+(?:Contest|Grit\s+Contest))\s*:?\s+(.+)', t, re.I)
            if m and m.group(2).strip():
                ln["text"] = m.group(1)
                ln["check_detail"] = m.group(2).strip()
            continue

        # "...requires a/an Check/Contest" not at start
        # Only match if 'requires' is in the first sentence (no period before it)
        req_m = re.search(r'requires\s+(a |an )', t, re.I)
        if (req_m and re.search(r'Check|Contest', t, re.I)):
            pre = t[:req_m.start()]
            if '. ' not in pre and '! ' not in pre:
                ln["kind"] = "check"
                continue

        # "You require a Grit Check" style
        if re.match(r'^You require\b', t, re.I) and re.search(r'Check|Contest', t, re.I):
            ln["kind"] = "check"
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

        # Rank headers
        if re.match(r'^Rank\s+\d+', t):
            ln["kind"] = "rank"
            continue

        # Section headers: non-bullet, short-ish, ends with ":"
        # e.g. "Formation:", "Ritual:", "Breeze Lalka:", "Skull Shot:"
        if (not ln["bullet"] and t.rstrip().endswith(":")
                and len(t.split()) <= 8
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
    bold the label. E.g. "Sweep Attack: strikes..." → "**Sweep Attack:** strikes..."
    """
    m = re.match(r'^([A-Z][a-zA-Z\']*(?:\s+[a-zA-Z][a-zA-Z\']*){0,4}):\s+(.+)', text)
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
    # Label words shouldn't be too long
    if any(len(w) > 15 for w in label.split()):
        return text
    if len(label) > 40:
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

        # ── Section header ──
        if k == "header":
            blank(out)
            header_text = t.rstrip()
            if not header_text.startswith("**"):
                out.append(f"**{header_text}**")
            else:
                out.append(header_text)
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

        # Non-bullet text after success/failure that has a bold label
        # → new section, not a sub-item (e.g. "Bone Brambles: text...")
        if state in ("success", "failure") and not ln["bullet"]:
            labeled = bold_label(t)
            if labeled != t:  # bold_label transformed it → new named section
                blank(out)
                out.append(labeled)
                state = "top"
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
