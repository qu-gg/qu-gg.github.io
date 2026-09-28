import { removeGearItem, rerollCharacter, rollCharacters } from "./generator.mjs?v=26";
import { downloadFoundryActor } from "./foundry-export.mjs?v=4";
import { downloadQuestlineCharacter } from "./questline-export.mjs?v=3";

const ENABLE_FOUNDRY_EXPORT = true;
const ENABLE_QUESTLINE_EXPORT = true;

const form = document.querySelector("#roll-form");
const countInput = document.querySelector("#character-count");
const rankInput = document.querySelector("#character-rank");
const budgetInput = document.querySelector("#gear-budget");
const rollButton = document.querySelector("#roll-button");
const expandedToggle = document.querySelector("#expanded-content");
const currencyWeightToggle = document.querySelector("#currency-weight");
const results = document.querySelector("#results");
const emptyState = document.querySelector("#empty-state");
const resultCount = document.querySelector("#result-count");
const captureStage = document.querySelector("#card-capture-stage");
const COPY_CAPTURE_WIDTH = 1100;
const MOBILE_LAYOUT_QUERY = "(max-width: 800px)";
const MAX_CHARACTER_NAME_LENGTH = 80;

let data;
let currentCharacters = [];

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function cleanCharacterName(value) {
    const normalized = String(value ?? "")
        .normalize("NFC")
        .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F-\u009F\u00AD\u061C\u180E\u200B-\u200F\u202A-\u202E\u2060-\u206F\uFEFF]/gu, "")
        .replace(/\s+/gu, " ")
        .trim();
    return Array.from(normalized).slice(0, MAX_CHARACTER_NAME_LENGTH).join("");
}

function resizeNameInput(input) {
    if (!input) return;
    const style = getComputedStyle(input);
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d");
    if (context) {
        context.font = style.font;
        const textWidth = context.measureText(input.value || " ").width;
        const horizontalPadding = Number.parseFloat(style.paddingLeft) + Number.parseFloat(style.paddingRight);
        input.style.width = `${Math.ceil(textWidth + horizontalPadding + 4)}px`;
    }
    input.size = Math.max(1, Math.min(MAX_CHARACTER_NAME_LENGTH, Array.from(input.value).length));
}

function pageReference(entry) {
    if (entry.sourceUrl) return `<a class="source-ref" href="${escapeHtml(entry.sourceUrl)}" target="_blank" rel="noopener">Blog ↗</a>`;
    if (entry.page) return `<span class="page-ref">p. ${entry.page}</span>`;
    if (entry.pages) {
        const [start, end] = entry.pages;
        return `<span class="page-ref">${start === end ? `p. ${start}` : `pp. ${start}–${end}`}</span>`;
    }
    return "";
}

function rerollIcon(target, label, extraClass = "") {
    return `<button type="button" class="reroll-button ${extraClass}" data-reroll-target="${target}" data-html2canvas-ignore aria-label="Reroll ${escapeHtml(label)}" title="Reroll ${escapeHtml(label)}">↻</button>`;
}

function cardLockButton() {
    return `<button type="button" class="card-lock-toggle" data-card-lock-toggle data-html2canvas-ignore aria-pressed="false" aria-label="Lock character card" title="Lock card from rerolls"><span class="card-lock-icon" aria-hidden="true"></span></button>`;
}

function nameEditButton() {
    return `<button type="button" class="name-edit-button" data-name-edit data-html2canvas-ignore aria-pressed="false" aria-label="Edit character name" title="Edit character name">✎</button>`;
}

function referenceItem(label, value, reference, rerollTarget = "", suppressBlogLink = false, prefix = "") {
    const control = rerollTarget ? rerollIcon(rerollTarget, label) : "";
    const referenceMarkup = suppressBlogLink && reference.sourceUrl ? "" : pageReference(reference);
    return `<li class="${rerollTarget ? "rerollable-item" : ""}"><span class="field-heading"><strong>${escapeHtml(label)}</strong>${control}</span><span class="reference-value">${prefix}${escapeHtml(value)}</span> ${referenceMarkup}</li>`;
}

function modifierMarkup(modifiers = []) {
    return modifiers.map((modifier) => {
        const amount = modifier.kind === "gift"
            ? ""
            : modifier.kind === "gear" && modifier.amount === 0
            ? ""
            : modifier.kind === "allegiance"
            ? `${modifier.amount > 0 ? "+" : ""}${modifier.amount} ${modifier.alignment}`
            : modifier.kind === "set"
            ? `=${modifier.amount}`
            : `${modifier.amount > 0 ? "+" : ""}${modifier.amount}`;
        const title = modifier.kind === "gift"
            ? "Gift earned from Allegiance"
            : modifier.kind === "allegiance"
            ? `${modifier.amount > 0 ? "+" : ""}${modifier.amount} ${modifier.alignment} from ${escapeHtml(modifier.source)}`
            : `Modifier from ${escapeHtml(modifier.source)}`;
        const alignmentClass = modifier.kind === "allegiance" ? ` allegiance-chip allegiance-${modifier.alignment.toLowerCase()}` : "";
        return `<span class="source-chip${alignmentClass}" title="${title}">${escapeHtml(modifier.source)}${amount ? ` ${amount}` : ""}</span>`;
    }).join("");
}

function combatValue(character, label, key, value) {
    const modifiers = key === "allegiance"
        ? character.modifiers.combat[key].filter((modifier) => modifier.kind !== "allegiance")
        : character.modifiers.combat[key];
    return `<div><dt>${escapeHtml(label)}</dt><dd><span>${escapeHtml(value)}</span><span class="value-modifiers">${modifierMarkup(modifiers)}</span></dd></div>`;
}

function allegianceDots(alignment, amount, source) {
    if (!alignment || !amount) return "";
    const normalizedAlignment = alignment === "Light" ? "Bright" : alignment;
    const label = `+${amount} ${normalizedAlignment} Allegiance from ${source}`;
    const dots = Array.from({ length: amount }, () => `<span class="allegiance-dot allegiance-dot-${normalizedAlignment.toLowerCase()}" aria-hidden="true"></span>`).join("");
    return `<span class="allegiance-dots" role="img" aria-label="${escapeHtml(label)}" title="${escapeHtml(label)}">${dots}</span>`;
}

function abilityAllegiance(character, ability) {
    if (ability.allegiance) return ability.allegiance;
    if (character.calling.name !== "Henshin Hero" || !ability.magical) return "";
    return character.selections.find((selection) => selection.label === "Allegiance Motif")?.value || "";
}

function selectionAllegianceDots(character, selection) {
    if (selection.label === "Prodigy Ability" && character.abilities.prodigy) {
        return allegianceDots(abilityAllegiance(character, character.abilities.prodigy), 1, character.abilities.prodigy.name);
    }
    if (selection.label === "Allegiance Motif") {
        return allegianceDots(selection.value, 2, "Allegiance Motif");
    }
    return "";
}

function formatCurrency(totalStones) {
    const denominations = [
        ["Gem", 10000],
        ["Coin", 100],
        ["Stone", 1],
    ];
    let remainder = totalStones;
    return denominations.flatMap(([name, value]) => {
        const amount = Math.floor(remainder / value);
        remainder %= value;
        return amount ? [`${amount} ${name}${amount === 1 ? "" : "s"}`] : [];
    }).join(" · ") || "0 Stones";
}

function formatSlots(slotTenths) {
    const slots = slotTenths / 10;
    return `${slots} ${slots === 1 ? "slot" : "slots"}`;
}

function formatSlotHundredths(slotHundredths) {
    const slots = slotHundredths / 100;
    return `${slots} ${slots === 1 ? "slot" : "slots"}`;
}

function gearMeta(...parts) {
    return `<span class="gear-meta">${parts.filter(Boolean).map(escapeHtml).join(" · ")}</span>`;
}

function startingGearCost(item) {
    if (item.costStones === null || item.costStones === undefined) return "Cost N/A";
    return `${formatCurrency(item.costStones)}${item.costRate ? ` ${item.costRate}` : ""}`;
}

function carriedStateMarkup(item) {
    if (item.equipped) return `<span class="equipped-badge" aria-label="Equipped" title="Equipped">Eq.</span>`;
    if (item.stowed) return `<span class="equipped-badge stowed-badge">Stowed</span>`;
    return "";
}

function displayedGearSlots(item) {
    if (item.equipped) return "0 slots worn";
    if (item.stowed) return "0 slots stowed";
    return formatSlots(item.slotTenths || 0);
}

function isMobileLayout() {
    return matchMedia(MOBILE_LAYOUT_QUERY).matches;
}

function imageActionLabel() {
    return isMobileLayout() ? "Save Image" : "Copy as Image";
}

function imageActionAriaLabel() {
    return isMobileLayout() ? "Save character card as an image" : "Copy character card as an image";
}

function imageActionTitle() {
    return isMobileLayout() ? "Save card as image" : "Copy card as image";
}

function gearRemoveButton(section, index, item) {
    const label = `Remove ${item.name} from ${section === "gear" ? "Starting Gear" : "Purchased Gear"}`;
    return `<button type="button" class="gear-remove-button" data-remove-gear data-remove-section="${section}" data-remove-index="${index}" aria-label="${escapeHtml(label)}" title="${escapeHtml(label)}"><span class="gear-bullet" aria-hidden="true"></span><span class="gear-remove-x" aria-hidden="true">×</span></button>`;
}

function displaySpeciesName(name) {
    if (name === "Human, Native") return "Native Human";
    if (name === "Human, Dimensional Stray") return "Dimensional Stray Human";
    return name;
}

function renderCharacter(character, index) {
    const aptitudeOrder = ["might", "deftness", "grit", "insight", "aura"];
    const aptitudeMarkup = aptitudeOrder.map((aptitude) => {
        const traits = character.traits
            .filter((trait) => trait.aptitude === aptitude)
            .map((trait) => {
                const modifier = `${trait.amount > 0 ? "+" : ""}${trait.amount}`;
                return `<span class="trait-chip" aria-label="${modifier} trait" title="Trait modifier">Trait ${modifier}</span>`;
            })
            .join("");
        const sourceModifiers = modifierMarkup(character.modifiers.aptitudes[aptitude]);
        const traitRow = traits ? `<span class="trait-modifiers">${traits}</span>` : "";
        const sourceRow = sourceModifiers ? `<span class="source-modifiers">${sourceModifiers}</span>` : "";
        return `
            <div>
                <dt>${escapeHtml(aptitude)}</dt>
                <dd>${character.aptitudes[aptitude]}</dd>
                <dd class="stat-modifiers">${traitRow}${sourceRow}</dd>
            </div>
        `;
    }).join("");

    const abilityMarkup = [
        ...character.abilities.calling.map((ability) => referenceItem("Calling", ability.name, ability)),
        ...character.abilities.species.map((ability) => referenceItem("Species", ability.name, ability)),
    ].join("");
    const electiveAbilityMarkup = character.abilities.elective.map((ability) =>
        referenceItem(`${ability.tier} · Rank ${ability.acquiredRank}`, ability.name, ability, "", false, allegianceDots(abilityAllegiance(character, ability), 1, ability.name))
    ).join("");
    const electiveSectionMarkup = character.abilities.elective.length
        ? `<section class="card-section rerollable-section elective-abilities-section" data-balance-section data-balance-order="2">
            <div class="section-heading"><h4>Elective abilities</h4>${rerollIcon("abilities", "elective abilities")}</div>
            <ul class="reference-list">${electiveAbilityMarkup}</ul>
        </section>`
        : "";

    const choicesControl = character.selections.some((selection) => selection.rerollable !== false)
        ? rerollIcon("choices", "resolved choices")
        : "";
    const selectionMarkup = character.selections.length
        ? `<section class="card-section ${choicesControl ? "rerollable-section" : ""}"><div class="section-heading"><h4>Resolved choices</h4>${choicesControl}</div><ul class="selection-list">${character.selections.map((selection) => referenceItem(selection.label, selection.value, selection, "", true, selectionAllegianceDots(character, selection))).join("")}</ul></section>`
        : "";

    const quirkValue = [character.quirk.name, ...character.additionalQuirks.map((quirk) => quirk.name)].join(" + ");
    const additionalHistoryMarkup = character.additionalHistory
        ? referenceItem("Additional History", `${character.additionalHistory.name} [${character.additionalHistory.tier}]`, character.additionalHistory)
        : "";
    const gearItems = character.gear.map((item, itemIndex) => {
        const nickname = item.nickname ? `, <em>${escapeHtml(item.nickname)}</em>` : "";
        const restrictionSources = item.restrictions
            .map((entry) => entry.source)
            .join(" + ");
        const restriction = item.restricted
            ? `<span class="restriction-badge">Restricted: ${escapeHtml(restrictionSources)}</span>`
            : "";
        return `<li class="removable-gear-item">${gearRemoveButton("gear", itemIndex, item)}${escapeHtml(item.name)}${nickname} ${pageReference(item)}${carriedStateMarkup(item)}${gearMeta(startingGearCost(item), displayedGearSlots(item))}${restriction}</li>`;
    });
    gearItems.push(`<li class="starting-coins-item rerollable-item"><span class="coin-heading"><strong>d20 Coins: ${formatCurrency(character.coins * 100)}</strong>${rerollIcon("coins", "d20 Coins")}</span></li>`);
    const purchasedGearItems = character.purchasedGear.map((item, itemIndex) => `
        <li class="removable-gear-item">${gearRemoveButton("purchasedGear", itemIndex, item)}${escapeHtml(item.name)}${item.quantity > 1 ? ` ×${item.quantity}` : ""} ${pageReference(item)}${carriedStateMarkup(item)}${gearMeta(formatCurrency(item.costStones), displayedGearSlots(item))}</li>
    `).join("");
    const purchasedGearMarkup = character.shopping.budgetCoins > 0
        ? `<section class="card-section rerollable-section purchased-gear-section">
            <div class="section-heading"><h4>Purchased gear</h4>${rerollIcon("purchasedGear", "purchased gear")}</div>
            ${purchasedGearItems ? `<ul class="gear-list">${purchasedGearItems}</ul>` : `<p class="no-purchases">No legal purchases fit.</p>`}
        </section>`
        : "";
    const currencySlotsMarkup = character.currencyWeightEnabled
        ? `<span class="resource-detail">${formatSlotHundredths(character.shopping.currencySlotHundredths)}</span>`
        : "";

    return `
        <article class="character-card" data-locked="false" style="--card-index: ${index}" aria-labelledby="character-${index + 1}-title">
            <header class="character-header">
                <div class="character-title-row">
                    <div class="character-name-tools">
                        <div class="character-name-display" data-name-display>
                            <h3 id="character-${index + 1}-title" class="character-name-heading" aria-label="${escapeHtml(character.name)}">${escapeHtml(character.name)}</h3>
                            ${rerollIcon("name", "name")}
                            ${nameEditButton()}
                        </div>
                    </div>
                    <div class="character-card-actions" id="character-${index + 1}-actions" data-card-actions data-html2canvas-ignore>
                        <button type="button" class="copy-image-button" data-copy-image data-html2canvas-ignore role="menuitem" aria-label="${escapeHtml(imageActionAriaLabel())}" title="${escapeHtml(imageActionTitle())}">${imageActionLabel()}</button>
                        ${ENABLE_FOUNDRY_EXPORT ? `<button type="button" class="foundry-export-button" data-export-foundry data-html2canvas-ignore role="menuitem" aria-label="Export ${escapeHtml(character.name)} to FoundryVTT" title="Export character to FoundryVTT">Export to FoundryVTT</button>` : ""}
                        ${ENABLE_QUESTLINE_EXPORT ? `<button type="button" class="questline-export-button" data-export-questline data-html2canvas-ignore role="menuitem" aria-label="Export ${escapeHtml(character.name)} to QuestlineVTT" title="Export character to QuestlineVTT">Export to QuestlineVTT</button>` : ""}
                    </div>
                    ${cardLockButton()}
                    <button type="button" class="card-actions-menu-toggle" data-card-actions-toggle data-html2canvas-ignore aria-haspopup="menu" aria-expanded="false" aria-controls="character-${index + 1}-actions" aria-label="Character actions" title="Character actions"><span class="card-actions-menu-icon" aria-hidden="true"></span></button>
                </div>
                <p class="character-build">${escapeHtml(displaySpeciesName(character.species.name))} ${escapeHtml(character.calling.name)}, Rank ${character.rank}</p>
                <p class="character-origin">${escapeHtml(character.history.name)} [${escapeHtml(character.history.tier)}] · ${escapeHtml(character.homeland.name)}</p>
            </header>
            <div class="character-body">
                <div class="card-column card-column-primary">
                    <section class="identity-section">
                        <ul class="reference-list identity-list">
                            ${referenceItem("Calling", character.calling.name, character.calling, "calling")}
                            ${referenceItem("Species", character.species.name, character.species, "species", false, allegianceDots(character.species.name === "Promethean" ? "Bright" : ["Tenebrate", "Neridian"].includes(character.species.name) ? "Dark" : "", 1, character.species.name))}
                            ${referenceItem("Size", character.size.name, character.size)}
                            ${referenceItem("Homeland", character.homeland.name, character.homeland, character.homelandRerollable ? "homeland" : "")}
                            ${referenceItem("History", `${character.history.name} [${character.history.tier}]`, character.history, "history")}
                            ${additionalHistoryMarkup}
                            ${referenceItem("Languages", character.languages.join(", "), { page: 109 }, character.languageRerollable ? "language" : "")}
                            ${referenceItem("Quirk", `${quirkValue} [${character.quirk.category}]`, character.quirk, "quirk")}
                        </ul>
                    </section>

                    <section class="aptitude-section rerollable-section">
                        ${rerollIcon("traits", "traits", "reroll-section")}
                        <dl class="stat-grid">${aptitudeMarkup}</dl>
                    </section>

                    <section class="card-section combat-section">
                        <h4>Combat &amp; capacity</h4>
                        <dl class="combat-grid">
                            ${combatValue(character, "Attack", "attack", `${character.combat.attack >= 0 ? "+" : ""}${character.combat.attack}`)}
                            ${combatValue(character, "Hearts", "hearts", character.combat.hearts)}
                            ${combatValue(character, "Defense", "defense", character.combat.defense)}
                            ${combatValue(character, "Speed", "speed", character.combat.speed)}
                            ${combatValue(character, "Inventory", "inventory", `${character.combat.inventory} slots`)}
                            ${combatValue(character, "Allegiance", "allegiance", character.allegiance)}
                        </dl>
                    </section>

                </div>

                <div class="card-column card-column-secondary">
                    <section class="card-section abilities-section" data-balance-section data-balance-order="1">
                        <h4>Starting abilities</h4>
                        <ul class="reference-list">${abilityMarkup}</ul>
                    </section>

                    ${electiveSectionMarkup}

                    ${selectionMarkup}

                    <section class="card-section rerollable-section">
                        <div class="section-heading"><h4>Starting gear</h4>${rerollIcon("gear", "starting gear")}</div>
                        <ul class="gear-list">${gearItems.join("")}</ul>
                    </section>

                    ${purchasedGearMarkup}

                    <section class="card-section resources-section">
                        <h4>Currency &amp; capacity</h4>
                        <dl class="resource-grid">
                            <div><dt>Total currency</dt><dd><span>${formatCurrency(character.shopping.totalCurrencyStones)}</span>${currencySlotsMarkup}</dd></div>
                            <div><dt>Inventory used</dt><dd>${formatSlotHundredths(character.shopping.usedSlotHundredths)} / ${formatSlots(character.shopping.capacityTenths)}</dd></div>
                        </dl>
                    </section>
                </div>
            </div>
        </article>
    `;
}

function balanceCharacterCard(card, forceDesktop = false) {
    const primary = card.querySelector(".card-column-primary");
    const secondary = card.querySelector(".card-column-secondary");
    const sections = [...card.querySelectorAll("[data-balance-section]")]
        .sort((left, right) => Number(left.dataset.balanceOrder) - Number(right.dataset.balanceOrder));
    if (!primary || !secondary || !sections.length) return;
    if (!forceDesktop && matchMedia("(max-width: 800px)").matches) {
        primary.append(...sections);
        return;
    }

    const placements = [];
    for (let mask = 0; mask < 2 ** sections.length; mask += 1) {
        const leftSections = sections.filter((_, index) => mask & (1 << index));
        const rightSections = sections.filter((_, index) => !(mask & (1 << index)));
        primary.append(...leftSections);
        secondary.prepend(...rightSections);
        const left = primary.getBoundingClientRect().height;
        const right = secondary.getBoundingClientRect().height;
        placements.push({ mask, left, right, delta: Math.abs(left - right) });
    }
    const smallestDelta = Math.min(...placements.map((placement) => placement.delta));
    const closePlacements = placements.filter((placement) => placement.delta <= smallestDelta + 8);
    const placement = closePlacements.find((candidate) => candidate.right >= candidate.left) || closePlacements[0];
    primary.append(...sections.filter((_, index) => placement.mask & (1 << index)));
    secondary.prepend(...sections.filter((_, index) => !(placement.mask & (1 << index))));
}

function balanceCharacterCards() {
    results.querySelectorAll(".character-card").forEach(balanceCharacterCard);
}

function renderCharacters(characters) {
    currentCharacters = characters;
    results.innerHTML = characters.map(renderCharacter).join("");
    results.querySelectorAll("[data-name-input]").forEach(resizeNameInput);
    balanceCharacterCards();
    emptyState.hidden = true;
    resultCount.textContent = `${characters.length} ${characters.length === 1 ? "Result" : "Results"}`;
}

function replaceCharacter(index, target) {
    const previousCharacter = currentCharacters[index];
    const nextCharacter = rerollCharacter(data, previousCharacter, target);
    if (target !== "name" && previousCharacter.nameOverride) {
        nextCharacter.name = previousCharacter.name;
        nextCharacter.nameOverride = true;
    }
    currentCharacters[index] = nextCharacter;
    const replacement = document.createElement("template");
    replacement.innerHTML = renderCharacter(nextCharacter, index).trim();
    const nextCard = replacement.content.firstElementChild;
    results.children[index].replaceWith(nextCard);
    resizeNameInput(nextCard.querySelector("[data-name-input]"));
    balanceCharacterCard(nextCard);
    nextCard.classList.add("rerolled");
}

function setCardLocked(card, locked) {
    if (!card) return;
    card.dataset.locked = String(locked);
    card.classList.toggle("is-locked", locked);
    const toggle = card.querySelector("[data-card-lock-toggle]");
    toggle?.setAttribute("aria-pressed", String(locked));
    toggle?.setAttribute("aria-label", locked ? "Unlock character card" : "Lock character card");
    toggle?.setAttribute("title", locked ? "Unlock card for rerolls" : "Lock card from rerolls");
    card.querySelectorAll(".reroll-button").forEach((button) => {
        button.disabled = locked;
    });
}

function startNameEdit(card) {
    if (!card) return;
    const heading = card.querySelector(".character-name-heading");
    const toggle = card.querySelector("[data-name-edit]");
    if (!heading || !toggle || heading.querySelector("[data-name-input]")) return;
    card.dataset.editingName = heading.textContent;
    const input = document.createElement("input");
    input.type = "text";
    input.className = "character-name-input";
    input.dataset.nameInput = "";
    input.value = heading.textContent;
    input.maxLength = MAX_CHARACTER_NAME_LENGTH;
    input.autocomplete = "off";
    input.spellcheck = false;
    input.setAttribute("aria-label", "Character name");
    heading.replaceChildren(input);
    heading.setAttribute("aria-label", "Editing character name");
    card.classList.add("name-editing");
    toggle.dataset.editing = "true";
    toggle.setAttribute("aria-pressed", "true");
    toggle.setAttribute("aria-label", "Save character name");
    toggle.setAttribute("title", "Save character name");
    toggle.textContent = "✓";
    resizeNameInput(input);
    input.focus();
    input.select();
}

function finishNameEdit(card, restoreFocus = true) {
    if (!card) return;
    const heading = card.querySelector(".character-name-heading");
    const toggle = card.querySelector("[data-name-edit]");
    const input = heading?.querySelector("[data-name-input]");
    if (!input || !heading || !toggle) return;
    heading.textContent = input.value;
    heading.setAttribute("aria-label", heading.textContent);
    card.classList.remove("name-editing");
    toggle.dataset.editing = "false";
    toggle.setAttribute("aria-pressed", "false");
    toggle.setAttribute("aria-label", "Edit character name");
    toggle.setAttribute("title", "Edit character name");
    toggle.textContent = "✎";
    delete card.dataset.editingName;
    if (restoreFocus) toggle.focus();
}

function cancelNameEdit(card, restoreFocus = true) {
    if (!card) return;
    const heading = card.querySelector(".character-name-heading");
    const input = heading?.querySelector("[data-name-input]");
    if (!input) return;
    if (card.dataset.editingName !== undefined) input.value = card.dataset.editingName;
    finishNameEdit(card, restoreFocus);
}

function saveCharacterName(card) {
    if (!card) return;
    const input = card.querySelector("[data-name-input]");
    const heading = input?.closest(".character-name-heading");
    if (!input || !heading) return;
    const name = cleanCharacterName(input.value);
    if (!name) {
        input.classList.add("name-edit-invalid");
        input.setAttribute("aria-invalid", "true");
        input.setAttribute("title", "Enter a character name.");
        input.focus();
        return;
    }
    input.value = name;
    resizeNameInput(input);
    input.classList.remove("name-edit-invalid");
    const index = [...results.children].indexOf(card);
    const wasLocked = card.dataset.locked === "true";
    currentCharacters[index] = { ...currentCharacters[index], name, nameOverride: true };
    finishNameEdit(card, false);
    const replacement = document.createElement("template");
    replacement.innerHTML = renderCharacter(currentCharacters[index], index).trim();
    const nextCard = replacement.content.firstElementChild;
    results.children[index].replaceWith(nextCard);
    resizeNameInput(nextCard.querySelector("[data-name-input]"));
    balanceCharacterCard(nextCard);
    setCardLocked(nextCard, wasLocked);
    nextCard.classList.add("name-updated");
    nextCard.querySelector("[data-name-edit]")?.focus();
}

function removeCharacterGear(index, section, itemIndex) {
    const wasLocked = results.children[index]?.dataset.locked === "true";
    const nextCharacter = removeGearItem(currentCharacters[index], section, itemIndex);
    currentCharacters[index] = nextCharacter;
    const replacement = document.createElement("template");
    replacement.innerHTML = renderCharacter(nextCharacter, index).trim();
    const nextCard = replacement.content.firstElementChild;
    results.children[index].replaceWith(nextCard);
    resizeNameInput(nextCard.querySelector("[data-name-input]"));
    balanceCharacterCard(nextCard);
    setCardLocked(nextCard, wasLocked);
    nextCard.classList.add("rerolled");
}

function setCopyButtonState(button, state) {
    clearTimeout(button.copyStateTimeout);
    button.dataset.state = state;
    button.disabled = state === "copying";
    button.textContent = state === "copying" ? (isMobileLayout() ? "Saving..." : "Copying...") : state === "success" ? (isMobileLayout() ? "Saved" : "Copied") : state === "error" ? (isMobileLayout() ? "Save failed" : "Copy failed") : imageActionLabel();
    button.setAttribute("aria-label", state === "success" ? `Character card ${isMobileLayout() ? "saved" : "copied"} as an image` : state === "error" ? `Character card image ${isMobileLayout() ? "save" : "copy"} failed` : imageActionAriaLabel());
    if (state === "success" || state === "error") {
        button.copyStateTimeout = setTimeout(() => {
            button.dataset.state = "";
            button.disabled = false;
            button.textContent = imageActionLabel();
            button.title = imageActionTitle();
            button.setAttribute("aria-label", imageActionAriaLabel());
        }, 1800);
    }
}

function canvasToBlob(canvas) {
    return new Promise((resolve, reject) => {
        canvas.toBlob((blob) => blob ? resolve(blob) : reject(new Error("PNG creation failed")), "image/png");
    });
}

function imageFileName(name) {
    const baseName = String(name || "break-character")
        .replace(/[^a-z0-9]+/gi, "-")
        .replace(/^-+|-+$/g, "")
        .toLowerCase();
    return `${baseName || "break-character"}.png`;
}

function downloadImageBlob(blob, name) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = imageFileName(name);
    link.hidden = true;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 0);
}

async function copyCardAsImage(card, button) {
    const mobileLayout = isMobileLayout();
    if (!window.html2canvas || (!mobileLayout && (!navigator.clipboard || !window.ClipboardItem))) {
        setCopyButtonState(button, "error");
        return;
    }
    card.classList.add("copying");
    setCopyButtonState(button, "copying");
    try {
        captureStage.replaceChildren();
        captureStage.style.width = `${COPY_CAPTURE_WIDTH}px`;
        const clone = card.cloneNode(true);
        clone.classList.remove("copying", "rerolled");
        clone.classList.add("capture-card");
        clone.style.width = `${COPY_CAPTURE_WIDTH}px`;
        clone.querySelectorAll("[data-html2canvas-ignore]").forEach((element) => element.remove());
        captureStage.appendChild(clone);
        balanceCharacterCard(clone, true);
        const canvasPromise = window.html2canvas(clone, {
            scale: 2,
            useCORS: true,
            backgroundColor: "#fffefe",
            logging: false,
        });
        if (mobileLayout) {
            const blob = await canvasPromise.then(canvasToBlob);
            downloadImageBlob(blob, card.querySelector("h3")?.textContent);
        } else {
            const pngPromise = canvasPromise.then(canvasToBlob);
            await navigator.clipboard.write([new ClipboardItem({ "image/png": pngPromise })]);
        }
        setCopyButtonState(button, "success");
    } catch (error) {
        console.error(error);
        setCopyButtonState(button, "error");
    } finally {
        captureStage.replaceChildren();
        card.classList.remove("copying");
    }
}

function updateImageActionButtons() {
    results.querySelectorAll("[data-copy-image]").forEach((button) => {
        if (button.dataset.state) return;
        button.textContent = imageActionLabel();
        button.title = imageActionTitle();
        button.setAttribute("aria-label", imageActionAriaLabel());
    });
}

function setCardActionsMenu(card, open, focusFirst = false) {
    const menu = card?.querySelector("[data-card-actions]");
    const toggle = card?.querySelector("[data-card-actions-toggle]");
    if (!menu || !toggle) return;
    if (open) menu.dataset.menuOpen = "true";
    else delete menu.dataset.menuOpen;
    toggle.setAttribute("aria-expanded", String(open));
    if (open && focusFirst) menu.querySelector("button")?.focus();
}

function closeCardActionsMenus(except = null) {
    results.querySelectorAll("[data-card-actions][data-menu-open='true']").forEach((menu) => {
        const card = menu.closest(".character-card");
        if (card !== except) setCardActionsMenu(card, false);
    });
}

async function loadData() {
    try {
        const response = await fetch("./data.json", { cache: "no-store" });
        if (!response.ok) throw new Error(`Data request failed (${response.status})`);
        data = await response.json();
        rollButton.disabled = false;
    } catch (error) {
        resultCount.textContent = "Data Unavailable";
        console.error(error);
    }
}

form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!data) return;
    const count = Math.max(1, Math.min(12, Math.trunc(Number(countInput.value)) || 1));
    const rank = Math.max(1, Math.min(10, Math.trunc(Number(rankInput.value)) || 1));
    const gearBudget = Math.max(0, Math.min(10000, Math.trunc(Number(budgetInput.value)) || 0));
    countInput.value = count;
    rankInput.value = rank;
    budgetInput.value = gearBudget || "";
    renderCharacters(rollCharacters(data, count, Math.random, expandedToggle.checked ? "expanded" : "core", gearBudget, currencyWeightToggle.checked, rank));
    results.querySelector(".character-card")?.scrollIntoView({ behavior: "smooth", block: "start" });
});

results.addEventListener("click", (event) => {
    const menuToggle = event.target.closest("[data-card-actions-toggle]");
    if (menuToggle) {
        const card = menuToggle.closest(".character-card");
        const menu = card?.querySelector("[data-card-actions]");
        const open = menu?.dataset.menuOpen === "true";
        closeCardActionsMenus(card);
        setCardActionsMenu(card, !open, !open);
        return;
    }
    if (event.target.closest("a")) {
        closeCardActionsMenus();
        return;
    }
    const foundryButton = event.target.closest("[data-export-foundry]");
    if (foundryButton) {
        closeCardActionsMenus();
        const card = foundryButton.closest(".character-card");
        const index = [...results.children].indexOf(card);
        if (currentCharacters[index]) downloadFoundryActor(currentCharacters[index], data);
        return;
    }
    const questlineButton = event.target.closest("[data-export-questline]");
    if (questlineButton) {
        closeCardActionsMenus();
        const card = questlineButton.closest(".character-card");
        const index = [...results.children].indexOf(card);
        if (currentCharacters[index]) downloadQuestlineCharacter(currentCharacters[index], data);
        return;
    }
    const copyButton = event.target.closest("[data-copy-image]");
    if (copyButton) {
        closeCardActionsMenus();
        copyCardAsImage(copyButton.closest(".character-card"), copyButton);
        return;
    }
    const nameEdit = event.target.closest("[data-name-edit]");
    if (nameEdit) {
        const card = nameEdit.closest(".character-card");
        if (nameEdit.dataset.editing === "true") saveCharacterName(card);
        else startNameEdit(card);
        return;
    }
    const lockToggle = event.target.closest("[data-card-lock-toggle]");
    if (lockToggle) {
        const card = lockToggle.closest(".character-card");
        setCardLocked(card, card?.dataset.locked !== "true");
        return;
    }
    const removeButton = event.target.closest("[data-remove-gear]");
    if (removeButton) {
        const card = removeButton.closest(".character-card");
        const index = [...results.children].indexOf(card);
        removeCharacterGear(index, removeButton.dataset.removeSection, Number(removeButton.dataset.removeIndex));
        return;
    }
    const rerollButton = event.target.closest(".reroll-button");
    if (!rerollButton || rerollButton.disabled) return;
    const card = rerollButton.closest(".character-card");
    if (card?.dataset.locked === "true") return;
    const index = [...results.children].indexOf(card);
    replaceCharacter(index, rerollButton.dataset.rerollTarget);
});

results.addEventListener("keydown", (event) => {
    const heading = event.target.closest("[data-name-input]");
    if (!heading) return;
    const card = heading.closest(".character-card");
    if (event.key === "Enter") {
        event.preventDefault();
        saveCharacterName(card);
    } else if (event.key === "Escape") {
        event.preventDefault();
        cancelNameEdit(card);
    }
});

results.addEventListener("input", (event) => {
    const input = event.target.closest("[data-name-input]");
    if (!input) return;
    input.classList.remove("name-edit-invalid");
    input.removeAttribute("aria-invalid");
    input.removeAttribute("title");
    resizeNameInput(input);
});

document.addEventListener("click", (event) => {
    if (event.target.closest("[data-card-actions-toggle], [data-card-actions]")) return;
    closeCardActionsMenus();
});

document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    const menu = results.querySelector("[data-card-actions][data-menu-open='true']");
    if (!menu) return;
    const card = menu.closest(".character-card");
    setCardActionsMenu(card, false);
    card?.querySelector("[data-card-actions-toggle]")?.focus();
});

const navToggle = document.querySelector(".nav-toggle");
navToggle?.addEventListener("click", () => {
    const isOpen = navToggle.classList.toggle("active");
    document.querySelector(".nav-links")?.classList.toggle("active", isOpen);
    navToggle.setAttribute("aria-expanded", String(isOpen));
});

let balanceFrame;
addEventListener("resize", () => {
    cancelAnimationFrame(balanceFrame);
    balanceFrame = requestAnimationFrame(balanceCharacterCards);
    updateImageActionButtons();
});

rollButton.disabled = true;
loadData();