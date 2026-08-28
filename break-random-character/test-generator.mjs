import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { rerollCharacter, rollCharacters } from "./generator.mjs";


const data = JSON.parse(await readFile(new URL("./data.json", import.meta.url), "utf8"));
const hereticAllowance = data.callings.find((calling) => calling.name === "Heretic").gearAllowance;
assert.ok(hereticAllowance.weapons.includes("Lash"));
assert.ok(!hereticAllowance.weapons.includes("Master"));
assert.ok(data.sizeRules.Small.restricted.weapons.includes("Mighty"));
assert.ok(data.sizeRules.Small.restricted.weapons.includes("Arc"));

function seededRandom(seed) {
    let state = seed >>> 0;
    return () => {
        state = (state * 1664525 + 1013904223) >>> 0;
        return state / 4294967296;
    };
}

const characters = rollCharacters(data, 12, seededRandom(0xB4EA5));
assert.equal(characters.length, 12);
assert.equal(rollCharacters(data, 99, seededRandom(1)).length, 12);
assert.equal(rollCharacters(data, 0, seededRandom(1)).length, 1);

const baseCharacter = rollCharacters(data, 1, seededRandom(0xC0FFEE))[0];
const rerollCases = {
    name: ["calling", "species", "homeland", "history", "traits", "quirk", "gear", "coins"],
    calling: ["name", "species", "homeland", "history", "traits", "quirk", "gear", "coins"],
    species: ["traits", "coins"],
    language: ["name", "calling", "species", "homeland", "history", "traits", "quirk", "gear", "coins"],
    homeland: ["name", "calling", "species", "traits", "quirk", "coins"],
    history: ["name", "calling", "species", "homeland", "traits", "quirk", "coins"],
    traits: ["name", "calling", "species", "homeland", "history", "quirk", "gear", "coins"],
    quirk: ["name", "calling", "species", "homeland", "history", "traits", "coins"],
    gear: ["name", "calling", "species", "homeland", "history", "traits", "quirk", "coins"],
    coins: ["name", "calling", "species", "homeland", "history", "traits", "quirk", "gear"],
};
const comparable = (character, key) => {
    if (key === "name" || key === "coins") return character[key];
    if (key === "traits") return character.traits.map(({ aptitude, amount }) => ({ aptitude, amount }));
    if (key === "gear") return character.gear.map(({ option, name }) => ({ option, name }));
    if (key === "language") return character.languages;
    return character[key].name;
};
for (const [target, preservedKeys] of Object.entries(rerollCases)) {
    const rerolled = rerollCharacter(data, baseCharacter, target, seededRandom(target.length * 997));
    assert.notDeepEqual(comparable(rerolled, target), comparable(baseCharacter, target), `${target} should change`);
    preservedKeys.forEach((key) => assert.deepEqual(comparable(rerolled, key), comparable(baseCharacter, key), `${target} should preserve ${key}`));
}

let tenebrateCharacter;
for (let seed = 1; seed <= 1000 && !tenebrateCharacter; seed += 1) {
    const candidate = rollCharacters(data, 1, seededRandom(seed))[0];
    if (candidate.species.name === "Tenebrate" && candidate.quirk.name !== "Weary") tenebrateCharacter = candidate;
}
assert.ok(tenebrateCharacter, "expected a seeded Tenebrate regression fixture");
const darkGift = (character) => character.selections.find((selection) => selection.label === "Dark Gift")?.value;
for (const target of ["history", "calling", "traits", "gear", "coins", "name"]) {
    const rerolled = rerollCharacter(data, tenebrateCharacter, target, seededRandom(target.charCodeAt(0) * 313));
    assert.deepEqual(rerolled.languages, tenebrateCharacter.languages, `${target} should preserve languages`);
    assert.equal(darkGift(rerolled), darkGift(tenebrateCharacter), `${target} should preserve Dark Gift`);
}
const historyReroll = rerollCharacter(data, tenebrateCharacter, "history", seededRandom(0xD4A6));
assert.notEqual(historyReroll.history.name, tenebrateCharacter.history.name);
assert.deepEqual(historyReroll.languages, tenebrateCharacter.languages);
assert.equal(darkGift(historyReroll), darkGift(tenebrateCharacter));

let normalLanguageCharacter;
let nearsightedCharacter;
let fixedStrayCharacter;
let nearsightedStrayCharacter;
for (let seed = 1; seed <= 20000; seed += 1) {
    const candidate = rollCharacters(data, 1, seededRandom(seed))[0];
    const isStray = candidate.species.name === "Human, Dimensional Stray";
    const isNearsighted = candidate.quirk.name === "Nearsighted";
    if (!normalLanguageCharacter && !isStray && !isNearsighted) normalLanguageCharacter = candidate;
    if (!nearsightedCharacter && !isStray && isNearsighted) nearsightedCharacter = candidate;
    if (!fixedStrayCharacter && isStray && !isNearsighted) fixedStrayCharacter = candidate;
    if (!nearsightedStrayCharacter && isStray && isNearsighted) nearsightedStrayCharacter = candidate;
    if (normalLanguageCharacter && nearsightedCharacter && fixedStrayCharacter && nearsightedStrayCharacter) break;
}
assert.ok(normalLanguageCharacter && nearsightedCharacter && fixedStrayCharacter && nearsightedStrayCharacter);
const homelandLanguages = (character) => data.homelands.find((homeland) => homeland.name === character.homeland.name)?.languages || [];
const rerolledNormalLanguage = rerollCharacter(data, normalLanguageCharacter, "language", seededRandom(0x1A46));
assert.equal(rerolledNormalLanguage.languages[0], "Low Speech");
assert.ok(homelandLanguages(normalLanguageCharacter).includes(rerolledNormalLanguage.languages[1]));
assert.notDeepEqual(rerolledNormalLanguage.languages, normalLanguageCharacter.languages);
assert.equal(rerolledNormalLanguage.history.name, normalLanguageCharacter.history.name);

const rerolledNearsightedLanguage = rerollCharacter(data, nearsightedCharacter, "language", seededRandom(0xE4A5));
assert.equal(rerolledNearsightedLanguage.languages.length, 4);
assert.equal(new Set(rerolledNearsightedLanguage.languages).size, 4);
assert.ok(homelandLanguages(nearsightedCharacter).includes(rerolledNearsightedLanguage.languages[1]));
assert.notDeepEqual(rerolledNearsightedLanguage.languages, nearsightedCharacter.languages);
assert.equal(rerolledNearsightedLanguage.quirk.name, "Nearsighted");

assert.equal(fixedStrayCharacter.languageRerollable, false);
assert.deepEqual(fixedStrayCharacter.languages, ["Low Speech", "Other Wording"]);
assert.equal(nearsightedStrayCharacter.languageRerollable, true);
const rerolledStrayLanguage = rerollCharacter(data, nearsightedStrayCharacter, "language", seededRandom(0x57A4));
assert.deepEqual(rerolledStrayLanguage.languages.slice(0, 2), ["Low Speech", "Other Wording"]);
assert.equal(rerolledStrayLanguage.languages.length, 4);
assert.equal(new Set(rerolledStrayLanguage.languages).size, 4);
assert.notDeepEqual(rerolledStrayLanguage.languages, nearsightedStrayCharacter.languages);

const seen = {
    callings: new Set(),
    species: new Set(),
    quirks: new Set(),
    nameTables: new Set(),
    callingRestriction: false,
    sizeRestriction: false,
    armorDefense: false,
    shieldDefense: false,
};

for (let seed = 1; seed <= 5000; seed += 1) {
    const [character] = rollCharacters(data, 1, seededRandom(seed));
    seen.callings.add(character.calling.name);
    seen.species.add(character.species.name);
    seen.quirks.add(character.quirk.name);
    seen.nameTables.add(character.nameTable);

    assert.ok(character.name.length > 0);
    assert.notEqual(character.name, "(Random name from another chart)");
    assert.ok(data.nameTables[character.nameTable].some((entry) => entry.name === character.name));
    assert.ok(character.rolls.name.length >= 1);
    assert.equal(Object.keys(character.aptitudes).length, 5);
    assert.ok(Object.values(character.aptitudes).every(Number.isInteger));
    assert.ok(character.combat.hearts >= 1);
    assert.ok(character.combat.inventory >= 8);
    assert.equal(character.traits.length, 3);
    assert.ok(character.modifiers);
    assert.ok(character.gear.length >= 4);
    assert.notEqual(character.gear[0].option, character.gear[1].option);
    assert.equal(new Set(character.languages).size, character.languages.length);
    assert.ok(character.abilities.calling.length >= 3);
    assert.ok(character.abilities.species.length >= 1);

    const calling = data.callings.find((entry) => entry.name === character.calling.name);
    const sizeRule = data.sizeRules[character.size.name];
    for (const gear of character.gear.filter((item) => item.gearCategory)) {
        const callingRestricted = !calling.gearAllowance[gear.gearCategory].includes(gear.gearType);
        const sizeRestricted = sizeRule.restricted[gear.gearCategory].includes(gear.gearType);
        assert.equal(gear.restricted, callingRestricted || sizeRestricted);
        assert.equal(gear.restrictions.some((restriction) => restriction.source === calling.name), callingRestricted);
        assert.equal(gear.restrictions.some((restriction) => restriction.source === `${character.size.name} Species`), sizeRestricted);
        seen.callingRestriction ||= callingRestricted;
        seen.sizeRestriction ||= sizeRestricted;
    }
    const expectedArmorBonus = Math.max(0, ...character.gear.filter((item) => item.gearCategory === "armor").map((item) => item.defenseBonus));
    const expectedShieldBonus = Math.max(0, ...character.gear.filter((item) => item.gearCategory === "shields").map((item) => item.defenseBonus));
    const gearDefenseModifiers = character.modifiers.combat.defense.filter((modifier) => modifier.kind === "gear");
    assert.equal(gearDefenseModifiers.reduce((total, modifier) => total + modifier.amount, 0), expectedArmorBonus + expectedShieldBonus);
    seen.armorDefense ||= expectedArmorBonus > 0;
    seen.shieldDefense ||= expectedShieldBonus > 0;

    if (character.species.name === "Human, Dimensional Stray") {
        assert.equal(character.homeland.name, "Other World");
        assert.equal(character.rolls.homeland, null);
        assert.ok(character.languages.includes("Other Wording"));
        assert.ok(character.selections.some((selection) => selection.label === "Leisurely Focus"));
    }
    if (character.species.name === "Tenebrate") {
        assert.equal(character.allegiance, "1 Dark");
        assert.ok(character.selections.some((selection) => selection.label === "Dark Gift"));
    }
    if (character.species.name === "Promethean") assert.equal(character.allegiance, "1 Bright");
    if (!["Tenebrate", "Promethean"].includes(character.species.name)) assert.equal(character.allegiance, "None");
    if (character.calling.name === "Battle Princess") {
        assert.ok(character.selections.some((selection) => selection.label === "Soul Companion"));
    }
    if (character.quirk.name === "Weary") {
        const wearyPath = character.selections.find((selection) => selection.label === "Weary Path");
        assert.ok(wearyPath);
        if (wearyPath.value.startsWith("Walker")) {
            assert.ok(character.additionalHistory);
            assert.notEqual(character.additionalHistory.name, character.history.name);
            assert.equal(character.gear.length, 6);
        } else {
            assert.equal(character.additionalHistory, null);
            assert.equal(character.gear.length, 5);
            assert.ok(character.modifiers.combat.attack.some((modifier) => modifier.source === "Weary" && modifier.amount === 1));
        }
    }
    if (character.quirk.name === "Bioskin") assert.ok(character.selections.some((selection) => selection.label === "Bioskin"));
    if (character.quirk.name === "Figment Follower") assert.ok(character.selections.some((selection) => selection.label === "Figment Follower"));
    const quirkAdjustment = data.quirkAdjustments[character.quirk.name] || {};
    for (const [aptitude, amount] of Object.entries(quirkAdjustment.aptitudes || {})) {
        assert.ok(character.modifiers.aptitudes[aptitude].some((modifier) => modifier.source === character.quirk.name && modifier.amount === amount));
    }
    for (const key of ["attack", "hearts", "defense", "speed"]) {
        if (quirkAdjustment[key]) {
            assert.ok(character.modifiers.combat[key].some((modifier) => modifier.source === character.quirk.name && modifier.amount === quirkAdjustment[key]));
        }
    }
    if (quirkAdjustment.defenseSet !== undefined) {
        assert.ok(character.modifiers.combat.defense.some((modifier) => modifier.source === character.quirk.name && modifier.kind === "set" && modifier.amount === quirkAdjustment.defenseSet));
    }
    if (character.quirk.name === "Nearsighted") assert.ok(character.modifiers.aptitudes.insight.some((modifier) => modifier.source === "Nearsighted" && modifier.amount === 1));
    if (character.quirk.name === "Girthsome") {
        assert.ok(character.modifiers.aptitudes.grit.some((modifier) => modifier.source === "Girthsome" && modifier.amount === 1));
        assert.ok(character.modifiers.combat.hearts.some((modifier) => modifier.source === "Girthsome" && modifier.amount === 1));
        assert.ok(character.modifiers.combat.speed.some((modifier) => modifier.source === "Girthsome" && modifier.amount === -1));
    }
    if (character.quirk.name === "Unhinged") {
        assert.ok(character.modifiers.combat.attack.some((modifier) => modifier.source === "Unhinged" && modifier.amount === 2));
        assert.ok(character.modifiers.combat.defense.some((modifier) => modifier.source === "Unhinged" && modifier.amount === -1));
    }

    const allowedCategories = data.quirkCategoryTables[
        data.species.find((entry) => entry.name === character.species.name).quirkTable
    ].map((entry) => entry.name);
    assert.ok(allowedCategories.includes(character.quirk.category));
}

assert.equal(seen.callings.size, data.callings.length);
assert.equal(seen.species.size, data.species.length);
assert.equal(seen.quirks.size, 50);
assert.equal(seen.nameTables.size, 10);
assert.equal(seen.callingRestriction, true);
assert.equal(seen.sizeRestriction, true);
assert.equal(seen.armorDefense, true);
assert.equal(seen.shieldDefense, true);
console.log("5000 seeded character rolls passed");