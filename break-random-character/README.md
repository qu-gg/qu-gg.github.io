# BREAK!! Random Character

A static, browser-only rank 1 character roller for BREAK!! RPG. The tool follows
the six-step procedure in the Core Rules and is intentionally isolated from the
rest of the site until it is ready to be linked publicly.

## Current scope

- Roll 1-12 characters and replace the previous results.
- Optionally use the official 2026 Expanded Content Calling and Species tables.
  Purr is rerolled; Henshin Hero, Balladeer, and all eight linked Calling
  variants are supported.
- Expanded Species include Hoppalong, Gadabovid, Mundymutt, Neridian, and
  Unterkin. Added Species use the confirmed Inheritor Quirk route except
  Unterkin, whose source defines its own Physiology/Eldritch route.
- Neridians use an even standard/undersea origin split. Mundymutt sizes are
  evenly weighted. Unterkin use their fixed Homeland, unique Histories, and
  compatible core/variant Calling families.
- Roll Calling, Species, Homeland, History, Traits, Quirk, and starting Coins.
- Add a species-matched name from the official BREAK!! Random Name Tables post.
- Apply Calling, Species Size, Species, Trait, and Quirk value adjustments.
- Label Species Size contributions to Aptitudes, Defense, and base Inventory
  Slots alongside other modifier provenance.
- Display Inventory relative to the Medium Species baseline of 10 Slots:
  Small Species `-2`, Large Species `+2`. Factotum Pack adds `+8`; Dwarf Sturdy
  adds `+2`. Scribe does not receive the Pack bonus because Journey Journal
  replaces Factotum Pack.
- Roll an appropriate core Gift for each complete 3 Bright or Dark Allegiance
  Points and mark each earned Gift beneath Allegiance.
- Neridian's fixed Melodious Voice Gift references the core Dark Gifts table on
  p. 207 and remains separate from Gifts earned at Allegiance thresholds.
- Resolve bounded creation choices, including blade forms and materials, Soul
  Companions, Dark Gifts, Prodigy Abilities, and relevant nested Quirk choices.
- Select two distinct options from each History's Starting Gear.
- Add the universal Functional Outfit and unresolved Standard Weapon.
- Mark combat gear restricted by the Calling and/or final Species Size, with
  the relevant allowance page. Restricted gear remains in the rolled result.
- Apply the highest selected Armor and Shield Defense bonuses to Defense Rating
  and label each modifier with its gear source.
- Show only names, generated values, and Core Rules page references.
- Show Blog links on expanded Calling, Species, History, and Starting Ability
  records. Resolved choices omit repetitive Blog suffixes while retaining core
  page references.
- Reroll individual random components while preserving unrelated results and
  rebuilding dependent values, gear restrictions, and modifiers.
- Use the `Copy Image` button on a card to copy it to the system clipboard as a
  PNG. Normal browser right-click behavior remains available.

The official post does not provide a separate Dimensional Stray name table, so
Dimensional Strays currently use the Native Human table. An Elf result that says
to use another chart follows the post's weighted Random Name Table and resolves
to a concrete name.

Expanded Species use the example names published with their posts as equal
name pools. Mundymutt names are a small project-provided pool pending an
official random name table.

Card subtitles use `Native Human` and `Dimensional Stray Human` for readability;
the canonical Species labels remain unchanged in the detailed field. The local
`BreakBanner.webp` masthead art is credited to
[Levi Lagoon](https://levilagoon.carrd.co/). Expanded table data links to the
official 2026 Expanded Roll Tables post.

The initial version does not select the physical form of the universal Standard
Weapon and does not spend Starting Coins. Those belong in a later gear phase.

Some choices have no finite rules table and depend on the character concept or
party. These are marked `Player-defined` or `Team-dependent` rather than being
filled from an unofficial table. Examples include a Soul Link target, Guardian
ward, Peculiar Taste nourishment, and Sneezles allergen.

## Card interactions

- Click a rerollable value or its circular-arrow control to replace that result.
- Calling rerolls rebuild base values, Starting Abilities, Calling-owned
  choices, and gear restrictions while preserving Species choices.
- Species rerolls also rebuild the name, size, Homeland/History when required,
  Quirk, Species Abilities, modifiers, and gear restrictions.
- Homeland rerolls rebuild its language, mapped History, History gear,
  restrictions, and defensive gear bonuses.
- History rerolls preserve languages and unrelated Calling, Species, and Quirk
  choices while rebuilding History gear and its dependent values.
- Language rerolls stay within the current Homeland's options and also reroll
  extra random languages from Quirks such as Nearsighted. Fixed-only language
  results do not show a reroll control.
- Trait, Quirk, resolved-choice, gear, and coin controls preserve unrelated
  results while recalculating their dependent values.
- Use `Copy Image` to copy a high-resolution PNG to the system clipboard.

## Non-commercial license boundary

The deployed files must not reproduce ability, quirk, history, item, or other
gameplay descriptions. Public data is limited to names, table ranges, generated
values, and printed page references. Players need the Core Rules to use the
result.

`build_data.py` reads the local transcriptions in `../questline-vtt-tools/` but
deliberately excludes description, body, flavor, and notes fields from
`data.json`. Treat a failing public-data validation as a release blocker.

## Files

- `index.html`: Standalone page shell.
- `styles.css`: Responsive generator-specific presentation.
- `app.mjs`: Browser rendering and form behavior.
- `generator.mjs`: Pure random table and dependency-resolution engine.
- `data.json`: Generated public, sanitized rules data.
- `build_data.py`: Local normalization step for the transcribed source data.
- `test-generator.mjs`: Seeded rules and coverage checks.

## Local development

From the repository root:

```bash
python break-random-character/build_data.py
node break-random-character/test-generator.mjs
python -m http.server 8765
```

Open `http://127.0.0.1:8765/break-random-character/`.

The Core PDF is the authority. The older `break-dice-bot` tables are useful for
comparison only and should not override the PDF.

## Roadmap

### Gear phase

- Resolve the free Standard Weapon's physical form.
- Add optional Starting Coin spending.
- Apply restricted-gear penalties beyond the current warning labels.
- Keep item output limited to names, costs, and page references.

### Per-field controls

- Add explicit lock controls for generating a new card around favored results.
- Consider editable selectors alongside random rerolls.

### Expanded content

- Consider a transformed-state view for Henshin Hero Form combat values.
- Revisit Purr only if the generator later supports nonstandard character
  archetypes; it is intentionally excluded from normal Calling generation.

### Questline export

Questline export is explicitly deferred, but the roller's structured character
object is designed to support a later adapter.

The current official `.characters` reference is a ZIP-based Questline package
containing `manifest.json`, `entities.json`, and optional assets. It contains
adversaries, companions, and guides rather than a reusable player-character
template, so export should not be built by mutating one of those entities.

A future export phase should:

1. Confirm the current Questline player-character schema with a clean manual
   player export.
2. Map the roller result into that schema in a separate adapter module.
3. Generate deterministic IDs for character-owned fields and entries.
4. Package a minimal `manifest.json` and `entities.json`; omit assets initially.
5. Validate round-trip import in Questline before exposing a download button.

Questline export must remain optional and must not add licensed rule descriptions
to the generated package.
