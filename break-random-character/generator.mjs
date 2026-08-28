const SPEEDS = ["Slow", "Average", "Fast"];
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
        restrictions.push({ source: calling.name, page: calling.gearAllowancePage });
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
    const homeland = chooseByRange(data.homelands, rolls.homeland);
    return { homeland, language: choose(homeland.languages, languageRandom) };
}

export function rollCharacter(data, random = Math.random, suppliedSeeds = {}) {
    const seeds = createSeeds(random, suppliedSeeds);
    const streams = Object.fromEntries(SEED_KEYS.map((key) => [key, seededRandom(seeds[key])]));
    const rolls = {
        calling: rollDie(20, streams.calling),
        species: rollDie(20, streams.species),
    };
    const calling = chooseByRange(data.callings, rolls.calling);
    const species = chooseByRange(data.species, rolls.species);
    const rolledName = rollName(data, species, streams.name);
    rolls.name = rolledName.rolls;
    Object.assign(rolls, {
        homeland: species.name === "Human, Dimensional Stray" ? null : rollDie(20, streams.homeland),
        history: rollDie(20, streams.history),
        positiveTraits: [rollDie(20, streams.traits), rollDie(20, streams.traits)],
        negativeTrait: rollDie(20, streams.traits),
        quirkCategory: rollDie(20, streams.quirk),
        quirk: rollDie(20, streams.quirk),
        coins: rollDie(20, streams.coins),
    });

    const { homeland, language } = resolveHomeland(data, species, streams.language, rolls);
    const history = chooseByRange(data.histories[homeland.name], rolls.history);
    const quirkCategory = chooseByRange(data.quirkCategoryTables[species.quirkTable], rolls.quirkCategory);
    const quirk = chooseByRange(data.quirks[quirkCategory.name], rolls.quirk);
    const finalSize = resolveFinalSize(species, quirk);
    const sizeRule = { ...data.sizeRules[finalSize], name: finalSize };
    const speciesSizeRule = data.sizeRules[species.size];
    const modifiers = {
        aptitudes: Object.fromEntries(data.choices.aptitudes.map((aptitude) => [aptitude, []])),
        combat: { attack: [], hearts: [], defense: [], speed: [], inventory: [] },
    };

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

    if (finalSize !== species.size) {
        data.choices.aptitudes.forEach((aptitude) => {
            const amount = (sizeRule.aptitudes[aptitude] || 0) - (speciesSizeRule.aptitudes[aptitude] || 0);
            if (amount) addModifier(modifiers, "aptitudes", aptitude, quirk.name, amount);
        });
        const defenseAmount = sizeRule.defense - speciesSizeRule.defense;
        const inventoryAmount = sizeRule.inventory - speciesSizeRule.inventory;
        if (defenseAmount) addModifier(modifiers, "combat", "defense", quirk.name, defenseAmount);
        if (inventoryAmount) addModifier(modifiers, "combat", "inventory", quirk.name, inventoryAmount);
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
            selections.push({ label: "Weary Path", value: `Scarred Soul / ${trustyWeapon} Weapon`, pages: quirk.pages });
            extraGear.push({ name: `${trustyWeapon} Weapon`, page: 152, gearCategory: "weapons", gearType: trustyWeapon });
        } else {
            additionalHistory = rollDistinctHistory(data, homeland.name, history, streams.quirkChoices);
            selections.push({ label: "Weary Path", value: `Walker of Two Paths / ${additionalHistory.name}`, page: additionalHistory.page });
            extraGear.push(...sample(additionalHistory.gear, 2, streams.gear));
        }
    }

    const gear = [
        ...sample(history.gear, 2, streams.gear),
        ...extraGear,
        { name: "Functional Outfit", page: 172 },
        { name: "Standard Weapon", page: 152, gearCategory: "weapons", gearType: "Standard" },
    ].map((item) => evaluateGear(item, calling, sizeRule));

    let defense = calling.defense + sizeRule.defense + (quirkAdjustment.defense || 0);
    if (quirkAdjustment.defense) addModifier(modifiers, "combat", "defense", quirk.name, quirkAdjustment.defense);
    if (quirkAdjustment.defenseSet !== undefined) defense = quirkAdjustment.defenseSet;
    if (quirkAdjustment.defenseSet !== undefined) addModifier(modifiers, "combat", "defense", quirk.name, quirkAdjustment.defenseSet, "set");
    const armor = bestDefensiveGear(gear, "armor");
    const shield = bestDefensiveGear(gear, "shields");
    for (const defensiveGear of [armor, shield].filter(Boolean)) {
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
        name: rolledName.name,
        nameTable: rolledName.table,
        rank: 1,
        rolls,
        calling: { name: calling.name, page: calling.page },
        species: { name: species.name, page: species.page },
        size: { name: finalSize, page: sizeRule.page },
        homeland: { name: homeland.name, page: homeland.page },
        history: { name: history.name, tier: history.tier, page: history.page },
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
            inventory: sizeRule.inventory + (species.inventoryBonus || 0),
        },
        allegiance: species.name === "Tenebrate" ? "1 Dark" : species.name === "Promethean" ? "1 Bright" : "None",
        abilities: {
            calling: data.callingAbilities[calling.name].starting,
            species: data.speciesAbilities[species.name],
        },
        selections,
        gear,
        coins: rolls.coins,
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
        nextCharacter = rollCharacter(data, random, seeds);
        if (componentSignature(nextCharacter, target) !== previousSignature) break;
    }
    return nextCharacter;
}

export function rollCharacters(data, count, random = Math.random) {
    const safeCount = Math.max(1, Math.min(12, Math.trunc(Number(count)) || 1));
    return Array.from({ length: safeCount }, () => rollCharacter(data, random));
}
