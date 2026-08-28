const SPEEDS = ["Slow", "Average", "Fast"];
const MAX_PURCHASE_LINES = 8;
const SHOP_CATEGORY_LIMITS = {
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
const SEED_KEYS = [
    "calling",
    "species",
    "name",
    "homeland",
    "language",
    "history",
    "traits",
    "quirk",
    "callingChoices",
    "speciesChoices",
    "quirkChoices",
    "gear",
    "purchasedGear",
    "outfit",
    "coins",
];
const REROLL_DEPENDENCIES = {
    name: ["name"],
    calling: ["calling", "callingChoices"],
    species: ["species", "name"],
    language: ["language"],
    homeland: ["homeland", "language"],
    history: ["history"],
    traits: ["traits"],
    quirk: ["quirk", "quirkChoices"],
    choices: ["callingChoices", "speciesChoices", "quirkChoices"],
    gear: ["gear"],
    purchasedGear: ["purchasedGear"],
    coins: ["coins"],
};

export function rollDie(sides, random = Math.random) {
    return Math.floor(random() * sides) + 1;
}

function choose(values, random) {
    return values[rollDie(values.length, random) - 1];
}

function createSeed(random) {
    return Math.floor(random() * 0x100000000) >>> 0;
}

function seededRandom(seed) {
    let state = seed >>> 0;
    return () => {
        state = (state * 1664525 + 1013904223) >>> 0;
        return state / 0x100000000;
    };
}

function createSeeds(random, suppliedSeeds = {}) {
    return Object.fromEntries(SEED_KEYS.map((key) => [key, suppliedSeeds[key] ?? createSeed(random)]));
}

function chooseByRange(entries, roll) {
    const result = entries.find((entry) => roll >= entry.range[0] && roll <= entry.range[1]);
    if (!result) {
        throw new RangeError(`No table result for roll ${roll}`);
    }
    return result;
}

function rollByRange(entries, random) {
    for (let attempt = 0; attempt < 100; attempt += 1) {
        const roll = rollDie(20, random);
        const entry = entries.find((candidate) => roll >= candidate.range[0] && roll <= candidate.range[1]);
        if (entry) return { roll, entry };
    }
    throw new RangeError("No accepted table result after 100 rolls");
}

function sample(values, count, random) {
    const remaining = [...values];
    const selected = [];
    while (selected.length < count && remaining.length) {
        selected.push(remaining.splice(rollDie(remaining.length, random) - 1, 1)[0]);
    }
    return selected;
}

function titleCase(value) {
    return value.replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function shiftSpeed(speed, amount) {
    const currentIndex = SPEEDS.indexOf(speed);
    return SPEEDS[Math.max(0, Math.min(SPEEDS.length - 1, currentIndex + amount))];
}

function applyAptitudes(target, adjustments = {}) {
    Object.entries(adjustments).forEach(([aptitude, amount]) => {
        target[aptitude] += amount;
    });
}

function addModifier(modifiers, group, key, source, amount, kind = "delta") {
    modifiers[group][key].push({ source, amount, kind });
}

function evaluateGear(gear, calling, sizeRule) {
    const restrictions = [];
    if (gear.gearCategory && !calling.gearAllowance[gear.gearCategory].includes(gear.gearType)) {
        restrictions.push({
            source: calling.name,
            page: calling.gearAllowancePage,
            sourceUrl: calling.gearAllowanceSourceUrl || (!calling.gearAllowancePage ? calling.sourceUrl : undefined),
        });
    }
    if (gear.gearCategory && sizeRule.restricted[gear.gearCategory].includes(gear.gearType)) {
        restrictions.push({ source: `${sizeRule.name} Species`, page: sizeRule.page });
    }
    return { ...gear, restricted: restrictions.length > 0, restrictions };
}

function bestDefensiveGear(gear, category) {
    return gear
        .filter((item) => item.gearCategory === category && item.defenseBonus !== undefined)
        .sort((left, right) => right.defenseBonus - left.defenseBonus)[0] || null;
}

function sumGearValue(gear, key) {
    return gear.reduce((total, item) => total + (item[key] || 0), 0);
}

function currencyUnitCount(totalStones) {
    const gems = Math.floor(totalStones / 10000);
    const afterGems = totalStones % 10000;
    const coins = Math.floor(afterGems / 100);
    const stones = afterGems % 100;
    return gems + coins + stones;
}

function currencySummary(startingCoins, remainingStones, gear, currencyWeightEnabled) {
    const totalStones = startingCoins * 100 + remainingStones + sumGearValue(gear, "currencyStones");
    const slotHundredths = currencyWeightEnabled ? currencyUnitCount(totalStones) : 0;
    return { totalStones, slotHundredths };
}

function isOutfit(gear) {
    return gear.category === "Outfits" || gear.name === "Costume" || gear.name.includes("Outfit");
}

function equipOutfit(gear, purchasedGear, outfitRandom) {
    const allGear = [...gear, ...purchasedGear];
    const outfitCandidates = allGear.filter(isOutfit);
    const uniqueOutfitCandidates = outfitCandidates.filter((item) => item.name !== "Functional Outfit");
    const equippedOutfit = outfitCandidates.length
        ? choose(uniqueOutfitCandidates.length ? uniqueOutfitCandidates : outfitCandidates, outfitRandom)
        : null;
    const markEquipped = (item) => ({ ...item, equipped: item === equippedOutfit });
    return {
        gear: gear.map(markEquipped),
        purchasedGear: purchasedGear.map(markEquipped),
        equippedOutfit: equippedOutfit?.name || null,
    };
}

function rollPurchasedGear(data, budgetCoins, startingGear, calling, sizeRule, baseInventory, startingCoins, currencyWeightEnabled, random) {
    const safeBudgetCoins = Math.max(0, Math.trunc(Number(budgetCoins)) || 0);
    const budgetStones = safeBudgetCoins * 100;
    const startingSlotsTenths = sumGearValue(startingGear, "slotTenths");
    const fixedCurrencyStones = startingCoins * 100 + sumGearValue(startingGear, "currencyStones");
    const callingHasPack = calling.inventoryBonusSource === "Factotum Pack";
    const startingContainer = callingHasPack
        ? null
        : startingGear
            .filter((item) => item.inventoryBonusTenths)
            .sort((left, right) => right.inventoryBonusTenths - left.inventoryBonusTenths)[0] || null;
    const startingCapacityBonusTenths = startingContainer?.inventoryBonusTenths || 0;
    const startingNames = new Set(startingGear.map((item) => item.name));
    const blockedCategories = new Set();
    if (startingGear.some((item) => item.gearCategory === "armor")) blockedCategories.add("Armor");
    if (startingGear.some((item) => item.gearCategory === "shields")) blockedCategories.add("Shields");
    const candidates = safeBudgetCoins > 0
        ? data.shopItems
            .filter((item) => !startingNames.has(item.name) || item.stackLimit)
            .filter((item) => !blockedCategories.has(item.category))
            .map((item) => evaluateGear(item, calling, sizeRule))
            .filter((item) => !item.restricted && (!(callingHasPack || startingContainer) || !item.inventoryBonusTenths))
        : [];
    const purchasedGear = [];
    const categoryCounts = {};
    let spentStones = 0;
    let purchasedSlotsTenths = 0;
    let purchasedCapacityBonusTenths = 0;
    let categoryQueue = [];

    const itemFits = (item, quantity = 1) => {
        const hasPurchasedContainer = purchasedGear.some((item) => item.inventoryBonusTenths);
        if (hasPurchasedContainer && item.inventoryBonusTenths) return false;
        const projectedCapacity = baseInventory * 10 + startingCapacityBonusTenths
            + purchasedCapacityBonusTenths + (item.inventoryBonusTenths || 0);
        const projectedSpentStones = spentStones + item.costStones * quantity;
        const projectedGearSlotHundredths = (startingSlotsTenths + purchasedSlotsTenths + item.slotTenths * quantity) * 10;
        const projectedCurrencySlotHundredths = currencyWeightEnabled
            ? currencyUnitCount(fixedCurrencyStones + budgetStones - projectedSpentStones)
            : 0;
        return projectedSpentStones <= budgetStones
            && projectedGearSlotHundredths + projectedCurrencySlotHundredths <= projectedCapacity * 10;
    };

    while (candidates.length && purchasedGear.length < MAX_PURCHASE_LINES) {
        const availableCategories = [...new Set(candidates
            .filter((item) => itemFits(item))
            .filter((item) => (categoryCounts[item.category] || 0) < SHOP_CATEGORY_LIMITS[item.category])
            .map((item) => item.category))];
        if (!availableCategories.length) break;
        categoryQueue = categoryQueue.filter((category) => availableCategories.includes(category));
        if (!categoryQueue.length) {
            categoryQueue = sample(availableCategories.filter((category) => category !== "Weapons"), availableCategories.length, random);
            if (availableCategories.includes("Weapons")) {
                const firstWeaponPosition = Math.floor(random() * Math.min(4, categoryQueue.length + 1));
                categoryQueue.splice(firstWeaponPosition, 0, "Weapons");
                categoryQueue.splice(Math.min(categoryQueue.length, 5 + Math.floor(random() * 3)), 0, "Weapons");
            }
        }
        const category = categoryQueue.shift();
        const eligible = candidates.filter((item) => item.category === category && itemFits(item));
        if (!eligible.length) continue;
        const selected = choose(eligible, random);
        const maxByBudget = Math.floor((budgetStones - spentStones) / selected.costStones);
        const maxQuantity = Math.max(1, ...Array.from(
            { length: Math.min(selected.stackLimit || 1, maxByBudget) },
            (_, quantityIndex) => quantityIndex + 1,
        ).filter((quantity) => itemFits(selected, quantity)));
        const quantity = rollDie(maxQuantity, random);
        candidates.splice(candidates.indexOf(selected), 1);
        purchasedGear.push({
            ...selected,
            quantity,
            unitCostStones: selected.costStones,
            unitSlotTenths: selected.slotTenths,
            costStones: selected.costStones * quantity,
            slotTenths: selected.slotTenths * quantity,
        });
        categoryCounts[category] = (categoryCounts[category] || 0) + 1;
        spentStones += selected.costStones * quantity;
        purchasedSlotsTenths += selected.slotTenths * quantity;
        purchasedCapacityBonusTenths += selected.inventoryBonusTenths || 0;
    }

    return {
        gear: purchasedGear,
        budgetCoins: safeBudgetCoins,
        budgetStones,
        spentStones,
        remainingStones: budgetStones - spentStones,
        startingSlotsTenths,
        purchasedSlotsTenths,
        capacityBonusTenths: startingCapacityBonusTenths + purchasedCapacityBonusTenths,
        containerName: startingContainer?.name || purchasedGear.find((item) => item.inventoryBonusTenths)?.name || null,
    };
}

function resolveAllegiance(calling, species, selections) {
    let bright = species.name === "Promethean" ? 1 : 0;
    let dark = species.name === "Tenebrate" || species.name === "Neridian" ? 1 : 0;
    const henshinMotif = calling.name === "Henshin Hero"
        ? selections.find((selection) => selection.label === "Allegiance Motif")?.value
        : null;
    if (henshinMotif === "Light") bright += 2;
    if (henshinMotif === "Dark") dark += 2;
    const parts = [];
    if (bright) parts.push(`${bright} Bright`);
    if (dark) parts.push(`${dark} Dark`);
    return { bright, dark, label: parts.join(" / ") || "None" };
}

function traitAptitude(roll) {
    if (roll <= 4) return "might";
    if (roll <= 8) return "deftness";
    if (roll <= 13) return "grit";
    if (roll <= 16) return "insight";
    return "aura";
}

function reducedSize(size) {
    if (size === "Large") return "Medium";
    if (size === "Medium") return "Small";
    return "Small";
}

function rollName(data, species, random) {
    const tableRoll = rollDie(20, random);
    let tableName = species.nameTable;
    let result = chooseByRange(data.nameTables[tableName], tableRoll);
    const rolls = [{ table: tableName, roll: tableRoll }];

    if (result.name === "(Random name from another chart)") {
        do {
            tableName = chooseByRange(data.nameTableChart, rollDie(20, random)).name;
        } while (tableName === "Elf");
        const otherTableRoll = rollDie(20, random);
        result = chooseByRange(data.nameTables[tableName], otherTableRoll);
        rolls.push({ table: tableName, roll: otherTableRoll });
    }

    return { name: result.name, table: tableName, rolls };
}

function resolveNestedChoices(data, calling, species, quirk, streams) {
    const choices = [];

    if (calling.name === "Champion") {
        choices.push({ label: "Favored Weapon", value: choose(data.choices.weaponTypes, streams.callingChoices), page: 29 });
    }

    if (calling.name === "Bright-Heart Paladin") {
        choices.push({
            label: "Holy Sword",
            value: `${choose(data.choices.bladeWeaponTypes, streams.callingChoices)} / ${choose(data.choices.brightBladeMaterials, streams.callingChoices)}`,
            sourceUrl: calling.sourceUrl,
        });
        choices.push({ label: "Bonded Mount", value: "Guardian Animal / Mount", sourceUrl: calling.sourceUrl });
    }

    if (calling.name === "Haunted Knight") {
        choices.push({
            label: "Wrath's Blade",
            value: `${choose(data.choices.bladeWeaponTypes, streams.callingChoices)} / ${choose(data.choices.darkBladeMaterials, streams.callingChoices)}`,
            sourceUrl: calling.sourceUrl,
        });
    }

    if (calling.name === "Balladeer") {
        choices.push({ label: "Focus Instrument", value: "Player-defined", sourceUrl: calling.sourceUrl, rerollable: false });
        choices.push({ label: "Leitmotif", value: "Player-defined", sourceUrl: calling.sourceUrl, rerollable: false });
    }

    if (calling.name === "Henshin Hero") {
        const motifCount = rollDie(3, streams.callingChoices);
        const motifs = sample(data.choices.henshinMotifs, motifCount, streams.callingChoices);
        const allegianceMotif = choose(data.choices.henshinAllegianceMotifs, streams.callingChoices);
        const driverBenefits = sample(data.choices.henshinDriverBenefits, 2, streams.callingChoices);
        choices.push({ label: "Heroic Motifs", value: motifs.join(" / "), sourceUrl: calling.sourceUrl });
        choices.push({ label: "Allegiance Motif", value: allegianceMotif, sourceUrl: calling.sourceUrl });
        choices.push({ label: "Driver Benefits", value: driverBenefits.join(" / "), sourceUrl: calling.sourceUrl });
        if (driverBenefits.includes("Weapon")) {
            choices.push({ label: "Driver Weapon", value: choose(data.choices.henshinDriverWeapons, streams.callingChoices), sourceUrl: calling.sourceUrl });
        }
        choices.push({ label: "Primary Form", value: choose(data.choices.henshinForms, streams.callingChoices), sourceUrl: calling.sourceUrl });
        choices.push({ label: "Finisher Quality", value: choose(data.choices.henshinFinishers, streams.callingChoices), sourceUrl: calling.sourceUrl });
        choices.push({ label: "Hero / Form / Finisher Names", value: "Player-defined", sourceUrl: calling.sourceUrl, rerollable: false });
    }

    if (species.sizeOptions) {
        choices.push({ label: "Mundymutt Size", value: species.size, page: 403 });
    }

    if (calling.name === "Battle Princess" || calling.name === "Murder Princess") {
        const bright = calling.name === "Battle Princess";
        choices.push({
            label: bright ? "Heart's Blade" : "Wrath's Blade",
            value: `${choose(data.choices.bladeWeaponTypes, streams.callingChoices)} / ${choose(bright ? data.choices.brightBladeMaterials : data.choices.darkBladeMaterials, streams.callingChoices)}`,
            page: bright ? 41 : 51,
        });
    }

    if (calling.name === "Battle Princess") {
        const companionType = choose(data.choices.companionTypes, streams.callingChoices);
        const companionAbilities = companionType === "Guardian Animal"
            ? data.choices.animalCompanionAbilities
            : data.choices.toyCompanionAbilities;
        choices.push({ label: "Soul Companion", value: `${companionType} / ${choose(companionAbilities, streams.callingChoices)}`, pages: [47, 48] });
    }

    if (species.name === "Tenebrate") {
        choices.push({ label: "Dark Gift", value: choose(data.choices.darkGifts, streams.speciesChoices), page: 207 });
    }

    if (species.fixedGift) {
        choices.push({ label: "Gift", value: species.fixedGift, page: species.fixedGiftPage, rerollable: false });
    }

    if (species.name === "Unterkin") {
        choices.push({ label: "Heart's Craft", value: choose(data.choices.craftingDisciplines, streams.speciesChoices), sourceUrl: species.sourceUrl });
    }

    if (species.name === "Elf") {
        choices.push({ label: "Immortal Ego", value: choose(data.choices.ailments, streams.speciesChoices), pages: [103, 268] });
    }

    if (quirk.name === "Magitech Graft") {
        const graft = chooseByRange([
            { range: [1, 7], name: "Utility Servo", page: 145 },
            { range: [8, 15], name: "Sproing Sprockets", page: 145 },
            { range: [16, 20], name: "Nox-Vision", page: 147 },
        ], rollDie(20, streams.quirkChoices));
        choices.push({ label: "Magitech Graft", value: graft.name, page: graft.page });
        if (graft.name === "Utility Servo") {
            choices.push({ label: "Utility Servo", value: choose(data.choices.specialistKits, streams.quirkChoices), page: 176 });
        }
    }

    if (quirk.name === "Utility Servo") {
        choices.push({ label: "Utility Servo", value: choose(data.choices.specialistKits, streams.quirkChoices), page: 176 });
    }

    if (quirk.name === "Bioskin") {
        choices.push({ label: "Bioskin", value: choose(data.choices.bioskinSpecies, streams.quirkChoices), pages: quirk.pages });
    }

    if (quirk.name === "Figment Follower") {
        choices.push({ label: "Figment Follower", value: choose(data.choices.petNames, streams.quirkChoices), pages: quirk.pages });
    }

    const contextualChoices = {
        "Soul Link": ["Linked Character", "Player-defined"],
        "Guardian": ["Ward", "Team-dependent"],
        "Peculiar Taste": ["Alternative Nourishment", "Player-defined"],
        "Sneezles": ["Allergen", "Player-defined"],
    };
    if (contextualChoices[quirk.name]) {
        const [label, value] = contextualChoices[quirk.name];
        choices.push({ label, value, pages: quirk.pages, rerollable: false });
    }

    return choices;
}

function rollDistinctHistory(data, homelandName, currentHistory, random) {
    let history;
    do {
        history = chooseByRange(data.histories[homelandName], rollDie(20, random));
    } while (history.name === currentHistory.name);
    return history;
}

function resolveFinalSize(species, quirk) {
    if (quirk.name === "Young") return reducedSize(species.size);
    if (quirk.name === "Mascot Chassis") return "Small";
    return species.size;
}

function resolveHomeland(data, species, languageRandom, rolls) {
    if (species.name === "Human, Dimensional Stray") {
        return {
            homeland: { name: "Other World", page: 126 },
            language: "Other Wording",
        };
    }
    if (species.fixedHomeland) {
        const homeland = data.homelands.find((entry) => entry.name === species.fixedHomeland);
        return { homeland, language: choose(homeland.languages, languageRandom) };
    }
    const homeland = chooseByRange(data.homelands, rolls.homeland);
    return { homeland, language: choose(homeland.languages, languageRandom) };
}

export function rollCharacter(data, random = Math.random, suppliedSeeds = {}, contentMode = "core", gearBudgetCoins = 0, currencyWeightEnabled = false) {
    const seeds = createSeeds(random, suppliedSeeds);
    const streams = Object.fromEntries(SEED_KEYS.map((key) => [key, seededRandom(seeds[key])]));
    const speciesResult = contentMode === "expanded"
        ? rollByRange(data.expandedSpecies, streams.species)
        : { roll: rollDie(20, streams.species), entry: null };
    const speciesEntry = speciesResult.entry || chooseByRange(data.species, speciesResult.roll);
    const callingTable = speciesEntry.compatibleCallings
        ? data.expandedCallings.filter((calling) => speciesEntry.compatibleCallings.includes(calling.name))
        : data.expandedCallings;
    const callingResult = contentMode === "expanded"
        ? rollByRange(callingTable, streams.calling)
        : { roll: rollDie(20, streams.calling), entry: null };
    const rolls = {
        calling: callingResult.roll,
        species: speciesResult.roll,
    };
    const calling = callingResult.entry || chooseByRange(data.callings, rolls.calling);
    const species = {
        ...speciesEntry,
        size: speciesEntry.sizeOptions ? choose(speciesEntry.sizeOptions, streams.speciesChoices) : speciesEntry.size,
    };
    const rolledName = rollName(data, species, streams.name);
    rolls.name = rolledName.rolls;
    Object.assign(rolls, {
        homeland: species.name === "Human, Dimensional Stray" || species.fixedHomeland ? null : rollDie(20, streams.homeland),
        originPath: species.name === "Neridian" ? rollDie(2, streams.history) : null,
        history: rollDie(20, streams.history),
        positiveTraits: [rollDie(20, streams.traits), rollDie(20, streams.traits)],
        negativeTrait: rollDie(20, streams.traits),
        quirkCategory: rollDie(20, streams.quirk),
        quirk: rollDie(20, streams.quirk),
        coins: rollDie(20, streams.coins),
    });

    const useNeridianOrigin = species.name === "Neridian" && rolls.originPath === 1;
    const neridianHistory = useNeridianOrigin ? chooseByRange(data.neridianHistories, rolls.history) : null;
    const unterkinHistory = species.name === "Unterkin" ? chooseByRange(data.unterkinHistories, rolls.history) : null;
    const homelandResult = resolveHomeland(data, species, streams.language, rolls);
    const homeland = neridianHistory
        ? data.homelands.find((entry) => entry.name === neridianHistory.homeland)
        : homelandResult.homeland;
    const language = neridianHistory ? choose(homeland.languages, streams.language) : homelandResult.language;
    const history = unterkinHistory || neridianHistory || chooseByRange(data.histories[homeland.name], rolls.history);
    const quirkCategory = chooseByRange(data.quirkCategoryTables[species.quirkTable], rolls.quirkCategory);
    const quirk = chooseByRange(data.quirks[quirkCategory.name], rolls.quirk);
    const finalSize = resolveFinalSize(species, quirk);
    const sizeRule = { ...data.sizeRules[finalSize], name: finalSize };
    const modifiers = {
        aptitudes: Object.fromEntries(data.choices.aptitudes.map((aptitude) => [aptitude, []])),
        combat: { attack: [], hearts: [], defense: [], speed: [], inventory: [], allegiance: [] },
    };

    Object.entries(sizeRule.aptitudes).forEach(([aptitude, amount]) => {
        addModifier(modifiers, "aptitudes", aptitude, `${finalSize} Species`, amount, "species");
    });
    if (sizeRule.defense) {
        addModifier(modifiers, "combat", "defense", `${finalSize} Species`, sizeRule.defense, "species");
    }
    const sizeInventoryDelta = sizeRule.inventory - data.sizeRules.Medium.inventory;
    if (sizeInventoryDelta) {
        addModifier(modifiers, "combat", "inventory", `${finalSize} Species`, sizeInventoryDelta, "species");
    }
    if (species.inventoryBonus) {
        addModifier(modifiers, "combat", "inventory", species.inventoryBonusSource || species.name, species.inventoryBonus, "ability");
    }
    if (calling.inventoryBonus) {
        addModifier(modifiers, "combat", "inventory", calling.inventoryBonusSource || calling.name, calling.inventoryBonus, "ability");
    }

    const aptitudes = { ...calling.aptitudes };
    const traitTouched = new Set();
    const traits = [];
    rolls.positiveTraits.forEach((roll) => {
        const aptitude = traitAptitude(roll);
        traitTouched.add(aptitude);
        aptitudes[aptitude] += 1;
        traits.push({ aptitude, amount: 1, roll });
    });
    const negativeAptitude = traitAptitude(rolls.negativeTrait);
    traitTouched.add(negativeAptitude);
    aptitudes[negativeAptitude] -= 1;
    traits.push({ aptitude: negativeAptitude, amount: -1, roll: rolls.negativeTrait });

    applyAptitudes(aptitudes, sizeRule.aptitudes);

    const selections = resolveNestedChoices(data, calling, species, quirk, streams);
    const allegiance = resolveAllegiance(calling, species, selections);
    const allegianceGifts = [];
    for (let index = 0; index < Math.floor(allegiance.bright / 3); index += 1) {
        allegianceGifts.push({ label: "Allegiance Gift", value: `Bright: ${choose(data.choices.brightGifts, streams.callingChoices)}`, page: 206 });
    }
    for (let index = 0; index < Math.floor(allegiance.dark / 3); index += 1) {
        allegianceGifts.push({ label: "Allegiance Gift", value: `Dark: ${choose(data.choices.darkGifts, streams.callingChoices)}`, page: 207 });
    }
    selections.push(...allegianceGifts);
    allegianceGifts.forEach(() => addModifier(modifiers, "combat", "allegiance", "+1 Gift", 0, "gift"));
    if (species.name === "Human, Dimensional Stray") {
        const available = data.choices.aptitudes.filter((aptitude) => !traitTouched.has(aptitude));
        const focusedAptitude = choose(available, streams.speciesChoices);
        aptitudes[focusedAptitude] += 1;
        selections.push({ label: "Leisurely Focus", value: titleCase(focusedAptitude), page: 87 });
    }

    if (species.name === "Human, Native") {
        const elective = choose(data.callingAbilities[calling.name].standard, streams.speciesChoices);
        selections.push({ label: "Prodigy Ability", value: elective.name, pages: elective.pages });
        if (elective.name === "Crafting Prodigy") {
            selections.push({ label: "Crafting Discipline", value: choose(data.choices.craftingDisciplines, streams.speciesChoices), page: 17 });
        }
    }

    const quirkAdjustment = data.quirkAdjustments[quirk.name] || {};
    applyAptitudes(aptitudes, quirkAdjustment.aptitudes);
    Object.entries(quirkAdjustment.aptitudes || {}).forEach(([aptitude, amount]) => {
        addModifier(modifiers, "aptitudes", aptitude, quirk.name, amount);
    });
    if (quirkAdjustment.randomAptitudePenalty) {
        const aptitude = choose(data.choices.aptitudes, streams.quirkChoices);
        aptitudes[aptitude] += quirkAdjustment.randomAptitudePenalty;
        addModifier(modifiers, "aptitudes", aptitude, quirk.name, quirkAdjustment.randomAptitudePenalty);
        selections.push({ label: "Past Injury", value: titleCase(aptitude), page: 140 });
    }

    const bonusLanguages = [];
    if (quirkAdjustment.extraLanguages) {
        const known = new Set(["Low Speech", language]);
        const languagePool = [...new Set(data.homelands.flatMap((entry) => entry.languages).concat("Other Wording"))]
            .filter((entry) => !known.has(entry));
        bonusLanguages.push(...sample(languagePool, quirkAdjustment.extraLanguages, streams.language));
        selections.push({ label: "Bonus Languages", value: bonusLanguages.join(", "), page: 109 });
    }


    let attackBonus = calling.attack + (quirkAdjustment.attack || 0);
    if (quirkAdjustment.attack) addModifier(modifiers, "combat", "attack", quirk.name, quirkAdjustment.attack);
    let additionalHistory = null;
    const extraGear = [];
    if (quirk.name === "Weary") {
        if (rollDie(2, streams.quirkChoices) === 1) {
            attackBonus += 1;
            addModifier(modifiers, "combat", "attack", quirk.name, 1);
            const trustyWeapon = choose(data.choices.weaponTypes, streams.quirkChoices);
            const trustyWeaponData = data.shopItems.find((item) => item.gearCategory === "weapons" && item.gearType === trustyWeapon);
            selections.push({ label: "Weary Path", value: `Scarred Soul / ${trustyWeapon} Weapon`, pages: quirk.pages });
            extraGear.push({ ...trustyWeaponData, name: `${trustyWeapon} Weapon`, page: 152 });
        } else {
            additionalHistory = rollDistinctHistory(data, homeland.name, history, streams.quirkChoices);
            selections.push({ label: "Weary Path", value: `Walker of Two Paths / ${additionalHistory.name}`, page: additionalHistory.page });
            extraGear.push(...sample(additionalHistory.gear, 2, streams.gear));
        }
    }

    const gear = [
        ...sample(history.gear, 2, streams.gear),
        ...extraGear,
        data.shopItems.find((item) => item.name === "Functional Outfit"),
        data.shopItems.find((item) => item.name === "Standard Weapon"),
    ].map((item) => evaluateGear(item, calling, sizeRule));

    const baseInventory = sizeRule.inventory + (species.inventoryBonus || 0) + (calling.inventoryBonus || 0);
    const shopping = rollPurchasedGear(data, gearBudgetCoins, gear, calling, sizeRule, baseInventory, rolls.coins, currencyWeightEnabled, streams.purchasedGear);
    const equippedGear = equipOutfit(gear, shopping.gear, streams.outfit);
    const equippedOutfit = [...gear, ...shopping.gear].find((item) => item.name === equippedGear.equippedOutfit && isOutfit(item));
    const finalGear = equippedGear.gear;
    const purchasedGear = equippedGear.purchasedGear;
    const allGear = [...finalGear, ...purchasedGear];
    const equippedOutfitSlotsTenths = equippedOutfit.slotTenths || 0;
    const startingSlotsTenths = shopping.startingSlotsTenths - (gear.includes(equippedOutfit) ? equippedOutfitSlotsTenths : 0);
    const purchasedSlotsTenths = shopping.purchasedSlotsTenths - (shopping.gear.includes(equippedOutfit) ? equippedOutfitSlotsTenths : 0);
    const currency = currencySummary(rolls.coins, shopping.remainingStones, finalGear, currencyWeightEnabled);
    const gearSlotHundredths = (startingSlotsTenths + purchasedSlotsTenths) * 10;
    if (shopping.containerName) {
        addModifier(modifiers, "combat", "inventory", shopping.containerName, shopping.capacityBonusTenths / 10, "gear");
    }

    let defense = calling.defense + sizeRule.defense + (quirkAdjustment.defense || 0);
    if (quirkAdjustment.defense) addModifier(modifiers, "combat", "defense", quirk.name, quirkAdjustment.defense);
    if (quirkAdjustment.defenseSet !== undefined) defense = quirkAdjustment.defenseSet;
    if (quirkAdjustment.defenseSet !== undefined) {
        modifiers.combat.defense = modifiers.combat.defense.filter((modifier) => modifier.kind !== "species");
        addModifier(modifiers, "combat", "defense", quirk.name, quirkAdjustment.defenseSet, "set");
    }
    const armor = bestDefensiveGear(allGear, "armor");
    const shield = bestDefensiveGear(allGear, "shields");
    if (calling.name === "Bruiser") {
        const armorBonus = armor?.defenseBonus || 0;
        if (armorBonus < 4) {
            defense = calling.defense + sizeRule.defense + 4;
            modifiers.combat.defense = modifiers.combat.defense.filter((modifier) => modifier.kind !== "gear" && modifier.source !== quirk.name);
            addModifier(modifiers, "combat", "defense", "Brazen Defense", 4, "ability");
        }
    }
    for (const defensiveGear of [armor, shield].filter(Boolean)) {
        if (defensiveGear === armor && calling.name === "Bruiser" && armor.defenseBonus < 4) continue;
        defense += defensiveGear.defenseBonus;
        addModifier(modifiers, "combat", "defense", defensiveGear.name, defensiveGear.defenseBonus, "gear");
    }

    let speed = calling.speed;
    if (quirkAdjustment.speed) speed = shiftSpeed(speed, quirkAdjustment.speed);
    if (quirkAdjustment.speed) addModifier(modifiers, "combat", "speed", quirk.name, quirkAdjustment.speed);
    if (quirkAdjustment.hearts) addModifier(modifiers, "combat", "hearts", quirk.name, quirkAdjustment.hearts);

    const additionalQuirks = [];
    if ((quirk.name === "Young" && species.size === "Small") || quirk.name === "Mascot Chassis") {
        additionalQuirks.push({ name: "Adorable", page: 136 });
    }

    return {
        seeds,
        contentMode,
        currencyWeightEnabled: Boolean(currencyWeightEnabled),
        name: rolledName.name,
        nameTable: rolledName.table,
        rank: 1,
        rolls,
        calling: {
            name: calling.name,
            page: calling.page,
            sourceUrl: calling.sourceUrl,
            baseCalling: calling.baseCalling,
            expanded: calling.expanded || false,
        },
        species: {
            name: species.name,
            page: species.page,
            sourceUrl: species.sourceUrl,
            expanded: species.expanded || false,
        },
        size: { name: finalSize, page: sizeRule.page },
        homeland: { name: homeland.name, page: homeland.page },
        homelandRerollable: species.name !== "Human, Dimensional Stray" && !species.fixedHomeland && !neridianHistory,
        history: {
            name: history.name,
            tier: history.tier,
            page: history.page,
            sourceUrl: history.sourceUrl,
        },
        additionalHistory: additionalHistory && {
            name: additionalHistory.name,
            tier: additionalHistory.tier,
            page: additionalHistory.page,
        },
        languages: ["Low Speech", language, ...bonusLanguages],
        languageRerollable: species.name !== "Human, Dimensional Stray" || bonusLanguages.length > 0,
        traits,
        quirk: { name: quirk.name, category: quirkCategory.name, pages: quirk.pages },
        additionalQuirks,
        aptitudes,
        modifiers,
        combat: {
            attack: attackBonus,
            hearts: calling.hearts + (species.name === "Gruun" ? 1 : 0) + (quirkAdjustment.hearts || 0),
            defense,
            speed,
            inventory: baseInventory + shopping.capacityBonusTenths / 10,
        },
        allegiance: allegiance.label,
        abilities: {
            calling: data.callingAbilities[calling.name].starting,
            species: data.speciesAbilities[species.name],
        },
        selections,
        gear: finalGear,
        purchasedGear,
        equippedOutfit: equippedGear.equippedOutfit,
        shopping: {
            budgetCoins: shopping.budgetCoins,
            budgetStones: shopping.budgetStones,
            spentStones: shopping.spentStones,
            remainingStones: shopping.remainingStones,
            totalCurrencyStones: currency.totalStones,
            currencySlotHundredths: currency.slotHundredths,
            startingSlotsTenths,
            purchasedSlotsTenths,
            gearSlotHundredths,
            usedSlotHundredths: gearSlotHundredths + currency.slotHundredths,
            usedSlotsTenths: (gearSlotHundredths + currency.slotHundredths) / 10,
            capacityTenths: baseInventory * 10 + shopping.capacityBonusTenths,
        },
        coins: rolls.coins,
    };
}

export function removeGearItem(character, section, index) {
    if (!['gear', 'purchasedGear'].includes(section)) throw new RangeError(`Unknown gear section: ${section}`);
    if (!Number.isInteger(index) || index < 0 || index >= character[section].length) {
        throw new RangeError(`No ${section} item at index ${index}`);
    }

    const gear = section === "gear" ? character.gear.filter((_, itemIndex) => itemIndex !== index) : character.gear;
    const purchasedGear = section === "purchasedGear"
        ? character.purchasedGear.filter((_, itemIndex) => itemIndex !== index)
        : character.purchasedGear;
    const equippedGear = equipOutfit(gear, purchasedGear, seededRandom(character.seeds.outfit));
    const allGear = [...equippedGear.gear, ...equippedGear.purchasedGear];
    const startingSlotsTenths = sumGearValue(equippedGear.gear.filter((item) => !item.equipped), "slotTenths");
    const purchasedSlotsTenths = sumGearValue(equippedGear.purchasedGear.filter((item) => !item.equipped), "slotTenths");
    const spentStones = sumGearValue(equippedGear.purchasedGear, "costStones");
    const remainingStones = character.shopping.budgetStones - spentStones;
    const currency = currencySummary(character.coins, remainingStones, equippedGear.gear, character.currencyWeightEnabled);
    const gearSlotHundredths = (startingSlotsTenths + purchasedSlotsTenths) * 10;

    const inventoryModifiers = character.modifiers.combat.inventory.filter((modifier) => modifier.kind !== "gear");
    const previousContainerBonus = character.modifiers.combat.inventory
        .filter((modifier) => modifier.kind === "gear")
        .reduce((total, modifier) => total + modifier.amount, 0);
    const baseInventory = character.combat.inventory - previousContainerBonus;
    const factotumPack = inventoryModifiers.some((modifier) => modifier.source === "Factotum Pack");
    const activeContainer = factotumPack
        ? null
        : allGear.filter((item) => item.inventoryBonusTenths)
            .sort((left, right) => right.inventoryBonusTenths - left.inventoryBonusTenths)[0] || null;
    if (activeContainer) {
        inventoryModifiers.push({ source: activeContainer.name, amount: activeContainer.inventoryBonusTenths / 10, kind: "gear" });
    }

    const oldGearDefense = character.modifiers.combat.defense.filter((modifier) => modifier.kind === "gear");
    const oldBrazenDefense = character.modifiers.combat.defense.find((modifier) => modifier.source === "Brazen Defense");
    const defenseModifiers = character.modifiers.combat.defense
        .filter((modifier) => modifier.kind !== "gear" && modifier.source !== "Brazen Defense");
    let defense = character.combat.defense
        - oldGearDefense.reduce((total, modifier) => total + modifier.amount, 0)
        - (oldBrazenDefense?.amount || 0);
    const armor = bestDefensiveGear(allGear, "armor");
    const shield = bestDefensiveGear(allGear, "shields");
    const usesBrazenDefense = character.calling.name === "Bruiser" && (armor?.defenseBonus || 0) < 4;
    if (usesBrazenDefense) {
        defense += 4;
        defenseModifiers.push({ source: "Brazen Defense", amount: 4, kind: "ability" });
    }
    for (const defensiveGear of [armor, shield].filter(Boolean)) {
        if (defensiveGear === armor && usesBrazenDefense) continue;
        defense += defensiveGear.defenseBonus;
        defenseModifiers.push({ source: defensiveGear.name, amount: defensiveGear.defenseBonus, kind: "gear" });
    }

    const capacityTenths = baseInventory * 10 + (activeContainer?.inventoryBonusTenths || 0);
    return {
        ...character,
        gear: equippedGear.gear,
        purchasedGear: equippedGear.purchasedGear,
        equippedOutfit: equippedGear.equippedOutfit,
        modifiers: {
            ...character.modifiers,
            combat: {
                ...character.modifiers.combat,
                defense: defenseModifiers,
                inventory: inventoryModifiers,
            },
        },
        combat: {
            ...character.combat,
            defense,
            inventory: capacityTenths / 10,
        },
        shopping: {
            ...character.shopping,
            spentStones,
            remainingStones,
            totalCurrencyStones: currency.totalStones,
            currencySlotHundredths: currency.slotHundredths,
            startingSlotsTenths,
            purchasedSlotsTenths,
            gearSlotHundredths,
            usedSlotHundredths: gearSlotHundredths + currency.slotHundredths,
            usedSlotsTenths: (gearSlotHundredths + currency.slotHundredths) / 10,
            capacityTenths,
        },
    };
}

function componentSignature(character, target) {
    const signatures = {
        name: character.name,
        calling: character.calling.name,
        species: character.species.name,
        language: character.languages.join("|"),
        homeland: `${character.homeland.name}|${character.languages.join("|")}`,
        history: character.history.name,
        traits: character.traits.map((trait) => `${trait.aptitude}:${trait.amount}`).join("|"),
        quirk: character.quirk.name,
        choices: character.selections.map((selection) => `${selection.label}:${selection.value}`).join("|"),
        gear: character.gear.map((item) => `${item.option || 0}:${item.name}`).join("|"),
        purchasedGear: character.purchasedGear.map((item) => `${item.name}:${item.quantity}`).join("|"),
        coins: character.coins,
    };
    return JSON.stringify(signatures[target]);
}

export function rerollCharacter(data, character, target, random = Math.random) {
    const dependencies = REROLL_DEPENDENCIES[target];
    if (!dependencies) throw new RangeError(`Unknown reroll target: ${target}`);
    const previousSignature = componentSignature(character, target);
    let nextCharacter = character;
    for (let attempt = 0; attempt < 20; attempt += 1) {
        const seeds = { ...character.seeds };
        dependencies.forEach((key) => { seeds[key] = createSeed(random); });
        nextCharacter = rollCharacter(data, random, seeds, character.contentMode, character.shopping.budgetCoins, character.currencyWeightEnabled);
        if (componentSignature(nextCharacter, target) !== previousSignature) break;
    }
    return nextCharacter;
}

export function rollCharacters(data, count, random = Math.random, contentMode = "core", gearBudgetCoins = 0, currencyWeightEnabled = false) {
    const safeCount = Math.max(1, Math.min(12, Math.trunc(Number(count)) || 1));
    return Array.from({ length: safeCount }, () => rollCharacter(data, random, {}, contentMode, gearBudgetCoins, currencyWeightEnabled));
}
