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

    const sizeAptitudes = data.sizeRules[character.size.name].aptitudes;
    for (const aptitude of data.choices.aptitudes) {
        const sizeModifier = character.modifiers.aptitudes[aptitude].find((modifier) => modifier.kind === "species");
        if (sizeAptitudes[aptitude]) {
            assert.deepEqual(sizeModifier, { source: `${character.size.name} Species`, amount: sizeAptitudes[aptitude], kind: "species" });
        } else {
            assert.equal(sizeModifier, undefined);
        }
    }
    const expectedSizeInventoryDelta = data.sizeRules[character.size.name].inventory - data.sizeRules.Medium.inventory;
    const sizeInventoryModifier = character.modifiers.combat.inventory.find((modifier) => modifier.kind === "species");
    if (expectedSizeInventoryDelta) {
        assert.deepEqual(sizeInventoryModifier, { source: `${character.size.name} Species`, amount: expectedSizeInventoryDelta, kind: "species" });
    } else {
        assert.equal(sizeInventoryModifier, undefined);
    }
    const expectedCallingInventory = data.expandedCallings.find((calling) => calling.name === character.calling.name)?.inventoryBonus
        ?? data.callings.find((calling) => calling.name === character.calling.name)?.inventoryBonus
        ?? 0;
    if (expectedCallingInventory) {
        assert.ok(character.modifiers.combat.inventory.some((modifier) => modifier.source === "Factotum Pack" && modifier.amount === 8));
    }
    if (character.species.name === "Dwarf") {
        assert.ok(character.modifiers.combat.inventory.some((modifier) => modifier.source === "Sturdy" && modifier.amount === 2));
    }
    assert.equal(character.combat.inventory, data.sizeRules[character.size.name].inventory + (character.species.name === "Dwarf" ? 2 : 0) + expectedCallingInventory);
    const speciesDefenseModifier = character.modifiers.combat.defense.find((modifier) => modifier.kind === "species");
    if (data.quirkAdjustments[character.quirk.name]?.defenseSet !== undefined || !data.sizeRules[character.size.name].defense) {
        assert.equal(speciesDefenseModifier, undefined);
    } else {
        assert.deepEqual(speciesDefenseModifier, { source: `${character.size.name} Species`, amount: data.sizeRules[character.size.name].defense, kind: "species" });
    }

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

const expectedExpandedCallings = new Set(data.expandedCallings.map((calling) => calling.name));
const seenExpandedCallings = new Set();
const expectedExpandedSpecies = new Set(data.expandedSpecies.map((species) => species.name));
const seenExpandedSpecies = new Set();
const seenMundymuttSizes = new Set();
const expectedVariantAbilities = {
    "Scribe": ["Journey Journal", "Folklorist", "Don't Mind Me"],
    "Scoundrel": ["Sidestep", "Furtive", "Flanker"],
    "Bruiser": ["Brawler", "Brazen Defense", "Into the Fray"],
    "Bladesmith": ["Like the Wind", "Ranger", "Artisan Smithy"],
    "Bright-Heart Paladin": ["Holy Sword", "Bonded Mount", "Lay on Hands"],
    "Haunted Knight": ["Wrath's Blade", "Beloved Wraith", "Frost Blade"],
    "Mountebank": ["Murky Mask", "Light Footed", "Prestidigitonium"],
    "Soothsayer": ["Fitful Sleep", "Dire Divination", "Seer Kasnah"],
};
for (let seed = 1; seed <= 10000; seed += 1) {
    const character = rollCharacters(data, 1, seededRandom(seed), "expanded")[0];
    seenExpandedCallings.add(character.calling.name);
    seenExpandedSpecies.add(character.species.name);
    if (character.species.name === "Mundymutt") seenMundymuttSizes.add(character.size.name);
    assert.equal(character.contentMode, "expanded");
    assert.ok(character.rolls.calling !== 4);
    if (expectedVariantAbilities[character.calling.name]) {
        assert.deepEqual(character.abilities.calling.map((ability) => ability.name), expectedVariantAbilities[character.calling.name]);
        assert.equal(character.calling.expanded, true);
        assert.ok(character.calling.sourceUrl);
    }
    if (character.calling.name === "Bright-Heart Paladin") {
        assert.ok(character.selections.some((selection) => selection.label === "Holy Sword"));
        assert.ok(character.selections.some((selection) => selection.label === "Bonded Mount" && selection.value === "Guardian Animal / Mount"));
    }
    if (character.calling.name === "Haunted Knight") {
        assert.ok(character.selections.some((selection) => selection.label === "Wrath's Blade"));
    }
    if (character.calling.name === "Bruiser") {
        const armorBonus = Math.max(0, ...character.gear.filter((item) => item.gearCategory === "armor").map((item) => item.defenseBonus));
        if (armorBonus < 4) assert.ok(character.modifiers.combat.defense.some((modifier) => modifier.source === "Brazen Defense" && modifier.amount === 4));
    }
    if (character.calling.name === "Balladeer") {
        assert.deepEqual(character.abilities.calling.map((ability) => ability.name), ["Leitmotif", "Focus Instrument", "The Song in Your Heart"]);
        assert.ok(character.selections.some((selection) => selection.label === "Focus Instrument" && selection.rerollable === false));
    }
    if (character.calling.name === "Henshin Hero") {
        assert.deepEqual(character.abilities.calling.map((ability) => ability.name), ["Transformation Driver", "Primary Form", "Finisher"]);
        assert.deepEqual(character.calling.sourceUrl, data.expandedCallings.find((calling) => calling.name === "Henshin Hero").sourceUrl);
        assert.equal(character.combat.attack, 1 + (character.modifiers.combat.attack.find((modifier) => modifier.source === character.quirk.name)?.amount || 0));
        const motifs = character.selections.find((selection) => selection.label === "Heroic Motifs").value.split(" / ");
        const benefits = character.selections.find((selection) => selection.label === "Driver Benefits").value.split(" / ");
        assert.ok(motifs.length >= 1 && motifs.length <= 3);
        assert.equal(new Set(motifs).size, motifs.length);
        assert.equal(benefits.length, 2);
        assert.equal(new Set(benefits).size, 2);
        assert.equal(character.selections.some((selection) => selection.label === "Driver Weapon"), benefits.includes("Weapon"));
        assert.ok(data.choices.henshinForms.includes(character.selections.find((selection) => selection.label === "Primary Form").value));
        assert.ok(data.choices.henshinFinishers.includes(character.selections.find((selection) => selection.label === "Finisher Quality").value));
        const allowance = data.expandedCallings.find((calling) => calling.name === "Henshin Hero").gearAllowance;
        for (const item of character.gear.filter((gear) => gear.gearCategory)) {
            const callingRestricted = !allowance[item.gearCategory].includes(item.gearType);
            assert.equal(item.restrictions.some((restriction) => restriction.source === "Henshin Hero"), callingRestricted);
        }
    }
    if (["Hoppalong", "Gadabovid", "Mundymutt"].includes(character.species.name)) {
        assert.equal(data.expandedSpecies.find((species) => species.name === character.species.name).quirkTable, "Inheritor");
        assert.ok(data.nameTables[character.nameTable].some((entry) => entry.name === character.name));
        assert.equal(character.species.expanded, true);
    }
}
assert.deepEqual(seenExpandedCallings, expectedExpandedCallings);
assert.deepEqual(seenExpandedSpecies, expectedExpandedSpecies);
assert.deepEqual(seenMundymuttSizes, new Set(["Small", "Medium", "Large"]));
assert.ok(!seenExpandedCallings.has("Purr"));
assert.ok(seenExpandedCallings.has("Henshin Hero"));
assert.ok(seenExpandedCallings.has("Balladeer"));

const neridianOrigins = { standard: 0, undersea: 0 };
const seenNeridianHistories = new Set();
const neridianFixtures = [];
for (let seed = 1; seed <= 100000 && neridianFixtures.length < 200; seed += 1) {
    const character = rollCharacters(data, 1, seededRandom(seed), "expanded")[0];
    if (character.species.name !== "Neridian") continue;
    neridianFixtures.push(character);
    assert.equal(character.species.expanded, true);
    const henshinMotif = character.calling.name === "Henshin Hero"
        ? character.selections.find((selection) => selection.label === "Allegiance Motif")?.value
        : null;
    assert.equal(character.allegiance, henshinMotif === "Light" ? "2 Bright / 1 Dark" : henshinMotif === "Dark" ? "3 Dark" : "1 Dark");
    assert.deepEqual(character.abilities.species.map((ability) => ability.name), ["Ocean Farer", "Sea Song"]);
    assert.ok(character.selections.some((selection) => selection.label === "Gift" && selection.value === "Melodious Voice" && selection.page === 207));
    assert.ok(data.nameTables.Neridian.some((entry) => entry.name === character.name));
    assert.ok(["Spirit", "Physiology", "Fate"].includes(character.quirk.category));
    if (character.history.sourceUrl) {
        neridianOrigins.undersea += 1;
        seenNeridianHistories.add(character.history.name);
        const sourceHistory = data.neridianHistories.find((history) => history.name === character.history.name);
        assert.equal(character.homeland.name, sourceHistory.homeland);
        assert.ok(character.gear.slice(0, 2).every((item) => item.sourceUrl === sourceHistory.sourceUrl));
        assert.equal(character.homelandRerollable, false);
    } else {
        neridianOrigins.standard += 1;
        assert.equal(character.homelandRerollable, true);
    }
}
assert.equal(neridianFixtures.length, 200);
assert.ok(neridianOrigins.standard >= 75 && neridianOrigins.standard <= 125, JSON.stringify(neridianOrigins));
assert.ok(neridianOrigins.undersea >= 75 && neridianOrigins.undersea <= 125, JSON.stringify(neridianOrigins));
assert.deepEqual(seenNeridianHistories, new Set(["Shadow Sea Recluse", "Ruin Dweller", "Coral Farmer"]));
const neridian = neridianFixtures[0];
const rerolledNeridianHistory = rerollCharacter(data, neridian, "history", seededRandom(0x0CE4));
assert.equal(rerolledNeridianHistory.species.name, "Neridian");
assert.equal(rerolledNeridianHistory.contentMode, "expanded");
assert.equal(rerolledNeridianHistory.calling.name, neridian.calling.name);
assert.deepEqual(rerolledNeridianHistory.traits, neridian.traits);
assert.equal(rerolledNeridianHistory.quirk.name, neridian.quirk.name);
assert.equal(rerolledNeridianHistory.coins, neridian.coins);
assert.ok(rerolledNeridianHistory.selections.some((selection) => selection.label === "Gift" && selection.value === "Melodious Voice"));

const unterkinFixtures = [];
const seenUnterkinCallings = new Set();
const seenUnterkinHistories = new Set();
const seenUnterkinQuirks = new Set();
const seenHeartCrafts = new Set();
for (let seed = 1; seed <= 200000 && unterkinFixtures.length < 300; seed += 1) {
    const character = rollCharacters(data, 1, seededRandom(seed), "expanded")[0];
    if (character.species.name !== "Unterkin") continue;
    unterkinFixtures.push(character);
    seenUnterkinCallings.add(character.calling.name);
    seenUnterkinHistories.add(character.history.name);
    seenUnterkinQuirks.add(character.quirk.category);
    seenHeartCrafts.add(character.selections.find((selection) => selection.label === "Heart's Craft")?.value);
    assert.equal(character.homeland.name, "Buried Kingdom");
    assert.equal(character.homelandRerollable, false);
    assert.equal(character.size.name, "Small");
    assert.ok(data.expandedSpecies.find((species) => species.name === "Unterkin").compatibleCallings.includes(character.calling.name));
    assert.notEqual(character.calling.name, "Henshin Hero");
    assert.ok(["Physiology", "Eldritch"].includes(character.quirk.category));
    assert.ok(data.nameTables.Unterkin.some((entry) => entry.name === character.name));
    assert.deepEqual(character.abilities.species.map((ability) => ability.name), ["Ageless", "Heart's Craft"]);
    assert.ok(character.history.sourceUrl);
    assert.ok(character.gear.slice(0, 2).every((item) => item.sourceUrl === character.history.sourceUrl));
}
assert.equal(unterkinFixtures.length, 300);
assert.deepEqual(seenUnterkinCallings, new Set(["Factotum", "Scribe", "Sneak", "Scoundrel", "Balladeer", "Sage", "Mountebank"]));
assert.deepEqual(seenUnterkinHistories, new Set(["Red Hand", "Fizzicist", "Storyteller", "Wonder Aspirant"]));
assert.deepEqual(seenUnterkinQuirks, new Set(["Physiology", "Eldritch"]));
assert.deepEqual(seenHeartCrafts, new Set(data.choices.craftingDisciplines));
const unterkin = unterkinFixtures[0];
for (let seed = 1; seed <= 100; seed += 1) {
    const rerolledCalling = rerollCharacter(data, unterkin, "calling", seededRandom(seed));
    assert.ok(data.expandedSpecies.find((species) => species.name === "Unterkin").compatibleCallings.includes(rerolledCalling.calling.name));
    assert.equal(rerolledCalling.species.name, "Unterkin");
}
const rerolledUnterkinHistory = rerollCharacter(data, unterkin, "history", seededRandom(0xA11CE));
assert.equal(rerolledUnterkinHistory.homeland.name, "Buried Kingdom");
assert.equal(rerolledUnterkinHistory.calling.name, unterkin.calling.name);
assert.equal(rerolledUnterkinHistory.quirk.name, unterkin.quirk.name);
let rerolledIntoUnterkin;
const nonUnterkin = neridianFixtures[0];
for (let seed = 1; seed <= 10000 && !rerolledIntoUnterkin; seed += 1) {
    const candidate = rerollCharacter(data, nonUnterkin, "species", seededRandom(seed));
    if (candidate.species.name === "Unterkin") rerolledIntoUnterkin = candidate;
}
assert.ok(rerolledIntoUnterkin);
assert.equal(rerolledIntoUnterkin.contentMode, "expanded");
assert.ok(data.expandedSpecies.find((species) => species.name === "Unterkin").compatibleCallings.includes(rerolledIntoUnterkin.calling.name));

const henshinFixtures = [];
const seenHenshinForms = new Set();
const seenHenshinFinishers = new Set();
const seenHenshinMotifs = new Set();
const seenHenshinAllegiances = new Set();
let henshinWithDriverWeapon = false;
for (let seed = 1; seed <= 100000 && henshinFixtures.length < 250; seed += 1) {
    const character = rollCharacters(data, 1, seededRandom(seed), "expanded")[0];
    if (character.calling.name !== "Henshin Hero") continue;
    henshinFixtures.push(character);
    const selections = Object.fromEntries(character.selections.map((selection) => [selection.label, selection.value]));
    seenHenshinForms.add(selections["Primary Form"]);
    seenHenshinFinishers.add(selections["Finisher Quality"]);
    seenHenshinAllegiances.add(selections["Allegiance Motif"]);
    selections["Heroic Motifs"].split(" / ").forEach((motif) => seenHenshinMotifs.add(motif));
    henshinWithDriverWeapon ||= Boolean(selections["Driver Weapon"]);
    const speciesBright = character.species.name === "Promethean" ? 1 : 0;
    const speciesDark = ["Tenebrate", "Neridian"].includes(character.species.name) ? 1 : 0;
    const expectedBright = speciesBright + (selections["Allegiance Motif"] === "Light" ? 2 : 0);
    const expectedDark = speciesDark + (selections["Allegiance Motif"] === "Dark" ? 2 : 0);
    const expectedAllegiance = [expectedBright && `${expectedBright} Bright`, expectedDark && `${expectedDark} Dark`].filter(Boolean).join(" / ") || "None";
    assert.equal(character.allegiance, expectedAllegiance);
    const expectedGiftCount = Math.floor(expectedBright / 3) + Math.floor(expectedDark / 3);
    const allegianceGifts = character.selections.filter((selection) => selection.label === "Allegiance Gift");
    assert.equal(allegianceGifts.length, expectedGiftCount);
    assert.equal(character.modifiers.combat.allegiance.filter((modifier) => modifier.kind === "gift").length, expectedGiftCount);
    for (const gift of allegianceGifts) {
        const [alignment, name] = gift.value.split(": ");
        const table = alignment === "Bright" ? data.choices.brightGifts : data.choices.darkGifts;
        assert.ok(table.includes(name));
        assert.equal(gift.page, alignment === "Bright" ? 206 : 207);
    }
}
assert.equal(henshinFixtures.length, 250);
assert.deepEqual(seenHenshinForms, new Set(data.choices.henshinForms));
assert.deepEqual(seenHenshinFinishers, new Set(data.choices.henshinFinishers));
assert.deepEqual(seenHenshinMotifs, new Set(data.choices.henshinMotifs));
assert.deepEqual(seenHenshinAllegiances, new Set(data.choices.henshinAllegianceMotifs));
assert.equal(henshinWithDriverWeapon, true);
const henshin = henshinFixtures[0];
const rerolledHenshinChoices = rerollCharacter(data, henshin, "choices", seededRandom(0x445256));
assert.equal(rerolledHenshinChoices.calling.name, "Henshin Hero");
assert.equal(rerolledHenshinChoices.species.name, henshin.species.name);
assert.notDeepEqual(rerolledHenshinChoices.selections, henshin.selections);
const expandedCharacter = rollCharacters(data, 1, seededRandom(0xE7A4), "expanded")[0];
const rerolledExpandedCalling = rerollCharacter(data, expandedCharacter, "calling", seededRandom(0xCA11));
assert.equal(rerolledExpandedCalling.contentMode, "expanded");
assert.ok(expectedExpandedCallings.has(rerolledExpandedCalling.calling.name));
console.log("Core and expanded seeded character tests passed");