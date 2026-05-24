"""Hand-curated profile overrides for Core Book adversaries.

This file is the single source of truth for adversary content that comes
directly from the BREAK!! Core Rules PDF.  build_adversaries.py reads
PROFILES[name] and overlays it on top of the OCR-derived skeleton
during the main build loop.

See docs/ADVERSARIES_DESIGN.md for the full pipeline design and the
"no invention" authoring policy (s2a).  Every value in this file MUST
trace back to either the PDF or the OCR characters file -- nothing
invented or embellished.

Profile schema (all fields optional; missing = "don't override")::

    PROFILES["[N] Name"] = {
        "pdf_page":  408,             # source page in BREAK_RPG_CORE_RULES_v1.pdf
        "source":    "core-book",     # core-book | blog | homebrew
        "rank":      8,
        "tier":      "mega-boss",     # mook | adversary | boss | mega-boss
        "bio": {
            "name":     "Skelemonarch",
            "subname":  "Rank 8 Mega-Boss",
            "type":     "Monster [Undead]",
            "size":     "Medium",
            "details":  "**Autarch of the fleshless.** ...",
        },
        "stats": {
            "attack_bonus":     6,
            "defense_rating":   16,
            "speed":            "average",   # slow | average | fast | very_fast
            "hearts":           5,
            "hearts_adversary": 5,
            "aptitudes": {
                "might": 10, "deftness": 11, "grit": 8,
                "insight": 13, "aura": 13,
            },
            "allegiance": {"dark": 7, "bright": 0},
            "allegiance_area": "dark",       # dark | bright | neutral
        },
        "abilities": [                       # ability displayName seeds, in order
            "Living Dead",
            "Pull Yourself Together",
            "Macabre Aura",
            "Hollow Eyed Servants",
            "Skelemancy",
            "Curse of the Skull",
        ],
        "gear": [                            # item names; resolved against items file
            # e.g. "Standard Weapon", "Light Armor"
        ],
        "notes": {                           # Quick Facts; keys = note originId
            "habitat":             "...",
            "combat-gear":         "...",
            "communication":       "...",
            "tactics":             "...",
            "indicators":          "...",
            "role-playing-notes":  "...",
            "customization":       "...",
        },
        "actions": [                         # appended AFTER derived actions
            # Each entry is a partial VTT action dict.  Minimum required:
            #   {"name": str, "description": str}
            # Optional fields the build will preserve / fill defaults for:
            #   "subtype": str (default "")
            #   "effects": list[dict]   # raw VTT effect shapes; usually omit
            #   "details": list[dict]   # raw VTT detail shapes; usually omit
            # Use sparingly -- generic derivation from ability text covers
            # most cases.  Hand-author only when derivation gets it wrong
            # or misses an action entirely.
        ],
        # Optional flags
        "incomplete": [],                    # field names left blank (book had none)
        "shares_notes_with": None,           # name of another profile to reuse notes
    }

Keys in PROFILES are the *full* output character name (post-prefix-strip
where applicable), e.g. "[8] Skelemonarch", "Demon - Blighted Beast",
"Lalka - Breeze".


STRICT TEMPLATE RULES (re-aligned May 16):
==========================================

These rules MUST be followed for every new profile.  When in doubt:
omit, don't invent.

1.  **No invention.**  Every value in a profile must trace to either
    the PDF or the OCR characters file.  If the PDF stat block has no
    "Gear:" line, omit the `combat-gear` notes key -- do NOT fabricate
    one with "None --" prose.  Same for any other missing notes
    subfield.  Add an entry to `incomplete` documenting the omission.

2.  **`notes["customization"]` contains ONLY two things:**
        a. The verbatim PDF "Customization:" line text.
        b. The verbatim PDF "Reskin" block, labelled as
           ``"\n\n**Reskin (pNNN):** ..."``.
    Nothing else.  In particular:
        -  NO Mood Table content.
        -  NO Yield content.
        -  NO Combat-Gear summaries.
        -  NO editorial framing.

3.  **Mood Table and non-item Yield are TODO.**  These are PDF
    sub-sections that don't currently have a schema home.  A future
    schema revision will add dedicated fields (e.g. `notes["mood"]`,
    `notes["yield"]`).  Until then: DO NOT include this content in
    any other field.  Item-based yields (Buzz Bombs, Synthetic Limbs,
    etc.) continue to flow through the inventory pipeline.

4.  **`stats` values are post-trait totals**, matching the BIG
    NUMBERS in the PDF stat block.  Trait modifiers (e.g.
    "Persistent (+2 Grit)") are documented in inline comments next
    to each aptitude line, not subtracted back out.

5.  **DR includes baseline armor/ability bonuses** that the PDF stat
    block bakes in (e.g. Light Armor +2, Made of Sterner Puff +2,
    Labor Frame +4).  Annotate the source in an inline comment.

6.  **Speed** uses the PDF rating word: slow | average | fast |
    very_fast.

7.  **`hearts` and `hearts_adversary` must be equal** -- they are the
    same field rendered in two VTT contexts (build invariant).

8.  **Allegiance values** are taken verbatim from the PDF
    "ALLEGIANCE" stat-block line.  Unaligned = {"dark": 0, "bright":
    0, area: "neutral"}.  Scorecard will flag 0/0 as a gap; add an
    `incomplete` entry to document it as the correct value.

9.  **`abilities`** lists displayName seeds in PDF order.  The build
    resolves them against the 3-source skill lookup; verify each
    resolves before committing.  If a `[B]`-tagged ability is
    described in the PDF as costing an Action, inject an explicit
    entry in `actions`.

10. **`incomplete`** entries follow the format
    ``"<field-code>: <reason>"`` where <field-code> is either a
    top-level field ("inventory", "allegiance") or a subfield code
    ("notes(combat-gear)").  The scorecard honors these to suppress
    structurally-N/A gaps.
"""

# Phase 1 scope (see docs/ADVERSARIES_DESIGN.md s2).  Used by the
# per-run scorecard in build_adversaries.py to limit completeness
# reporting to the in-scope adversaries.  Spy-D3R is intentionally
# excluded; Category D (mounts / companions) is deferred to Phase 2.
PHASE1_NAMES: frozenset[str] = frozenset({
    # A. Ranked [N] Core Book adversaries (21)
    "[1] Mange Hexer", "[1] Pit Mange", "[1] Tiny Unhelpful Cloud",
    "[2] Bizzer Swarm", "[2] Drone",
    "[3] Blaster Mage", "[3] Undead Peddler",
    "[4] Chompa", "[4] Skelemaster",
    "[5] Battle Butler", "[5] Murder Maid",
    # [5] Mushdoom -- removed: not in Core Book PDF or Homebrew Sheet source.
    "[6] Chosen One", "[6] Croak Ronin",
    # [6] Ocularion -- removed: not in Core Book PDF.
    "[6] Proudhound Sellsword",
    "[7] Urarani", "[7] Grim Wing", "[7] Eruptle",
    "[8] Shadow Beast", "[8] Skelemonarch",
    # [8] Varubali -- removed: not in Core Book PDF or Homebrew Sheet source.
    "[9] Giga Gruun",
    # B. Demon variants (5) -- PDF p372
    "Demon - Blighted Beast", "Demon - Caustic Spittle",
    "Demon - Mocking Beauty", "Demon - Winter's Shackles",
    "Demon - Revolting Excess",
    # C. Unranked Core Monsters (4)
    "Skelemen", "Mange Bandit", "Lalka - Breeze", "Lalka - Mud",
})


# ------------------------------------------------------------------
# PHASE 2 -- Blog-post-sourced adversaries.
# Source: /home/rxm/Projects/qu-gg.github.io/break-blog-index/posts/raw/
# Per-adversary profile docstrings carry the blog post id + title.
# ------------------------------------------------------------------
PHASE2_NAMES: frozenset[str] = frozenset({
    "Funguy",
    "[4] Lug",
    "[4] Lank",
    "[5] Mushdoom",
    "[6] Ocularion",
    "[8] Varubali",
})


PROFILES: dict[str, dict] = {

    # ------------------------------------------------------------------
    # [8] Skelemonarch -- PDF p408-409
    # ------------------------------------------------------------------
    # Migrated verbatim from build_adversaries.extra_characters().
    # Stat values and prose all trace to PDF p408 ("MEGA BOSS / RANK 8"
    # stat box) and p409 (full ability + Quick Facts text).  The only
    # deliberate correction vs. the prior code is `speed = "average"`
    # (was inheriting "fast" from the Shadow Beast structural template).
    "[8] Skelemonarch": {
        "pdf_page":  408,
        "source":    "core-book",
        "rank":      8,
        "tier":      "mega-boss",
        "bio": {
            "name":    "Skelemonarch",
            "subname": "Rank 8 Mega-Boss",
            "type":    "Monster [Undead]",
            "size":    "Medium",
            "details": (
                "**Autarch of the fleshless.** When an ancient ritual seals "
                "a powerful soul within the body of a Skelemaster, the "
                "result is an ageless tyrant."
            ),
        },
        "stats": {
            "attack_bonus":     6,
            "defense_rating":   16,
            "speed":            "average",
            "hearts":           5,
            "hearts_adversary": 5,
            "aptitudes": {
                "might": 10, "deftness": 11, "grit": 8,
                "insight": 13, "aura": 13,
            },
            "allegiance": {"dark": 7, "bright": 0},
            "allegiance_area": "dark",
        },
        "abilities": [
            "Living Dead",
            "Pull Yourself Together",
            "Macabre Aura",
            "Hollow Eyed Servants",
            "Skelemancy",
            "Curse of the Skull",
        ],
        "gear": [],   # PDF lists only "ceremonial regalia" flavor -- no item entries
        "notes": {
            "habitat": (
                "Usually found in one of two places: in their ghastly "
                "stronghold, or behind a skeletal horde."
            ),
            "combat-gear": (
                "Each Skelemonarch has its own individual style, but most "
                "are partial to ceremonial regalia."
            ),
            "communication": (
                "They are able to speak Low Speech, Dark Tongue, and any "
                "other languages they knew when they were alive."
            ),
            "tactics": (
                "Despite their great power, Skelemonarchs avoid direct "
                "confrontation, obscuring themselves behind a loyal horde. "
                "The living are granted audience only to be subjected to "
                "the Curse of the Skull."
            ),
            "indicators": (
                "A garrison of highly organized Skelemasters and Skelemen, "
                "the sound of crackling energy, husks of discarded flesh."
            ),
            "role-playing-notes": (
                "Skelemonarchs are not just heartless, they are actively "
                "cruel. They taunt opposition in hopes of rash retaliation, "
                "and adorn skeletons under their command with mementos of "
                "their past lives so they can point them out to loved ones "
                "seeking revenge."
            ),
            "customization": (
                "Some Skelemonarchs might inflict other Ailments with their "
                "Curse of the Skull Ability."
            ),
        },
        "incomplete": [],
    },

    # ------------------------------------------------------------------
    # Remaining 29 profiles will be added as PDF pages are read.
    # See docs/ADVERSARIES_DESIGN.md s2 for the full Phase 1 list and
    # s6 for progress tracking.
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # [1] Mange Hexer -- PDF p436 (recipe), base p400 (Mange Bandit),
    #                    Small Species mods p106, Mortifying Bloat p61.
    # ------------------------------------------------------------------
    # This is a "Customization / Reskin" adversary from the p436 panel:
    #     Mange Bandit (p400)
    #   + Increase Rank by 1
    #   + Make Small Species (p106)        -- (+1 Deft, -1 Might, +1 DR)
    #   + Add Sage's Mortifying Bloat (p61)
    #
    # Stats are derived strictly per the book's mechanical recipe (no
    # invention), even where this differs from the prior OCR baseline.
    "[1] Mange Hexer": {
        "pdf_page":  436,
        "source":    "core-book",
        "rank":      1,
        "tier":      "boss",
        "bio": {
            "name":    "Mange Hexer",
            "subname": "Rank 1 Boss",
            "type":    "Folk [Animal-kin]",
            "size":    "Small",
            "details": (
                "**Ruff neck miscreant.** Outcasts banished from their pack "
                "for heinous crimes. The exile extends to their offspring, "
                "resulting in the formation of bandit packs.\n\n"
                "*Derived from Mange Bandit (p400) via Increase Rank by 1 + "
                "Make Small Species (p106) + Add Sage's Mortifying Bloat "
                "(p61). See p436.*"
            ),
        },
        "stats": {
            "attack_bonus":     1,     # Bandit +0, Rank+1 -> +1
            "defense_rating":   15,    # Bandit 14, Small Species +1 DR
            "speed":            "fast",
            "hearts":           2,     # Bandit 1, Rank+1 -> 2 (hp == hp-adv invariant)
            "hearts_adversary": 2,
            "aptitudes": {
                "might":    5,         # Bandit 6, Small -1
                "deftness": 8,         # Bandit 7, Small +1
                "grit":     6,
                "insight":  7,
                "aura":     5,
            },
            # Mortifying Bloat is a Dark spell ([D] +1 Dark per use); record
            # the +1 baseline allegiance the OCR carried.
            "allegiance": {"dark": 1, "bright": 0},
            "allegiance_area": "dark",
        },
        "abilities": [
            # Resolved against the 3-source skill lookup at build time.
            # Mortifying Bloat is the Sage Calling player ability (p61);
            # the player-skills bundle carries the verbatim PDF text.
            "Doggone Good Sense",
            "Stray's Step",
            "Mortifying Bloat",
        ],
        "gear": [
            "Light Armor",
            "Standard Weapon",
            "Thrown Weapon",
        ],
        "notes": {
            "habitat": (
                "These strays have spread from the Pride Coast, their "
                "ancestral homeland, in search of coin."
            ),
            "combat-gear": "Light Armor, a Standard Weapon, and some Thrown Weapons.",
            "communication": (
                "Low Speech and another language related to their home "
                "region. They refuse to learn Hoshi-Ban, the tongue of cats."
            ),
            "tactics": (
                "Mange are cowardly combatants and will:\n"
                "- Use ambush techniques.\n"
                "- Use ranged attacks when they are low in number.\n"
                "- Will only engage in melee if they are confident of the win."
            ),
            "indicators": (
                "Gnawed sticks, the sound of growling and howling, corpses "
                "with throwing knives in their backs."
            ),
            "role-playing-notes": (
                "Packs consist of varied personalities. Universally "
                "pragmatic and ruthless, most have a strong sense of "
                "loyalty to the pack and feel they are in it together, "
                "surviving in a cruel world."
            ),
            "customization": (
                "Hexers are Mange Bandits who picked up Sage magic. They "
                "lean on Mortifying Bloat to neutralize threats their pack "
                "can then swarm or rob. (See p436 Reskins.)"
            ),
        },
        "actions": [],   # generic derivation handles Standard Weapon, Thrown Weapon, Mortifying Bloat
        "incomplete": [],
    },

    # ------------------------------------------------------------------
    # [1] Pit Mange -- PDF p436 (recipe), base p400 (Mange Bandit),
    #                  Large Species mods p106, Brute Ability p30.
    # ------------------------------------------------------------------
    # Reskin from the p436 Customizations panel:
    #     Mange Bandit (p400)
    #   + Increase Rank by 1
    #   + Make Large Species (p106)        -- (+1 Might, -1 DR)
    #   + Add Champion's Brute Ability (p30)
    "[1] Pit Mange": {
        "pdf_page":  436,
        "source":    "core-book",
        "rank":      1,
        "tier":      "boss",
        "bio": {
            "name":    "Pit Mange",
            "subname": "Rank 1 Boss",
            "type":    "Folk [Animal-kin]",
            "size":    "Large",
            "details": (
                "**Ruff neck miscreant.** Outcasts banished from their pack "
                "for heinous crimes. The exile extends to their offspring, "
                "resulting in the formation of bandit packs.\n\n"
                "*Derived from Mange Bandit (p400) via Increase Rank by 1 + "
                "Make Large Species (p106) + Add Champion's Brute Ability "
                "(p30). See p436.*"
            ),
        },
        "stats": {
            "attack_bonus":     1,     # Bandit +0, Rank+1 -> +1
            "defense_rating":   13,    # Bandit 14, Large Species -1 DR
            "speed":            "fast",
            "hearts":           2,     # Bandit 1, Rank+1 -> 2
            "hearts_adversary": 2,
            "aptitudes": {
                "might":    7,         # Bandit 6, Large +1
                "deftness": 7,
                "grit":     6,
                "insight":  7,
                "aura":     5,
            },
            "allegiance": {"dark": 0, "bright": 0},   # Unaligned per p400
            "allegiance_area": "neutral",
        },
        "abilities": [
            "Doggone Good Sense",
            "Stray's Step",
            "Brute",
        ],
        "gear": [
            "Light Armor",
            "Standard Weapon",
            "Thrown Weapon",
        ],
        "notes": {
            "habitat": (
                "These strays have spread from the Pride Coast, their "
                "ancestral homeland, in search of coin."
            ),
            "combat-gear": "Light Armor, a Standard Weapon, and some Thrown Weapons.",
            "communication": (
                "Low Speech and another language related to their home "
                "region. They refuse to learn Hoshi-Ban, the tongue of cats."
            ),
            "tactics": (
                "Mange are cowardly combatants and will:\n"
                "- Use ambush techniques.\n"
                "- Use ranged attacks when they are low in number.\n"
                "- Will only engage in melee if they are confident of the win."
            ),
            "indicators": (
                "Gnawed sticks, the sound of growling and howling, corpses "
                "with throwing knives in their backs."
            ),
            "role-playing-notes": (
                "Packs consist of varied personalities. Universally "
                "pragmatic and ruthless, most have a strong sense of "
                "loyalty to the pack and feel they are in it together, "
                "surviving in a cruel world."
            ),
            "customization": (
                "Pit Mange are bulked-up bruisers from the bandit packs "
                "who picked up the Champion's Brute Ability. They prefer "
                "smashing straight through cover, shields, and softer "
                "opponents to any of the subtler bandit tactics. "
                "(See p436 Reskins.)"
            ),
        },
        "actions": [],   # generic derivation handles Standard Weapon, Thrown Weapon, Brute
        "incomplete": [],
    },

    # ------------------------------------------------------------------
    # [1] Tiny Unhelpful Cloud -- PDF p416-417.
    # ------------------------------------------------------------------
    # Atomic stat-block (not a reskin).  All values verbatim from the
    # adversary page; no Increase Rank / Species mods involved.
    "[1] Tiny Unhelpful Cloud": {
        "pdf_page":  416,
        "source":    "core-book",
        "rank":      1,
        "tier":      "boss",
        "bio": {
            "name":    "Tiny Unhelpful Cloud",
            "subname": "Rank 1 Boss",
            "type":    "Monster [Manifestation]",
            "size":    "Small",
            "details": (
                "**Nimbostratus Nemesis.** A strange cousin of the Very "
                "Useful Cloud (p62), Tiny Unhelpful Clouds are actually the "
                "manifestation of another creature's unpleasantness. These "
                "minuscule menaces stick close to their progenitor, and "
                "work hard to be a pain in the neck for just about anyone "
                "else."
            ),
        },
        "stats": {
            "attack_bonus":     1,
            "defense_rating":   12,    # 10 base + Made of Sterner Puff (+2)
            "speed":            "average",
            "hearts":           2,
            "hearts_adversary": 2,
            "aptitudes": {
                "might":    7,
                "deftness": 8,
                "grit":     9,         # includes "Stubborn (+1 Grit)" trait
                "insight":  7,
                "aura":     8,
            },
            "allegiance":     {"dark": 2, "bright": 0},
            "allegiance_area": "dark",
        },
        "abilities": [
            "Made of Sterner Puff",
            "Personal Rainy Day",
            "Your Worst Friend",
        ],
        "gear": [],   # Cloud carries no gear of its own.
        "notes": {
            "habitat": "The Cloud will always be found near its progenitor creature.",
            # combat-gear: PDF p416 has no Gear: line; field intentionally omitted.
            "communication": (
                "The Tiny Unhelpful Cloud can speak and understand Low "
                "Speech and has a small but angry voice."
            ),
            "tactics": (
                "The Cloud acts in ways that will help its progenitor "
                "defeat their enemies by:\n"
                "- Swiping, and carrying off, strategically valuable items.\n"
                "- Focusing their Personal Rainy Day Ability on any foes "
                "that seem to be a true threat to their progenitor."
            ),
            "indicators": (
                "The smell of rain, tiny but angry mumbling, fallen "
                "creatures with oddly wet hair."
            ),
            "role-playing-notes": (
                "Tiny Unhelpful Clouds are terrible conversationalists. "
                "They usually speak only to heckle, taunt, and mock anyone "
                "they come in contact with... even their host!"
            ),
            "customization": (
                "Some Tiny Unhelpful Clouds may cause Ailments (p268) or "
                "even blast targets with harmful electricity.\n\n"
                "**Reskin (p417):** A small, imp-like creature could be "
                "created using the Tiny Unhelpful Cloud. If one of the "
                "PCs is meaner and grumpier than the Cloud's progenitor, "
                "they may want to swap allegiances; if accepted, this "
                "will count as one of their Companions. The Cloud will "
                "evaporate if the PC starts to show more empathy or "
                "generosity."
            ),
        },
        "actions": [   # Personal Rainy Day is tagged [B] in the skills bundle
                       # so the action-deriver skips it, but the PDF (p417)
                       # describes it as costing "the Cloud's Action for a
                       # Turn".  Inject the action explicitly.
            {
                "name": "Personal Rainy Day",
                "subtype": "",
                "description": (
                    "A tiny storm cloud is still a storm cloud. The Tiny "
                    "Unhelpful Cloud hovers above someone its host is "
                    "openly hostile towards and pelts them with localized "
                    "rainfall and tiny lightning bolts. This is supremely "
                    "annoying and often a bit painful.\n\n"
                    "- Costs the Cloud's Action for a Turn.\n"
                    "- The target has a Snag on all Rolls until the end "
                    "of their next action.\n"
                    "- [D] Adds 1 Dark Allegiance Point."
                ),
            },
        ],
        "incomplete": [
            "inventory: Cloud carries no gear of its own (PDF p416-417); scorecard "
            "flags empty inventory as a gap but this is structurally N/A.",
            "notes(combat-gear): PDF p416 stat block has no Gear: line; field "
            "intentionally omitted per strict-no-invention policy.",
        ],
    },

    # ------------------------------------------------------------------
    # [2] Bizzer Swarm -- PDF p364-365.
    # ------------------------------------------------------------------
    "[2] Bizzer Swarm": {
        "pdf_page":  364,
        "source":    "core-book",
        "rank":      2,
        "tier":      "boss",
        "bio": {
            "name":    "Bizzer Swarm",
            "subname": "Rank 2 Boss",
            "type":    "Monster [Insectoid Swarm]",
            "size":    "Medium",
            "details": (
                "**Mana-sucking menaces.** Bizzers are small flying "
                "insects that feed off magic. While not dangerous on "
                "their own, they have a tendency to travel in huge "
                "groups, capable of hindering the spells of even the "
                "most experienced casters."
            ),
        },
        "stats": {
            "attack_bonus":     2,
            "defense_rating":   12,    # 10 base + Buzzing Mass (+2)
            "speed":            "fast",
            "hearts":           2,
            "hearts_adversary": 2,
            "aptitudes": {
                "might":     7,
                "deftness":  8,
                "grit":     10,        # includes Persistent (+2 Grit)
                "insight":   8,
                "aura":      6,        # includes Annoying (-1 Aura)
            },
            "allegiance":      {"dark": 0, "bright": 0},   # Unaligned
            "allegiance_area": "neutral",
        },
        "abilities": [
            "Buzzing Mass",
            "Engulf",
        ],
        "gear": [],   # Swarm of insects; carries no gear.
        "notes": {
            "habitat": (
                "Bizzer Swarms make their nests in mana-rich environments, "
                "for example wizarding structures or magical biomes. They "
                "are infamous for causing injuries, and even a few "
                "fatalities, at Shard's University and its rival school in "
                "the Galvanus Peninsula, by showing up during an important "
                "magical demonstration or eating the flight spell of a "
                "commuting professor. However, soldiers and bandits have "
                "been known to weaponize them for use against arcane foes. "
                "Buzz Bombs, glass jars filled with Bizzers, are very "
                "popular among raiders in particular."
            ),
            # combat-gear: PDF p364 has no Gear: line; field intentionally omitted.
            "communication": (
                "Bizzers have no means of communicating to other "
                "creatures, unless you count their incessant buzzing."
            ),
            "tactics": (
                "Bizzers are instinctual creatures and don't formulate "
                "combat strategies."
            ),
            "indicators": (
                "Rusty imbued items, a single Bizzer moving along a wall, "
                "that horrible buzzing noise."
            ),
            "role-playing-notes": "Buzz, buzz buzz. Buzz buzz!",
            "customization": (
                "Certain Swarms may inflict an Ailment (p268) in addition "
                "to hindering magic use when they use their Engulf "
                "Ability.\n\n"
                "**Reskin (p365):** Make the Engulf Ability drain Hearts, "
                "rather than mana, to reskin the Bizzer Swarm as more "
                "conventional bloodsucking insects."
            ),
        },
        "actions": [   # Engulf is [B] in the skills bundle so derivation
                       # skips it, but the PDF (p365) explicitly calls it
                       # an Action.
            {
                "name": "Engulf",
                "subtype": "",
                "description": (
                    "Bizzer Swarms surround a target and drain away any "
                    "mana on or around them. A hungry swarm is noisy and "
                    "incessant.\n\n"
                    "- Requires the Swarm's Action; no Attack roll needed.\n"
                    "- Targets a single creature or item in the Swarm's "
                    "Area that has Magical Abilities (no interest in "
                    "non-magical entities).\n"
                    "- The target cannot use any Magical Abilities while "
                    "engulfed.\n"
                    "- Anyone attacking the Swarm while it is engulfing "
                    "hits the engulfed target instead on a failed roll.\n"
                    "- The Swarm follows its target, but abandons pursuit "
                    "if it becomes hazardous (e.g. flames, submersion).\n"
                    "- A target who escapes the Swarm remains unable to "
                    "use any Magical Abilities for 1 Turn."
                ),
            },
        ],
        "incomplete": [
            "inventory: Bizzer Swarm carries no gear (PDF p364-365); "
            "structurally N/A.",
            "allegiance: per PDF p364 the Swarm is Unaligned (0 Dark / 0 "
            "Bright); scorecard treats 0/0 as missing but this is the "
            "correct value.",
            "notes(combat-gear): PDF p364 stat block has no Gear: line; field "
            "intentionally omitted per strict-no-invention policy.",
        ],
    },

    # ------------------------------------------------------------------
    # [2] Drone  (PDF: Maintenance Drone) -- PDF p376-377.
    # ------------------------------------------------------------------
    # The OCR baseline names this entry "Drone - Worker" but the PDF
    # clearly identifies the Rank 2 Boss as MAINTENANCE DRONE.  Per the
    # strict-PDF policy the bio name is set from the book.
    "[2] Drone": {
        "pdf_page":  376,
        "source":    "core-book",
        "rank":      2,
        "tier":      "boss",
        "bio": {
            "name":    "Maintenance Drone",
            "subname": "Rank 2 Boss",
            "type":    "Monster [Mechanical]",
            "size":    "Medium",
            "details": (
                "**Synthetic being.** Precursor to the Bio-Mechanoid, "
                "these simpler machines were built to perform repetitive "
                "tasks. During the 3rd Cataclysm, the First Hero rendered "
                "all synthetics dormant. Recently they are flickering "
                "back to life.\n\n"
                "*[protocol error; searching...]* These sleepless "
                "caretakers of long-forgotten factories from the previous "
                "aeon suffer a strange derangement, developed while "
                "inert, which has caused them to abandon their duties."
            ),
        },
        "stats": {
            "attack_bonus":     2,
            "defense_rating":   14,    # 10 base + Labor Frame (+4)
            "speed":            "slow",  # Labor Frame: "Maintenance Drones are Slow"
            "hearts":           3,     # 2 base + Labor Frame (+1 Hearts Total)
            "hearts_adversary": 3,
            "aptitudes": {
                "might":     7,
                "deftness": 10,        # includes "Efficient (+? Deftness)" trait
                "grit":      8,
                "insight":   9,        # includes "Precise (+? Insight)" trait
                "aura":      5,        # includes "Rule (-? Aura)" trait
            },
            # OCR trait labels for Drone are partially scrambled in the
            # source PDF text extract ("fficient Deftne / reci e n i t /
            # ule ura").  Aptitude totals are taken verbatim from the
            # stat block; the trait names are reconstructed only where
            # clearly readable.
            "allegiance":      {"dark": 0, "bright": 0},   # Unaligned
            "allegiance_area": "neutral",
        },
        "abilities": [
            "Synthetic",
            "Mad Machine",
            "Labor Frame",
        ],
        "gear": [],   # Drone has no carried gear; limbs are body weapons.
        "notes": {
            "habitat": (
                "Drones are found in the ruins of ancient Gleysian "
                "facilities, but many wander further afield."
            ),
            # combat-gear: PDF p376 has no Gear: line; field intentionally omitted.
            "communication": (
                "Drones exclusively speak and understand Gleysian Code."
            ),
            "tactics": (
                "Maintenance Drones cannot formulate sophisticated "
                "strategies, they simply identify weak or 'broken' "
                "opponents and target them."
            ),
            "indicators": (
                "Loud clanking noises, bodies that have been crushed and "
                "torn apart, devices that have been dismantled or badly "
                "repaired."
            ),
            "role-playing-notes": (
                "Maintenance Drones can only speak in a calm and polite "
                "manner. However, their new 'emotions' are poorly "
                "regulated and they often say disturbing, morose, or "
                "incomprehensible things. Drones harbor a misplaced "
                "sibling rivalry with Bio-Mechanoids."
            ),
            "customization": (
                "Drones might be fitted with limbs that strike as "
                "different Weapon Types, or with a Mender's Kit (p176). "
                "They may also be able to hover, climb, or float "
                "depending on their original function.\n\n"
                "**Reskin (p377):** A reskinned Maintenance Drone can be "
                "used as a golem or animated suit of armor."
            ),
        },
        "actions": [
            {
                "name": "Limb Strike (Standard Weapon)",
                "subtype": "",
                "description": (
                    "The Maintenance Drone's mechanical limbs strike as "
                    "a Standard Weapon (Labor Frame Ability, p377)."
                ),
            },
            {
                "name": "Mad Machine -- Enter Rampage",
                "subtype": "",
                "description": (
                    "As a result of overexposure to mana, the Drone now "
                    "has thoughts and feelings it wasn't designed to "
                    "process.\n\n"
                    "- The Drone can enter at will into an erratic, "
                    "rampaging state.\n"
                    "- While rampaging: grants a Minor Bonus (+2) to "
                    "Might rolls; +1 Heart of Damage to physical Attacks; "
                    "-2 Defense Rating (reckless flailing).\n"
                    "- Attempting to exit this state requires the Drone "
                    "to make a successful Insight Check."
                ),
            },
        ],
        "incomplete": [
            "inventory: Maintenance Drone carries no gear (PDF p376-377); "
            "structurally N/A. Yield items (Synthetic Limbs, Puretech "
            "Salvage) only apply after death.",
            "allegiance: per PDF p376 the Drone is Unaligned (0/0); "
            "scorecard treats 0/0 as missing but this is the correct value.",
            "notes(combat-gear): PDF p376 stat block has no Gear: line; field "
            "intentionally omitted per strict-no-invention policy.",
        ],
    },

    # ------------------------------------------------------------------
    # [3] Blaster Mage -- PDF p366-367.
    # ------------------------------------------------------------------
    "[3] Blaster Mage": {
        "pdf_page":  366,
        "source":    "core-book",
        "rank":      3,
        "tier":      "boss",
        "bio": {
            "name":    "Blaster Mage",
            "subname": "Rank 3 Boss",
            "type":    "Folk [Extraordinary]",
            "size":    "Medium",
            "details": (
                "**Hot-headed spell slinger.** 'Blaster Mage' is a "
                "pejorative term coined by Sages for wizards who can only "
                "perform relatively simplistic pyrotechnics."
            ),
        },
        "stats": {
            "attack_bonus":     2,
            "defense_rating":   12,    # 10 base + Light Armor (+2)
            "speed":            "average",
            "hearts":           3,
            "hearts_adversary": 3,
            "aptitudes": {
                "might":     8,
                "deftness": 11,        # includes Nimble (+2 Deftness)
                "grit":      9,
                "insight":   6,        # includes Impulsive (-2 Insight)
                "aura":     11,        # includes Impressive (+2 Aura)
            },
            "allegiance":      {"dark": 0, "bright": 3},   # Bright Aligned, 3 Bright
            "allegiance_area": "bright",
        },
        "abilities": [
            "Magic Shot",
            "Big Magic Shot",
            "Mana Burst",
        ],
        "gear": [
            "Light Armor",
            "Standard Weapon",
        ],
        "notes": {
            "habitat": (
                "Found anywhere in Outer World, often working alongside "
                "bandits, mercenaries, and warlords."
            ),
            "combat-gear": (
                "Light Armor and a Standard Weapon, in case things get "
                "physical."
            ),
            "communication": (
                "They speak and understand Low Speech, as well as another "
                "language appropriate to their home region."
            ),
            "tactics": (
                "They do their best to stick with what they are good at "
                "and will:\n"
                "- Stay behind the front line, hiding behind their allies.\n"
                "- Pummel targets with their Magic Shots from a safe "
                "distance."
            ),
            "indicators": (
                "Seared walls, corpses covered in neatly burned holes, "
                "loud and brash declarations."
            ),
            "role-playing-notes": (
                "Prone to using insulting or dramatic gestures. Amused by "
                "their own brilliance."
            ),
            "customization": (
                "Blaster Mages may occasionally take advantage of "
                "Appealing or Authoritative Outfits.\n\n"
                "**Reskin (p367):** Removing the Mana Burst Ability and "
                "providing more powerful arms and armor creates a "
                "'Blaster Knight'."
            ),
        },
        "actions": [],   # All three abilities are [M]-tagged; derivation handles them.
        "incomplete": [],
    },

    # ------------------------------------------------------------------
    # [3] Undead Peddler -- PDF p418-419.
    # ------------------------------------------------------------------
    "[3] Undead Peddler": {
        "pdf_page":  418,
        "source":    "core-book",
        "rank":      3,
        "tier":      "boss",
        "bio": {
            "name":    "Undead Peddler",
            "subname": "Rank 3 Boss",
            "type":    "Folk [Undead]",
            "size":    "Medium",
            "details": (
                "**Buy somethin', will ya?** Cursed merchants who, having "
                "perished with an outrageous unpaid debt, now wander "
                "dangerous places looking for business."
            ),
        },
        "stats": {
            "attack_bonus":     2,
            "defense_rating":   10,    # no armor / ability bonus baked in
            "speed":            "average",
            "hearts":           3,
            "hearts_adversary": 3,
            "aptitudes": {
                "might":     7,
                "deftness":  9,
                "grit":      8,        # includes Skin n' bone (-1 Grit)
                "insight":  11,        # includes Shrewd (+2 Insight)
                "aura":      9,
            },
            "allegiance":      {"dark": 2, "bright": 0},   # Dark Aligned, 2 Dark
            "allegiance_area": "dark",
        },
        "abilities": [
            "Living Dead",
            "Corpse Commodities",
        ],
        "gear": [],   # PDF p418 has no Gear: line; inventory comes from Corpse Commodities.
        "notes": {
            "habitat": (
                "Found almost exclusively in monster filled dungeons, "
                "ruins and cave networks. Peddlers occasionally wander "
                "the roads of the Wistful Dark and Buried Kingdom."
            ),
            # combat-gear: PDF p418 has no Gear: line; field intentionally omitted.
            "communication": (
                "Undead Peddlers are well versed in every language used "
                "in the Outer World, they want to guarantee they can do "
                "business with anyone they meet."
            ),
            "tactics": (
                "Peddlers are not really into fighting. They will offer a "
                "free item if threatened by someone tough, but happily "
                "blow themselves up rather than let greedy murder hobos "
                "make off with their goods."
            ),
            "indicators": (
                "Clamor made by the rattling of merchandise, dungeon "
                "inhabitants with gear they wouldn't normally have, "
                "signs that say \"Sale End is Nigh\"."
            ),
            "role-playing-notes": (
                "Undead Peddlers are consummate deal-makers with a "
                "certain charm to them. They will do anything to pursue "
                "a sale as long as it means some sort of profit, though "
                "they don't take kindly to threats or other overly "
                "aggressive techniques. Being so used to dealing with "
                "any number of monsters and unsavory customers, it's "
                "actually pretty hard to phase them."
            ),
            "customization": (
                "More fortunate Undead Peddlers travel with Skeleman "
                "bodyguards. It's also rumored that some Peddlers "
                "possess magical inventory boxes that can hold a vast "
                "amount of items.\n\n"
                "**Reskin (p419):** Reanimated Physicians and "
                "Ever-living Blacksmiths can be made by giving a Peddler "
                "additional Abilities from the Factotum Calling (p17) "
                "or... Create a Dwarf dungeon shopkeep or a Goblin "
                "apothecary by swapping Living Dead with the appropriate "
                "Species Abilities."
            ),
        },
        "actions": [   # Corpse Commodities self-destruct is described in the
                       # PDF as an instant, intentional Action by the Peddler,
                       # but the ability is [B]-tagged so derivation skips it.
            {
                "name": "Self-Destruct (Corpse Commodities)",
                "subtype": "",
                "description": (
                    "Most Undead Peddlers are wired with explosives that "
                    "they can detonate instantly when they are worried "
                    "about being exploited. The explosives are powerful "
                    "enough to destroy them and all their wares. Anyone "
                    "within 1 Battlefield Area of the exploding Peddler "
                    "feels the effect of the Bomb (p178).\n\n"
                    "- [D] Adds 1 Dark Allegiance Point."
                ),
            },
        ],
        "incomplete": [
            "notes(combat-gear): PDF p418 stat block has no Gear: line; field "
            "intentionally omitted per strict-no-invention policy.",
        ],
    },

    # ------------------------------------------------------------------
    # [4] Chompa -- PDF p368-369.
    # ------------------------------------------------------------------
    "[4] Chompa": {
        "pdf_page":  368,
        "source":    "core-book",
        "rank":      4,
        "tier":      "boss",
        "bio": {
            "name":    "Chompa",
            "subname": "Rank 4 Boss",
            "type":    "Beast [Megafauna]",
            "size":    "Large",
            "details": (
                "**One massive muncher.** A distant cousin of the Bumpo, "
                "these omnivorous bovines are much less docile and armed "
                "with an enormous tusk-filled mouth."
            ),
        },
        "stats": {
            "attack_bonus":     3,
            "defense_rating":  13,     # 10 base + Blubbery Hide (+4) + Large (-1)
            "speed":            "slow",  # Blubbery Hide reduces speed by 1 level
            "hearts":           4,     # 3 base + Blubbery Hide (+1 Hearts Total)
            "hearts_adversary": 4,
            "aptitudes": {
                "might":    12,        # includes Brutish (+2) and Large Species (+1)
                "deftness":  6,        # includes Lumbering (-2)
                "grit":     10,        # includes Stubborn (+1)
                "insight":   9,
                "aura":      8,
            },
            "allegiance":      {"dark": 0, "bright": 0},   # Unaligned
            "allegiance_area": "neutral",
        },
        "abilities": [
            "Big 'Un",
            "Mighty Munch",
            "Blubbery Hide",
        ],
        "gear": [],
        "notes": {
            "habitat": (
                "Any place that has enough flora and fauna to satiate "
                "their monstrous appetites."
            ),
            "combat-gear": (
                "Sometimes interesting things can be found in their dung."
            ),
            "communication": "Belches and snorts.",
            "tactics": (
                "In combat they are motivated by hunger and will:\n"
                "- Attempt to swallow the closest, or juiciest, prey "
                "first.\n"
                "- Spit rocks, or other parts of the environment, at "
                "escaping food."
            ),
            "indicators": (
                "Big bites taken out of the landscape, deep and wide "
                "footprints, the sound of open-mouthed chewing and "
                "flatulence."
            ),
            "role-playing-notes": (
                "They are only interested in filling their bellies, and "
                "won't be motivated by anger or retribution."
            ),
            "customization": (
                "Chompas are occasionally caught and used as Packbeasts "
                "or even Mounts by creatures who favor strength and "
                "ferocity over speed.\n\n"
                "**Reskin (p369):** Remove the Chompa's Blubbery Hide "
                "Ability and provide it with Supernatural Leaping or "
                "Might to create a wolf or bear-like beast. Giving the "
                "Chompa an Ability to move Fast in the water will create "
                "a monstrous turtle or hippopotamus. They could even "
                "suck in water and spray it back out in a powerful "
                "stream with Mighty Munch!"
            ),
        },
        "actions": [],   # Mighty Munch is [A]-tagged; derivation handles it.
                         # Big 'Un is a passive Species reference, not an action.
                         # Blubbery Hide is purely passive (DR/HP/Speed mods).
        "incomplete": [
            "allegiance: per PDF p368 the Chompa is Unaligned (0/0); "
            "scorecard treats 0/0 as missing but this is the correct value.",
        ],
    },

    # ------------------------------------------------------------------
    # [4] Skelemaster -- PDF p406-407.
    # ------------------------------------------------------------------
    "[4] Skelemaster": {
        "pdf_page":  406,
        "source":    "core-book",
        "rank":      4,
        "tier":      "boss",
        "bio": {
            "name":    "Skelemaster",
            "subname": "Rank 4 Boss",
            "type":    "Monster [Undead]",
            "size":    "Medium",
            "details": (
                "**Bossy bones.** A Skeleman that has claimed the eyes "
                "and tongue of the living gains enhanced vision, the "
                "power of speech, and poisonous ambition."
            ),
        },
        "stats": {
            "attack_bonus":     3,     # +3 base (+4 with Master Weapon)
            "defense_rating":  14,     # 10 base + Medium Armor (+4)
            "speed":            "average",
            "hearts":           3,
            "hearts_adversary": 3,
            "aptitudes": {
                "might":     7,        # Lazy bones (-1 Might)
                "deftness": 10,        # Eager hands (+1 Deftness)
                "grit":      7,        # Brittle (-1 Grit)
                "insight":  10,        # Actual eyes (+1 Insight)
                "aura":     10,        # Silver tongue (+1 Aura)
            },
            "allegiance":      {"dark": 3, "bright": 0},
            "allegiance_area": "dark",
        },
        "abilities": [
            "Living Dead [B]",
            "Pull Yourself Together [B]",
            "Hollow Eyed Servants [A][M]",
        ],
        "gear": [],   # OCR inventory already carries Medium Armor + Master Weapon.
        "notes": {
            "habitat": (
                "Often found accompanying large groups of Skelemen. The "
                "boldest use masks and disguises to infiltrate cities."
            ),
            "combat-gear": (
                "Usually wear Medium Armor in conjunction with an "
                "Authoritative or Appealing Outfit. Most will wield a "
                "Master Weapon."
            ),
            "communication": (
                "They have high pitched, nasally voices. They can speak "
                "Low Speech and any other languages they knew when alive."
            ),
            "tactics": (
                "Skelemasters stick to the same tactics used by "
                "Skelemen, although they will utilize decoy groups and "
                "more sophisticated hit and run tactics. They are also "
                "more cautious and they will:\n"
                "- Gather as much information as possible on unknown "
                "foes before confronting them directly.\n"
                "- Only join a battle when they have established a "
                "clear advantage.\n\n"
                "If more than one Skelemaster inhabits the same "
                "Adventure Site, they will try to undermine or usurp "
                "the other whilst dealing with the PCs."
            ),
            "indicators": (
                "The sound of wicked cackling, the glint of a well kept "
                "weapon among rusted ones, disturbingly organized "
                "Skelemen."
            ),
            "role-playing-notes": (
                "Skelemasters are as conniving as their Skeleman "
                "minons, but their love of dramatics is tempered by a "
                "sadistic streak and an increased desire for self "
                "preservation. Skelemasters literally love the sound of "
                "their own voice and their recently acquired tongues "
                "can make them prone to monologuing or singing."
            ),
            "customization": (
                "Arm with different weapons, or heavier armor, at the "
                "lamented expense of style. Toughen them up with a "
                "Champion or Raider's Elective Ability.\n\n"
                "**Reskin (p407):** Replacing Hollow Eyed Servants with "
                "a Calling Elective Ability can change the Skelemaster "
                "into a solitary undead foe."
            ),
        },
        "actions": [],   # Living Dead [B] and Pull Yourself Together [B] are
                         # purely passive.  Hollow Eyed Servants is [A][M]-tagged
                         # so derivation handles its action entry.
    },

    # ------------------------------------------------------------------
    # [5] Battle Butler -- PDF p390-391.
    # ------------------------------------------------------------------
    "[5] Battle Butler": {
        "pdf_page":  390,
        "source":    "core-book",
        "rank":      5,
        "tier":      "boss",
        "bio": {
            "name":    "Battle Butler",
            "subname": "Rank 5 Boss",
            "type":    "Folk [Extraordinary]",
            "size":    "Medium",
            "details": (
                "**One heck of a steward.** Murder Maids are trained to "
                "tidy up messy situations whereas Battle Butlers prevent "
                "them from occurring in the first place. Calm and "
                "unflappable, they are always present when their master "
                "requires."
            ),
        },
        "stats": {
            "attack_bonus":     4,     # +4 base (+5 with Chosen Weapon)
            "defense_rating":  17,     # 10 + Tidy Battle Stance (+2) + Immaculate
                                       # Uniform (+2) + Speed Bonus (+2) + Quick
                                       # Weapon (+1)
            "speed":            "fast",  # Expeditious Manner raises 1 level
            "hearts":           4,
            "hearts_adversary": 4,
            "aptitudes": {
                "might":     8,        # A bit thin (-1 Might)
                "deftness": 10,
                "grit":     11,        # Stoic (+1 Grit)
                "insight":  11,        # Observant (+1 Insight)
                "aura":      9,
            },
            "allegiance":      {"dark": 0, "bright": 0},   # Unaligned
            "allegiance_area": "neutral",
        },
        "abilities": [
            "Immaculate Uniform [B]",
            "Tidy Battle Stance [A]",
            "Expeditious Manner [B]",
            "Unruffled Monotony [A]",
        ],
        "gear": [],   # OCR inventory carries the Authoritative Outfit / weapon.
        "notes": {
            "habitat": (
                "Found in the service of Outer World's most wealthy, "
                "such as the Patricians of Shard or the Samurai of the "
                "Seven Holy Isles."
            ),
            "combat-gear": (
                "They wear their Immaculate Uniform and carry a notable "
                "Chosen Weapon. For example, a duelling sabre that has "
                "a timepiece built in."
            ),
            "communication": (
                "Low Speech and their employer's preferred language."
            ),
            "tactics": (
                "Butlers work best when they are part of a team and "
                "will:\n"
                "- Attempt to thwart the most challenging opponent "
                "while their compatriots pick off the rest.\n"
                "- If isolated, they will withdraw unless they are "
                "acting as a decoy."
            ),
            "indicators": (
                "Noticeably well ordered areas, the sound of patient "
                "footsteps, a body of someone slain by clean, precise "
                "cuts."
            ),
            "role-playing-notes": (
                "Polite to a fault. They put duty before emotion and "
                "are respectful no matter what their intent."
            ),
            "customization": (
                "Experienced Battle Butlers might know Battle Princess "
                "Elective Abilities (p42).\n\n"
                "**Reskin (p391):** The Battle Butler can be used to "
                "represent a loyal and upright bodyguard."
            ),
        },
        "actions": [],   # Tidy Battle Stance [A] and Unruffled Monotony [A]
                         # auto-derive; Immaculate Uniform [B] and Expeditious
                         # Manner [B] are purely passive.
        "incomplete": [
            "allegiance: per PDF p390 the Battle Butler is Unaligned "
            "(0/0); scorecard treats 0/0 as missing but this is the "
            "correct value.",
        ],
    },

    # ------------------------------------------------------------------
    # [5] Murder Maid -- PDF p388-389.
    # ------------------------------------------------------------------
    "[5] Murder Maid": {
        "pdf_page":  388,
        "source":    "core-book",
        "rank":      5,
        "tier":      "boss",
        "bio": {
            "name":    "Murder Maid",
            "subname": "Rank 5 Boss",
            "type":    "Folk [Extraordinary]",
            "size":    "Medium",
            "details": (
                "**They'll mop the floor with you.** Murder Maids will "
                "eliminate anyone who threatens to disrupt the domestic "
                "bliss they maintain."
            ),
        },
        "stats": {
            "attack_bonus":     4,     # +4 base (+5 with Chosen Weapon)
            "defense_rating":  14,     # 10 + Tidy Battle Stance (+2) +
                                       # Immaculate Uniform (+2)
            "speed":            "average",
            "hearts":           4,
            "hearts_adversary": 4,
            "aptitudes": {
                "might":    10,        # Spirited (+1 Might)
                "deftness": 11,        # Careful (+1 Deftness)
                "grit":     10,
                "insight":  10,
                "aura":      8,        # Demure (-1 Aura)
            },
            "allegiance":      {"dark": 0, "bright": 0},   # Unaligned
            "allegiance_area": "neutral",
        },
        "abilities": [
            "Immaculate Uniform [B]",
            "Tidy Battle Stance [A]",
            "Out Damn Spot [B]",
            "Back Forth Without Fuss [B]",   # addendum skill name (PDF: "Back & Forth Without a Fuss")
        ],
        "gear": [],
        "notes": {
            "habitat": (
                "Killservants are employed wherever there are folk rich "
                "enough to train and hire them."
            ),
            "combat-gear": (
                "They wear their Immaculate Uniform and carry a discrete "
                "Chosen Weapon. For example, an Arc Weapon disguised as "
                "a Broom."
            ),
            "communication": (
                "Low Speech and their employer's preferred language."
            ),
            "tactics": (
                "Once an individual has been targeted they will:\n"
                "- Use Back and Forth without a Fuss to avoid being "
                "cornered.\n"
                "- Fight relentlessly, but not with suicidal loyalty. "
                "After all, who will clean up the mess if they are "
                "killed?"
            ),
            "indicators": (
                "An extremely neat and tidy area, soft humming and "
                "rhythmic footsteps."
            ),
            "role-playing-notes": (
                "Pleasant and polite when on duty, but individuals can "
                "be shy, bubbly or brusque."
            ),
            "customization": (
                "Individual Maids will carry different Chosen Weapons. "
                "When working in groups, Maids will also choose accent "
                "colors to differentiate their uniforms. Experienced "
                "Murder Maids may know Magical Murder Princess Elective "
                "Abilities (p52).\n\n"
                "**Reskin (p389):** The Murder Maid can be used to "
                "represent a zealous soldier or crusader."
            ),
        },
        "actions": [],   # Tidy Battle Stance [A] auto-derives; the three [B]
                         # abilities are purely passive.
        "incomplete": [
            "allegiance: per PDF p388 the Murder Maid is Unaligned "
            "(0/0); scorecard treats 0/0 as missing but this is the "
            "correct value.",
        ],
    },

    # ------------------------------------------------------------------
    # [6] Chosen One -- PDF p370-371.
    # ------------------------------------------------------------------
    "[6] Chosen One": {
        "pdf_page":  370,
        "source":    "core-book",
        "rank":      6,
        "tier":      "boss",
        "bio": {
            "name":    "Chosen One",
            "subname": "Rank 6 Boss",
            "type":    "Folk [Extraordinary]",
            "size":    "Medium",
            "details": (
                "**The hero of another story.** Occasionally, youths "
                "are given great powers and a quest by the whims of "
                "fate. Legends describe how these enterprising figures "
                "fulfill their destinies, but in reality many fail and "
                "their exploits go unchronicled."
            ),
        },
        "stats": {
            "attack_bonus":     4,     # +4 base (+5 with Red Edge Master Weapon)
            "defense_rating":  14,     # 10 + Medium Armor (+4); +1 more with Cleary Shield
            "speed":            "average",
            "hearts":           4,
            "hearts_adversary": 4,
            "aptitudes": {
                "might":    11,        # Surprisingly strong (+1 Might)
                "deftness":  9,
                "grit":     11,        # Spirited (+1 Grit)
                "insight":   9,
                "aura":      9,        # Silent type (-1 Aura)
            },
            "allegiance":      {"dark": 0, "bright": 0},   # Unaligned
            "allegiance_area": "neutral",
        },
        "abilities": [
            "Legendary Items [A]",          # PDF heading: "LEGENDARY GEAR"
            "Courageous Determination [A]",
            "Favored By Fate [B]",          # not in skill lookup; kept as legacy seed
        ],
        "gear": [],
        "notes": {
            "habitat": (
                "Although hailing from remote and peaceful villages, "
                "their quests can lead them anywhere."
            ),
            "combat-gear": "See Legendary Gear Ability!",
            "communication": (
                "Low Speech and a language based on their homeland."
            ),
            "tactics": (
                "Bold combatants who rely on resilience and daring "
                "Stunts to:\n"
                "- Target leaders first.\n"
                "- Identify and exploit weak spots."
            ),
            "indicators": (
                "A valorous battle cry, villages filled with people who "
                "have had small requests recently fulfilled, and a "
                "trail of slain monsters."
            ),
            "role-playing-notes": (
                "They believe their quest is just. Challenging their "
                "cause will result in being seen as a true villain to "
                "be silenced."
            ),
            "customization": (
                "Experienced Chosen Ones can have an Elective Champion "
                "or Battle Princess Ability. Some travel with "
                "companions, usually a fairy.\n\n"
                "**Reskin (p371):** Swapping out the Chosen One's "
                "Legendary Gear for more sinister Imbued Items will "
                "create a villainous character, rather than a sadly "
                "misguided heroic one."
            ),
        },
        "actions": [],   # Legendary Items [A] and Courageous Determination [A]
                         # auto-derive; Favored By Fate [B] is purely passive.
        "incomplete": [
            "allegiance: per PDF p370 the Chosen One is Unaligned "
            "(0/0); scorecard treats 0/0 as missing but this is the "
            "correct value.",
            "inventory: per PDF p370 gear text is 'See Legendary Gear "
            "Ability!'.  The Legendary Items (Red Edge, Cleary Shield, "
            "Spring Heel Boots, Mighty Mitten, Wooly Warm Tunic) are "
            "unique Imbued Items not present in BREAK!! Core Book "
            "Items; selected items are described in the Legendary "
            "Items ability text.",
        ],
    },

    # ------------------------------------------------------------------
    # [6] Croak Ronin -- PDF p436 (Example Adversary Customization).
    # Derived from Proudhound Sellsword (p402).
    # ------------------------------------------------------------------
    "[6] Croak Ronin": {
        "pdf_page":  436,
        "source":    "core-book",
        "rank":      6,
        "tier":      "boss",
        "bio": {
            "name":    "Croak Ronin",
            "subname": "Rank 6 Boss",
            "type":    "Folk [Animal-kin]",
            "size":    "Medium",
            "details": (
                "**A toad-folk mercenary reskin of the Proudhound "
                "Sellsword.**\n\n"
                "*Derived from Proudhound Sellsword (p402) via the p436 "
                "Example Customization: remove Doggone Good Sense; "
                "reskin Fearsome Growl to Fearsome Croak; add new "
                "Tongue Tachi ability (ballistic tongue strikes as a "
                "Lash Weapon).*"
            ),
        },
        "stats": {
            # All inherited unchanged from Proudhound base (p402).
            "attack_bonus":     4,     # +4 base (+5 with Packsword Master)
            "defense_rating":  16,     # 10 + Heavy Armor (+6)
            "speed":            "average",
            "hearts":           4,
            "hearts_adversary": 4,
            "aptitudes": {
                "might":    10,
                "deftness":  8,        # Rough (-1 Deftness)
                "grit":     12,        # Stalwart (+2 Grit)
                "insight":  11,        # Aware (+1 Insight)
                "aura":      9,
            },
            "allegiance":      {"dark": 0, "bright": 0},   # Unaligned
            "allegiance_area": "neutral",
        },
        "abilities": [
            "Frog Leap [A]",
            "Fearsome Croak [B]",
            "Tongue Tachi [A]",
        ],
        "gear": [],   # OCR carries Heavy Armor + Packsword from Proudhound base.
        "notes": {
            "habitat": (
                "Most common around the Pride Coast, their ancestral "
                "homeland, Proudhounds travel far and wide in search "
                "of worthy foes."
            ),
            "combat-gear": (
                "Heavy Armor and a Packsword (Mighty/Master "
                "Combination Weapon)."
            ),
            "communication": (
                "Low Speech and another language related to their "
                "home region. They refuse to learn Hoshi-Ban, the "
                "tongue of cats."
            ),
            "tactics": (
                "Proudhounds abhor deception and other tricks and "
                "will:\n"
                "- Seek a head-to-head fight whenever practical.\n"
                "- Target challenging or skilled warriors first.\n"
                "- Use Canine Pounce to quickly dispatch a weakened "
                "adversary."
            ),
            "indicators": (
                "A wistful howl in the wind, heavy paw prints, "
                "corpses with large slash wounds."
            ),
            "role-playing-notes": (
                "Proudhounds are dignified mercenaries and are "
                "occasionally too honest for such a profession. They "
                "are tremendously loyal, and are unlikely to betray "
                "friends or employers."
            ),
            "customization": (
                "Proudhound breeds also come in Small (Puggoe) and "
                "Large (Bernord) varieties. Each clan is known for "
                "having a different Mighty Combination Weapon as "
                "their signature Packsword. Note, Small Proudhounds "
                "can still use their Packsword without penalty.\n\n"
                "**Reskin (p403):** Proudhounds can be reskinned to "
                "make other animalistic humanoids. Swap out Doggone "
                "Good Sense for aquatic abilities to create toad-men "
                "(Croaks), or swap Canine Pounce for the Big Eater "
                "Quirk (p137) to create pig-men (Porcs)."
            ),
        },
        "actions": [],   # All three abilities are [A]-tagged ([B] for the
                         # purely passive-styled Fearsome Croak per PDF) and
                         # auto-derive where applicable.
        "incomplete": [
            "allegiance: per PDF p402 (Proudhound base) the Croak "
            "Ronin is Unaligned (0/0); scorecard treats 0/0 as "
            "missing but this is the correct value.",
            "abilities: PDF p436 customization keeps Canine Pounce, "
            "but the OCR file and skill addendum substitute Frog "
            "Leap (same Supernatural Leaping mechanic, frog-themed "
            "name).  Using the addendum spelling so the swap "
            "resolves.",
            "notes(habitat,communication,tactics,indicators,"
            "role-playing-notes,customization): no dedicated Croak "
            "Ronin entries in the PDF; copied verbatim from the "
            "Proudhound Sellsword base (p402-403) per reskin "
            "inheritance.",
        ],
    },

    # ------------------------------------------------------------------
    # [6] Proudhound Sellsword -- PDF p402-403.
    # ------------------------------------------------------------------
    "[6] Proudhound Sellsword": {
        "pdf_page":  402,
        "source":    "core-book",
        "rank":      6,
        "tier":      "boss",
        "bio": {
            "name":    "Proudhound Sellsword",
            "subname": "Rank 6 Boss",
            "type":    "Folk [Animal-kin]",
            "size":    "Medium",
            "details": (
                "**Woofing wayfarer.** Proudhounds once belonged to "
                "tightly knit clans, but have dispersed. A few remain "
                "in their ancestral homeland trying to eke out a new "
                "life, or struggling to preserve the old one. Many "
                "have taken to wandering. The Proudhounds seek fame "
                "and fortune to immortalize their lost clans."
            ),
        },
        "stats": {
            "attack_bonus":     4,     # +4 base (+5 with Packsword Master)
            "defense_rating":  16,     # 10 + Heavy Armor (+6)
            "speed":            "average",
            "hearts":           4,
            "hearts_adversary": 4,
            "aptitudes": {
                "might":    10,
                "deftness":  8,        # Rough (-1 Deftness)
                "grit":     12,        # Stalwart (+2 Grit)
                "insight":  11,        # Aware (+1 Insight)
                "aura":      9,
            },
            "allegiance":      {"dark": 0, "bright": 0},   # Unaligned
            "allegiance_area": "neutral",
        },
        "abilities": [
            "Doggone Good Sense [B]",
            "Canine Pounce [A]",
            "Fearsome Growl [B]",
        ],
        "gear": [],
        "notes": {
            "habitat": (
                "Most common around the Pride Coast, their ancestral "
                "homeland, Proudhounds travel far and wide in search "
                "of worthy foes."
            ),
            "combat-gear": (
                "Heavy Armor and a Packsword (Mighty/Master "
                "Combination Weapon)."
            ),
            "communication": (
                "Low Speech and another language related to their "
                "home region. They refuse to learn Hoshi-Ban, the "
                "tongue of cats."
            ),
            "tactics": (
                "Proudhounds abhor deception and other tricks and "
                "will:\n"
                "- Seek a head-to-head fight whenever practical.\n"
                "- Target challenging or skilled warriors first.\n"
                "- Use Canine Pounce to quickly dispatch a weakened "
                "adversary."
            ),
            "indicators": (
                "A wistful howl in the wind, heavy paw prints, "
                "corpses with large slash wounds."
            ),
            "role-playing-notes": (
                "Proudhounds are dignified mercenaries and are "
                "occasionally too honest for such a profession. They "
                "are tremendously loyal, and are unlikely to betray "
                "friends or employers."
            ),
            "customization": (
                "Proudhound breeds also come in Small (Puggoe) and "
                "Large (Bernord) varieties. Each clan is known for "
                "having a different Mighty Combination Weapon as "
                "their signature Packsword. Note, Small Proudhounds "
                "can still use their Packsword without penalty.\n\n"
                "**Reskin (p403):** Proudhounds can be reskinned to "
                "make other animalistic humanoids. Swap out Doggone "
                "Good Sense for aquatic abilities to create toad-men "
                "(Croaks), or swap Canine Pounce for the Big Eater "
                "Quirk (p137) to create pig-men (Porcs)."
            ),
        },
        "actions": [],   # Canine Pounce [A] auto-derives; Doggone Good Sense
                         # [B] and Fearsome Growl [B] are passive per PDF.
        "incomplete": [
            "allegiance: per PDF p402 the Proudhound Sellsword is "
            "Unaligned (0/0); scorecard treats 0/0 as missing but "
            "this is the correct value.",
        ],
    },

    # ------------------------------------------------------------------
    # [7] Urarani -- PDF p426-428.  Colossus Rank 7.
    # ------------------------------------------------------------------
    "[7] Urarani": {
        "pdf_page":  426,
        "source":    "core-book",
        "rank":      7,
        "tier":      "colossus",
        "bio": {
            "name":    "Urarani",
            "subname": "Rank 7 Colossus",
            "type":    "Monster [Aberration]",
            "size":    "Colossal",
            "details": (
                "**The forgotten crystal beast.** A killing machine "
                "from the 1st Aeon made of unbreakable glass. Most of "
                "its kind have been destroyed or withered away in a "
                "reality they find suffocating, but a few have found a "
                "way to remain."
            ),
        },
        "stats": {
            "attack_bonus":     5,
            "defense_rating":  14,     # 10 + Living Nightmare (+6) + Colossal (-2)
            "speed":            "average",
            "hearts":           5,     # Per Strike Point (PDF p426 footnote 1)
            "hearts_adversary": 5,
            "aptitudes": {
                "might":    16,        # Inexorable (+3) + Colossal Species (+2)
                "deftness":  6,        # Writhing (-4)
                "grit":     13,        # Unassailable (+2)
                "insight":  10,
                "aura":     11,
            },
            "allegiance":      {"dark": 2, "bright": 0},
            "allegiance_area": "dark",
        },
        "abilities": [
            "Mountain Of Glass [B]",
            "Arachnid Armament [B]",
            "Living Nightmare [B]",
        ],
        "gear": [],
        "notes": {
            "habitat": (
                "Urarani only intrudes on reality to expel a build up "
                "of painful mana. Urarani appears exclusively in the "
                "Shadowed Lands, perhaps it resembles its original "
                "home."
            ),
            "communication": (
                "Urarani can only communicate in Dream Call, but its "
                "speech is so distorted that it requires an Insight "
                "Check to decipher."
            ),
            "tactics": (
                "Urarani is uninterested in fighting, preferring "
                "instead to mutilate the surroundings. If forced to "
                "fight Urarani will target the strongest first, "
                "hoping the weak will flee so it can continue its "
                "frustrated rampage."
            ),
            "indicators": (
                "A landscape covered in crystalline webs, garbled "
                "cries of lament, the smell of sulphur."
            ),
            "role-playing-notes": (
                "Created and abandoned by the Unshaped, Urarani "
                "loudly laments its own existence. It will bemoan the "
                "loneliness of immortality and extol the virtues of "
                "oblivion but its actions are driven by unbearable "
                "suffering."
            ),
            "customization": (
                "Variants might spray acid or other substances from "
                "their tails and may deal with their suffering in "
                "different ways."
            ),
        },
        # PDF p428 Mountain of Glass [B] and Arachnid Armament [B] are tagged
        # passive but describe named Attacks that cost the Colossus's Turn.
        # Per the strict template's [B]-with-actions rule we expose each
        # named Attack explicitly.
        "actions": [
            {
                "name": "Sweep Attack",
                "subtype": "",
                "description": (
                    "Gooey gossamer can be spewed from the end of "
                    "Urarani's tail, covering large areas in a thick "
                    "crystalline webbing.\n\n"
                    "- The web can spray up to 1 Battlefield Area "
                    "away.\n"
                    "- Everyone within a targeted Battlefield Area "
                    "must make a Deftness Check or be completely "
                    "Restrained (p270) by the web.\n"
                    "- Breaking free requires you, or an ally, to "
                    "use an Action and make a Might Check. Due to "
                    "the web's strength, all Checks suffer a Snag.\n"
                    "- Urarani can also target one of their own "
                    "Strike Points but, due to their size, they are "
                    "immune to the effects."
                ),
            },
            {
                "name": "Repulse Attack",
                "subtype": "",
                "description": (
                    "Urarani is able to blink between The Nihility "
                    "and Outer World at will, and any pests crawling "
                    "along its body will find themselves standing "
                    "on thin air.\n\n"
                    "- Anyone currently resting on one of Urarani's "
                    "Strike Points must make a Grit Check or plummet "
                    "to the ground and are Toppled (p271).\n"
                    "- At the GM's discretion the fallen also take "
                    "Impact Injury damage from the height (see "
                    "Colossal Combat, p264)."
                ),
            },
            {
                "name": "Smash (Pincer)",
                "subtype": "",
                "description": (
                    "On a successful Attack, a pincer does 3 Hearts "
                    "of Damage, and can target you up to 1 "
                    "Battlefield Area away."
                ),
            },
            {
                "name": "Swipe (Tail)",
                "subtype": "",
                "description": (
                    "Urarani's tail can target all foes located on "
                    "one of its Strike Points. On a successful "
                    "Attack, the tail does 2 Hearts of Damage. In "
                    "addition, targets must make a successful Grit "
                    "or Deftness Check or be knocked off Urarani."
                ),
            },
            {
                "name": "Snatch (Pincer)",
                "subtype": "",
                "description": (
                    "On a successful Attack, a pincer grabs and "
                    "fully Restrains (p270) you. You can attempt to "
                    "escape at the beginning of each Turn by making "
                    "a Might Check.\n\n"
                    "- Uranani can Restrain a maximum of two "
                    "enemies at one time."
                ),
            },
            {
                "name": "Crush (Pincer)",
                "subtype": "",
                "description": (
                    "If Urarani has you in its pincers, it can "
                    "crush you and do 2 Hearts of damage without "
                    "requiring an Attack roll."
                ),
            },
            {
                "name": "Throw (Pincer)",
                "subtype": "",
                "description": (
                    "If Urarani has you in its pincers, it can "
                    "throw you at a target up to 2 Battlefield "
                    "Areas away. On a successful Attack, you and "
                    "the target take 1 Heart of Damage and are "
                    "Toppled (p271). On a miss, you land 2 "
                    "Battlefield Areas away (no damage to either)."
                ),
            },
        ],
        "incomplete": [
            "hearts: PDF p426 lists Hearts as '5' Per Strike Point "
            "(footnote 1).  Urarani has 5 Strike Points (Prosoma, "
            "Nightmare Crystal/Core, Chelicerae, Pedipalps, Tail) "
            "with the Core and Tail at 5xx multiplier per Colossal "
            "Combat rules (p435).  The single-value 'hearts' field "
            "represents the per-Strike-Point value; the full "
            "Creature Map is recorded only in the PDF.",
            "notes(combat-gear): PDF p426-427 stat block has no "
            "Gear: line (Urarani is a glass colossus with no "
            "carried items); field intentionally omitted per "
            "strict-no-invention policy.",
            "inventory: Urarani carries no gear (PDF p426 -- it is "
            "a Colossal aberration); structurally N/A.",
        ],
    },

    # ------------------------------------------------------------------
    # [7] Grim Wing -- PDF p386-387.  Massive Mega Boss.
    # ------------------------------------------------------------------
    "[7] Grim Wing": {
        "pdf_page":  386,
        "source":    "core-book",
        "rank":      7,
        "tier":      "mega-boss",
        "bio": {
            "name":    "Grim Wing",
            "subname": "Rank 7 Mega Boss",
            "type":    "Monster [Bio-sorcerous construction]",
            "size":    "Massive",
            "details": (
                "**Murderous skybound tyrant.** Engineered by the lost "
                "Calian empire, Grim Wings are enormous flying beasts "
                "that suffer no natural enemy or predator. They snatch "
                "up livestock, tear apart sky ships, and terrorize "
                "populated areas."
            ),
        },
        "stats": {
            "attack_bonus":     7,
            "defense_rating":  16,     # 10 + Bio-Sorcerous Body (+8) + Massive (-2);
                                       # +2 more (=18) when flying via Speed Bonus
            "speed":            "average",   # Av./Fast (Fast in flight via Skybound Destroyer)
            "hearts":           7,     # 5 base + Sun Blotter (+2)
            "hearts_adversary": 7,
            "aptitudes": {
                "might":    14,        # Monstrous (+1) + Massive Species (+2 per p435) -- net 14
                "deftness": 11,
                "grit":     14,        # Inexorable (+2)
                "insight":   8,        # Heedless (-2)
                "aura":     10,
            },
            "allegiance":      {"dark": 0, "bright": 0},   # Unaligned; Mana Burst grants +1 Bright per use
            "allegiance_area": "neutral",
        },
        "abilities": [
            "Sun Blotter [B]",
            "Bio-Sorcerous Body [B]",
            "Skybound Destroyer [B]",
            "Mana Burst [B]",                # PDF heading shows [L] tag; skill addendum name "Mana Burst"
        ],
        "gear": [],
        "notes": {
            "habitat": (
                "The skies of Outer World. They prefer coastal "
                "regions where they can escape to sea if required."
            ),
            "communication": (
                "Grim Wings cannot speak or understand any language, "
                "but can sense hostility and fear."
            ),
            "tactics": (
                "While violent, Grim Wings are not mindlessly so, "
                "they will:\n"
                "- Create panic with strafing runs.\n"
                "- Isolate and pummel threatening prey with "
                "everything they have.\n"
                "- Retreat if things turn sour."
            ),
            "indicators": (
                "Horrible screeches. A swift shadow passing overhead. "
                "Burning corpses and ruins."
            ),
            "role-playing-notes": (
                "Grim Wings are unnatural creatures, created to be "
                "living weapons for long forgotten wars. They are "
                "only motivated by hunger, destruction, and a strong "
                "survival instinct."
            ),
            "customization": (
                "Other 'models' might be equipped with Mana Blasts "
                "which inflict less damage but cause Ailments like "
                "Petrified or Blinded.\n\n"
                "**Reskin (p387):** Grim Wings can be reskinned as "
                "wyverns or small dragons."
            ),
        },
        # All four abilities are [B]-tagged in the PDF; the action-bearing
        # ones (Sun Blotter, Skybound Destroyer, Mana Burst) need explicit
        # profile actions per the strict template's [B]-with-actions rule.
        "actions": [
            {
                "name": "Sweep Attack (Tail/Wings)",
                "subtype": "",
                "description": (
                    "Tail and wings strike as Arc Weapons (Massive "
                    "Species attack, p435)."
                ),
            },
            {
                "name": "Focus Attack (Jaws/Talons)",
                "subtype": "",
                "description": (
                    "Talons and fangs strike as Mighty Weapons "
                    "(Massive Species attack, p435)."
                ),
            },
            {
                "name": "Swoop Attack (Skybound Destroyer)",
                "subtype": "",
                "description": (
                    "Instead of using its other physical Attacks, "
                    "the Grim Wing can make a claw Attack that does "
                    "3 Hearts of Damage to anyone standing in a "
                    "Battlefield Area it flies through."
                ),
            },
            {
                "name": "Beam (Mana Burst)",
                "subtype": "",
                "description": (
                    "The Attack can target an enemy up to 2 "
                    "Battlefield Areas away. A hit deals 3 Hearts of "
                    "Bright Damage and forces you to make a Might "
                    "Check or be Toppled (p271).\n\n"
                    "Adds 1 Bright Allegiance Point."
                ),
            },
            {
                "name": "Spray (Mana Burst)",
                "subtype": "",
                "description": (
                    "The Grim Wing can target a Battlefield Area up "
                    "to 1 Area away. A single Attack roll is made "
                    "and compared to the Defense Rating of everyone "
                    "in the targeted Area. Those hit suffer 1 Heart "
                    "of Bright Damage.\n\n"
                    "Adds 1 Bright Allegiance Point."
                ),
            },
        ],
        "incomplete": [
            "allegiance: per PDF p386 the Grim Wing is Unaligned "
            "(0/0).  The '1 Bright' shown on the stat box refers to "
            "the per-use Bright Point gained from Mana Burst, not "
            "starting allegiance.  Scorecard treats 0/0 as missing "
            "but this is the correct value.",
            "notes(combat-gear): PDF p386 stat block has no Gear: "
            "line (Grim Wing is a wild bio-sorcerous beast with no "
            "gear); field intentionally omitted per "
            "strict-no-invention policy.",
            "inventory: Grim Wing carries no gear (PDF p386); "
            "structurally N/A.  Yield 'Grim Eyes' only applies "
            "after death.",
        ],
    },

    # ------------------------------------------------------------------
    # [7] Eruptle -- PDF p437 (Example Adversary Creation).
    # Built as a Rank 7 Mega Boss example for a Thunda Sands encounter.
    # No traditional stat-card page; all values derive from the
    # walkthrough on p437 + base Rank 7 row of the Adversary Table p432.
    # ------------------------------------------------------------------
    "[7] Eruptle": {
        "pdf_page":  437,
        "source":    "core-book",
        "rank":      7,
        "tier":      "mega-boss",
        "bio": {
            "name":    "Eruptle",
            "subname": "Rank 7 Mega Boss",
            "type":    "Beast [fabled fiery beast]",
            "size":    "Massive",
            "details": (
                "**Mobile volcano.** A tough Adversary for a "
                "Thunda Sands Map Encounter, built as an example "
                "on PDF p437.  A fabled beast that surfaces "
                "sporadically to deliver a fiery argument with "
                "anyone it deems intruders into its territory."
            ),
        },
        "stats": {
            "attack_bonus":     5,        # Rank 7 Mega Boss base, p432
            "defense_rating":  14,        # 10 base + Obsidian Shell (+4); Massive -2 not applied in example
            "speed":            "slow",   # Obsidian Shell -> Slow on surface;
                                          # Sand Tunneller -> Fast under the surface
            "hearts":           6,        # 5 base + Obsidian Shell (+1)
            "hearts_adversary": 6,
            "aptitudes": {
                "might":    11,           # Primary
                "deftness":  9,           # Secondary 10, Cumbersome (-1)
                "grit":     13,           # Primary 11, Extremely Rugged (+2)
                "insight":  10,           # Secondary
                "aura":     11,           # Primary
            },
            "allegiance":      {"dark": 0, "bright": 0},   # Unaligned per p437 (Lava Breath & Pyroclastic Blast explicitly grant no Allegiance Points)
            "allegiance_area": "neutral",
        },
        "abilities": [
            "Mini Mountain [B]",
            "Blubbery Hide [B]",        # reskinned as 'Obsidian Shell' per PDF p437
            "Sand Tunneler [B]",        # reskinned from Bellzuub's Burrowing Mandibles
            "Lava Breath [A][M]",       # reskinned from Blaster Mage's Magic Big Shot
            "Sand Shifter [A]",         # NEW custom Ability per p437
            "Pyroclastic Blast [A][M]", # reskinned from Murder Princess' Sword Storm
        ],
        "gear": [],
        "notes": {
            "customization": (
                "Built from the Rank 7 Mega Boss row of the "
                "Adversary Table (p432) with the following "
                "customizations (p437):\n"
                "- **Mini Mountain:** new Ability that makes the "
                "Eruptle Massive (p434).\n"
                "- **Obsidian Shell:** reskin of Chompa's Blubbery "
                "Hide (p369).  Makes Eruptle Slow on the surface "
                "and grants +4 to its base Defense Rating and +1 "
                "to its Hearts Total.\n"
                "- **Lava Breath:** reskin of Blaster Mage's Magic "
                "Big Shot (p367).  Non-magical, no Allegiance Point "
                "gained, deals Flame instead of Bright Damage.\n"
                "- **Sand Tunneller:** reskin of Bellzuub's "
                "Insectoid Aspect: Burrowing Mandibles (p423).  "
                "Same Ability except Speed Rating under the surface "
                "will be Fast.\n"
                "- **Pyroclastic Blast:** reskin of Murder "
                "Princess' Sword Storm (p54).  Non-magical, no "
                "Allegiance Point gained, range extended to 2 "
                "Battlefield Areas, deals Flame Damage instead of "
                "Mundane."
            ),
        },
        # Sand Shifter is the only [A]-tagged net-new Ability that
        # needs an explicit profile action (the others are reskins
        # whose mechanics live in the source Ability text).
        "actions": [
            {
                "name": "Sand Shifter",
                "subtype": "",
                "description": (
                    "When under the sand the Eruptle can create a "
                    "ripple across the surface.  Everyone in a "
                    "Battlefield Area the Eruptle has moved "
                    "through must make a Deftness Check or be "
                    "Toppled.  This Ability can be used in "
                    "addition to the monster's allowed Action."
                ),
            },
        ],
        "incomplete": [
            "notes(habitat): PDF p437 example-creation page has no "
            "structured Habitat: line (concept-only entry); "
            "implied 'Thunda Sands desert' but not strict-PDF.",
            "notes(communication): PDF p437 has no Communication: "
            "line.",
            "notes(tactics): PDF p437 has no Tactics: line "
            "(walkthrough is creation-focused, not encounter-focused).",
            "notes(indicators): PDF p437 has no Indicators: line.",
            "notes(role-playing-notes): PDF p437 has no "
            "Role-Playing Notes: line.",
            "notes(combat-gear): PDF p437 has no Gear: line "
            "(Eruptle is a wild beast); field intentionally omitted "
            "per strict-no-invention policy.",
            "inventory: Eruptle carries no gear; structurally N/A.",
            "allegiance: example explicitly notes the two ranged "
            "Abilities grant no Allegiance Points; Unaligned 0/0 "
            "is correct.  Scorecard treats 0/0 as missing but this "
            "is the documented value.",
        ],
    },

    # ------------------------------------------------------------------
    # [8] Shadow Beast -- PDF p412-413.  Massive Aberration Mega Boss.
    # ------------------------------------------------------------------
    "[8] Shadow Beast": {
        "pdf_page":  412,
        "source":    "core-book",
        "rank":      8,
        "tier":      "mega-boss",
        "bio": {
            "name":    "Shadow Beast",
            "subname": "Rank 8 Mega Boss",
            "type":    "Monster [Aberration]",
            "size":    "Massive",
            "details": (
                "**The wrath of the departed.** Shadow Beasts are "
                "born of tragedy.  When a large number of "
                "individuals die during a violent or gruesome "
                "event, it can poison the ambient mana.  This "
                "corrupted mana can coalesce and congeal into a "
                "terrible, destructive mass that lashes out at "
                "everything that moves."
            ),
        },
        "stats": {
            "attack_bonus":     8,
            "defense_rating":  16,     # 10 + Surging Darkness (+6) + Speed Bonus (+2) + Tragic Behemoth/Massive (-2)
            "speed":            "fast",  # Average base + Surging Darkness (+1 level) -> Fast
            "hearts":           7,
            "hearts_adversary": 7,
            "aptitudes": {
                "might":    16,        # Primary 11 + Inexorable (+3) + Massive Species (+2)
                "deftness":  8,        # Secondary 10 + Clumsy (-2)
                "grit":     11,        # Primary
                "insight":   8,        # Secondary 10 + Destructive monomania (-2)
                "aura":     13,        # Primary 11 + Intense (+2)
            },
            "allegiance":      {"dark": 4, "bright": 0},   # Dark Aligned
            "allegiance_area": "dark",
        },
        "abilities": [
            "Tragic Behemoth [B]",
            "Forsaken Shadow [B]",
            "Howls Of The Lost [B]",
            "Surging Darkness [B]",
            "Caustic Miasma [B]",
        ],
        "gear": [],
        "notes": {
            "habitat": (
                "Shadow Beasts are only found in the Wistful Dark "
                "due to the region's high levels of dark mana.  "
                "Reports from the Hollow Queen's Kingdom suggest "
                "they clash with the region's other curious creatures."
            ),
            "communication": (
                "It cannot meaningfully communicate.  The temporary "
                "faces that emerge on its body only wail in "
                "remembrance, and the creature itself thinks only "
                "of destruction."
            ),
            "tactics": (
                "The Beasts are instinctual rather than strategic "
                "and will:\n"
                "- Rely on their Caustic Miasma to clear out weaker "
                "foes, saving their direct attacks for their more "
                "powerful opponents.\n"
                "- Focus on targets that remind them of their tragic "
                "origin.  For example, armored warriors may enrage "
                "a Beast who came into being after the slaughter of "
                "a nomad village by the Knights of the Sacred Chain."
            ),
            "indicators": (
                "Corpses and scenery that have been melted away, "
                "dark mist, terrible cries and moans, an acrid smell."
            ),
            "role-playing-notes": (
                "Shadow Beasts are the personification of suffering "
                "and rage, they are not interested in discourse and "
                "will attack anything that moves.  The howling faces "
                "that move along their surface are individually "
                "comprehensible, even if they only beg or cry.  "
                "Maybe the PCs recognize one of the faces?"
            ),
            "customization": (
                "Replace their Caustic Miasma with an Ability that "
                "is related to the originating event.  For example, "
                "innocents gunned down by mercenaries might create "
                "a Shadow Beast that shoots black spines from "
                "its body."
            ),
        },
        # Tragic Behemoth is [B] but encompasses the Massive Species
        # Sweep/Focus attacks -- add explicit action cards.
        "actions": [
            {
                "name": "Focused Attack (Tragic Behemoth -- bite)",
                "subtype": "",
                "description": (
                    "Bite strikes as a Mighty Weapon (Massive "
                    "Species attack, p435)."
                ),
            },
            {
                "name": "Sweep Attack (Tragic Behemoth -- tail)",
                "subtype": "",
                "description": (
                    "Tail strikes as an Arc Weapon (Massive "
                    "Species attack, p435).\n\n"
                    "Wins all Might Contests unless against "
                    "Supernatural Might."
                ),
            },
        ],
        "incomplete": [
            "notes(combat-gear): PDF p412 stat block has no Gear: "
            "line (Shadow Beasts are amorphous mana entities with "
            "no gear); field intentionally omitted per "
            "strict-no-invention policy.",
            "inventory: Shadow Beast carries no gear (PDF p412); "
            "structurally N/A.",
        ],
    },

    # ------------------------------------------------------------------
    # [9] Giga Gruun -- PDF p384-385.  Massive Mega Boss.
    # ------------------------------------------------------------------
    "[9] Giga Gruun": {
        "pdf_page":  384,
        "source":    "core-book",
        "rank":      9,
        "tier":      "mega-boss",
        "bio": {
            "name":    "Giga Gruun",
            "subname": "Rank 9 Mega Boss",
            "type":    "Monster [Bio-sorcerous construction]",
            "size":    "Massive",
            "details": (
                "**Berserking brute.** Larger and meaner than the "
                "common Gruun, Giga Gruun are living siege weaponry "
                "from the 3rd Aeon.  Without masters, their brutal "
                "yet childlike nature is a danger to anyone they "
                "come across."
            ),
        },
        "stats": {
            "attack_bonus":     9,
            "defense_rating":  14,     # 10 + Giga Hide (+6) + Massive Species (-2)
            "speed":            "average",
            "hearts":           8,     # 7 base + Giga Body/Massive (+1)
            "hearts_adversary": 8,
            "aptitudes": {
                "might":    16,        # Primary 11 + Overpowering (+2) + Massive Species (+2) + (+1 size)
                "deftness": 12,        # Primary
                "grit":     14,        # Primary 11 + Indomitable (+2) + (+1)
                "insight":   7,        # Secondary 10 + Tragically stupid (-3)
                "aura":     11,        # Secondary
            },
            "allegiance":      {"dark": 0, "bright": 0},   # Unaligned per p384
            "allegiance_area": "neutral",
        },
        "abilities": [
            "Giga Body [B]",
            "Giga Hide [B]",          # PDF tag [L]; passive defensive trait
            "Furious Rampage [B]",    # PDF tag [L]; provides +1 Combat Action per Round
        ],
        "gear": [],
        "notes": {
            "habitat": (
                "Giga Gruun distrust the dark so they remain "
                "outdoors in the sunny hemisphere."
            ),
            "communication": (
                "Giga Gruun only understand Low Speech and will "
                "get angry when spoken to in another tongue."
            ),
            "tactics": (
                "Giga Gruun are not smart, but know they are "
                "strong, and will:\n"
                "- Take pleasure in crushing the strongest "
                "opponents first.\n"
                "- Grab and Restrain opponents in their enormous "
                "hands, or toss them out of the Battlefield.\n\n"
                "In spite of all their anger, Giga Gruun are fond "
                "of tiny creatures and will:\n"
                "- Not harm Small PCs or creatures, unless they "
                "are attacking them.\n"
                "- Attempt to claim any surviving tiny folk as "
                "their pets."
            ),
            "indicators": (
                "Broken structures, angry bellowing, massive "
                "footprints."
            ),
            "role-playing-notes": (
                "Violent and emotionally stunted, Giga Gruun are "
                "like malicious children.  While not entirely "
                "unreasonable, they will get aggressive if things "
                "get too complicated for them."
            ),
            "customization": (
                "Some Giga Gruun carry massive weapons that do +1 "
                "Heart of Damage compared to their man-sized "
                "equivalents.\n\n"
                "**Reskin (p385):** Giga Gruun can be reskinned to "
                "represent trolls, ogres, and other giants."
            ),
        },
        # Giga Body [B] embeds the Massive Species Sweep/Focus
        # attacks; Furious Rampage [B] embeds a bonus Combat Action
        # -- both need explicit profile actions per the
        # [B]-with-actions rule.
        "actions": [
            {
                "name": "Sweep Attack (Giga Body -- flailing arms/tusks)",
                "subtype": "",
                "description": (
                    "Flailing arms or tusks strike as Arc Weapons "
                    "(Massive Species attack, p435)."
                ),
            },
            {
                "name": "Focus Attack (Giga Body -- stomps/headbutts)",
                "subtype": "",
                "description": (
                    "Stomps and headbutts strike as Mighty Weapons "
                    "(Massive Species attack, p435)."
                ),
            },
            {
                "name": "Bonus Combat Action (Furious Rampage)",
                "subtype": "",
                "description": (
                    "In addition to its other permitted Actions, "
                    "the Giga Gruun can make a bonus Combat Action "
                    "(p254)."
                ),
            },
        ],
        "incomplete": [
            "notes(combat-gear): PDF p384 stat block has no Gear: "
            "line (Giga Gruun is a wild bio-sorcerous construct "
            "with no gear); field intentionally omitted per "
            "strict-no-invention policy.  See Customization for the "
            "optional 'massive weapons' variant.",
            "inventory: Giga Gruun carries no gear (PDF p384); "
            "structurally N/A.  Yield 'Berserker Hide' / 'Fury "
            "Gland' only apply after death.",
            "allegiance: Unaligned per PDF p384.  Scorecard treats "
            "0/0 as missing but this is the documented value.",
        ],
    },

    # ==================================================================
    # Demon, Blighted variants -- PDF p372-373.
    # Single stat block (Mook Rank 0) with 5 Malignant Gift sub-types
    # rolled on a 1d20 (Signs of the Beast / Mocking Beauty / Winter's
    # Shackles / Revolting Excess / Caustic Spittle).
    # All five share base atk/hp/apts/notes; DR differs only for
    # Revolting Excess (+2 -> 14).
    # ==================================================================

    "Demon - Blighted Beast": {
        "pdf_page":  372,
        "source":    "core-book",
        "rank":      0,
        "tier":      "mook",
        "bio": {
            "name":    "Demon, Blighted -- Signs of the Beast",
            "subname": "Rank 0 Mook",
            "type":    "Monster [Demon]",
            "size":    "Medium",
            "details": (
                "**Those taken by darkness.** Demons were ordinary "
                "folk who've been warped by contact with Shadow "
                "Blight, a potent strain of Dark Mana.  They "
                "remember little of their old lives and exist only "
                "with a compulsion to spread the Blight.\n\n"
                "Malignant Gift roll **1-4: Signs of the Beast.**  "
                "The Demon has large, exaggerated natural weapons.  "
                "Unarmed Attacks strike as a Mighty Weapon."
            ),
        },
        "stats": {
            "attack_bonus":     0,
            "defense_rating":  12,     # 10 base + Numb to Pain (+2 from Consumed By Darkness)
            "speed":            "average",
            "hearts":           1,
            "hearts_adversary": 1,
            "aptitudes": {
                "might":    6,         # Primary
                "deftness": 6,         # Secondary
                "grit":     8,         # Primary 6 + Unrelenting (+2)
                "insight":  5,         # Secondary 6 + Dulled (-1)
                "aura":     6,         # Primary
            },
            "allegiance":      {"dark": 6, "bright": 0},   # Dark Aligned
            "allegiance_area": "dark",
        },
        "abilities": [
            "Consumed By Darkness [B]",
            "Shadow Blight Host [B]",
            "Signs of the Beast [B]",  # Malignant Gift
        ],
        "gear": ["Remnants of a previous life"],
        "notes": {
            "habitat": (
                "Found where the sun doesn't shine: the Wistful "
                "Dark, or the Buried Kingdom."
            ),
            "communication": (
                "Dark Tongue, they might reluctantly use Low Speech."
            ),
            "tactics": (
                "Spreading the Blight is a demon's primary goal, "
                "they will:\n"
                "- Die in droves attempting to infect a "
                "significant individual.\n"
                "- Target the Bright Aligned (p206), they are the "
                "most offensive."
            ),
            "indicators": (
                "The cry of obscenities in Dark Tongue, the "
                "shuffling of the misshapen, a trail of violent "
                "revelry."
            ),
            "role-playing-notes": (
                "Their primary impulse is to spread the Blight, "
                "acting like cruel children who find joy in the "
                "misery of others."
            ),
            "combat-gear": "Remnants of a previous life.",
            "customization": (
                "Invent alternative Malignant Gifts.  For example, "
                "add the power to inflict a Status Ailment, or "
                "modify their natural weapon type (e.g a Lash "
                "Tongue).\n\n"
                "**Reskin (p374):** To create an Ascended Demon, "
                "a rare individual who manages to retain their "
                "knowledge and Abilities after contracting the "
                "Blight, make a Rank 5 Character and replace their "
                "Innate Species Abilities with Consumed By "
                "Darkness, Shadow Blight Host, and Malignant Gift."
            ),
        },
        "incomplete": [
            "inventory: 'Remnants of a previous life' (PDF p372 "
            "Gear: line) is a flavor descriptor, not a specific "
            "named item; combat-gear note carries the text but "
            "inventory remains empty per strict-no-invention policy.",
        ],
    },

    "Demon - Mocking Beauty": {
        "pdf_page":  372,
        "source":    "core-book",
        "rank":      0,
        "tier":      "mook",
        "bio": {
            "name":    "Demon, Blighted -- Mocking Beauty",
            "subname": "Rank 0 Mook",
            "type":    "Monster [Demon]",
            "size":    "Medium",
            "details": (
                "**Those taken by darkness.** Demons were ordinary "
                "folk who've been warped by contact with Shadow "
                "Blight, a potent strain of Dark Mana.\n\n"
                "Malignant Gift roll **5-8: Mocking Beauty.**  "
                "The Demon possesses a haunting innocence.  A "
                "Grit Check is required to harm or hinder them.  "
                "Failing the Check momentarily mesmerizes their "
                "attacker, who misses their next Turn."
            ),
        },
        "stats": {
            "attack_bonus":     0,
            "defense_rating":  12,
            "speed":            "average",
            "hearts":           1,
            "hearts_adversary": 1,
            "aptitudes": {
                "might": 6, "deftness": 6, "grit": 8,
                "insight": 5, "aura": 6,
            },
            "allegiance":      {"dark": 6, "bright": 0},
            "allegiance_area": "dark",
        },
        "abilities": [
            "Consumed By Darkness [B]",
            "Shadow Blight Host [B]",
            "Mocking Beauty [B]",
        ],
        "gear": ["Remnants of a previous life"],
        "notes": {
            "habitat": (
                "Found where the sun doesn't shine: the Wistful "
                "Dark, or the Buried Kingdom."
            ),
            "communication": (
                "Dark Tongue, they might reluctantly use Low Speech."
            ),
            "tactics": (
                "Spreading the Blight is a demon's primary goal, "
                "they will:\n"
                "- Die in droves attempting to infect a "
                "significant individual.\n"
                "- Target the Bright Aligned (p206), they are the "
                "most offensive."
            ),
            "indicators": (
                "The cry of obscenities in Dark Tongue, the "
                "shuffling of the misshapen, a trail of violent "
                "revelry."
            ),
            "role-playing-notes": (
                "Their primary impulse is to spread the Blight, "
                "acting like cruel children who find joy in the "
                "misery of others."
            ),
            "combat-gear": "Remnants of a previous life.",
            "customization": (
                "Invent alternative Malignant Gifts.  For example, "
                "add the power to inflict a Status Ailment, or "
                "modify their natural weapon type (e.g a Lash "
                "Tongue).\n\n"
                "**Reskin (p374):** To create an Ascended Demon, "
                "make a Rank 5 Character and replace their Innate "
                "Species Abilities with Consumed By Darkness, "
                "Shadow Blight Host, and Malignant Gift."
            ),
        },
        "incomplete": [
            "inventory: 'Remnants of a previous life' is a flavor "
            "descriptor; no specific named items per "
            "strict-no-invention policy.",
        ],
    },

    "Demon - Winter's Shackles": {
        "pdf_page":  372,
        "source":    "core-book",
        "rank":      0,
        "tier":      "mook",
        "bio": {
            "name":    "Demon, Blighted -- Winter's Shackles",
            "subname": "Rank 0 Mook",
            "type":    "Monster [Demon]",
            "size":    "Medium",
            "details": (
                "**Those taken by darkness.** Demons were ordinary "
                "folk who've been warped by contact with Shadow "
                "Blight, a potent strain of Dark Mana.\n\n"
                "Malignant Gift roll **9-12: Winter's Shackles.**  "
                "The Demon's body is so cold that contact results "
                "in frostbite.  Unarmed Attacks do +1 Heart of "
                "Frost Damage."
            ),
        },
        "stats": {
            "attack_bonus":     0,
            "defense_rating":  12,
            "speed":            "average",
            "hearts":           1,
            "hearts_adversary": 1,
            "aptitudes": {
                "might": 6, "deftness": 6, "grit": 8,
                "insight": 5, "aura": 6,
            },
            "allegiance":      {"dark": 6, "bright": 0},
            "allegiance_area": "dark",
        },
        "abilities": [
            "Consumed By Darkness [B]",
            "Shadow Blight Host [B]",
            "Winter's Shackles [B]",
        ],
        "gear": ["Remnants of a previous life"],
        "notes": {
            "habitat": (
                "Found where the sun doesn't shine: the Wistful "
                "Dark, or the Buried Kingdom."
            ),
            "communication": (
                "Dark Tongue, they might reluctantly use Low Speech."
            ),
            "tactics": (
                "Spreading the Blight is a demon's primary goal, "
                "they will:\n"
                "- Die in droves attempting to infect a "
                "significant individual.\n"
                "- Target the Bright Aligned (p206), they are the "
                "most offensive."
            ),
            "indicators": (
                "The cry of obscenities in Dark Tongue, the "
                "shuffling of the misshapen, a trail of violent "
                "revelry."
            ),
            "role-playing-notes": (
                "Their primary impulse is to spread the Blight, "
                "acting like cruel children who find joy in the "
                "misery of others."
            ),
            "combat-gear": "Remnants of a previous life.",
            "customization": (
                "Invent alternative Malignant Gifts.  For example, "
                "add the power to inflict a Status Ailment, or "
                "modify their natural weapon type (e.g a Lash "
                "Tongue).\n\n"
                "**Reskin (p374):** To create an Ascended Demon, "
                "make a Rank 5 Character and replace their Innate "
                "Species Abilities with Consumed By Darkness, "
                "Shadow Blight Host, and Malignant Gift."
            ),
        },
        "incomplete": [
            "inventory: 'Remnants of a previous life' is a flavor "
            "descriptor; no specific named items per "
            "strict-no-invention policy.",
        ],
    },

    "Demon - Revolting Excess": {
        "pdf_page":  372,
        "source":    "core-book",
        "rank":      0,
        "tier":      "mook",
        "bio": {
            "name":    "Demon, Blighted -- Revolting Excess",
            "subname": "Rank 0 Mook",
            "type":    "Monster [Demon]",
            "size":    "Medium",
            "details": (
                "**Those taken by darkness.** Demons were ordinary "
                "folk who've been warped by contact with Shadow "
                "Blight, a potent strain of Dark Mana.\n\n"
                "Malignant Gift roll **13-16: Revolting Excess.**  "
                "The demon's flesh has become tumorous and "
                "ponderously thick, they gain +2 Defense Rating."
            ),
        },
        "stats": {
            "attack_bonus":     0,
            "defense_rating":  14,     # base 12 + Revolting Excess (+2)
            "speed":            "average",
            "hearts":           1,
            "hearts_adversary": 1,
            "aptitudes": {
                "might": 6, "deftness": 6, "grit": 8,
                "insight": 5, "aura": 6,
            },
            "allegiance":      {"dark": 6, "bright": 0},
            "allegiance_area": "dark",
        },
        "abilities": [
            "Consumed By Darkness [B]",
            "Shadow Blight Host [B]",
            "Revolting Excess [B]",
        ],
        "gear": ["Remnants of a previous life"],
        "notes": {
            "habitat": (
                "Found where the sun doesn't shine: the Wistful "
                "Dark, or the Buried Kingdom."
            ),
            "communication": (
                "Dark Tongue, they might reluctantly use Low Speech."
            ),
            "tactics": (
                "Spreading the Blight is a demon's primary goal, "
                "they will:\n"
                "- Die in droves attempting to infect a "
                "significant individual.\n"
                "- Target the Bright Aligned (p206), they are the "
                "most offensive."
            ),
            "indicators": (
                "The cry of obscenities in Dark Tongue, the "
                "shuffling of the misshapen, a trail of violent "
                "revelry."
            ),
            "role-playing-notes": (
                "Their primary impulse is to spread the Blight, "
                "acting like cruel children who find joy in the "
                "misery of others."
            ),
            "combat-gear": "Remnants of a previous life.",
            "customization": (
                "Invent alternative Malignant Gifts.  For example, "
                "add the power to inflict a Status Ailment, or "
                "modify their natural weapon type (e.g a Lash "
                "Tongue).\n\n"
                "**Reskin (p374):** To create an Ascended Demon, "
                "make a Rank 5 Character and replace their Innate "
                "Species Abilities with Consumed By Darkness, "
                "Shadow Blight Host, and Malignant Gift."
            ),
        },
        "incomplete": [
            "inventory: 'Remnants of a previous life' is a flavor "
            "descriptor; no specific named items per "
            "strict-no-invention policy.",
        ],
    },

    "Demon - Caustic Spittle": {
        "pdf_page":  372,
        "source":    "core-book",
        "rank":      0,
        "tier":      "mook",
        "bio": {
            "name":    "Demon, Blighted -- Caustic Spittle",
            "subname": "Rank 0 Mook",
            "type":    "Monster [Demon]",
            "size":    "Medium",
            "details": (
                "**Those taken by darkness.** Demons were ordinary "
                "folk who've been warped by contact with Shadow "
                "Blight, a potent strain of Dark Mana.\n\n"
                "Malignant Gift roll **17-20: Caustic Spittle.**  "
                "The demon may spit acidic bile which strikes "
                "like a Thrown Weapon."
            ),
        },
        "stats": {
            "attack_bonus":     0,
            "defense_rating":  12,
            "speed":            "average",
            "hearts":           1,
            "hearts_adversary": 1,
            "aptitudes": {
                "might": 6, "deftness": 6, "grit": 8,
                "insight": 5, "aura": 6,
            },
            "allegiance":      {"dark": 6, "bright": 0},
            "allegiance_area": "dark",
        },
        "abilities": [
            "Consumed By Darkness [B]",
            "Shadow Blight Host [B]",
            "Caustic Spittle [B]",
        ],
        "gear": ["Remnants of a previous life"],
        "notes": {
            "habitat": (
                "Found where the sun doesn't shine: the Wistful "
                "Dark, or the Buried Kingdom."
            ),
            "communication": (
                "Dark Tongue, they might reluctantly use Low Speech."
            ),
            "tactics": (
                "Spreading the Blight is a demon's primary goal, "
                "they will:\n"
                "- Die in droves attempting to infect a "
                "significant individual.\n"
                "- Target the Bright Aligned (p206), they are the "
                "most offensive."
            ),
            "indicators": (
                "The cry of obscenities in Dark Tongue, the "
                "shuffling of the misshapen, a trail of violent "
                "revelry."
            ),
            "role-playing-notes": (
                "Their primary impulse is to spread the Blight, "
                "acting like cruel children who find joy in the "
                "misery of others."
            ),
            "combat-gear": "Remnants of a previous life.",
            "customization": (
                "Invent alternative Malignant Gifts.  For example, "
                "add the power to inflict a Status Ailment, or "
                "modify their natural weapon type (e.g a Lash "
                "Tongue).\n\n"
                "**Reskin (p374):** To create an Ascended Demon, "
                "make a Rank 5 Character and replace their Innate "
                "Species Abilities with Consumed By Darkness, "
                "Shadow Blight Host, and Malignant Gift."
            ),
        },
        "incomplete": [
            "inventory: 'Remnants of a previous life' is a flavor "
            "descriptor; no specific named items per "
            "strict-no-invention policy.",
        ],
    },

    # ==================================================================
    # Unranked Core Monsters
    # ==================================================================

    # ------------------------------------------------------------------
    # Skelemen (Skeleman) -- PDF p404-405.  Mook Rank 0.
    # ------------------------------------------------------------------
    "Skelemen": {
        "pdf_page":  404,
        "source":    "core-book",
        "rank":      0,
        "tier":      "mook",
        "bio": {
            "name":    "Skeleman",
            "subname": "Rank 0 Mook",
            "type":    "Monster [Undead]",
            "size":    "Medium",
            "details": (
                "**Vainglorious bones.** Skelemen are the "
                "reanimated remains of the greedy or the "
                "criminally ambitious.  Death is not the end for "
                "the excessively conniving."
            ),
        },
        "stats": {
            "attack_bonus":     0,
            "defense_rating":  10,    # base; Quick Weapon footnote raises to 11
            "speed":            "average",
            "hearts":           1,
            "hearts_adversary": 1,
            "aptitudes": {
                "might":    6,
                "deftness": 7,        # Primary 6 + Sneaky (+1)
                "grit":     5,        # Secondary 6 + Brittle (-1)
                "insight":  6,        # Primary
                "aura":     7,        # Primary 6 + Scary (+1)
            },
            "allegiance":      {"dark": 2, "bright": 0},
            "allegiance_area": "dark",
        },
        "abilities": [
            "Living Dead [B]",
            "Pull Yourself Together [B]",
        ],
        "gear": ["Standard or Quick Weapon (ravaged by time)"],
        "notes": {
            "habitat": (
                "Old roads, tunnels or ruins where they can "
                "ambush passers-by."
            ),
            "communication": (
                "They cannot speak, so use mime and gesticulation "
                "instead.  They understand Low Speech and any "
                "other languages they knew in their previous lives."
            ),
            "tactics": (
                "They target the unsuspecting or solitary, "
                "working as a group to ambush or distract.  "
                "They will:\n"
                "- Pretend to be normal corpses then suddenly "
                "spring into action at an opportune moment.\n"
                "- Defend fallen allies in order to give them "
                "time to Self-Assemble.\n"
                "- Try to take a hostage, to later carefully "
                "remove their eyes and tongue, for use in their "
                "transition into Skelemasters (p406)."
            ),
            "indicators": (
                "The sound of clacking bones, corpses with eyes "
                "and tongues removed, fresh blood on discarded "
                "weapons."
            ),
            "role-playing-notes": (
                "Prone to insulting or dramatic gestures.  Amused "
                "by their own brilliance."
            ),
            "combat-gear": (
                "Armed with a Standard or Quick Weapon that's "
                "ravaged by time."
            ),
            "customization": (
                "Increase the threat by equipping them with "
                "better weapons or armor.  Skelemen could also be "
                "made from the bones of Large or Small Species "
                "(p106).\n\n"
                "**Reskin (p405):** Skelemen can be reskinned as "
                "enchanted dolls or robotic creatures that "
                "possess a primitive self-assembly function."
            ),
        },
        "incomplete": [
            "inventory: PDF p404 Gear: line lists a generic "
            "'Standard or Quick Weapon (ravaged by time)' as a "
            "type-choice rather than a specific named item; "
            "combat-gear note carries the text but inventory "
            "remains empty per strict-no-invention policy.",
        ],
    },

    # ------------------------------------------------------------------
    # Mange Bandit -- PDF p400-401.  Mook Rank 0.
    # ------------------------------------------------------------------
    "Mange Bandit": {
        "pdf_page":  400,
        "source":    "core-book",
        "rank":      0,
        "tier":      "mook",
        "bio": {
            "name":    "Mange Bandit",
            "subname": "Rank 0 Mook",
            "type":    "Folk [Animal-kin / Mundymutt]",
            "size":    "Medium",
            "details": (
                "**Ruff neck miscreant.** Outcasts banished from "
                "their pack for heinous crimes.  The exile extends "
                "to their offspring, resulting in the formation "
                "of bandit packs."
            ),
        },
        "stats": {
            "attack_bonus":     0,
            "defense_rating":  14,    # 10 + Light Armor (+2) + Speed Bonus (+2);
                                      # Stray's Step (+1 level) shown in footnote 2
            "speed":            "fast",
            "hearts":           1,
            "hearts_adversary": 1,
            "aptitudes": {
                "might":    6,
                "deftness": 7,        # Primary 6 + Quick paws (+1)
                "grit":     6,        # Primary
                "insight":  7,        # Primary 6 + Good nose (+1)
                "aura":     5,        # Secondary 6 + Yappy (-1)
            },
            "allegiance":      {"dark": 0, "bright": 0},   # Unaligned
            "allegiance_area": "neutral",
        },
        "abilities": [
            "Doggone Good Sense [B]",
            "Strays Step [B]",        # PDF spelling "Stray's Step"; addendum drops apostrophe
        ],
        "gear": [
            "Light Armor",
            "Standard Weapon",
            "Thrown Weapons",
        ],
        "notes": {
            "habitat": (
                "These strays have spread from the Pride Coast, "
                "their ancestral homeland, in search of coin."
            ),
            "communication": (
                "Low Speech and another language related to their "
                "home region.  They refuse to learn Hoshi-Ban, "
                "the tongue of cats."
            ),
            "tactics": (
                "Mange are cowardly combatants and will:\n"
                "- Use ambush techniques.\n"
                "- Use ranged attacks when they are low in number.\n"
                "- Will only engage in melee if they are confident "
                "of the win."
            ),
            "indicators": (
                "Gnawed sticks, the sound of growling and howling, "
                "corpses with throwing knives in their backs."
            ),
            "role-playing-notes": (
                "Packs consist of varied personalities.  "
                "Universally pragmatic and ruthless, most have a "
                "strong sense of loyalty to the pack and feel "
                "they are in it together, surviving in a cruel "
                "world."
            ),
            "combat-gear": (
                "Light Armor, a Standard Weapon, and some "
                "Thrown Weapons."
            ),
            "customization": (
                "Senior Mange Bandits might know Raider (p35) or "
                "Sneak (p23) Elective Abilities.\n\n"
                "**Reskin (p401):** Replace Doggone Good Sense "
                "with another set of Species Abilities to make a "
                "swift footed bandit."
            ),
        },
        "incomplete": [
            "inventory: PDF p400 Gear: line lists generic gear "
            "type-choices (Light Armor / Standard Weapon / Thrown "
            "Weapons) rather than specific named items; combat-gear "
            "note carries the verbatim text but inventory remains "
            "empty per strict-no-invention policy.",
        ],
    },

    # ------------------------------------------------------------------
    # Lalka, Breeze -- PDF p392-393.  Mook Rank 0, Tiny Construct.
    # Two variants on the same stat block (Breeze + Mud); only the
    # Elemental Vex and Arcane Beleaguerment effects differ.
    # ------------------------------------------------------------------
    "Lalka - Breeze": {
        "pdf_page":  392,
        "source":    "core-book",
        "rank":      0,
        "tier":      "mook",
        "bio": {
            "name":    "Lalka, Breeze",
            "subname": "Rank 0 Mook",
            "type":    "Construct [Elemental]",
            "size":    "Tiny",
            "details": (
                "**Exasperating little homunculus.** Lalka are "
                "small, doll-like elementals whose sole purpose "
                "is to harass and waylay the enemies of their "
                "creator.\n\n"
                "**Breeze Lalka** are servants formed from the "
                "wind and breath."
            ),
        },
        "stats": {
            "attack_bonus":     0,
            "defense_rating":  13,    # 10 + Mischievous Miniscule/Tiny (+3)
            "speed":            "average",
            "hearts":           1,
            "hearts_adversary": 1,
            "aptitudes": {
                "might":    6,
                "deftness": 8,        # Primary 6 + Nimble (+2)
                "grit":     4,        # Secondary 6 + Flakey (-2)
                "insight":  6,        # Primary
                "aura":     7,        # Primary 6 + Innately magical (+1)
            },
            "allegiance":      {"dark": 1, "bright": 1},   # Twilight Aligned
            "allegiance_area": "twilight",
        },
        "abilities": [
            "Mischievous Minuscule [B]",
            "Elemental Vex [B]",
            "Arcane Beleaguerment [B][M]",
        ],
        "gear": [],   # Tiny species can't carry or use gear (p434)
        "notes": {
            "habitat": (
                "Lalka are never too far from their Lalka Jar, "
                "the pot or container in which they were created. "
                " A jar may be positioned to protect a specific "
                "location or carried around by their master.  If "
                "freed, Lalka gravitate to locations related to "
                "their type.  Breeze Lalka settle in windy valleys "
                "and caves, while Mud Lalka enjoy swamps and "
                "river banks."
            ),
            "communication": (
                "Lalka are able to speak and understand Low "
                "Speech.  They tend to have squeaky voices."
            ),
            "tactics": (
                "Self-preservation is not a factor when "
                "confronting foes, they:\n"
                "- Use Elemental Vex for hit and run attacks to "
                "weaken or distract foes.\n"
                "- Use Attack Assists to help their masters and "
                "employ Arcane Beleaguerment at key moments."
            ),
            "indicators": (
                "Overturned pots and furniture, poorly timed "
                "pranks and other signs of childish mischief."
            ),
            "role-playing-notes": (
                "Lalka have simple thoughts.  They are belligerent "
                "and difficult with everyone except their master "
                "or fellow Lalka.  Lalka are happy to hurl insults "
                "at you but can't sustain any meaningful dialog."
            ),
            "customization": (
                "More powerful Lalka can reform after using "
                "Arcane Beleaguerment or have additional hexes "
                "like Mortifying Bloat (p61) or Hocus Pox (p62).\n\n"
                "**Reskin (p393):** Create Lalka related to "
                "different elements by re-theming their Abilities."
            ),
        },
        "incomplete": [
            "notes(combat-gear): PDF p392 stat block has no Gear: "
            "line (Tiny Species can't carry or use gear per p434); "
            "field intentionally omitted per strict-no-invention "
            "policy.",
            "inventory: Breeze Lalka carries no gear; structurally "
            "N/A per Tiny Species rules.",
        ],
    },

    # ------------------------------------------------------------------
    # Lalka, Mud -- PDF p392-393.  Same stat block as Breeze Lalka;
    # variant differs only in Elemental Vex (mud sling, Thrown Weapon)
    # and Arcane Beleaguerment (Deft vs. Might or be Petrified).
    # ------------------------------------------------------------------
    "Lalka - Mud": {
        "pdf_page":  392,
        "source":    "core-book",
        "rank":      0,
        "tier":      "mook",
        "bio": {
            "name":    "Lalka, Mud",
            "subname": "Rank 0 Mook",
            "type":    "Construct [Elemental]",
            "size":    "Tiny",
            "details": (
                "**Exasperating little homunculus.** Lalka are "
                "small, doll-like elementals whose sole purpose "
                "is to harass and waylay the enemies of their "
                "creator.\n\n"
                "**Mud Lalka** are created from blood and earth."
            ),
        },
        "stats": {
            "attack_bonus":     0,
            "defense_rating":  13,
            "speed":            "average",
            "hearts":           1,
            "hearts_adversary": 1,
            "aptitudes": {
                "might": 6, "deftness": 8, "grit": 4,
                "insight": 6, "aura": 7,
            },
            "allegiance":      {"dark": 1, "bright": 1},
            "allegiance_area": "twilight",
        },
        "abilities": [
            "Mischievous Minuscule [B]",
            "Elemental Vex [B]",
            "Arcane Beleaguerment [B][M]",
        ],
        "gear": [],
        "notes": {
            "habitat": (
                "Lalka are never too far from their Lalka Jar.  "
                "If freed, Mud Lalka enjoy swamps and river banks."
            ),
            "communication": (
                "Lalka are able to speak and understand Low "
                "Speech.  They tend to have squeaky voices."
            ),
            "tactics": (
                "Self-preservation is not a factor when "
                "confronting foes, they:\n"
                "- Use Elemental Vex for hit and run attacks to "
                "weaken or distract foes.\n"
                "- Use Attack Assists to help their masters and "
                "employ Arcane Beleaguerment at key moments."
            ),
            "indicators": (
                "Overturned pots and furniture, poorly timed "
                "pranks and other signs of childish mischief."
            ),
            "role-playing-notes": (
                "Lalka have simple thoughts.  They are belligerent "
                "and difficult with everyone except their master "
                "or fellow Lalka.  Lalka are happy to hurl insults "
                "at you but can't sustain any meaningful dialog."
            ),
            "customization": (
                "More powerful Lalka can reform after using "
                "Arcane Beleaguerment or have additional hexes "
                "like Mortifying Bloat (p61) or Hocus Pox (p62).\n\n"
                "**Reskin (p393):** Create Lalka related to "
                "different elements by re-theming their Abilities."
            ),
        },
        "incomplete": [
            "notes(combat-gear): PDF p392 stat block has no Gear: "
            "line (Tiny Species can't carry or use gear per p434); "
            "field intentionally omitted per strict-no-invention "
            "policy.",
            "inventory: Mud Lalka carries no gear; structurally "
            "N/A per Tiny Species rules.",
        ],
    },

    # ==================================================================
    # PHASE 2 -- Blog-post-sourced adversaries
    # ==================================================================

    # ------------------------------------------------------------------
    # Funguy -- Blog post "Freebie: FUNGUY and MUSHDOOM (Adversaries)"
    # Blog post id: 2944141604627972362
    # Mushroom Menace, Rank 0 Mook.
    # ------------------------------------------------------------------
    "Funguy": {
        "pdf_page":  0,        # N/A -- blog source
        "source":    "blog",
        "blog_post": "2944141604627972362",
        "rank":      0,
        "tier":      "mook",
        "bio": {
            "name":    "Funguy",
            "subname": "Rank 0 Mook",
            "type":    "Folk [Plant-kin]",
            "size":    "Small",
            "details": (
                "**Mushroom Menace.** Funguy are an eccentric species "
                "of walking, talking toadstools. Thanks to a habit of "
                "keeping to themselves and a tendency towards "
                "ruthlessly expunging outsiders, very little is known "
                "about them."
            ),
        },
        "stats": {
            "attack_bonus":     0,
            "defense_rating":   13,    # blog footnote: Size, Fist of the Fungus
            "speed":            "average",   # blog: Normal
            "hearts":           1,
            "hearts_adversary": 1,
            "aptitudes": {
                "might":    5,
                "deftness": 7,
                "grit":     6,
                "insight":  8,    # Primary + Excitable (+2 Insight)
                "aura":     5,    # Secondary + Excitable (-1 Aura)
            },
            "allegiance":      {"dark": 1, "bright": 0},
            "allegiance_area": "unaligned",   # blog: "Dark: 1 (No Allegiance)"
        },
        "abilities": [
            "Tiny Toadstool",
            "Telepathy Spores",
            "Fist of the Fungus",
        ],
        "gear": [],   # blog Yield: "Funguy don't tend to carry much around"
        "notes": {
            "habitat": (
                "Funguys have a preference for cold, wet places. "
                "Their favored region is the Wistful Dark (particularly "
                "the Murk) but they can also be found in thick forests "
                "or dank caves throughout the Outer World."
            ),
            "communication": (
                "Funguys are usually only capable of communicating "
                "with their Telepathy Spores, which can be a real "
                "hindrance. They utilize the signed component of low "
                "speech use when dealing with other species in a pinch."
            ),
            "tactics": (
                "Funguy generally weaponise their Spores against "
                "shaky or easily confused foes. Combined efforts and "
                "assault assists are favored when fighting against "
                "stronger adversaries."
            ),
            "indicators": (
                "A disconcerting amount of mushrooms, the sounds of "
                "very organized shuffling, a strange odor."
            ),
            "role-playing-notes": (
                "Funguys find the strange physical excesses and "
                "constant babbling of other humanoids to be nearly "
                "intolerable. They are generally pretty grumpy "
                "dealing with them as a result.\n\n"
                "While there is the occasional Funguy who is curious "
                "about non-mushroom forms of sentient life, they are "
                "considered oddballs by their fellows."
            ),
            "customization": (
                "Some Funguys learn Dark Aligned Sage Abilities. "
                "They have distinctly purple mushroom caps.\n\n"
                "**Reskin (blog \"FUNGUY and MUSHDOOM\"):** With a "
                "little work and adjustment on their fiction, Funguys "
                "could be used to represent a recently stranded "
                "species of psychic alien creatures."
            ),
        },
        "actions": [   # All three abilities are [B]-tagged in the skills
                       # bundle so the action-deriver skips them; inject
                       # explicit cards so VTT shows the rules text.
            {
                "name": "Tiny Toadstool",
                "subtype": "",
                "description": (
                    "*Funguy aren't particularly tall, barely waist "
                    "level to the average human (and this is even "
                    "with their mushroom caps).*\n\n"
                    "- Funguys are Small (already calculated into "
                    "this entry's stats).\n"
                    "- Funguys breathe and eat by absorbing liquids "
                    "and organic matter into their body along with "
                    "air. Consumables (such as potions or magical "
                    "food) still affect them like they would another "
                    "applicable creature, it just looks really odd.\n"
                    "- Funguys can also consume spoiled or unprepared "
                    "organic material as Rations."
                ),
            },
            {
                "name": "Telepathy Spores",
                "subtype": "",
                "description": (
                    "*Funguy do not speak in any conventional way; "
                    "they instead communicate by passing thoughts "
                    "to and from their spores.*\n\n"
                    "- A Funguy may take a Turn to release their "
                    "Telepathic Spores in the Area they currently "
                    "occupy. All Funguy in this Area can mentally "
                    "communicate for the remainder of the conflict.\n"
                    "- Any non-Funguy in the Area must make a Grit "
                    "Check.\n"
                    "  - **Failure:** Disoriented for the remainder "
                    "of the conflict.\n"
                    "  - **Success:** They can understand the "
                    "Funguy's thoughts and even communicate "
                    "telepathically. They get an Edge on any further "
                    "Grit Checks called by this Ability.\n"
                    "- Spores can be blown or washed away at the "
                    "GM's discretion, ending the effect immediately.\n"
                    "- Further use of this Ability on the same "
                    "targets within the same conflict has no effect, "
                    "unless the spores were blown or washed away.\n"
                    "- Synthetic Creatures (such as Bio-Mechanoids) "
                    "are entirely immune to this Ability.\n"
                    "- Out of combat, the effect lasts a few minutes."
                ),
            },
            {
                "name": "Fist of the Fungus",
                "subtype": "",
                "description": (
                    "*Most Funguy are well versed in a strange "
                    "martial art that takes advantage of their small "
                    "size and flexibility.*\n\n"
                    "- The Funguy makes Unarmed Attacks as if "
                    "wielding a Quick Weapon."
                ),
            },
        ],
        "incomplete": [
            "notes(combat-gear): blog has no Gear: line; Yield says "
            "Funguy don't carry much. Field intentionally omitted "
            "per strict-no-invention policy.",
            "inventory: Funguy carries no gear; structurally N/A.",
        ],
    },

    # ------------------------------------------------------------------
    # [5] Mushdoom -- Blog post "Freebie: FUNGUY and MUSHDOOM (Adversaries)"
    # Blog post id: 2944141604627972362
    # Titanic Toadstool, Rank 5 Boss.  Big brother to Funguy.
    # ------------------------------------------------------------------
    "[5] Mushdoom": {
        "pdf_page":  0,        # N/A -- blog source
        "source":    "blog",
        "blog_post": "2944141604627972362",
        "rank":      5,
        "tier":      "boss",
        "bio": {
            "name":    "Mushdoom",
            "subname": "Rank 5 Boss",
            "type":    "Folk [Plant-kin]",
            "size":    "Large",
            "details": (
                "**Titanic Toadstool.** Occasionally a Funguy will "
                "get a little too angry or self-important and build "
                "up enough bluster to cause them to grow in size and "
                "strength. The resulting mass of belligerence and "
                "saprophytic muscle is known as a Mushdoom, and they "
                "have a dangerous tendency to rile up and lead their "
                "more docile brethren."
            ),
        },
        "stats": {
            "attack_bonus":     4,
            "defense_rating":  13,    # blog footnote: Size, Not so Tiny Toadstool
            "speed":            "average",   # blog: Normal
            "hearts":           4,
            "hearts_adversary": 4,
            "aptitudes": {
                "might":   13,    # Primary + Overbearing (+2 Might)
                "deftness": 7,    # Secondary + Oafish (-2 Deftness)
                "grit":    12,    # Primary + Stubborn (+2 Grit)
                "insight":  9,    # Secondary
                "aura":    10,    # Primary
            },
            "allegiance":      {"dark": 1, "bright": 0},
            "allegiance_area": "unaligned",   # blog: "Dark: 1 (No Allegiance)"
        },
        "abilities": [
            "Not so Tiny Toadstool",
            "Telepathic Spores",
            "Fist of the Fungus MkII",
        ],
        "gear": [],   # blog Yield: "Mushdooms don't generally carry around much"
        "notes": {
            "habitat": (
                "Mushdooms most often live among large groups of "
                "Funguys, though they are a little more likely than "
                "their smaller brethren to encroach on land "
                "inhabited by other sentient creatures."
            ),
            "communication": (
                "Mushdooms are limited in their communication in the "
                "same ways that Funguys are. They will order "
                "subordinates to relay any messages they have to "
                "members of other species in their stead."
            ),
            "tactics": (
                "Mushdooms like to bully and overwhelm opponents. A "
                "favored trick is to knock over an enemy with their "
                "punch and then have Funguy minions swarm them for a "
                "pin or a finish."
            ),
            "indicators": (
                "Air thick with inert telepathic spores, enormous "
                "circular footprints in the ground, emboldened and "
                "aggressive groups of funguys in the area."
            ),
            "role-playing-notes": (
                "Mushdooms are nasty bullies at their core. Even if "
                "not communicating directly with someone, they loom "
                "with aggressive body language and open hostility. "
                "Naturally, if something noticeably bigger or "
                "stronger confronts them they quickly revert to "
                "meeker habits."
            ),
            "customization": (
                "Mushdooms take well to certain Champion Abilities, "
                "having the appropriate amount of strength if lacking "
                "in true courage.\n\n"
                "**Reskin (blog \"FUNGUY and MUSHDOOM\"):** Like "
                "Funguys, the Mushdoom can be reworked to be a "
                "strange, telepathic alien -- just a larger, much "
                "punchier one."
            ),
        },
        "actions": [   # Auto-derivation skips these: Toadstool/Spores have no
                       # active verbs, and Fist of the Fungus MkII says
                       # "as if wielding a Mighty Weapon" (the "wielding"
                       # token breaks WEAPON_REF_RE).  Inject explicitly.
            {
                "name": "Not so Tiny Toadstool",
                "subtype": "",
                "description": (
                    "*An overgrown, belligerent Funguy. This Ability "
                    "is identical to the Funguy's Tiny Toadstool, "
                    "with the following exceptions:*\n\n"
                    "- The Mushdoom is Large and has Supernatural "
                    "Might.\n"
                    "- The Mushdoom's body is oddly tough; they are "
                    "considered to be wearing Medium Armor.\n"
                    "- (All already calculated into this entry's "
                    "stats.)"
                ),
            },
            {
                "name": "Telepathic Spores",
                "subtype": "",
                "description": (
                    "*Identical to the Funguy Ability of the same "
                    "name, with the following exception:*\n\n"
                    "- The range of the Mushdoom's Spores is the "
                    "Area the Mushdoom is currently in **as well as** "
                    "any other Areas adjacent to them, excluding any "
                    "that represent things where the spores would be "
                    "unlikely to travel (places much higher than the "
                    "rest of the battlefield, areas in or under "
                    "water, etc.)."
                ),
            },
            {
                "name": "Fist of the Fungus MkII",
                "subtype": "",
                "description": (
                    "*Mushdooms eschew the swift fighting style of "
                    "their smaller brethren in favor of raw "
                    "brutality.*\n\n"
                    "- The Mushdoom makes Unarmed Attacks as if "
                    "wielding a Mighty Weapon.\n"
                    "- Anyone of normal size or smaller struck by "
                    "the Mushdoom must succeed on a Grit Check or "
                    "become Toppled."
                ),
            },
        ],
        "incomplete": [
            "notes(combat-gear): blog has no Gear: line; Yield says "
            "Mushdooms don't carry much. Field intentionally omitted "
            "per strict-no-invention policy.",
            "inventory: Mushdoom carries no gear; structurally N/A.",
        ],
    },

    # ------------------------------------------------------------------
    # [6] Ocularion -- Blog post "Freebie: Ocularion (Adversary)"
    # Blog post id: 7697882867965533352
    # "The melting ordeal of being perceived" -- floating eyeball homunculus.
    # ------------------------------------------------------------------
    "[6] Ocularion": {
        "pdf_page":  0,        # N/A -- blog source
        "source":    "blog",
        "blog_post": "7697882867965533352",
        "rank":      6,
        "tier":      "boss",
        "bio": {
            "name":    "Ocularion",
            "subname": "Rank 6 Boss",
            "type":    "Monster [Homunculus]",
            "size":    "Medium",
            "details": (
                "**The melting ordeal of being perceived.** These "
                "strange flying eyeballs are theorized to be the "
                "result of ancient Calian bio-sorcery. Unsettling "
                "due to their odd vestigial claws and unceasing "
                "gaze, Ocularions are often found skulking around "
                "old ruins or in a symbiotic partnership with other "
                "monsters or magic users."
            ),
        },
        "stats": {
            "attack_bonus":     4,
            "defense_rating":  14,    # blog: natural Fleshwarped Form DR 14
            "speed":            "slow",
            "hearts":           4,
            "hearts_adversary": 4,
            "aptitudes": {
                "might":    9,    # Secondary
                "deftness": 10,   # Primary
                "grit":     7,    # Secondary + Fragile (-2 Grit)
                "insight":  12,   # Primary + Observant (+2 Insight)
                "aura":     11,   # Primary + Mesmerizing (+1 Aura)
            },
            "allegiance":      {"dark": 3, "bright": 1},
            "allegiance_area": "dark",
        },
        "abilities": [
            "Fleshwarped Form",
            "Floating Eye",
            "Liquifying Gaze",
            "Shared Sight",
        ],
        "gear": [],   # blog Yield: only a harvested Deliquescing Iris
                      # (post-defeat crafting material), no carried gear
        "notes": {
            "habitat": (
                "Ocularions are most common in the Wistful Dark, "
                "but have managed to find themselves all over the "
                "Outer World."
            ),
            "communication": (
                "Ocularions communicate through a form of telepathy "
                "that involves sending messages in Dark Tongue "
                "through the flow of mana. They understand the "
                "spoken and signed components of that language as "
                "well."
            ),
            "tactics": (
                "Ocularions avoid direct combat whenever they can, "
                "often opting to try and keep away from an enemy "
                "and incapacitate or eliminate them with their "
                "melting gaze. Multiple Ocularions will often all "
                "use this ability on the same area at once for a "
                "truly devastating coordinated attack.\n\n"
                "They also tend to take advantage of their ability "
                "to float, trying to keep an Area or so above their "
                "targets or trying to escape via maneuverability if "
                "things aren't going their way."
            ),
            "indicators": (
                "The unnerving feeling of being watched, the sound "
                "of something slowly cutting through the air, glop "
                "that may have vaguely humanoid features."
            ),
            "role-playing-notes": (
                "Ocularions are intelligent, observant, and curious "
                "but also have little understanding of social "
                "niceties and come off as cold and blunt in the best "
                "of situations. They may be merciful to those "
                "willing to converse with them."
            ),
            "customization": (
                "There are almost certainly other variants of the "
                "Ocularion whose gaze causes dangerous versions of "
                "other status ailments.\n\n"
                "**Reskin (blog \"Ocularion\"):** The Ocularion's "
                "gaze attack could be given to other creatures to "
                "represent things like breath weapons or hexes that "
                "target a wide area.  Per the blog author's note, "
                "upping it to Rank 8 Mega-Boss with a legendary "
                "ability that fires multiple status-ailment beams "
                "per Round (and replacing Shared Sight with "
                "something justifying a higher Defense Rating) "
                "produces a closer homage to the inspiration "
                "creature."
            ),
        },
        "actions": [   # Inject explicit cards: Fleshwarped Form / Floating Eye
                       # are [B]-tagged (deriver skips them); Liquifying Gaze
                       # / Shared Sight are [A][M] but their descriptions
                       # don't reliably trip the active-verb regex.
            {
                "name": "Fleshwarped Form",
                "subtype": "",
                "description": (
                    "*Ocularions are homunculi created by ancient "
                    "magic and their physical forms reflect this. "
                    "Their \"bodies\" are enormous eyeballs about "
                    "the size of an average human's torso, with "
                    "four sharp claws jutting out at different "
                    "points in its circumference.*\n\n"
                    "- Ocularions have surprisingly sturdy bodies, "
                    "granting them a natural Defense Rating of 14.\n"
                    "- They do not need to eat or breathe, "
                    "sustaining themselves by absorbing mana.\n"
                    "- They can manipulate and grasp objects with "
                    "their claws like other humanoids, though "
                    "certain actions may be easier or more "
                    "difficult thanks to their odd spherical shape.\n"
                    "- Their claws strike as Standard Weapons."
                ),
            },
            {
                "name": "Floating Eye",
                "subtype": "",
                "description": (
                    "*Thanks to the arcane nature of their body, "
                    "Ocularions move through a limited version of "
                    "levitation.*\n\n"
                    "- Ocularions are able to hover through the air.\n"
                    "- While they have a Speed Rating of Slow, they "
                    "are able to avoid effects related to walking "
                    "or crawling along the ground (such as the "
                    "Perilous Battlefield Condition) and gain other "
                    "advantages of being able to float."
                ),
            },
            {
                "name": "Liquifying Gaze",
                "subtype": "",
                "description": (
                    "*The Ocularion's most feared power is its "
                    "oppressive glare, which has the ability to "
                    "desolidify objects and individuals alike.*\n\n"
                    "**Versus a creature:**\n"
                    "- Target an Area up to 2 Areas away with the "
                    "Ocularion's gaze. Takes an Action.\n"
                    "- Prompts a Contest between the Ocularion's "
                    "Insight and the Grit of each individual in the "
                    "targeted Area.\n"
                    "- On a win against a target, they are afflicted "
                    "with the **Jellyfied** Status Ailment for one "
                    "hour unless otherwise dispelled.\n"
                    "- If a Jellyfied target is subject to this "
                    "Ability again, they automatically take 1 Heart "
                    "of damage. If reduced to 0 or less Hearts this "
                    "way, they melt completely into formless sludge "
                    "and are physically destroyed.\n\n"
                    "**Versus an object (sundering):**\n"
                    "- Each Turn spent gazing on the object reduces "
                    "its Hearts by 1.\n"
                    "- Hearts lost this way are restored after an "
                    "hour if the object is not destroyed.\n"
                    "- This Ability can melt even magical materials, "
                    "so it's considered very powerful."
                ),
            },
            {
                "name": "Shared Sight",
                "subtype": "",
                "description": (
                    "*Ocularions have the curious ability to "
                    "telepathically bond with more powerful "
                    "entities, allowing their ally to see what they "
                    "see. It is theorized that they were created to "
                    "be scouts and guardians for practitioners of "
                    "dark magic.*\n\n"
                    "- Ocularions may bond with individuals that "
                    "have at least one Point of Dark Allegiance. "
                    "Both parties must agree; the bond is "
                    "established instantly and may be canceled at "
                    "any time by either side.\n"
                    "- An Ocularion may only bond with one "
                    "individual, but said individual may bond with "
                    "multiple Ocularions without hindrance.\n"
                    "- Bonded individuals can communicate with the "
                    "Ocularion telepathically regardless of "
                    "distance, and see whatever the Ocularion sees "
                    "at any given moment.\n"
                    "- Either side of the bond knows if the other "
                    "is unconscious or killed."
                ),
            },
        ],
        "incomplete": [
            "notes(combat-gear): blog has no Gear: line (Yield is a "
            "post-defeat crafting harvest only). Field intentionally "
            "omitted per strict-no-invention policy.",
            "inventory: Ocularion carries no gear; structurally N/A.",
        ],
    },

    # ------------------------------------------------------------------
    # [8] Varubali -- Blog post "Ennies Update and Freebie: Varubali,
    # the Wicked Guardian (Adversary)"
    # Blog post id: 4253908469976567
    # Mega-Boss Rank 8 Celestial Order / Divine Beast.
    # ------------------------------------------------------------------
    "[8] Varubali": {
        "pdf_page":  0,        # N/A -- blog source
        "source":    "blog",
        "blog_post": "4253908469976567",
        "rank":      8,
        "tier":      "mega-boss",
        "bio": {
            "name":    "Varubali",
            "subname": "Rank 8 Mega-Boss",
            "type":    "Celestial Order [Divine Beast]",
            "size":    "Massive",
            "details": (
                "**The Wicked Guardian.** A divine beast created to "
                "oversee the eternal suffering of a disgraced god, "
                "Varubali guards a temple located on a remote island "
                "in the Galvanus Archipelago. Cruel to the extreme, "
                "he refuses to allow anyone to attend to his long "
                "suffering charge -- even though their punishment "
                "has spanned aeons at this point.\n\n"
                "Varubali is an armored, crawling creature with "
                "sword-like claws and a bladed tail. His physical "
                "presence and aura are so intense that it strikes "
                "unnatural fear in those less powerful than him."
            ),
        },
        "stats": {
            "attack_bonus":     8,    # Mega-Boss: Atk = Rank
            "defense_rating":  14,    # 16 Heavy-Armor natural - 2 Massive
            "speed":            "average",   # blog: Normal
            "hearts":           6,    # 5 base + 1 from Divine Behemoth
            "hearts_adversary": 6,
            "aptitudes": {
                "might":   15,    # Primary + Deadly (+2 Might)
                "deftness": 7,    # Secondary + Graceless (-3 Deftness)
                "grit":    11,    # Primary
                "insight":  10,   # Secondary
                "aura":     13,   # Primary + Overwhelming (+2 Aura)
            },
            "allegiance":      {"dark": 0, "bright": 3},
            "allegiance_area": "bright",
        },
        "abilities": [
            "Divine Behemoth",
            "Fearsome Aura",
            "Retributive Claw",
            "Breath of Frost and Flame",
            "Lightning Blast",
        ],
        "gear": [],   # blog Yield: only a harvested Frost-Flame Amethyst
                      # (post-defeat crafting material), no carried gear
        "notes": {
            "habitat": (
                "The Temple of the Poisoned God, located on a small "
                "island close to the City of Portia."
            ),
            "communication": (
                "Varubali can communicate and comprehend Low Speech "
                "and Bright Speech, but greatly prefers the latter."
            ),
            "tactics": (
                "Varubali is a vicious combatant. If anyone afflicted "
                "with the Terrified ailment by his aura doesn't run, "
                "he'll try to pick them off first. He will open "
                "battles with his breath weapon when possible, "
                "hoping to weaken the enemy as a group and then draw "
                "them in to wear them down with his retributive "
                "strikes. If he can identify a particularly powerful "
                "opponent (or one that annoys him) he'll target them "
                "with his lightning attack in hopes of finishing "
                "them off quickly."
            ),
            "indicators": (
                "Bodies that have been charred or frozen solid, a "
                "low rumbling sound, two glowing eyes with a gem "
                "between them in the distance."
            ),
            "role-playing-notes": (
                "Varubali revels in his duty and insists upon it in "
                "spite of the fact that the Divine Ruler who created "
                "him for the task is long gone. Some theorize he "
                "simply cannot envision any other life for himself "
                "due to his nature as a Divine Beast, but Varubali "
                "himself would insist that was nonsense. For all "
                "his wickedness, Varubali will not attack anyone "
                "not attempting to enter the Temple of the Poisoned "
                "God -- in fact, he'll engage in polite conversation "
                "with them if they don't retreat from his presence. "
                "Similarly, he has no interest in pursuing those "
                "that flee him, lest they draw him away from his "
                "task."
            ),
            "customization": (
                "Varubali could be used to represent a type of "
                "temple guardian rather than a singular entity. "
                "Other versions may do variant types of damage, "
                "inflict Status Ailments with their breath weapon, "
                "or have some other sort of divine gift.\n\n"
                "**Reskin (blog \"Varubali, the Wicked Guardian\"):** "
                "Varubali could be given an ability that grants him "
                "Synthetic qualities rather than Divine/Infernal "
                "ones, and used to represent a sort of automated "
                "war machine."
            ),
        },
        "actions": [   # All five abilities need explicit cards: Divine
                       # Behemoth/Fearsome Aura are passive/aura, and the
                       # [A]/[L] active ones don't reliably trip the
                       # active-verb regex.
            {
                "name": "Divine Behemoth",
                "subtype": "",
                "description": (
                    "*Large even for a Divine Beast, Varubali "
                    "towers over even the largest of folk and most "
                    "other monsters. He relishes this advantage.*\n\n"
                    "- Varubali is **Massive** (per page 434 of the "
                    "BREAK!! Rulebook).\n"
                    "- **Sweep Attack:** Bladed Tail strikes as an "
                    "Arc Weapon.\n"
                    "- **Crush Attack:** Claws strike as a Mighty "
                    "Weapon.\n"
                    "- Varubali's armored body has a Natural Defense "
                    "of 16 like Heavy Armor (reduced to 14 due to "
                    "Massive size) and grants him an additional "
                    "Heart.\n"
                    "- (All already calculated into this entry's "
                    "stats.)"
                ),
            },
            {
                "name": "Fearsome Aura",
                "subtype": "",
                "description": (
                    "*Perceiving Varubali and hearing his echoing "
                    "voice fills the heart with dread and a feeling "
                    "that it is against the will of the divine to "
                    "oppose him.*\n\n"
                    "- Anyone encountering Varubali enters a Contest "
                    "between his Aura and their Grit. On a Fail, "
                    "they are inflicted with the **Terrified** "
                    "Status Ailment.\n"
                    "- This Ability does not work against "
                    "individuals who are equal to Varubali's Rank "
                    "or higher."
                ),
            },
            {
                "name": "Retributive Claw",
                "subtype": "",
                "description": (
                    "*To strike Varubali is to defy his divinely "
                    "ordained task, and prompts him to swift, "
                    "furious retribution.*\n\n"
                    "- Varubali may attack any individual who "
                    "successfully strikes him in melee. This may be "
                    "a Sweep or a Strike, per his Massive Size.\n"
                    "- These Attacks are **in addition** to any "
                    "Actions Varubali takes in the round."
                ),
            },
            {
                "name": "Breath of Frost and Flame",
                "subtype": "",
                "description": (
                    "*Gifted access to a summer's gale and a "
                    "winter's wind by his divine creator, Varubali "
                    "can call forth either in a torrent of fire or "
                    "ice that can decimate those who dare oppose "
                    "him.*\n\n"
                    "- Varubali may spew a breath weapon with an "
                    "Attack Roll up to 2 Areas away. The attack "
                    "hits the entire Area and does **2 Hearts** of "
                    "Damage to anyone successfully hit.\n"
                    "- The Breath Weapon may do Flame or Frost "
                    "damage as Varubali wishes.\n"
                    "- **Cooldown:** Once used, Varubali cannot use "
                    "this Ability for 2 more Turns."
                ),
            },
            {
                "name": "Lightning Blast",
                "subtype": "",
                "description": (
                    "*When truly pressed, the divine behemoth may "
                    "draw from the power of his long banished "
                    "creator to strike down a foe with thunderous "
                    "fury.*\n\n"
                    "- Varubali may target an individual up to 3 "
                    "Areas away with a burst of holy lightning.\n"
                    "- Requires a successful Attack Roll and does "
                    "**3 Hearts** of Damage on a hit.\n"
                    "- **Cooldown:** May only be used once a fight."
                ),
            },
        ],
        "incomplete": [
            "notes(combat-gear): blog has no Gear: line (Yield is a "
            "post-defeat Frost-Flame Amethyst crafting harvest only). "
            "Field intentionally omitted per strict-no-invention "
            "policy.",
            "inventory: Varubali carries no gear; structurally N/A.",
        ],
    },

    # ------------------------------------------------------------------
    # [4] Lug -- Blog post "Adversary Templates: LUG and LANK (Freebie)"
    # Blog post id: 3072228726992976447
    # Rank 4 Boss adversary TEMPLATE -- "a violent oaf"; designed to
    # be reskinned for any "big bully" the GM needs.  Per the blog
    # the only mandatory ability is Champion's Brazen Defense; the
    # other abilities ("Brute", "As Tough as the Look", reskinned
    # Passion's Fire / Frost Blade) are GM-pick suggestions, so they
    # are documented in customization rather than baked into stats.
    # ------------------------------------------------------------------
    "[4] Lug": {
        "pdf_page":  0,        # N/A -- blog source
        "source":    "blog",
        "blog_post": "3072228726992976447",
        "rank":      4,
        "tier":      "boss",
        "bio": {
            "name":    "Lug",
            "subname": "Rank 4 Boss",
            "type":    "Folk [Variable]",   # blog: Type Main/Sub -> Variable
            "size":    "Large",
            "details": (
                "**A violent oaf.** Use this template when you need "
                "some hired muscle, a lumbering threat, or a big "
                "bully."
            ),
        },
        "stats": {
            "attack_bonus":     3,
            "defense_rating":  14,    # blog: +4 Brazen Defense, +1 Standard
                                      # Shield, -1 Large
            "speed":            "average",   # blog: Normal
            "hearts":           3,
            "hearts_adversary": 3,
            "aptitudes": {
                "might":   12,    # Primary + Big/Strong (+2 Might)
                "deftness": 9,    # Primary
                "grit":    11,    # Primary + Dense (+2 Grit)
                "insight":  6,    # Secondary + Oafish (-2 Insight)
                "aura":     7,    # Secondary + Oafish (-1 Aura)
            },
            "allegiance":      {"dark": 0, "bright": 0},   # blog: Variable
            "allegiance_area": "unaligned",
        },
        "abilities": [
            "Brazen Defense",   # blog: "Lugs always have ... Brazen Defense"
        ],
        "gear": [],   # blog gear is a "choose one" between Mighty/Arc
                      # (Crescent Maul) or Mighty/Lash (Chain Flail) plus
                      # a Standard Shield; encoded in combat-gear note,
                      # not invented into inventory
        "notes": {
            "habitat": (
                "Variable -- the Lug is an adversary template. Per "
                "the blog example, a Lug repurposed as a Knight of "
                "the Sacred Chain would have a Home Region in the "
                "Wistful Dark."
            ),
            "combat-gear": (
                "A Mighty/Arc (Crescent Maul) or Mighty/Lash (Chain "
                "Flail) combination weapon.\n\n"
                "Standard Shield."
            ),
            "communication": (
                "Low Speech, Variable."
            ),
            "tactics": (
                "Variable, but Lugs are usually bullies at heart, "
                "using their attacks to try and take down weaker "
                "members of a group to help thin out their numbers."
            ),
            "indicators": (
                "Foes that have been crushed by mighty blows, angry "
                "stomping, the occasional guffaw."
            ),
            "role-playing-notes": (
                "Lugs are single-minded as a rule. Even the smartest "
                "among them would rather be ruthlessly direct than "
                "employ any amount of etiquette or finesse."
            ),
            "customization": (
                "Besides the Abilities you choose for them, you "
                "might give a Lug some sort of imbued weapon or "
                "shield. You can also increase their rank to make "
                "them a more difficult opponent.\n\n"
                "Lugs always have the Champion's **Brazen Defense** "
                "elective ability, which gives them an improved "
                "defense. This can be replaced with the Chompa's "
                "**Blubbery Hide** ability to make a more overtly "
                "monstrous Lug.\n\n"
                "As a Rank 4 Adversary, Lugs should have 2-4 "
                "Abilities total. The Champion's **Brute**, the "
                "Gruun's **As Tough as the Look** make for good "
                "choices. The Battle Princess's **Passion's Fire** "
                "or the Murder Princess's **Frost Blade** could be "
                "reskinned to represent different forms of elemental "
                "attacks for them as well.\n\n"
                "**Reskin (blog \"LUG and LANK\"):** You can change "
                "a lot based on what Abilities you give a Lug. For "
                "example, mechanical Lugs can be created by giving "
                "them Abilities from Drones."
            ),
        },
        "actions": [],   # Brazen Defense is [S]-passive; no derived
                         # action expected.  GM-pick abilities are not
                         # baked in here (see customization note).
        "incomplete": [
            "inventory: blog combat-gear is a 'choose one' between "
            "Mighty/Arc (Crescent Maul) and Mighty/Lash (Chain "
            "Flail) plus a Standard Shield; picking one would be "
            "invention per strict-no-invention policy.  GM populates "
            "the inventory at play time.",
        ],
    },

    # ------------------------------------------------------------------
    # [4] Lank -- Blog post "Adversary Templates: LUG and LANK (Freebie)"
    # Blog post id: 3072228726992976447
    # Rank 4 Boss adversary TEMPLATE -- "a scrawny troublemaker";
    # speedy trickster / cackling toady.  Mandatory abilities:
    # Bulwark of Disdain (Murder Princess) + Stray's Step (Mange
    # Bandit).  Optional abilities are GM-pick (see customization).
    # ------------------------------------------------------------------
    "[4] Lank": {
        "pdf_page":  0,        # N/A -- blog source
        "source":    "blog",
        "blog_post": "3072228726992976447",
        "rank":      4,
        "tier":      "boss",
        "bio": {
            "name":    "Lank",
            "subname": "Rank 4 Boss",
            "type":    "Folk [Variable]",
            "size":    "Medium",
            "details": (
                "**A scrawny troublemaker.** Use this template when "
                "you need a speedy trickster or cackling toady."
            ),
        },
        "stats": {
            "attack_bonus":     3,
            "defense_rating":  16,    # blog: +4 Bulwark of Disdain,
                                      # +2 Fast
            "speed":            "fast",
            "hearts":           3,
            "hearts_adversary": 3,
            "aptitudes": {
                "might":    9,    # Primary
                "deftness": 11,   # Primary + Wiry (+2 Deftness)
                "grit":     6,    # Secondary + Frail (-2 Grit)
                "insight":  11,   # Primary + Clever (+2 Insight)
                "aura":      7,   # Secondary + Annoying (-1 Aura)
            },
            "allegiance":      {"dark": 0, "bright": 0},
            "allegiance_area": "unaligned",
        },
        "abilities": [
            "Bulwark of Disdain",   # blog: "Lanks always have ... "
            "Stray's Step",         # blog: "... and Stray's Step"
        ],
        "gear": [],   # blog gear is a "choose one" between Master/Arc
                      # and Master/Drawn combination weapons; encoded in
                      # combat-gear note, not invented into inventory
        "notes": {
            "habitat": (
                "Variable -- the Lank is an adversary template."
            ),
            "combat-gear": (
                "A Master/Arc or Master/Drawn Combination Weapon.\n\n"
                "10 units of Ammunition if the latter is chosen."
            ),
            "communication": (
                "Low Speech, Variable."
            ),
            "tactics": (
                "Variable, but Lanks generally like to use hit and "
                "run tactics to annoy and harry their foes rather "
                "than face them head on."
            ),
            "indicators": (
                "Foes struck down by multiple wounds, annoying "
                "cackling, the sound of someone shuffling about "
                "impatiently."
            ),
            "role-playing-notes": (
                "Lanks are nearly always petty and cruel. They will "
                "not miss a chance at a rude wisecrack or "
                "mean-spirited gesture."
            ),
            "customization": (
                "Besides the Abilities you choose for them, you "
                "might give a Lank some sort of imbued weapon or "
                "special ammunition. You can also increase their "
                "rank to make them a more difficult opponent.\n\n"
                "Lanks always have the Murder Princess's **Bulwark "
                "of Disdain** and Mange Bandit's **Stray's Step** "
                "Abilities, granting them a higher defense and "
                "making them Fast.\n\n"
                "As a Rank 4 Adversary, Lanks should have 2-4 "
                "Abilities total. The Raider's **Free Runner** and "
                "the Sneak's **Flanker** are good choices for them. "
                "You might also give them some Sage Abilities like "
                "**Hocus Pox** or **Eldritch Explosives** if you "
                "want them to be troublesome warrior-mages.\n\n"
                "**Reskin (blog \"LUG and LANK\"):** You can change "
                "a lot based on what Abilities you give a Lank. For "
                "example, giving them some of the Insectoid Aspects "
                "that Bellzuub has access to is a great way to "
                "create a bipedal bug warrior."
            ),
        },
        "actions": [],   # Bulwark of Disdain / Stray's Step are passive
                         # ([S]/[B]); no derived actions expected.
        "incomplete": [
            "inventory: blog combat-gear is a 'choose one' between "
            "Master/Arc and Master/Drawn combination weapons; "
            "picking one would be invention per strict-no-invention "
            "policy.  GM populates the inventory at play time.",
            "actions: both base-template abilities (Bulwark of "
            "Disdain, Stray's Step) are passive defensive/speed "
            "bonuses with no clickable action; GM-pick combat "
            "abilities will populate actions at play time.",
        ],
    },
}
