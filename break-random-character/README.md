# BREAK!! Random Character

A static, browser-only Rank 1-10 character roller for BREAK!! RPG. The tool follows
the six-step procedure in the Core Rules and is intentionally isolated from the
rest of the site until it is ready to be linked publicly.

## Current scope

- Roll 1-12 characters and replace the previous results.
- Apply one selected Rank from 1-10 to the entire generated batch. Each Calling
  uses its own Advancement Table for Attack, Hearts, Aptitudes, XP threshold,
  and elective-ability counts; Calling variants inherit their base table.
- Select Standard electives at Ranks 2 and 4. At Ranks 6, 8, and 10, first
  choose uniformly between available Standard, Advanced, and Species
  Maturative categories, then choose within that category.
- Prevent duplicate non-repeatable electives and resolve bounded repeatable
  choices for Crafting Prodigy and Henshin Hero Additional Form.
- Resolve rank milestones for Favored Weapon, Heart's Blade, Wrath's Blade,
  Shield of Love, Soul Companion, and Henshin Hero Forms/Finisher, plus finite
  acquisition choices for supported electives.
- Recalculate Allegiance and Gifts from magical acquired abilities. Apply only
  verified unconditional card effects, including permanent Speed increases,
  naked Defense alternatives, and Stowing; situational effects remain ability
  names rather than changing base values.
- Mark each contributing Species, Motif, Prodigy, or elective with compact
  Bright or Dark point dots beside its name. Hover text and accessible labels
  identify each contribution; award one Gift per complete 3 points in each
  alignment.
- Include core and expanded Species Maturatives where published. Gadabovid uses
  Labyrinthian Intuition, Porc uses Boarish Affront, and Mundymutt has no
  Maturative option.
- Optionally use the official 2026 Expanded Content Calling and Species tables.
  Purr is rerolled; Henshin Hero, Balladeer, and all eight linked Calling
  variants are supported.
- Expanded Species include Porc, Hoppalong, Gadabovid, Mundymutt, Neridian, and
  Unterkin. Porc uses roll 8 while Tenebrate uses roll 7 pending an official
  expanded-table update. Added Species use the confirmed Inheritor Quirk route
  except Unterkin, whose source defines its own Physiology/Eldritch route.
- Neridians use an even standard/undersea origin split. Mundymutt sizes are
  evenly weighted. Unterkin use their fixed Homeland, unique Histories, and
  compatible core/variant Calling families.
- Roll Calling, Species, Homeland, History, Traits, Quirk, and starting Coins.
- Optionally assign each character a Gear Budget in Coins. Blank or `0` leaves
  purchasing disabled. Positive budgets buy a legal, category-balanced random
  selection without spending the character's rolled starting Coins.
- Constrain purchased gear by both its price and the character's remaining
  Inventory capacity. A character can wear only one Backpack, Traveler's Bag,
  or Factotum Pack; Factotums therefore cannot add another container.
- Limit purchases to eight displayed item types and sample across categories.
  Purchased Outfits, Armor, and Shields are capped at one type, Weapons at two,
  and other categories at small category-specific limits. Granted Armor or a
  Shield blocks purchasing another of that category.
- Consolidate stackable supplies such as Rations, Treats, Potions, and Grenades
  into quantities on one line while charging their full combined price and
  Inventory cost.
- Display currency and slot costs for Starting and purchased gear. Starting
  Coins remain in the Starting Gear section; the summary shows only total
  currency and used versus available Inventory. Values use Gems, Coins, and
  Stones rather than decimal Coins.
- Optionally count currency toward Inventory, disabled by default. Total wealth
  is first expressed in canonical Gems, Coins, and Stones; each displayed unit
  occupies `0.01 slot`, following the rule that 100 units of any currency fill
  1 Slot. The currency contribution appears beneath Total Currency and is
  included in Inventory Used.
- Treat literal History rewards such as `50 Coins` and `Gem x1` as carried
  wealth rather than item prices. They contribute to both Total Currency and,
  when enabled, currency Inventory weight.
- Randomly equip one Outfit from all granted and purchased Outfits, preferring
  non-Functional options whenever any are available. The worn Outfit is marked
  `Eq.` and uses `0 slots`; every other Outfit retains its carried Inventory
  cost.
- Add a species-matched name from the official BREAK!! Random Name Tables post.
- Apply Calling, Species Size, Species, Trait, and Quirk value adjustments.
- Mark Dimensional Stray Leisurely Focus as a `+1` source beneath its randomly
  selected eligible Aptitude.
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
- Use the `Copy as Image` button on a card to copy it to the system clipboard as
  a PNG on desktop. On mobile layouts, the same action becomes `Save Image` and
  downloads the PNG instead, avoiding mobile clipboard permissions. The
  captured card uses a fixed desktop-style two-column layout in both cases.
  Normal browser right-click behavior remains available.
- On mobile layouts, use the character-actions menu in the card header to
  access `Save Image`, `Export to FoundryVTT`, and `Export to QuestlineVTT`
  without expanding the card header.
- Use the `Export to FoundryVTT` button on a card to download one portable
  Foundry v14 BREAK!! character Actor JSON document. The export includes the
  selected Calling, Species, identity Items, abilities, Gifts, generated gear,
  equipment references, rank, traits, currency, resolved choices, and portable
  numeric effects. It does not include compendium metadata, official
  descriptions, Actions, or separate Companion Actors.
- Use the `Export to QuestlineVTT` button on a card to download one native
  Questline `.characters` ZIP package. The package includes a generated player
  character, high-level identity and stat values, generated inventory,
  currency, Followers/Soul Companion entries, editable weapon Actions, feature
  records with completion guidance, and page/source references. It contains no external
  Questline files, assets, or full feature descriptions.

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

The generator does not select the physical form of the universal Standard
Weapon. Optional gear purchases use their own budget and never spend Starting
Coins.

Some choices have no finite rules table and depend on the character concept or
party. These are marked `Player-defined` or `Team-dependent` rather than being
filled from an unofficial table. Examples include a Soul Link target, Guardian
ward, Peculiar Taste nourishment, and Sneezles allergen.

## Card interactions

- Click a rerollable value or its circular-arrow control to replace that result.
- Hover a Starting or Purchased Gear item to change its diamond bullet into a
  remove control. Removing Starting Gear releases its carried Inventory Slots
  without changing currency. Removing Purchased Gear also returns its full
  cost, including all units in a stacked line, to total currency. Rerolling the
  corresponding Gear section restores a newly generated list.
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
- Purchased gear has its own reroll control. Rerolling starting Coins preserves
  purchases; Calling, Species, History, Quirk, and starting-gear changes
  recalculate purchase legality and capacity from the preserved purchase seed.
- Use `Copy Image` to copy a high-resolution PNG to the system clipboard.

## Non-commercial license boundary

The deployed files must not reproduce ability, quirk, history, item, or other
gameplay descriptions. Public data is limited to names, table ranges, generated
values, and printed page references. Players need the Core Rules to use the
result.

`build_data.py` reads the local transcriptions in `../questline-vtt-tools/` but
deliberately excludes description, body, flavor, and notes fields from
`data.json`. Treat a failing public-data validation as a release blocker.

Shop prices are stored as integer Stones (`100 Stones = 1 Coin`) and Inventory
costs as tenths of a slot. This preserves the book's fractional prices and slot
costs without floating-point comparisons. Only names, categories, costs, slot
values, combat classifications, and page references are exported.

## Files

- `index.html`: Standalone page shell.
- `styles.css`: Responsive generator-specific presentation.
- `app.mjs`: Browser rendering and form behavior.
- `generator.mjs`: Pure random table and dependency-resolution engine.
- `foundry-export.mjs`: Isolated Foundry Actor document builder and browser
  download adapter.
- `questline-export.mjs`: Isolated Questline character package builder and ZIP
  download adapter.
- `data.json`: Generated public, sanitized rules data.
- `build_data.py`: Local normalization step for the transcribed source data.
- `test-generator.mjs`: Seeded rules and coverage checks.
- `test-questline-export.mjs`: Questline package schema and ZIP checks.

## Local development

From the repository root:

```bash
python break-random-character/build_data.py
node break-random-character/test-generator.mjs
node break-random-character/test-foundry-export.mjs
node break-random-character/test-questline-export.mjs
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

Questline export is implemented in `questline-export.mjs` and enabled by the
`ENABLE_QUESTLINE_EXPORT` flag in `app.mjs`. It builds a native ZIP package with
only `manifest.json` and `entities.json`; no files from `questline-vtt-tools/`
or any other ignored Questline source are read by the browser adapter.

The exported character uses the BREAK!! player sheet, deterministic
Questline-compatible IDs, generated high-level values, custom inventory Items,
and reference-only descriptions. Weapon Actions contain a d20 roll linked to
the character Attack Bonus and are embedded on their corresponding weapon Item,
so Questline can surface them with the equipped item. Abilities and Quirks are
kept only in the Ability section; their records carry source references and
completion guidance instead of duplicate Action shells. Followers and Soul
Companions remain attached inventory/choice entries rather than separate
characters.

The package intentionally contains no full rules descriptions, external assets,
compendium dependencies, or separate Companion Actors. The generated data is
derived only from the roller result and sanitized `data.json`.

### FoundryVTT export

Foundry export is implemented as a separate adapter so the generator remains
browser-only and its public data boundary remains unchanged. The downloaded
document is a standard `character` Actor for Foundry v14 and the BREAK!! v1.2
system. It is self-contained: all generated Items are embedded in the Actor,
and every `system.equipment` reference points to the matching embedded Item
ID. The export retains minimal Foundry and system version metadata plus the
required prototype token defaults so Foundry v14 imports it as current document
data instead of treating it as a pre-v10 document. The Foundry button is enabled
for testing and can be disabled with the `ENABLE_FOUNDRY_EXPORT` flag in `app.mjs`.

The adapter exports portable numeric effects for verified unconditional
adjustments, including applicable aptitude, Attack, Defense, Hearts, Speed,
Inventory, and Allegiance changes. Foundry still recalculates derived values
from its Calling, Species, equipment, Active Effects, and world settings. The
export therefore stores the generator result in a custom flag for comparison
after import.

The public export deliberately leaves Item descriptions and Actions empty. It
also represents Followers and Soul Companions as Items or resolved-choice
notes, not fully populated Companion Actors. Those features can be added later
without changing the page hook by extending the isolated adapter.
