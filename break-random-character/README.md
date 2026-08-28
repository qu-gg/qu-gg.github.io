# BREAK!! Random Character

A static, browser-only rank 1 character roller for BREAK!! RPG. The tool follows
the six-step procedure in the Core Rules and is intentionally isolated from the
rest of the site until it is ready to be linked publicly.

## Current scope

- Roll 1-12 characters and replace the previous results.
- Roll Calling, Species, Homeland, History, Traits, Quirk, and starting Coins.
- Add a species-matched name from the official BREAK!! Random Name Tables post.
- Apply Calling, Species Size, Species, Trait, and Quirk value adjustments.
- Resolve bounded creation choices, including blade forms and materials, Soul
  Companions, Dark Gifts, Prodigy Abilities, and relevant nested Quirk choices.
- Select two distinct options from each History's Starting Gear.
- Add the universal Functional Outfit and unresolved Standard Weapon.
- Mark combat gear restricted by the Calling and/or final Species Size, with
  the relevant allowance page. Restricted gear remains in the rolled result.
- Apply the highest selected Armor and Shield Defense bonuses to Defense Rating
  and label each modifier with its gear source.
- Show only names, generated values, and Core Rules page references.
- Reroll individual random components while preserving unrelated results and
  rebuilding dependent values, gear restrictions, and modifiers.
- Use the `Copy Image` button on a card to copy it to the system clipboard as a
  PNG. Normal browser right-click behavior remains available.

The official post does not provide a separate Dimensional Stray name table, so
Dimensional Strays currently use the Native Human table. An Elf result that says
to use another chart follows the post's weighted Random Name Table and resolves
to a concrete name.

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
