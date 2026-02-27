#!/usr/bin/env python3
"""Port reformatted ability descriptions from .skills files into a .characters file.

Matches character abilities to skills entries via:
  1. originId → fieldName  (primary, exact)
  2. ability name → displayName  (fallback, case-insensitive)

Updates:
  - description  ← notes
  - subtext      ← subtext
  - name         ← displayName (adds suffix tags; preserves user renames)

Usage:
    python scripts/port-skills-to-characters.py [--dry-run]
"""

import json
import re
import sys
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
CHARACTERS_FILE = ROOT / "BREAK!! Full System.characters"
ADV_SKILLS_FILE = ROOT / "questline-vtt-tools" / "adversary-abilities-new.skills"
PLAYER_SKILLS_FILE = ROOT / "questline-vtt-tools" / "player-quirk-and-abilities-new.skills"

# ── Suffix-tag regex ─────────────────────────────────────────────────────────
TAG_RE = re.compile(r"(\s*(?:\[[A-Z]\])+)\s*$")


def strip_tags(name: str) -> str:
    """Remove trailing suffix tags like [B], [A][M] from a display name."""
    return TAG_RE.sub("", name).strip()


def extract_tags(display_name: str) -> str:
    """Extract the suffix-tags portion (e.g. ' [A][M]') from a display name."""
    m = TAG_RE.search(display_name)
    return m.group(1) if m else ""


def build_lookup(skills: list[dict]) -> tuple[dict, dict]:
    """Build fieldName-keyed and name-keyed lookup dicts from a skills list."""
    by_field = {}
    by_name = {}
    for s in skills:
        by_field[s["fieldName"]] = s
        dn = s.get("displayName", "").strip().lower()
        if dn:
            by_name[dn] = s
        # Also index by name without tags
        base = strip_tags(s.get("displayName", "")).lower()
        if base and base != dn:
            by_name[base] = s
    return by_field, by_name


def find_skill(ability: dict, adv_field, adv_name, player_field, player_name) -> dict | None:
    """Find the matching skills entry for a character ability."""
    origin = ability.get("originId") or ""

    # 1. Try originId → fieldName (adversary first, then player)
    if origin:
        if origin in adv_field:
            return adv_field[origin]
        if origin in player_field:
            return player_field[origin]

    # 2. Fallback to name matching
    name = ability.get("name", "").strip().lower()
    if name:
        if name in adv_name:
            return adv_name[name]
        if name in player_name:
            return player_name[name]

    return None


def update_ability(ability: dict, skill: dict) -> dict:
    """Update a character ability in-place with data from a matched skill.

    Returns a dict describing what changed (for reporting).
    """
    changes = {}

    # ── description ← notes ──────────────────────────────────────────────
    old_desc = ability.get("description", "")
    new_desc = skill.get("notes", "")
    if new_desc and old_desc != new_desc:
        ability["description"] = new_desc
        changes["description"] = True

    # ── subtext ← subtext ────────────────────────────────────────────────
    old_sub = ability.get("subtext", "")
    new_sub = skill.get("subtext", "")
    if old_sub != new_sub:
        ability["subtext"] = new_sub
        changes["subtext"] = True

    # ── name: add/update suffix tags ─────────────────────────────────────
    char_name = ability.get("name", "").strip()
    skill_display = skill.get("displayName", "").strip()
    skill_base = strip_tags(skill_display)
    skill_tags = extract_tags(skill_display)

    if char_name == skill_base:
        # Names match exactly (ignoring tags) → use the full displayName
        if char_name != skill_display and skill_tags:
            ability["name"] = skill_display
            changes["name"] = f"{char_name} → {skill_display}"
    elif skill_tags:
        # User renamed the ability → keep their name, append tags
        # First strip any existing tags from char name
        char_base = strip_tags(char_name)
        new_name = char_base + skill_tags
        if char_name != new_name:
            ability["name"] = new_name
            changes["name"] = f"{char_name} → {new_name}"

    return changes


def main():
    dry_run = "--dry-run" in sys.argv

    # Load files
    with open(CHARACTERS_FILE) as f:
        characters = json.load(f)
    with open(ADV_SKILLS_FILE) as f:
        adv_skills = json.load(f)
    with open(PLAYER_SKILLS_FILE) as f:
        player_skills = json.load(f)

    # Build lookups
    adv_field, adv_name = build_lookup(adv_skills)
    player_field, player_name = build_lookup(player_skills)

    # Stats
    total_abilities = 0
    matched = 0
    updated = 0
    unmatched_list = []

    for char in characters:
        abilities = char.get("sheetData", {}).get("abilities", [])
        for ab in abilities:
            total_abilities += 1
            skill = find_skill(ab, adv_field, adv_name, player_field, player_name)
            if skill is None:
                unmatched_list.append((char["name"], ab.get("name", "?")))
                continue
            matched += 1
            changes = update_ability(ab, skill)
            if changes:
                updated += 1
                if dry_run:
                    change_desc = ", ".join(
                        f"name: {v}" if k == "name" else k
                        for k, v in changes.items()
                    )
                    print(f"  [{char['name']}] {ab.get('name','?')}: {change_desc}")

    # Report
    print(f"\nTotal abilities:  {total_abilities}")
    print(f"Matched:          {matched}")
    print(f"Updated:          {updated}")
    print(f"Unmatched:        {len(unmatched_list)}")

    if unmatched_list:
        print("\nUnmatched abilities (no changes made):")
        for cname, aname in unmatched_list:
            print(f"  {cname:30s} | {aname}")

    if dry_run:
        print("\n[DRY RUN] No files were modified.")
    else:
        with open(CHARACTERS_FILE, "w") as f:
            json.dump(characters, f, indent=2, ensure_ascii=False)
        print(f"\nWrote → {CHARACTERS_FILE}")


if __name__ == "__main__":
    main()
