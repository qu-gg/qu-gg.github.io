import { rerollCharacter, rollCharacters } from "./generator.mjs?v=6";


const form = document.querySelector("#roll-form");
const countInput = document.querySelector("#character-count");
const rollButton = document.querySelector("#roll-button");
const expandedToggle = document.querySelector("#expanded-content");
const results = document.querySelector("#results");
const emptyState = document.querySelector("#empty-state");
const resultCount = document.querySelector("#result-count");
const captureStage = document.querySelector("#card-capture-stage");

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

function referenceItem(label, value, reference, rerollTarget = "", suppressBlogLink = false) {
    const control = rerollTarget ? rerollIcon(rerollTarget, label) : "";
    const interaction = rerollTarget ? `data-reroll-target="${rerollTarget}" title="Reroll ${escapeHtml(label)}"` : "";
    const referenceMarkup = suppressBlogLink && reference.sourceUrl ? "" : pageReference(reference);
    return `<li class="${rerollTarget ? "rerollable-item" : ""}" ${interaction}><span class="field-heading"><strong>${escapeHtml(label)}</strong>${control}</span>${escapeHtml(value)} ${referenceMarkup}</li>`;
}

function modifierMarkup(modifiers = []) {
    return modifiers.map((modifier) => {
        const amount = modifier.kind === "gift"
            ? ""
            : modifier.kind === "set"
            ? `=${modifier.amount}`
            : `${modifier.amount > 0 ? "+" : ""}${modifier.amount}`;
        return `<span class="source-chip" title="${modifier.kind === "gift" ? "Gift earned from Allegiance" : `Modifier from ${escapeHtml(modifier.source)}`}">${escapeHtml(modifier.source)}${amount ? ` ${amount}` : ""}</span>`;
    }).join("");
}

function combatValue(character, label, key, value) {
    return `<div><dt>${escapeHtml(label)}</dt><dd><span>${escapeHtml(value)}</span><span class="value-modifiers">${modifierMarkup(character.modifiers.combat[key])}</span></dd></div>`;
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

    const choicesControl = character.selections.some((selection) => selection.rerollable !== false)
        ? rerollIcon("choices", "resolved choices")
        : "";
    const selectionMarkup = character.selections.length
        ? `<section class="card-section ${choicesControl ? "rerollable-section" : ""}" ${choicesControl ? 'data-reroll-target="choices" title="Reroll resolved choices"' : ""}><div class="section-heading"><h4>Resolved choices</h4>${choicesControl}</div><ul class="selection-list">${character.selections.map((selection) => referenceItem(selection.label, selection.value, selection, "", true)).join("")}</ul></section>`
        : "";

    const quirkValue = [character.quirk.name, ...character.additionalQuirks.map((quirk) => quirk.name)].join(" + ");
    const additionalHistoryMarkup = character.additionalHistory
        ? referenceItem("Additional History", `${character.additionalHistory.name} [${character.additionalHistory.tier}]`, character.additionalHistory)
        : "";
    const gearItems = character.gear.map((item) => {
        const nickname = item.nickname ? `, <em>${escapeHtml(item.nickname)}</em>` : "";
        const restrictionSources = item.restrictions
            .map((entry) => entry.page ? `${entry.source} p. ${entry.page}` : `${entry.source} Blog`)
            .join(" + ");
        const restriction = item.restricted
            ? `<span class="restriction-badge">Restricted: ${escapeHtml(restrictionSources)}</span>`
            : "";
        return `<li>${escapeHtml(item.name)}${nickname} ${pageReference(item)}${restriction}</li>`;
    });
    gearItems.push(`<li class="rerollable-item" data-reroll-target="coins" title="Reroll coins"><span class="coin-heading"><strong>1D20 Coins: ${character.coins}</strong>${rerollIcon("coins", "coins")}</span> <span class="page-ref">p. 148</span></li>`);

    return `
        <article class="character-card" style="--card-index: ${index}" aria-labelledby="character-${index + 1}-title">
            <header class="character-header">
                <div class="character-title-row rerollable-section" data-reroll-target="name" title="Reroll name">
                    <h3 id="character-${index + 1}-title">${escapeHtml(character.name)}</h3>
                    ${rerollIcon("name", "name")}
                    <button type="button" class="copy-image-button" data-copy-image data-html2canvas-ignore aria-label="Copy ${escapeHtml(character.name)} as an image" title="Copy card as image">Copy as Image</button>
                </div>
                <p class="character-build">${escapeHtml(displaySpeciesName(character.species.name))} ${escapeHtml(character.calling.name)}, Rank ${character.rank}</p>
                <p class="character-origin">${escapeHtml(character.history.name)} [${escapeHtml(character.history.tier)}] · ${escapeHtml(character.homeland.name)}</p>
            </header>
            <div class="character-body">
                <div class="card-column card-column-primary">
                    <section class="identity-section">
                        <ul class="reference-list identity-list">
                            ${referenceItem("Calling", character.calling.name, character.calling, "calling")}
                            ${referenceItem("Species", character.species.name, character.species, "species")}
                            ${referenceItem("Size", character.size.name, character.size)}
                            ${referenceItem("Homeland", character.homeland.name, character.homeland, character.homelandRerollable ? "homeland" : "")}
                            ${referenceItem("History", `${character.history.name} [${character.history.tier}]`, character.history, "history")}
                            ${additionalHistoryMarkup}
                            ${referenceItem("Languages", character.languages.join(", "), { page: 109 }, character.languageRerollable ? "language" : "")}
                            ${referenceItem("Quirk", `${quirkValue} [${character.quirk.category}]`, character.quirk, "quirk")}
                        </ul>
                    </section>

                    <section class="aptitude-section rerollable-section" data-reroll-target="traits" title="Reroll traits">
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
                    <section class="card-section">
                        <h4>Starting abilities</h4>
                        <ul class="reference-list">${abilityMarkup}</ul>
                    </section>

                    ${selectionMarkup}

                    <section class="card-section rerollable-section" data-reroll-target="gear" title="Reroll starting gear">
                        <div class="section-heading"><h4>Starting gear &amp; coins</h4>${rerollIcon("gear", "starting gear")}</div>
                        <ul class="gear-list">${gearItems.join("")}</ul>
                    </section>
                </div>
            </div>
        </article>
    `;
}

function renderCharacters(characters) {
    currentCharacters = characters;
    results.innerHTML = characters.map(renderCharacter).join("");
    emptyState.hidden = true;
    resultCount.textContent = `${characters.length} ${characters.length === 1 ? "Result" : "Results"}`;
}

function replaceCharacter(index, target) {
    const nextCharacter = rerollCharacter(data, currentCharacters[index], target);
    currentCharacters[index] = nextCharacter;
    const replacement = document.createElement("template");
    replacement.innerHTML = renderCharacter(nextCharacter, index).trim();
    const nextCard = replacement.content.firstElementChild;
    results.children[index].replaceWith(nextCard);
    nextCard.classList.add("rerolled");
}

function setCopyButtonState(button, state) {
    clearTimeout(button.copyStateTimeout);
    button.dataset.state = state;
    button.disabled = state === "copying";
    button.setAttribute("aria-label", state === "success" ? "Character card copied as an image" : state === "error" ? "Character card image copy failed" : "Copy character card as an image");
    if (state === "success" || state === "error") {
        button.copyStateTimeout = setTimeout(() => {
            button.dataset.state = "";
            button.disabled = false;
            button.setAttribute("aria-label", "Copy character card as an image");
        }, 1800);
    }
}

function canvasToBlob(canvas) {
    return new Promise((resolve, reject) => {
        canvas.toBlob((blob) => blob ? resolve(blob) : reject(new Error("PNG creation failed")), "image/png");
    });
}

async function copyCardAsImage(card, button) {
    if (!window.html2canvas || !navigator.clipboard || !window.ClipboardItem) {
        setCopyButtonState(button, "error");
        return;
    }
    card.classList.add("copying");
    setCopyButtonState(button, "copying");
    try {
        const cardWidth = Math.ceil(card.getBoundingClientRect().width);
        captureStage.replaceChildren();
        captureStage.style.width = `${cardWidth}px`;
        const clone = card.cloneNode(true);
        clone.classList.remove("copying", "rerolled");
        clone.classList.add("capture-card");
        clone.style.width = `${cardWidth}px`;
        clone.querySelectorAll("[data-html2canvas-ignore]").forEach((element) => element.remove());
        captureStage.appendChild(clone);
        const canvas = await window.html2canvas(clone, {
            scale: 2,
            useCORS: true,
            backgroundColor: "#fffefe",
            logging: false,
        });
        const blob = await canvasToBlob(canvas);
        await navigator.clipboard.write([new ClipboardItem({ "image/png": blob })]);
        setCopyButtonState(button, "success");
    } catch (error) {
        console.error(error);
        setCopyButtonState(button, "error");
    } finally {
        captureStage.replaceChildren();
        card.classList.remove("copying");
    }
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
    countInput.value = count;
    renderCharacters(rollCharacters(data, count, Math.random, expandedToggle.checked ? "expanded" : "core"));
    results.querySelector(".character-card")?.scrollIntoView({ behavior: "smooth", block: "start" });
});

results.addEventListener("click", (event) => {
    if (event.target.closest("a")) return;
    const copyButton = event.target.closest("[data-copy-image]");
    if (copyButton) {
        copyCardAsImage(copyButton.closest(".character-card"), copyButton);
        return;
    }
    const target = event.target.closest("[data-reroll-target]");
    if (!target) return;
    const card = target.closest(".character-card");
    const index = [...results.children].indexOf(card);
    replaceCharacter(index, target.dataset.rerollTarget);
});

const navToggle = document.querySelector(".nav-toggle");
navToggle?.addEventListener("click", () => {
    const isOpen = navToggle.classList.toggle("active");
    document.querySelector(".nav-links")?.classList.toggle("active", isOpen);
    navToggle.setAttribute("aria-expanded", String(isOpen));
});

rollButton.disabled = true;
loadData();