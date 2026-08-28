import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { removeGearItem, rerollCharacter, rollCharacter, rollCharacters } from "./generator.mjs";


const data = JSON.parse(await readFile(new URL("./data.json", import.meta.url), "utf8"));
assert.equal(data.schemaVersion, 3);
assert.deepEqual(Object.keys(data.advancementTables).sort(), [
    "Balladeer", "Battle Princess", "Champion", "Factotum", "Henshin Hero",
    "Heretic", "Murder Princess", "Raider", "Sage", "Sneak",
]);
for (const [callingName, table] of Object.entries(data.advancementTables)) {
    assert.equal(table.length, 10, `${callingName} should have ten advancement rows`);
    assert.deepEqual(table.map((row) => row.rank), [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
    assert.deepEqual(table.map((row) => row.standardAbilities), [0, 1, 1, 2, 2, 2, 2, 2, 2, 2]);
    assert.deepEqual(table.map((row) => row.flexibleAbilities), [0, 0, 0, 0, 0, 1, 1, 2, 2, 3]);
}
assert.equal(data.advancementTables.Champion[9].attack, 10);
assert.equal(data.advancementTables.Champion[9].hearts, 7);
assert.deepEqual(data.advancementTables.Champion[9].aptitudes, { might: 14, deftness: 12, grit: 13, insight: 11, aura: 12 });
assert.deepEqual(data.advancementTables.Balladeer[9].aptitudes, { might: 10, deftness: 11, grit: 11, insight: 14, aura: 14 });
assert.equal(data.advancementTables["Henshin Hero"][9].attack, 7);
for (const calling of Object.values(data.callingAbilities)) {
    assert.ok(calling.starting.length >= 3);
    assert.ok(calling.standard.length >= 6);
    assert.ok(calling.advanced.length >= 6);
}
const publicAbilityKeys = new Set(["name", "pages", "sourceUrl", "tier", "magical", "allegiance", "repeatable", "effects"]);
for (const ability of [
    ...Object.values(data.callingAbilities).flatMap((calling) => [...calling.starting, ...calling.standard, ...calling.advanced]),
    ...Object.values(data.speciesMaturatives),
]) {
    assert.ok(Object.keys(ability).every((key) => publicAbilityKeys.has(key)), `${ability.name} has an unsafe public field`);
    assert.equal(typeof ability.name, "string");
}
assert.equal(data.speciesMaturatives.Gadabovid.name, "Labyrinthian Intuition");
assert.equal(data.speciesMaturatives.Mundymutt, undefined);
const hereticAllowance = data.callings.find((calling) => calling.name === "Heretic").gearAllowance;
assert.ok(hereticAllowance.weapons.includes("Lash"));
assert.ok(!hereticAllowance.weapons.includes("Master"));
assert.ok(data.sizeRules.Small.restricted.weapons.includes("Mighty"));
assert.ok(data.sizeRules.Small.restricted.weapons.includes("Arc"));
assert.ok(data.shopItems.length > 60);
const publicShopKeys = new Set(["name", "page", "category", "costStones", "slotTenths", "stackLimit", "inventoryBonusTenths", "gearCategory", "gearType", "defenseBonus"]);
for (const item of data.shopItems) {
    assert.ok(Object.keys(item).every((key) => publicShopKeys.has(key)));
    assert.equal(typeof item.name, "string");
    assert.ok(Number.isInteger(item.costStones));
    assert.ok(Number.isInteger(item.slotTenths));
}
const allHistories = [...Object.values(data.histories).flat(), ...data.neridianHistories, ...data.unterkinHistories];
for (const history of allHistories) {
    assert.ok(history.gear.every((item) => Object.hasOwn(item, "costStones")), `${history.name} should expose every starting cost`);
}
const startingItem = (name) => allHistories.flatMap((history) => history.gear).find((item) => item.name === name);
assert.equal(startingItem("Basic Potion x2").costStones, 2000);
assert.equal(startingItem("Treats x10").costStones, 30);
assert.equal(startingItem("Follower: Custrel").costRate, "per day");
assert.equal(startingItem("Tattered Outfit").costStones, 0);
assert.equal(startingItem("Other World Pocket Device").costStones, null);
assert.equal(startingItem("50 Coins").currencyStones, 5000);
assert.equal(startingItem("Gem x1").currencyStones, 10000);

function currencyUnitCount(totalStones) {
    const gems = Math.floor(totalStones / 10000);
    const afterGems = totalStones % 10000;
    return gems + Math.floor(afterGems / 100) + afterGems % 100;
}
assert.equal(currencyUnitCount(10000), 1);
assert.equal(currencyUnitCount(5000), 50);
assert.equal(currencyUnitCount(10068), 69);

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
assert.deepEqual(baseCharacter.purchasedGear, []);
assert.equal(baseCharacter.shopping.budgetCoins, 0);
assert.equal(baseCharacter.shopping.spentStones, 0);
assert.equal(baseCharacter.currencyWeightEnabled, false);
assert.equal(baseCharacter.shopping.currencySlotHundredths, 0);
assert.deepEqual(baseCharacter.abilities.elective, []);

const rankTenCharacter = rollCharacter(data, seededRandom(0xC0FFEE), baseCharacter.seeds, baseCharacter.contentMode, 0, false, 10);
const baseAdvancement = data.advancementTables[baseCharacter.calling.name][0];
const rankTenAdvancement = data.advancementTables[baseCharacter.calling.name][9];
assert.equal(rankTenCharacter.rank, 10);
assert.equal(rankTenCharacter.name, baseCharacter.name);
assert.equal(rankTenCharacter.calling.name, baseCharacter.calling.name);
assert.equal(rankTenCharacter.species.name, baseCharacter.species.name);
assert.equal(rankTenCharacter.history.name, baseCharacter.history.name);
assert.equal(rankTenCharacter.quirk.name, baseCharacter.quirk.name);
assert.deepEqual(rankTenCharacter.traits, baseCharacter.traits);
assert.deepEqual(rankTenCharacter.gear.map((item) => item.name), baseCharacter.gear.map((item) => item.name));
assert.equal(rankTenCharacter.combat.attack - baseCharacter.combat.attack, rankTenAdvancement.attack - baseAdvancement.attack);
assert.equal(rankTenCharacter.combat.hearts - baseCharacter.combat.hearts, rankTenAdvancement.hearts - baseAdvancement.hearts);
for (const aptitude of data.choices.aptitudes) {
    assert.equal(rankTenCharacter.aptitudes[aptitude] - baseCharacter.aptitudes[aptitude],
        rankTenAdvancement.aptitudes[aptitude] - baseAdvancement.aptitudes[aptitude]);
}
assert.equal(rollCharacter(data, seededRandom(1), {}, "core", 0, false, 99).rank, 10);
assert.equal(rollCharacter(data, seededRandom(1), {}, "core", 0, false, 0).rank, 1);

const seenRankedCallings = new Set();
for (let seed = 1; seed <= 20000 && seenRankedCallings.size < data.expandedCallings.length; seed += 1) {
    const rankOne = rollCharacter(data, seededRandom(seed), {}, "expanded", 0, false, 1);
    if (seenRankedCallings.has(rankOne.calling.name)) continue;
    const rankTen = rollCharacter(data, seededRandom(seed + 1), rankOne.seeds, "expanded", 0, false, 10);
    const progressionName = rankOne.calling.baseCalling || rankOne.calling.name;
    const firstRow = data.advancementTables[progressionName][0];
    const lastRow = data.advancementTables[progressionName][9];
    assert.equal(rankTen.calling.name, rankOne.calling.name);
    assert.equal(rankTen.combat.attack - rankOne.combat.attack, lastRow.attack - firstRow.attack);
    assert.equal(rankTen.combat.hearts - rankOne.combat.hearts, lastRow.hearts - firstRow.hearts);
    for (const aptitude of data.choices.aptitudes) {
        assert.equal(rankTen.aptitudes[aptitude] - rankOne.aptitudes[aptitude],
            lastRow.aptitudes[aptitude] - firstRow.aptitudes[aptitude]);
    }
    seenRankedCallings.add(rankOne.calling.name);
}
assert.equal(seenRankedCallings.size, data.expandedCallings.length);

for (const rank of [1, 2, 4, 6, 8, 10]) {
    const character = rollCharacter(data, seededRandom(rank * 101), {}, "core", 0, false, rank);
    const expectedCount = [2, 4, 6, 8, 10].filter((milestone) => milestone <= rank).length;
    assert.equal(character.abilities.elective.length, expectedCount);
    assert.deepEqual(character.abilities.elective.map((ability) => ability.acquiredRank),
        [2, 4, 6, 8, 10].filter((milestone) => milestone <= rank));
    assert.ok(character.abilities.elective.filter((ability) => ability.acquiredRank < 6)
        .every((ability) => ability.tier === "Standard"));
    const nonRepeatable = character.abilities.elective.filter((ability) => !ability.repeatable).map((ability) => ability.name);
    assert.equal(new Set(nonRepeatable).size, nonRepeatable.length);
}

let sawStandardFlexible = false;
let sawAdvancedFlexible = false;
let sawMaturativeFlexible = false;
for (let seed = 1; seed <= 1000; seed += 1) {
    const character = rollCharacter(data, seededRandom(seed), {}, "expanded", 0, false, 10);
    const flexible = character.abilities.elective.filter((ability) => ability.acquiredRank >= 6);
    sawStandardFlexible ||= flexible.some((ability) => ability.tier === "Standard");
    sawAdvancedFlexible ||= flexible.some((ability) => ability.tier === "Advanced");
    sawMaturativeFlexible ||= flexible.some((ability) => ability.tier === "Maturative");
    if (character.species.name === "Mundymutt") assert.ok(flexible.every((ability) => ability.tier !== "Maturative"));
}
assert.ok(sawStandardFlexible && sawAdvancedFlexible && sawMaturativeFlexible);
const rankTenAbilityCharacter = rollCharacter(data, seededRandom(0xAB1117), {}, "core", 0, false, 10);
const rerolledRankTenAbilities = rerollCharacter(data, rankTenAbilityCharacter, "abilities", seededRandom(0xAB1118));
assert.notDeepEqual(rerolledRankTenAbilities.abilities.elective, rankTenAbilityCharacter.abilities.elective);
assert.equal(rerolledRankTenAbilities.rank, 10);
assert.equal(rerolledRankTenAbilities.name, rankTenAbilityCharacter.name);
assert.deepEqual(rerolledRankTenAbilities.gear, rankTenAbilityCharacter.gear);

let rankTenChampion;
let rankTenBattlePrincess;
let rankTenMurderPrincess;
let rankTenHenshin;
let rankTenStaticSpeed;
let rankTenStowing;
let rankTenBrightHeart;
let rankTenHauntedKnight;
for (let seed = 1; seed <= 20000 && (!rankTenChampion || !rankTenBattlePrincess || !rankTenMurderPrincess || !rankTenHenshin || !rankTenStaticSpeed || !rankTenStowing || !rankTenBrightHeart || !rankTenHauntedKnight); seed += 1) {
    const core = rollCharacter(data, seededRandom(seed), {}, "core", 0, false, 10);
    if (core.calling.name === "Champion") rankTenChampion ||= core;
    if (core.calling.name === "Battle Princess") rankTenBattlePrincess ||= core;
    if (core.calling.name === "Murder Princess") rankTenMurderPrincess ||= core;
    if (core.abilities.elective.some((ability) => ability.effects?.speed)) rankTenStaticSpeed ||= core;
    if (core.abilities.elective.some((ability) => ability.name === "Stowing")) rankTenStowing ||= core;
    const expanded = rollCharacter(data, seededRandom(seed), {}, "expanded", 0, false, 10);
    if (expanded.calling.name === "Henshin Hero") rankTenHenshin ||= expanded;
    if (expanded.calling.name === "Bright-Heart Paladin") rankTenBrightHeart ||= expanded;
    if (expanded.calling.name === "Haunted Knight") rankTenHauntedKnight ||= expanded;
}
assert.ok(rankTenChampion && rankTenBattlePrincess && rankTenMurderPrincess && rankTenHenshin && rankTenStaticSpeed && rankTenStowing && rankTenBrightHeart && rankTenHauntedKnight);
assert.equal(rankTenChampion.selections.find((selection) => selection.label === "Favored Weapon").value.split(" / ").length, 2);
for (const princess of [rankTenBattlePrincess, rankTenMurderPrincess]) {
    const bladeLabel = princess.calling.name === "Battle Princess" ? "Heart's Blade" : "Wrath's Blade";
    assert.ok(princess.selections.find((selection) => selection.label === bladeLabel).value.includes(" + "));
    assert.ok(princess.selections.some((selection) => selection.label === `${bladeLabel.split(" Blade")[0]} Blade Property`));
}
assert.ok(rankTenBattlePrincess.selections.find((selection) => selection.label === "Soul Companion").value.includes("+1 Heart"));
assert.equal(rankTenBattlePrincess.selections.find((selection) => selection.label === "Shield of Love").value, "3 people");
assert.equal(rankTenHenshin.selections.find((selection) => selection.label === "Finisher Quality").value.split(" / ").length, 2);
assert.ok(rankTenBrightHeart.selections.find((selection) => selection.label === "Holy Sword").value.includes(" + "));
assert.ok(rankTenBrightHeart.selections.some((selection) => selection.label === "Holy Sword Property"));
assert.ok(rankTenHauntedKnight.selections.find((selection) => selection.label === "Wrath's Blade").value.includes(" + "));
assert.ok(rankTenHauntedKnight.selections.some((selection) => selection.label === "Wrath's Blade Property"));
assert.ok(rankTenStaticSpeed.modifiers.combat.speed.some((modifier) => modifier.kind === "ability"));
const stowedItems = [...rankTenStowing.gear, ...rankTenStowing.purchasedGear].filter((item) => item.stowed);
assert.equal(stowedItems.length, 1);
assert.ok(stowedItems[0].slotTenths > 0 && stowedItems[0].slotTenths <= 10);
assert.equal(stowedItems[0].name, rankTenStowing.stowedItem);

for (let seed = 1; seed <= 1000; seed += 1) {
    const character = rollCharacter(data, seededRandom(seed), {}, "expanded", 0, false, 10);
    let bright = character.species.name === "Promethean" ? 1 : 0;
    let dark = ["Tenebrate", "Neridian"].includes(character.species.name) ? 1 : 0;
    const henshinMotif = character.selections.find((selection) => selection.label === "Allegiance Motif")?.value;
    if (henshinMotif === "Light") bright += 2;
    if (henshinMotif === "Dark") dark += 2;
    for (const ability of [character.abilities.prodigy, ...character.abilities.elective].filter(Boolean)) {
        const allegiance = ability.allegiance || (character.calling.name === "Henshin Hero" && ability.magical ? henshinMotif : null);
        if (["Bright", "Light"].includes(allegiance)) bright += 1;
        if (allegiance === "Dark") dark += 1;
    }
    const expectedAllegiance = [bright ? `${bright} Bright` : "", dark ? `${dark} Dark` : ""].filter(Boolean).join(" / ") || "None";
    assert.equal(character.allegiance, expectedAllegiance);
    const allegianceSources = character.modifiers.combat.allegiance.filter((modifier) => modifier.kind === "allegiance");
    assert.equal(allegianceSources.filter((source) => source.alignment === "Bright").reduce((total, source) => total + source.amount, 0), bright);
    assert.equal(allegianceSources.filter((source) => source.alignment === "Dark").reduce((total, source) => total + source.amount, 0), dark);
    for (const ability of [character.abilities.prodigy, ...character.abilities.elective].filter(Boolean)) {
        const alignment = ability.allegiance || (character.calling.name === "Henshin Hero" && ability.magical ? henshinMotif : null);
        if (alignment) assert.ok(allegianceSources.some((source) => source.source === ability.name));
    }
    assert.equal(character.selections.filter((selection) => selection.value?.startsWith("Bright:")).length, Math.floor(bright / 3));
    assert.equal(character.selections.filter((selection) => selection.value?.startsWith("Dark:")).length, Math.floor(dark / 3));
}

const weightedBaseCharacter = rollCharacter(data, seededRandom(0xC0FFEE), baseCharacter.seeds, baseCharacter.contentMode, 0, true);
const weightedBaseCurrency = weightedBaseCharacter.coins * 100
    + weightedBaseCharacter.gear.reduce((total, item) => total + (item.currencyStones || 0), 0);
assert.equal(weightedBaseCharacter.currencyWeightEnabled, true);
assert.equal(weightedBaseCharacter.shopping.totalCurrencyStones, weightedBaseCurrency);
assert.equal(weightedBaseCharacter.shopping.currencySlotHundredths, currencyUnitCount(weightedBaseCurrency));
assert.equal(weightedBaseCharacter.shopping.usedSlotHundredths,
    [...weightedBaseCharacter.gear, ...weightedBaseCharacter.purchasedGear]
        .reduce((total, item) => total + (item.equipped || item.stowed ? 0 : item.slotTenths * 10), 0)
        + weightedBaseCharacter.shopping.currencySlotHundredths);
const rerolledWeightedCoins = rerollCharacter(data, weightedBaseCharacter, "coins", seededRandom(0xC01A));
assert.equal(rerolledWeightedCoins.currencyWeightEnabled, true);
assert.equal(rerolledWeightedCoins.shopping.currencySlotHundredths, currencyUnitCount(rerolledWeightedCoins.shopping.totalCurrencyStones));

const budgetCharacter = rollCharacter(data, seededRandom(0xB0D6E7), baseCharacter.seeds, baseCharacter.contentMode, 50);
assert.equal(budgetCharacter.name, baseCharacter.name);
assert.equal(budgetCharacter.coins, baseCharacter.coins);
assert.deepEqual(budgetCharacter.gear, baseCharacter.gear);
assert.equal(budgetCharacter.shopping.budgetCoins, 50);
assert.ok(budgetCharacter.purchasedGear.length > 0);
assert.ok(budgetCharacter.shopping.spentStones <= budgetCharacter.shopping.budgetStones);
assert.equal(budgetCharacter.shopping.remainingStones, budgetCharacter.shopping.budgetStones - budgetCharacter.shopping.spentStones);
assert.ok(budgetCharacter.shopping.usedSlotsTenths <= budgetCharacter.shopping.capacityTenths);
assert.equal(new Set(budgetCharacter.purchasedGear.map((item) => item.name)).size, budgetCharacter.purchasedGear.length);
assert.ok(budgetCharacter.purchasedGear.every((item) => !item.restricted));
assert.equal(budgetCharacter.shopping.purchasedSlotsTenths, budgetCharacter.purchasedGear.reduce((total, item) => total + (item.equipped || item.stowed ? 0 : item.slotTenths), 0));

const rerolledPurchases = rerollCharacter(data, budgetCharacter, "purchasedGear", seededRandom(0x5A0F));
assert.notDeepEqual(rerolledPurchases.purchasedGear.map((item) => item.name), budgetCharacter.purchasedGear.map((item) => item.name));
assert.equal(rerolledPurchases.name, budgetCharacter.name);
assert.equal(rerolledPurchases.coins, budgetCharacter.coins);
assert.deepEqual(rerolledPurchases.gear, budgetCharacter.gear);
assert.equal(rerolledPurchases.shopping.budgetCoins, 50);

const removableStartingIndex = budgetCharacter.gear.findIndex((item) => !item.equipped && !item.inventoryBonusTenths);
const removedStartingItem = budgetCharacter.gear[removableStartingIndex];
const withoutStartingItem = removeGearItem(budgetCharacter, "gear", removableStartingIndex);
assert.equal(withoutStartingItem.gear.length, budgetCharacter.gear.length - 1);
assert.equal(withoutStartingItem.shopping.remainingStones, budgetCharacter.shopping.remainingStones);
assert.equal(withoutStartingItem.shopping.usedSlotsTenths, budgetCharacter.shopping.usedSlotsTenths - removedStartingItem.slotTenths);
assert.equal(withoutStartingItem.coins, budgetCharacter.coins);

const removablePurchasedIndex = budgetCharacter.purchasedGear.findIndex((item) => !item.equipped && !item.inventoryBonusTenths);
const removedPurchasedItem = budgetCharacter.purchasedGear[removablePurchasedIndex];
const withoutPurchasedItem = removeGearItem(budgetCharacter, "purchasedGear", removablePurchasedIndex);
assert.equal(withoutPurchasedItem.purchasedGear.length, budgetCharacter.purchasedGear.length - 1);
assert.equal(withoutPurchasedItem.shopping.remainingStones, budgetCharacter.shopping.remainingStones + removedPurchasedItem.costStones);
assert.equal(withoutPurchasedItem.shopping.spentStones, budgetCharacter.shopping.spentStones - removedPurchasedItem.costStones);
assert.equal(withoutPurchasedItem.shopping.usedSlotsTenths, budgetCharacter.shopping.usedSlotsTenths - removedPurchasedItem.slotTenths);

const equippedSection = budgetCharacter.gear.some((item) => item.equipped) ? "gear" : "purchasedGear";
const equippedIndex = budgetCharacter[equippedSection].findIndex((item) => item.equipped);
const withoutEquippedOutfit = removeGearItem(budgetCharacter, equippedSection, equippedIndex);
const remainingEquipped = [...withoutEquippedOutfit.gear, ...withoutEquippedOutfit.purchasedGear].filter((item) => item.equipped);
assert.equal(remainingEquipped.length, 1);
assert.equal(remainingEquipped[0].name, withoutEquippedOutfit.equippedOutfit);

let defensivePurchaseCharacter;
let containerPurchaseCharacter;
let stackedPurchaseCharacter;
for (let seed = 1; seed <= 5000 && (!defensivePurchaseCharacter || !containerPurchaseCharacter || !stackedPurchaseCharacter); seed += 1) {
    const candidate = rollCharacter(data, seededRandom(seed), {}, "core", 100);
    defensivePurchaseCharacter ||= candidate.purchasedGear.some((item) => item.gearCategory === "armor" || item.gearCategory === "shields") ? candidate : null;
    containerPurchaseCharacter ||= candidate.purchasedGear.some((item) => item.inventoryBonusTenths) ? candidate : null;
    stackedPurchaseCharacter ||= candidate.purchasedGear.some((item) => item.quantity > 1) ? candidate : null;
}
assert.ok(defensivePurchaseCharacter && containerPurchaseCharacter && stackedPurchaseCharacter);
const defensiveIndex = defensivePurchaseCharacter.purchasedGear.findIndex((item) => item.gearCategory === "armor" || item.gearCategory === "shields");
const defensiveItem = defensivePurchaseCharacter.purchasedGear[defensiveIndex];
const withoutDefensiveItem = removeGearItem(defensivePurchaseCharacter, "purchasedGear", defensiveIndex);
assert.equal(withoutDefensiveItem.modifiers.combat.defense.some((modifier) => modifier.kind === "gear" && modifier.source === defensiveItem.name), false);
const containerIndex = containerPurchaseCharacter.purchasedGear.findIndex((item) => item.inventoryBonusTenths);
const containerItem = containerPurchaseCharacter.purchasedGear[containerIndex];
const withoutContainer = removeGearItem(containerPurchaseCharacter, "purchasedGear", containerIndex);
assert.equal(withoutContainer.combat.inventory, containerPurchaseCharacter.combat.inventory - containerItem.inventoryBonusTenths / 10);
assert.equal(withoutContainer.modifiers.combat.inventory.some((modifier) => modifier.source === containerItem.name), false);
const stackedIndex = stackedPurchaseCharacter.purchasedGear.findIndex((item) => item.quantity > 1);
const stackedItem = stackedPurchaseCharacter.purchasedGear[stackedIndex];
const withoutStack = removeGearItem(stackedPurchaseCharacter, "purchasedGear", stackedIndex);
assert.equal(withoutStack.shopping.remainingStones, stackedPurchaseCharacter.shopping.remainingStones + stackedItem.unitCostStones * stackedItem.quantity);
assert.throws(() => removeGearItem(budgetCharacter, "gear", -1), RangeError);
assert.throws(() => removeGearItem(budgetCharacter, "unknown", 0), RangeError);

let weightedPurchaseCharacter;
for (let seed = 1; seed <= 1000 && !weightedPurchaseCharacter; seed += 1) {
    const candidate = rollCharacter(data, seededRandom(seed), {}, "core", 100, true);
    if (candidate.purchasedGear.length) weightedPurchaseCharacter = candidate;
}
assert.ok(weightedPurchaseCharacter);
const weightedPurchasedIndex = weightedPurchaseCharacter.purchasedGear.findIndex((item) => !item.inventoryBonusTenths);
const weightedPurchasedItem = weightedPurchaseCharacter.purchasedGear[weightedPurchasedIndex];
const weightedAfterRefund = removeGearItem(weightedPurchaseCharacter, "purchasedGear", weightedPurchasedIndex);
assert.equal(weightedAfterRefund.shopping.totalCurrencyStones,
    weightedPurchaseCharacter.shopping.totalCurrencyStones + weightedPurchasedItem.costStones);
assert.equal(weightedAfterRefund.shopping.currencySlotHundredths,
    currencyUnitCount(weightedAfterRefund.shopping.totalCurrencyStones));

let literalCurrencyCharacter;
for (let seed = 1; seed <= 5000 && !literalCurrencyCharacter; seed += 1) {
    const candidate = rollCharacter(data, seededRandom(seed), {}, "core", 0, true);
    if (candidate.gear.some((item) => item.currencyStones)) literalCurrencyCharacter = candidate;
}
assert.ok(literalCurrencyCharacter);
const literalCurrencyIndex = literalCurrencyCharacter.gear.findIndex((item) => item.currencyStones);
const literalCurrencyItem = literalCurrencyCharacter.gear[literalCurrencyIndex];
const withoutLiteralCurrency = removeGearItem(literalCurrencyCharacter, "gear", literalCurrencyIndex);
assert.equal(withoutLiteralCurrency.shopping.remainingStones, literalCurrencyCharacter.shopping.remainingStones);
assert.equal(withoutLiteralCurrency.shopping.totalCurrencyStones,
    literalCurrencyCharacter.shopping.totalCurrencyStones - literalCurrencyItem.currencyStones);
assert.equal(withoutLiteralCurrency.shopping.currencySlotHundredths,
    currencyUnitCount(withoutLiteralCurrency.shopping.totalCurrencyStones));

const purchaseCategoryLimits = {
    "Weapons": 2,
    "Armor": 1,
    "Shields": 1,
    "Outfits": 1,
    "Wearable Accessories": 2,
    "Wayfinding": 2,
    "Illumination": 1,
    "Specialist's Kits": 1,
    "Books": 2,
    "Consumables": 3,
    "Combustibles & Chemicals": 2,
    "Miscellaneous": 2,
    "Curiosities, Artifacts & Gadgets": 2,
};

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
const leisurelyFocus = fixedStrayCharacter.selections.find((selection) => selection.label === "Leisurely Focus");
assert.ok(leisurelyFocus);
assert.ok(fixedStrayCharacter.modifiers.aptitudes[leisurelyFocus.value.toLowerCase()]
    .some((modifier) => modifier.source === "Leisurely Focus" && modifier.amount === 1 && modifier.kind === "ability"));
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
    assert.ok(character.gear.every((item) => Object.hasOwn(item, "costStones")));
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
    const gearInventoryBonus = expectedCallingInventory
        ? 0
        : Math.max(0, ...[...character.gear, ...character.purchasedGear].map((item) => (item.inventoryBonusTenths || 0) / 10));
    assert.equal(character.combat.inventory, data.sizeRules[character.size.name].inventory + (character.species.name === "Dwarf" ? 2 : 0) + expectedCallingInventory + gearInventoryBonus);
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
    const usesDefenseAlternative = ["Brazen Defense", "Bulwark of Disdain"].includes(character.abilities.prodigy?.name)
        && expectedArmorBonus < 4;
    const gearDefenseModifiers = character.modifiers.combat.defense.filter((modifier) => modifier.kind === "gear");
    assert.equal(gearDefenseModifiers.reduce((total, modifier) => total + modifier.amount, 0), (usesDefenseAlternative ? 0 : expectedArmorBonus) + expectedShieldBonus);
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
    if (character.species.name === "Human, Native") {
        assert.equal(character.allegiance, character.abilities.prodigy.allegiance ? `1 ${character.abilities.prodigy.allegiance}` : "None");
    } else if (!["Tenebrate", "Promethean"].includes(character.species.name)) {
        assert.equal(character.allegiance, "None");
    }
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
            const suppressedByBrazenDefense = key === "defense"
                && character.abilities.prodigy?.name === "Brazen Defense"
                && expectedArmorBonus < 4;
            if (!suppressedByBrazenDefense) {
                assert.ok(character.modifiers.combat[key].some((modifier) => modifier.source === character.quirk.name && modifier.amount === quirkAdjustment[key]));
            }
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

let sawStackedPurchase = false;
let sawMultipleWeapons = false;
let sawPurchasedOutfitEquipped = false;
let sawStartingOutfitEquipped = false;
for (let seed = 1; seed <= 1000; seed += 1) {
    const [character] = rollCharacters(data, 1, seededRandom(seed), seed % 2 ? "core" : "expanded", 75);
    assert.equal(character.shopping.budgetCoins, 75);
    assert.ok(character.shopping.spentStones <= 7500);
    assert.ok(character.shopping.usedSlotsTenths <= character.shopping.capacityTenths);
    const allGear = [...character.gear, ...character.purchasedGear];
    const equipped = allGear.filter((item) => item.equipped);
    assert.equal(equipped.length, 1);
    assert.equal(equipped[0].name, character.equippedOutfit);
    assert.ok(equipped[0].category === "Outfits" || equipped[0].name === "Costume" || equipped[0].name.includes("Outfit"));
    const uniqueOutfits = allGear.filter((item) => item.name !== "Functional Outfit"
        && (item.category === "Outfits" || item.name === "Costume" || item.name.includes("Outfit")));
    if (uniqueOutfits.length) assert.notEqual(character.equippedOutfit, "Functional Outfit");
    assert.equal(character.shopping.usedSlotsTenths, allGear.reduce((total, item) => total + (item.equipped || item.stowed ? 0 : item.slotTenths), 0));
    assert.equal(character.shopping.startingSlotsTenths, character.gear.reduce((total, item) => total + (item.equipped || item.stowed ? 0 : item.slotTenths), 0));
    assert.equal(character.shopping.purchasedSlotsTenths, character.purchasedGear.reduce((total, item) => total + (item.equipped || item.stowed ? 0 : item.slotTenths), 0));
    sawPurchasedOutfitEquipped ||= character.purchasedGear.some((item) => item.equipped);
    sawStartingOutfitEquipped ||= character.gear.some((item) => item.equipped);
    assert.equal(new Set(character.purchasedGear.map((item) => item.name)).size, character.purchasedGear.length);
    assert.ok(character.purchasedGear.every((item) => !item.restricted));
    assert.ok(character.purchasedGear.length <= 8);
    const categoryCounts = character.purchasedGear.reduce((counts, item) => ({
        ...counts,
        [item.category]: (counts[item.category] || 0) + 1,
    }), {});
    for (const [category, count] of Object.entries(categoryCounts)) {
        assert.ok(count <= purchaseCategoryLimits[category]);
    }
    sawMultipleWeapons ||= (categoryCounts.Weapons || 0) > 1;
    if (character.gear.some((item) => item.gearCategory === "armor")) {
        assert.equal(character.purchasedGear.some((item) => item.category === "Armor"), false);
    }
    if (character.gear.some((item) => item.gearCategory === "shields")) {
        assert.equal(character.purchasedGear.some((item) => item.category === "Shields"), false);
    }
    for (const item of character.purchasedGear) {
        assert.ok(item.quantity >= 1 && item.quantity <= (data.shopItems.find((shopItem) => shopItem.name === item.name).stackLimit || 1));
        assert.equal(item.costStones, item.unitCostStones * item.quantity);
        assert.equal(item.slotTenths, item.unitSlotTenths * item.quantity);
        sawStackedPurchase ||= item.quantity > 1;
    }
    const carriedContainers = [...character.gear, ...character.purchasedGear].filter((item) => item.inventoryBonusTenths);
    if (character.calling.name === "Factotum") assert.equal(character.purchasedGear.some((item) => item.inventoryBonusTenths), false);
    assert.ok(character.calling.name === "Factotum" || carriedContainers.length <= 1);
}
assert.equal(sawStackedPurchase, true);
assert.equal(sawMultipleWeapons, true);
assert.equal(sawPurchasedOutfitEquipped, true);
assert.equal(sawStartingOutfitEquipped, true);

for (let seed = 1; seed <= 1000; seed += 1) {
    const [character] = rollCharacters(data, 1, seededRandom(seed), seed % 2 ? "core" : "expanded", 100, true);
    const gearSlotHundredths = [...character.gear, ...character.purchasedGear]
        .reduce((total, item) => total + (item.equipped || item.stowed ? 0 : item.slotTenths * 10), 0);
    assert.equal(character.shopping.currencySlotHundredths, currencyUnitCount(character.shopping.totalCurrencyStones));
    assert.equal(character.shopping.usedSlotHundredths, gearSlotHundredths + character.shopping.currencySlotHundredths);
    assert.ok(character.shopping.usedSlotHundredths <= character.shopping.capacityTenths * 10);
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
    const prodigyMotif = character.abilities.prodigy?.magical ? 1 : 0;
    const expectedBright = speciesBright + (selections["Allegiance Motif"] === "Light" ? 2 + prodigyMotif : 0);
    const expectedDark = speciesDark + (selections["Allegiance Motif"] === "Dark" ? 2 + prodigyMotif : 0);
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